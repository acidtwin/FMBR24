"""FM24 Save Editor - main window."""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QStatusBar, QFrame, QSizePolicy, QCheckBox, QMessageBox,
    QAbstractItemView, QMenu,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from gui.theme import COLORS
from fm_editor.cache import load_cache, save_cache, clear_cache

DEFAULT_SAVE_DIR = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c'
    '/users/steamuser/Documents/Sports Interactive/Football Manager 2024/games/'
)

NATIONS = {
    # Africa
    11:  'Egypt',         29:  'Morocco',      33:  'Nigeria',
    # Americas
    97:  'Canada',        120: 'USA',
    187: 'Argentina',     189: 'Brazil',       195: 'Uruguay',
    # Asia / Oceania
    61:  'Japan',         80:  'South Korea',  177: 'Australia',
    # Europe - Balkans / Eastern
    126: 'Albania',       129: 'Austria',      135: 'Croatia',
    146: 'Greece',        147: 'Hungary',      161: 'Poland',
    165: 'Russia',        176: 'Serbia',       219: 'Kosovo',
    # Europe - Western / Northern
    131: 'Belgium',       137: 'Czech Rep.',   138: 'Denmark',
    139: 'England',       143: 'France',       145: 'Germany',
    150: 'Italy',         158: 'Netherlands',  159: 'N.Ireland',
    160: 'Norway',        162: 'Portugal',     163: 'Rep.Ireland',
    167: 'Scotland',      170: 'Spain',        171: 'Sweden',
    172: 'Switzerland',   173: 'Turkey',       175: 'Wales',
}


POSITIONS = ['GK','SW','DL','DC','DR','DM','ML','MC','MR','AML','AMC','AMR','ST','WBL','WBR']
FM_SEASON_YEAR = 2024  # base year for age calculations


class _SortItem(QTableWidgetItem):
    """QTableWidgetItem with optional explicit sort key; numeric-aware fallback."""
    def __init__(self, text, sort_key=None):
        super().__init__(text)
        self._sk = sort_key  # None = use text
    def __lt__(self, other):
        a = self._sk if self._sk is not None else self.text()
        b = other._sk if isinstance(other, _SortItem) and other._sk is not None else other.text()
        try:
            return float(a) < float(b)
        except (ValueError, TypeError):
            return str(a) < str(b)


def _primary_pos(positions):
    return POSITIONS[positions.index(max(positions))]


def _progress_rate(person):
    """Development speed 1-20: ambition + professionalism + determination / 3."""
    personality = person.get('personality', [])
    raw_attrs = person.get('raw_attrs', [])
    if not personality or not raw_attrs:
        return None
    ambition = personality[1]           # index 55 in attrs.json, scale=1
    professionalism = personality[4]    # index 58 in attrs.json, scale=1
    det_raw = raw_attrs[51]             # determination, scale=5
    determination = max(1, min(20, round(det_raw / 5)))
    return round((ambition + professionalism + determination) / 3)


# -- Background worker ---------------------------------------------------------

class ParseWorker(QThread):
    progress = pyqtSignal(str)
    pct = pyqtSignal(int)
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, save_path):
        super().__init__()
        self.save_path = save_path

    def _emit(self, msg, p):
        self.progress.emit(msg)
        self.pct.emit(p)

    def run(self):
        try:
            from fm_editor.archive import parse_archive, get_member
            from fm_editor.gamedb import (find_names, find_clubs, find_squads,
                                          find_people, match_identities, find_abilities)
            from fm_editor.patch import is_homegrown

            cached = load_cache(self.save_path)
            if cached:
                self._emit("Loaded from cache.", 100)
                self.done.emit(cached)
                return

            self._emit("Parsing archive...", 3)
            header, members, index_marker, archive_name, subdir_count, subdirs = \
                parse_archive(self.save_path)

            gdb_m = next((m for m in members if m['name'] == 'game_db.dat'), None)
            if not gdb_m:
                self.error.emit("game_db.dat not found in archive.")
                return

            self._emit(
                f"Extracting game_db.dat ({gdb_m['p'] // 1024 // 1024} MB)...", 5)
            b = get_member(self.save_path, gdb_m)

            self._emit("Finding name tables...", 45)
            first_names, last_names, names_start, names_end = find_names(b)

            self._emit("Finding clubs...", 55)
            clubs = find_clubs(b, names_start)

            self._emit("Finding squad memberships...", 65)
            squads = find_squads(b, clubs, names_start)

            self._emit("Finding people and matching identities...", 72)
            people = find_people(b, first_names, last_names, names_end)
            match_identities(b, people, names_end)

            self._emit("Checking homegrown status...", 82)
            for p in people:
                p['hgp'] = is_homegrown(b, p)

            self._emit("Scanning abilities (CA/PA)...", 88)
            abilities = find_abilities(b, names_end)
            for p in people:
                ab = abilities.get(p.get('id', -1))
                if ab:
                    p['ca'] = ab['ca']
                    p['pa'] = ab['pa']
                    p['positions'] = ab['positions']
                    p['raw_attrs'] = ab['raw_attrs']

            self._emit("Caching results...", 97)
            save_cache(self.save_path, clubs, squads, people)

            self.pct.emit(100)
            result = {
                'clubs': clubs,
                'squads': squads,
                'people': people,
                'b': b,
                'header': header,
                'members': members,
                'index_marker': index_marker,
                'archive_name': archive_name,
                'subdir_count': subdir_count,
                'subdirs': subdirs,
            }
            self.done.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class PatchWorker(QThread):
    progress = pyqtSignal(str)
    pct = pyqtSignal(int)
    done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, save_data, output_path, people_to_patch, mode='hgp',
                 club_entity_id=None):
        super().__init__()
        self.save_data = save_data
        self.output_path = output_path
        self.people_to_patch = people_to_patch
        self.mode = mode
        self.club_entity_id = club_entity_id

    def run(self):
        try:
            from fm_editor.patch import patch_to_homegrown, patch_to_hgc
            from fm_editor.archive import write_archive

            b = self.save_data['b']
            count = 0
            n = len(self.people_to_patch)

            if self.mode == 'hgp':
                for i, person in enumerate(self.people_to_patch):
                    if patch_to_homegrown(b, person):
                        count += 1
                    self.pct.emit(5 + 5 * i // max(n, 1))
            else:  # hgc
                # Must process descending by end offset so insertions don't
                # invalidate earlier offsets
                ordered = sorted(self.people_to_patch,
                                 key=lambda p: p['end'], reverse=True)
                count = patch_to_hgc(b, ordered, self.club_entity_id)
                self.pct.emit(10)

            self.progress.emit(f"Patched {count} player(s). Writing file...")
            self.pct.emit(10)

            # Update the member's stored plain size in case insertions grew b
            members = self.save_data['members']
            gdb_m = next(m for m in members if m['name'] == 'game_db.dat')
            gdb_m['p'] = len(b)

            def _cb(msg, p):
                self.progress.emit(msg)
                self.pct.emit(10 + p * 90 // 100)

            write_archive(
                self.output_path,
                self.save_data['save_path'],
                self.save_data['header'],
                members,
                self.save_data['index_marker'],
                self.save_data['archive_name'],
                self.save_data['subdir_count'],
                self.save_data['subdirs'],
                {'game_db.dat': b},
                progress_cb=_cb,
            )
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))


# -- Main window ---------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FM24 Homegrown Editor')
        self.setMinimumSize(900, 620)
        self.resize(1100, 720)

        self._save_data = None      # holds parsed result dict
        self._squad = []            # current displayed squad list (people dicts)
        self._club_entity_id = None # HGC: entity ID for current squad's club
        self._worker = None
        self._status_base = ''      # message without animated dots
        self._dot_phase = 0

        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(420)
        self._dot_timer.timeout.connect(self._tick_dots)

        self._build_ui()
        self._update_ui_state()

    # -- UI construction -------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        title = QLabel('FM24 Homegrown Editor')
        title.setObjectName('header')
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        # File picker row
        file_row = QHBoxLayout()
        self._file_label = QLabel('No file selected')
        self._file_label.setObjectName('dim')
        self._file_label.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Preferred)
        self._pick_btn = QPushButton('Open Save File...')
        self._pick_btn.clicked.connect(self._pick_file)
        self._load_btn = QPushButton('Load / Reload')
        self._load_btn.clicked.connect(self._load_save)
        self._load_btn.setEnabled(False)
        file_row.addWidget(self._file_label)
        file_row.addWidget(self._pick_btn)
        file_row.addWidget(self._load_btn)
        layout.addLayout(file_row)

        # Progress bar (hidden until loading)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_lbl = QLabel('Search:')
        search_lbl.setObjectName('subheader')
        search_lbl.setFixedWidth(52)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('Search clubs or players...')
        self._search_box.setEnabled(False)
        self._search_box.returnPressed.connect(self._do_search)
        self._search_btn = QPushButton('Search')
        self._search_btn.clicked.connect(self._do_search)
        self._search_btn.setEnabled(False)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self._search_box)
        search_row.addWidget(self._search_btn)
        layout.addLayout(search_row)

        # Scout row
        scout_row = QHBoxLayout()
        scout_row.setSpacing(8)
        scout_lbl = QLabel('Scout:')
        scout_lbl.setObjectName('subheader')
        scout_lbl.setFixedWidth(52)
        self._scout_wonderkids_btn = QPushButton('Wonderkids')
        self._scout_wonderkids_btn.setToolTip('Under 21, PA ≥ 150 — sorted by PA')
        self._scout_wonderkids_btn.clicked.connect(self._scout_wonderkids)
        self._scout_wonderkids_btn.setEnabled(False)
        self._scout_high_pa_btn = QPushButton('High Potential')
        self._scout_high_pa_btn.setToolTip('PA ≥ 160, any age — sorted by PA')
        self._scout_high_pa_btn.clicked.connect(self._scout_high_potential)
        self._scout_high_pa_btn.setEnabled(False)
        self._pos_btn = QPushButton('Best by Position')
        self._pos_btn.setToolTip('Show top players by CA for a specific position')
        self._pos_btn.setEnabled(False)
        self._pos_btn.clicked.connect(self._show_pos_menu)
        scout_row.addWidget(scout_lbl)
        scout_row.addWidget(self._scout_wonderkids_btn)
        scout_row.addWidget(self._scout_high_pa_btn)
        scout_row.addWidget(self._pos_btn)
        scout_row.addStretch()
        layout.addLayout(scout_row)

        # Squad table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setEnabled(False)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_table_context_menu)
        self._configure_table_for_mode('squad')
        layout.addWidget(self._table)

        # Bottom action row
        action_row = QHBoxLayout()
        self._sel_hgp_btn = QPushButton('Select Non-HGP')
        self._sel_hgp_btn.setToolTip('Select all players without Homegrown Player (nation) status')
        self._sel_hgp_btn.clicked.connect(self._select_all_non_hgp)
        self._sel_hgp_btn.setEnabled(False)
        self._sel_hgc_btn = QPushButton('Select Non-HGC')
        self._sel_hgc_btn.setToolTip('Select all players without Homegrown at Club status')
        self._sel_hgc_btn.clicked.connect(self._select_all_non_hgc)
        self._sel_hgc_btn.setEnabled(False)
        self._clear_sel_btn = QPushButton('Clear Selection')
        self._clear_sel_btn.clicked.connect(self._table.clearSelection)
        self._clear_sel_btn.setEnabled(False)
        action_row.addWidget(self._sel_hgp_btn)
        action_row.addWidget(self._sel_hgc_btn)
        action_row.addWidget(self._clear_sel_btn)
        action_row.addStretch()

        self._squad_info = QLabel('')
        self._squad_info.setObjectName('dim')
        action_row.addWidget(self._squad_info)

        action_row.addSpacing(16)
        self._patch_hgp_btn = QPushButton('Make HGP')
        self._patch_hgp_btn.setObjectName('accent')
        self._patch_hgp_btn.setToolTip('Set selected players as Homegrown Player (nation / England)')
        self._patch_hgp_btn.clicked.connect(self._do_patch_hgp)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn = QPushButton('Make HGC')
        self._patch_hgc_btn.setObjectName('accent')
        self._patch_hgc_btn.setToolTip('Set selected players as Homegrown at Club (for UEFA registration)')
        self._patch_hgc_btn.clicked.connect(self._do_patch_hgc)
        self._patch_hgc_btn.setEnabled(False)
        action_row.addWidget(self._patch_hgp_btn)
        action_row.addWidget(self._patch_hgc_btn)
        layout.addLayout(action_row)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage('Open an FM24 save file to get started.')

        self._save_path = None

    def _configure_table_for_mode(self, mode):
        hdr = self._table.horizontalHeader()
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _TT = {  # column tooltip map reused across modes
            'CA':  'Current Ability (1–200): overall quality right now',
            'PA':  'Potential Ability (1–200): maximum this player can reach',
            'Dev': 'Development rate (1–20): predicted speed of improvement\n'
                   'Based on ambition, professionalism and determination',
            'Age': 'Age at start of FM24 season',
            'HGP': 'Homegrown Player (nation) — trained in England for ≥3 years\nbetween ages 15–21',
            'HGC': 'Homegrown at Club — trained at THIS club for ≥3 years\nbetween ages 15–21 (required for UEFA registration)',
        }
        if mode == 'squad':
            cols = ['Name', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'HGC']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for i in range(1, len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        elif mode == 'scout':
            cols = ['Name', 'Club', 'Pos', 'CA', 'PA', 'Dev', 'Age']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            for i in range(2, len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            self._table.setColumnWidth(1, 180)
        else:  # player
            cols = ['Name', 'Club', 'Nation', 'Born', 'HGP']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            for i in range(2, len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            self._table.setColumnWidth(1, 200)
        for i, col in enumerate(cols):
            if col in _TT:
                self._table.horizontalHeaderItem(i).setToolTip(_TT[col])
        self._table_mode = mode

    def closeEvent(self, event):
        if self._save_path:
            clear_cache(self._save_path)
        super().closeEvent(event)

    # -- State helpers ---------------------------------------------------------

    def _update_ui_state(self):
        has_file = bool(self._save_path)
        has_data = self._save_data is not None
        self._load_btn.setEnabled(has_file)
        self._search_box.setEnabled(has_data)
        self._search_btn.setEnabled(has_data)
        has_abilities = has_data and any(
            'ca' in p for p in self._save_data.get('people', []))
        self._scout_wonderkids_btn.setEnabled(has_abilities)
        self._scout_high_pa_btn.setEnabled(has_abilities)
        self._pos_btn.setEnabled(has_abilities)
        self._table.setEnabled(has_data)
        has_squad = bool(self._squad)
        has_b = has_data and 'b' in self._save_data
        self._sel_hgp_btn.setEnabled(has_squad)
        self._sel_hgc_btn.setEnabled(has_squad and has_b and self._club_entity_id is not None)
        self._clear_sel_btn.setEnabled(has_squad)
        has_sel = has_squad and bool(self._table.selectedItems())
        self._patch_hgp_btn.setEnabled(has_sel)
        self._patch_hgc_btn.setEnabled(has_sel and has_b and self._club_entity_id is not None)

    # -- File picker -----------------------------------------------------------

    def _pick_file(self):
        start_dir = DEFAULT_SAVE_DIR if os.path.isdir(DEFAULT_SAVE_DIR) else os.path.expanduser('~')
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open FM24 Save File', start_dir, 'FM Save Files (*.fm);;All Files (*)'
        )
        if path:
            self._save_path = path
            self._file_label.setText(os.path.basename(path))
            self._file_label.setToolTip(path)
            self._save_data = None
            self._squad = []
            self._table.setRowCount(0)
            self._squad_info.setText('')
            self._update_ui_state()
            self._status.showMessage(f'Selected: {os.path.basename(path)}')

    # -- Load / parse ----------------------------------------------------------

    def _load_save(self):
        if not self._save_path:
            return
        self._set_busy(True, 'Parsing save file...')
        self._worker = ParseWorker(self._save_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._progress.setValue)
        self._worker.done.connect(self._on_parse_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_parse_done(self, result):
        self._save_data = result
        self._save_data['save_path'] = self._save_path
        self._set_busy(False)
        n_clubs = len(result.get('clubs', []))
        self._status.showMessage(
            f"Loaded {n_clubs} clubs. Search for a team to view their squad.")
        self._update_ui_state()

    # -- Search ----------------------------------------------------------------

    def _do_search(self):
        if not self._save_data:
            return
        query = self._search_box.text().strip()
        if not query:
            return
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        query_l = query.lower()
        matches = [c for c in clubs if query_l in c['name'].lower()]
        if not matches:
            # Fall back to player name search
            people = self._save_data.get('people', [])
            player_matches = [p for p in people
                              if p.get('id', -1) != -1 and query_l in p['name'].lower()]
            if not player_matches:
                self._status.showMessage(f"No club or player matching '{query}'.")
                return
            player_matches.sort(key=lambda p: p['name'])
            self._show_player_results(player_matches)
            return
        if len(matches) == 1:
            self._show_squad(matches[0])
            return
        # Sort largest squad first so first team floats to the top
        squad_counts = {}
        for cid in squads.values():
            squad_counts[cid] = squad_counts.get(cid, 0) + 1
        matches.sort(key=lambda c: squad_counts.get(c['id'], 0), reverse=True)
        from PyQt6.QtWidgets import QInputDialog
        names = [c['name'] for c in matches]
        chosen, ok = QInputDialog.getItem(
            self, 'Multiple matches',
            f'{len(matches)} clubs match "{query}" - pick one:',
            names, 0, False)
        if ok:
            self._show_squad(matches[names.index(chosen)])

    def _show_squad(self, club):
        self._configure_table_for_mode('squad')
        squads = self._save_data.get('squads', {})
        people = self._save_data.get('people', [])

        club_pids = {pid for pid, cid in squads.items() if cid == club['id']}
        squad = [p for p in people if p.get('id', -1) in club_pids]
        squad.sort(key=lambda p: p['name'])
        self._squad = squad

        # Find club entity ID for HGC (needs b in memory)
        from fm_editor.patch import find_club_entity_id, is_hgc
        b = self._save_data.get('b')
        if b is not None:
            self._club_entity_id = find_club_entity_id(b, squad)
        else:
            self._club_entity_id = None

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(squad))
        self._table.clearSelection()

        for row, p in enumerate(squad):
            nation_name = NATIONS.get(p['nation'], f"n={p['nation']}")
            hgp = p.get('hgp', False)
            hgc = is_hgc(b, p, self._club_entity_id) if (b is not None and self._club_entity_id) else None
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            ca = p.get('ca')
            pa = p.get('pa')
            dev = _progress_rate(p)
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)

            name_item = _SortItem(p['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))

            hgc_text = ('HGC' if hgc else '-') if hgc is not None else '?'
            items = [
                name_item,
                _SortItem(pos),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(nation_name),
                _SortItem('HGP' if hgp else '-'),
                _SortItem(hgc_text),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 7:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgp
                                              else COLORS['text_dim']))
                elif col == 8:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgc
                                              else COLORS['text_dim']))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        n_hgc = sum(1 for p in squad
                    if b is not None and self._club_entity_id and is_hgc(b, p, self._club_entity_id))
        self._squad_info.setText(
            f"{club['name']}  ·  {len(squad)} players  ·  "
            f"{n_hgp} HGP  ·  {n_hgc} HGC")
        self._status.showMessage(f"Showing {club['name']} — {len(squad)} players")
        self._update_ui_state()
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _show_player_results(self, players):
        self._configure_table_for_mode('player')
        self._squad = []  # no squad in player mode - disable patch actions
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        # build person_id -> club_name lookup
        club_by_id = {c['id']: c['name'] for c in clubs}

        self._player_results = {p['id']: p for p in players}
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(players))
        self._table.clearSelection()

        for row, p in enumerate(players):
            club_id = squads.get(p['id'])
            club_name = club_by_id.get(club_id, '') if club_id else ''
            nation_name = NATIONS.get(p['nation'], f"n={p['nation']}")
            hgp = p.get('hgp', False)
            name_item = _SortItem(p['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item,
                _SortItem(club_name),
                _SortItem(nation_name),
                _SortItem(str(p.get('birth_year', '?')), p.get('birth_year', 0)),
                _SortItem('HGP' if hgp else '-'),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 4:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgp
                                              else COLORS['text_dim']))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
        self._squad_info.setText(f"{len(players)} players found")
        self._status.showMessage(f"{len(players)} players — double-click to view club squad")
        self._update_ui_state()

    def _on_row_double_clicked(self, index):
        if self._table_mode not in ('player', 'scout'):
            return
        item = self._table.item(index.row(), 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        player_results = getattr(self, '_player_results', {})
        if not isinstance(player_results, dict):
            return
        p = player_results.get(pid)
        if not p:
            return
        squads = self._save_data.get('squads', {})
        clubs = self._save_data.get('clubs', [])
        club_id = squads.get(p['id'])
        if not club_id:
            self._status.showMessage(f"{p['name']} has no club.")
            return
        club = next((c for c in clubs if c['id'] == club_id), None)
        if not club:
            self._status.showMessage(f"{p['name']}'s club not found.")
            return
        self._show_squad(club)

    # -- Scout views -----------------------------------------------------------

    def _show_scout_results(self, players, title):
        """Render scout mode table: Name, Club, Pos, CA, PA, Dev, Born."""
        self._configure_table_for_mode('scout')
        self._squad = []
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        club_by_id = {c['id']: c['name'] for c in clubs}
        self._player_results = {p['id']: p for p in players}
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(players))
        self._table.clearSelection()
        for row, p in enumerate(players):
            club_id = squads.get(p['id'])
            club_name = club_by_id.get(club_id, '') if club_id else ''
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            ca = p.get('ca')
            pa = p.get('pa')
            dev = _progress_rate(p)
            name_item = _SortItem(p['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item,
                _SortItem(club_name),
                _SortItem(pos),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(FM_SEASON_YEAR - p['birth_year']) if p.get('birth_year') else '?',
                          FM_SEASON_YEAR - p['birth_year'] if p.get('birth_year') else 0),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._table.setItem(row, col, item)
        self._table.setSortingEnabled(True)
        self._squad_info.setText(f"{title}  ·  {len(players)} players")
        self._status.showMessage(f"{title} — {len(players)} players shown — double-click to view club squad")
        self._update_ui_state()

    def _scout_wonderkids(self):
        if not self._save_data:
            return
        people = self._save_data.get('people', [])
        candidates = [p for p in people if p.get('ca') and p.get('birth_year', 0) >= 2003
                      and p.get('pa', 0) >= 150]
        candidates.sort(key=lambda p: -p['pa'])
        self._show_scout_results(candidates[:200], 'Wonderkids (≤21, PA≥150)')

    def _scout_high_potential(self):
        if not self._save_data:
            return
        people = self._save_data.get('people', [])
        candidates = [p for p in people if p.get('pa', 0) >= 160]
        candidates.sort(key=lambda p: -p['pa'])
        self._show_scout_results(candidates[:200], 'High Potential (PA≥160)')

    def _show_pos_menu(self):
        if not self._save_data:
            return
        menu = QMenu(self)
        for pos in POSITIONS:
            menu.addAction(pos)
        action = menu.exec(self._pos_btn.mapToGlobal(
            self._pos_btn.rect().bottomLeft()))
        if action:
            self._scout_best_by_pos(action.text())

    def _scout_best_by_pos(self, pos_name):
        if not self._save_data:
            return
        pos_idx = POSITIONS.index(pos_name)
        people = self._save_data.get('people', [])
        candidates = [p for p in people if p.get('positions')
                      and p['positions'][pos_idx] == max(p['positions'])]
        candidates.sort(key=lambda p: -p.get('ca', 0))
        self._show_scout_results(candidates[:200], f'Best {pos_name} (by CA)')

    def _on_table_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        name_col = 0
        item = self._table.item(row, name_col)
        if not item:
            return
        name = item.text()
        menu = QMenu(self)
        copy_action = menu.addAction(f'Copy name: {name}')
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == copy_action:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(name)
            self._status.showMessage(f'Copied: {name}')

    def _on_selection_changed(self):
        has_sel = bool(self._table.selectedItems())
        has_b = self._save_data is not None and 'b' in self._save_data
        self._patch_hgp_btn.setEnabled(bool(self._squad) and has_sel)
        self._patch_hgc_btn.setEnabled(bool(self._squad) and has_sel and has_b
                                        and self._club_entity_id is not None)

    def _select_all_non_hgp(self):
        id_to_hgp = {p.get('id', -1): p.get('hgp', False) for p in self._squad}
        self._table.clearSelection()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and not id_to_hgp.get(item.data(Qt.ItemDataRole.UserRole), True):
                self._table.selectRow(row)

    def _select_all_non_hgc(self):
        b = self._save_data.get('b') if self._save_data else None
        if b is None or not self._club_entity_id:
            return
        from fm_editor.patch import is_hgc
        id_to_person = {p.get('id', -1): p for p in self._squad}
        self._table.clearSelection()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if not item:
                continue
            pid = item.data(Qt.ItemDataRole.UserRole)
            person = id_to_person.get(pid)
            if person and not is_hgc(b, person, self._club_entity_id):
                self._table.selectRow(row)

    # -- Patch -----------------------------------------------------------------

    def _get_selected_persons(self):
        pid_map = {p.get('id', -1): p for p in self._squad}
        selected_rows = sorted({idx.row() for idx in self._table.selectedIndexes()})
        persons = []
        for r in selected_rows:
            pid = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole) if self._table.item(r, 0) else -1
            person = pid_map.get(pid)
            if person:
                persons.append(person)
        return persons

    def _do_patch_hgp(self):
        if not self._save_data or not self._squad:
            return

        people_to_patch = [p for p in self._get_selected_persons()
                           if not p.get('hgp', False)]
        if not people_to_patch:
            QMessageBox.information(self, 'Nothing to patch',
                                    'All selected players already have HGP status.')
            return

        if 'b' not in self._save_data:
            QMessageBox.warning(self, 'Reload required',
                                'Please click "Load / Reload" before patching.')
            return

        out_path = self._confirm_patch_dialog(people_to_patch, 'HGP')
        if not out_path:
            return

        self._set_busy(True, 'Patching HGP and writing...')
        self._worker = PatchWorker(self._save_data, out_path, people_to_patch, mode='hgp')
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._progress.setValue)
        self._worker.done.connect(self._on_patch_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _do_patch_hgc(self):
        if not self._save_data or not self._squad or not self._club_entity_id:
            return
        if 'b' not in self._save_data:
            QMessageBox.warning(self, 'Reload required',
                                'Please click "Load / Reload" before patching.')
            return

        from fm_editor.patch import is_hgc
        b = self._save_data['b']
        people_to_patch = [p for p in self._get_selected_persons()
                           if not is_hgc(b, p, self._club_entity_id)]
        if not people_to_patch:
            QMessageBox.information(self, 'Nothing to patch',
                                    'All selected players already have HGC status.')
            return

        out_path = self._confirm_patch_dialog(people_to_patch, 'HGC')
        if not out_path:
            return

        self._set_busy(True, 'Patching HGC and writing...')
        self._worker = PatchWorker(self._save_data, out_path, people_to_patch,
                                   mode='hgc', club_entity_id=self._club_entity_id)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._progress.setValue)
        self._worker.done.connect(self._on_patch_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _confirm_patch_dialog(self, people_to_patch, label):
        """Show output-file picker + confirm dialog. Return path or empty string."""
        orig = self._save_path
        suggested = orig.replace('.fm', f'_{label.lower()}.fm')
        out_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Patched File', suggested, 'FM Save Files (*.fm)')
        if not out_path:
            return ''

        names = ', '.join(p['name'] for p in people_to_patch[:5])
        if len(people_to_patch) > 5:
            names += f' ... (+{len(people_to_patch) - 5} more)'
        msg = QMessageBox(self)
        msg.setWindowTitle(f'Confirm {label} patch')
        msg.setText(
            f"Patch {len(people_to_patch)} player(s) as {label}?\n\n"
            f"{names}\n\n"
            f"Output: {os.path.basename(out_path)}\n\n"
            "This may take 30–60 seconds to recompress.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        return out_path if msg.exec() == QMessageBox.StandardButton.Ok else ''

    def _on_patch_done(self):
        self._set_busy(False)
        QMessageBox.information(
            self, 'Done',
            'File saved successfully.\n\n'
            'Load the new file in FM24. If it works, you can rename it '
            'over the original save.')
        self._status.showMessage('Patch complete.')

    # -- Progress / error ------------------------------------------------------

    def _tick_dots(self):
        self._dot_phase = (self._dot_phase + 1) % 4
        self._status.showMessage(self._status_base + '.' * self._dot_phase)

    def _on_progress(self, msg):
        self._status_base = msg
        self._dot_phase = 0
        self._status.showMessage(msg)

    def _on_error(self, msg):
        self._set_busy(False)
        QMessageBox.critical(self, 'Error', msg)
        self._status.showMessage(f'Error: {msg}')

    def _set_busy(self, busy, msg=''):
        if busy:
            self._progress.setValue(0)
            self._dot_phase = 0
            self._status_base = msg or self._status_base
            self._dot_timer.start()
        else:
            self._dot_timer.stop()
        self._progress.setVisible(busy)
        self._pick_btn.setEnabled(not busy)
        self._load_btn.setEnabled(not busy and bool(self._save_path))
        self._search_btn.setEnabled(not busy and self._save_data is not None)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn.setEnabled(False)
        if msg and not busy:
            self._status.showMessage(msg)
