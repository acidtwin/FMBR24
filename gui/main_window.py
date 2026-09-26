"""FM24 Save Editor — main window."""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QStatusBar, QFrame, QSizePolicy, QCheckBox, QMessageBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from gui.theme import COLORS
from fm_editor.cache import load_cache, save_cache

DEFAULT_SAVE_DIR = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c'
    '/users/steamuser/Documents/Sports Interactive/Football Manager 2024/games/'
)

NATIONS = {
    120: 'USA', 130: 'Belgium', 131: 'Croatia', 133: 'Denmark', 135: 'Germany',
    139: 'England', 142: 'France', 150: 'Italy', 153: 'N.Ireland', 155: 'Wales',
    158: 'Netherlands', 164: 'Netherlands', 167: 'Scotland', 171: 'Sweden',
    176: 'Serbia', 178: 'Portugal', 187: 'Argentina', 189: 'Brazil', 191: 'Spain',
    195: 'Uruguay',
}


# ── Background worker ─────────────────────────────────────────────────────────

class ParseWorker(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, save_path):
        super().__init__()
        self.save_path = save_path

    def run(self):
        try:
            from fm_editor.archive import parse_archive, get_member
            from fm_editor.gamedb import (find_names, find_clubs, find_squads,
                                          find_people, match_identities)
            from fm_editor.patch import is_homegrown

            cached = load_cache(self.save_path)
            if cached:
                self.progress.emit("Loaded from cache.")
                self.done.emit(cached)
                return

            self.progress.emit("Parsing archive...")
            header, members, index_marker, archive_name, subdir_count, subdirs = \
                parse_archive(self.save_path)

            gdb_m = next((m for m in members if m['name'] == 'game_db.dat'), None)
            if not gdb_m:
                self.error.emit("game_db.dat not found in archive.")
                return

            self.progress.emit(
                f"Extracting game_db.dat ({gdb_m['p'] // 1024 // 1024} MB)...")
            b = get_member(self.save_path, gdb_m)

            self.progress.emit("Finding name tables...")
            first_names, last_names, names_start, names_end = find_names(b)

            self.progress.emit("Finding clubs...")
            clubs = find_clubs(b, names_start)

            self.progress.emit("Finding squad memberships...")
            squads = find_squads(b, clubs, names_start)

            self.progress.emit("Finding people and matching identities...")
            people = find_people(b, first_names, last_names, names_end)
            match_identities(b, people, names_end)

            # Annotate HGP status into people list
            for p in people:
                p['hgp'] = is_homegrown(b, p)

            self.progress.emit("Caching results...")
            save_cache(self.save_path, clubs, squads, people)

            result = {
                'clubs': clubs,
                'squads': squads,
                'people': people,
                'b': b,  # keep bytearray in memory for patching
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
    done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, save_data, output_path, people_to_patch):
        super().__init__()
        self.save_data = save_data
        self.output_path = output_path
        self.people_to_patch = people_to_patch

    def run(self):
        try:
            from fm_editor.patch import patch_to_homegrown
            from fm_editor.archive import write_archive

            b = self.save_data['b']
            count = 0
            for person in self.people_to_patch:
                if patch_to_homegrown(b, person):
                    count += 1

            self.progress.emit(f"Patched {count} player(s). Writing file...")

            write_archive(
                self.output_path,
                self.save_data['save_path'],
                self.save_data['header'],
                self.save_data['members'],
                self.save_data['index_marker'],
                self.save_data['archive_name'],
                self.save_data['subdir_count'],
                self.save_data['subdirs'],
                {'game_db.dat': b},
                progress_cb=lambda msg: self.progress.emit(msg),
            )
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FM24 Homegrown Editor')
        self.setMinimumSize(900, 620)
        self.resize(1100, 720)

        self._save_data = None   # holds parsed result dict
        self._squad = []         # current displayed squad list (people dicts)
        self._worker = None

        self._build_ui()
        self._update_ui_state()

    # ── UI construction ───────────────────────────────────────────────────────

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
        self._progress.setRange(0, 0)   # indeterminate
        self._progress.setFixedHeight(4)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_lbl = QLabel('Team:')
        search_lbl.setObjectName('subheader')
        search_lbl.setFixedWidth(40)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('Search clubs...')
        self._search_box.setEnabled(False)
        self._search_box.returnPressed.connect(self._do_search)
        self._search_btn = QPushButton('Search')
        self._search_btn.clicked.connect(self._do_search)
        self._search_btn.setEnabled(False)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self._search_box)
        search_row.addWidget(self._search_btn)
        layout.addLayout(search_row)

        # Squad table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(['#', 'Name', 'Nation', 'Born', 'HGP'])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setEnabled(False)
        layout.addWidget(self._table)

        # Bottom action row
        action_row = QHBoxLayout()
        self._sel_all_btn = QPushButton('Select All Non-HGP')
        self._sel_all_btn.clicked.connect(self._select_all_non_hgp)
        self._sel_all_btn.setEnabled(False)
        self._clear_sel_btn = QPushButton('Clear Selection')
        self._clear_sel_btn.clicked.connect(self._table.clearSelection)
        self._clear_sel_btn.setEnabled(False)
        action_row.addWidget(self._sel_all_btn)
        action_row.addWidget(self._clear_sel_btn)
        action_row.addStretch()

        self._squad_info = QLabel('')
        self._squad_info.setObjectName('dim')
        action_row.addWidget(self._squad_info)

        action_row.addSpacing(16)
        self._patch_btn = QPushButton('Make Selected Homegrown')
        self._patch_btn.setObjectName('accent')
        self._patch_btn.clicked.connect(self._do_patch)
        self._patch_btn.setEnabled(False)
        action_row.addWidget(self._patch_btn)
        layout.addLayout(action_row)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage('Open an FM24 save file to get started.')

        self._save_path = None

    # ── State helpers ─────────────────────────────────────────────────────────

    def _update_ui_state(self):
        has_file = bool(self._save_path)
        has_data = self._save_data is not None
        self._load_btn.setEnabled(has_file)
        self._search_box.setEnabled(has_data)
        self._search_btn.setEnabled(has_data)
        self._table.setEnabled(has_data)
        has_squad = bool(self._squad)
        self._sel_all_btn.setEnabled(has_squad)
        self._clear_sel_btn.setEnabled(has_squad)
        # patch button enabled only when rows are selected
        self._patch_btn.setEnabled(has_squad and bool(self._table.selectedItems()))

    # ── File picker ───────────────────────────────────────────────────────────

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

    # ── Load / parse ──────────────────────────────────────────────────────────

    def _load_save(self):
        if not self._save_path:
            return
        self._set_busy(True, 'Parsing save file...')
        self._worker = ParseWorker(self._save_path)
        self._worker.progress.connect(self._on_progress)
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

    # ── Search ────────────────────────────────────────────────────────────────

    def _do_search(self):
        if not self._save_data:
            return
        query = self._search_box.text().strip()
        if not query:
            return
        clubs = self._save_data.get('clubs', [])
        matches = [c for c in clubs if query.lower() in c['name'].lower()]
        if not matches:
            self._status.showMessage(f"No club matching '{query}'.")
            return
        club = matches[0]
        self._show_squad(club)

    def _show_squad(self, club):
        squads = self._save_data.get('squads', {})
        people = self._save_data.get('people', [])

        club_pids = {pid for pid, cid in squads.items() if cid == club['id']}
        # squads keys may be str if loaded from JSON cache
        if not club_pids:
            club_pids = {pid for pid, cid in squads.items()
                         if cid == club['id'] or str(cid) == str(club['id'])}

        squad = [p for p in people
                 if str(p.get('id', -1)) in {str(x) for x in club_pids}
                 or p.get('id', -1) in club_pids]
        squad.sort(key=lambda p: p['name'])
        self._squad = squad

        self._table.setRowCount(len(squad))
        self._table.clearSelection()

        for row, p in enumerate(squad):
            nation_name = NATIONS.get(p['nation'], f"n={p['nation']}")
            hgp = p.get('hgp', False)

            items = [
                QTableWidgetItem(str(row + 1)),
                QTableWidgetItem(p['name']),
                QTableWidgetItem(nation_name),
                QTableWidgetItem(str(p.get('birth_year', '?'))),
                QTableWidgetItem('HGP' if hgp else '—'),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |
                                      (Qt.AlignmentFlag.AlignRight if col == 0
                                       else Qt.AlignmentFlag.AlignLeft))
                if col == 4:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgp
                                              else COLORS['text_dim']))
                self._table.setItem(row, col, item)

        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        self._squad_info.setText(
            f"{club['name']}  ·  {len(squad)} players  ·  "
            f"{n_hgp} HGP  ·  {len(squad) - n_hgp} non-HGP")
        self._status.showMessage(
            f"Showing {club['name']} — {len(squad)} players")
        self._update_ui_state()

        # connect selection change to enable/disable patch btn
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        has_sel = bool(self._table.selectedItems())
        self._patch_btn.setEnabled(bool(self._squad) and has_sel)

    def _select_all_non_hgp(self):
        self._table.clearSelection()
        for row, p in enumerate(self._squad):
            if not p.get('hgp', False):
                self._table.selectRow(row)

    # ── Patch ─────────────────────────────────────────────────────────────────

    def _do_patch(self):
        if not self._save_data or not self._squad:
            return

        selected_rows = sorted({idx.row() for idx in self._table.selectedIndexes()})
        people_to_patch = [self._squad[r] for r in selected_rows
                           if not self._squad[r].get('hgp', False)]

        if not people_to_patch:
            QMessageBox.information(self, 'Nothing to patch',
                                    'All selected players are already homegrown.')
            return

        # Prompt for output path
        orig = self._save_path
        suggested = orig.replace('.fm', '_homegrown.fm')
        out_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Patched File', suggested, 'FM Save Files (*.fm)')
        if not out_path:
            return

        names = ', '.join(p['name'] for p in people_to_patch[:5])
        if len(people_to_patch) > 5:
            names += f' ... (+{len(people_to_patch) - 5} more)'
        msg = QMessageBox(self)
        msg.setWindowTitle('Confirm patch')
        msg.setText(
            f"Patch {len(people_to_patch)} player(s) as homegrown?\n\n"
            f"{names}\n\n"
            f"Output: {os.path.basename(out_path)}\n\n"
            "This may take 30–60 seconds to recompress.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if msg.exec() != QMessageBox.StandardButton.Ok:
            return

        # Check if b (bytearray) is in save_data — cache loads don't include it
        if 'b' not in self._save_data:
            QMessageBox.warning(
                self, 'Reload required',
                'Please click "Load / Reload" before patching.\n'
                '(Cached session needs to reload game_db.dat into memory.)')
            return

        self._set_busy(True, 'Patching and writing...')
        self._worker = PatchWorker(self._save_data, out_path, people_to_patch)
        self._worker.progress.connect(self._on_progress)
        self._worker.done.connect(self._on_patch_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_patch_done(self):
        self._set_busy(False)
        QMessageBox.information(
            self, 'Done',
            'File saved successfully.\n\n'
            'Load the new file in FM24. If it works, you can rename it '
            'over the original save.')
        self._status.showMessage('Patch complete.')

    # ── Progress / error ──────────────────────────────────────────────────────

    def _on_progress(self, msg):
        self._status.showMessage(msg)

    def _on_error(self, msg):
        self._set_busy(False)
        QMessageBox.critical(self, 'Error', msg)
        self._status.showMessage(f'Error: {msg}')

    def _set_busy(self, busy, msg=''):
        self._progress.setVisible(busy)
        self._pick_btn.setEnabled(not busy)
        self._load_btn.setEnabled(not busy and bool(self._save_path))
        self._search_btn.setEnabled(not busy and self._save_data is not None)
        self._patch_btn.setEnabled(False)
        if msg:
            self._status.showMessage(msg)
