"""FM24 Save Editor - main window."""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QStatusBar, QFrame, QSizePolicy, QMessageBox,
    QAbstractItemView, QMenu, QStackedWidget, QDialog, QScrollArea,
    QComboBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QAction

from gui.theme import COLORS
from fm_editor.cache import load_cache, save_cache, clear_cache

DEFAULT_SAVE_DIR = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c'
    '/users/steamuser/Documents/Sports Interactive/Football Manager 2024/games/'
)

NATIONS = {
    11:  'Egypt',         29:  'Morocco',      33:  'Nigeria',
    97:  'Canada',        120: 'USA',
    187: 'Argentina',     189: 'Brazil',       195: 'Uruguay',
    61:  'Japan',         80:  'South Korea',  177: 'Australia',
    126: 'Albania',       129: 'Austria',      135: 'Croatia',
    146: 'Greece',        147: 'Hungary',      161: 'Poland',
    165: 'Russia',        176: 'Serbia',       219: 'Kosovo',
    131: 'Belgium',       137: 'Czech Rep.',   138: 'Denmark',
    139: 'England',       143: 'France',       145: 'Germany',
    150: 'Italy',         158: 'Netherlands',  159: 'N.Ireland',
    160: 'Norway',        162: 'Portugal',     163: 'Rep.Ireland',
    167: 'Scotland',      170: 'Spain',        171: 'Sweden',
    172: 'Switzerland',   173: 'Turkey',       175: 'Wales',
}

POSITIONS = ['GK','SW','DL','DC','DR','DM','ML','MC','MR','AML','AMC','AMR','ST','WBL','WBR']
FM_SEASON_YEAR = 2024

# -- SVG icon strings ----------------------------------------------------------

_SVG_SEARCH = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round">'
    '<circle cx="6.5" cy="6.5" r="4.5"/>'
    '<line x1="9.5" y1="9.5" x2="14" y2="14"/>'
    '</svg>'
)
_SVG_COG = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="8" cy="8" r="2.5"/>'
    '<path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2'
    'M3.55 3.55l1.41 1.41M11.04 11.04l1.41 1.41'
    'M3.55 12.45l1.41-1.41M11.04 4.96l1.41-1.41"/>'
    '</svg>'
)
_SVG_RELOAD = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2.5 8a5.5 5.5 0 1 0 1-3.2"/>'
    '<path d="M2.5 2v3h3"/>'
    '</svg>'
)
_SVG_CLUB = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="8" width="12" height="6" rx="1"/>'
    '<path d="M1 8h14M5 8V5.5M11 8V5.5M8 8V4.5M3 5.5h10"/>'
    '</svg>'
)
_SVG_SQUAD = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="5.5" cy="5" r="2.5"/>'
    '<path d="M1 14c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4"/>'
    '<circle cx="11.5" cy="5.5" r="2"/>'
    '<path d="M14.5 14c0-2-1.5-3.5-3-3.5"/>'
    '</svg>'
)
_SVG_STAFF = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="8" cy="5" r="3"/>'
    '<path d="M2 14c0-3 2.7-5 6-5s6 2 6 5"/>'
    '</svg>'
)
_SVG_SHORTLIST = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M8 2l1.6 3.2 3.5.5-2.5 2.5.6 3.5L8 10 4.8 11.7l.6-3.5L3 5.7l3.5-.5z"/>'
    '</svg>'
)
_SVG_REPORT = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="1" width="10" height="14" rx="1"/>'
    '<path d="M6 5h4M6 8h4M6 11h2"/>'
    '</svg>'
)


def _svg_icon(svg_tpl: str, color: str = '#8B96A8', size: int = 16) -> QIcon:
    """Render an SVG template string (with {c} color placeholder) to QIcon."""
    try:
        from PyQt6.QtSvg import QSvgRenderer
        svg_bytes = svg_tpl.replace('{c}', color).encode()
        renderer = QSvgRenderer(svg_bytes)
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        renderer.render(painter)
        painter.end()
        return QIcon(px)
    except Exception:
        return QIcon()


# -- Helpers -------------------------------------------------------------------

class _SortItem(QTableWidgetItem):
    def __init__(self, text, sort_key=None):
        super().__init__(text)
        self._sk = sort_key
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
    personality = person.get('personality', [])
    raw_attrs = person.get('raw_attrs', [])
    if not personality or not raw_attrs:
        return None
    ambition = personality[1]
    professionalism = personality[4]
    det_raw = raw_attrs[51]
    determination = max(1, min(20, round(det_raw / 5)))
    return round((ambition + professionalism + determination) / 3)


# -- Background workers --------------------------------------------------------

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

            self._emit(f"Extracting game_db.dat ({gdb_m['p'] // 1024 // 1024} MB)...", 5)
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
                'clubs': clubs, 'squads': squads, 'people': people,
                'b': b, 'header': header, 'members': members,
                'index_marker': index_marker, 'archive_name': archive_name,
                'subdir_count': subdir_count, 'subdirs': subdirs,
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
            else:
                ordered = sorted(self.people_to_patch,
                                 key=lambda p: p['end'], reverse=True)
                count = patch_to_hgc(b, ordered, self.club_entity_id)
                self.pct.emit(10)

            self.progress.emit(f"Patched {count} player(s). Writing file...")
            self.pct.emit(10)

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


# -- Player detail modal -------------------------------------------------------

class PlayerDetailDialog(QDialog):
    def __init__(self, person, save_data, club_entity_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(person['name'])
        self.setMinimumSize(700, 520)
        self.resize(780, 580)
        self._person = person
        self._save_data = save_data
        self._club_entity_id = club_entity_id
        self._build()

    def _build(self):
        p = self._person
        b = self._save_data.get('b') if self._save_data else None
        from fm_editor.patch import is_hgc as _is_hgc

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Modal top bar
        topbar = QFrame()
        topbar.setFixedHeight(40)
        topbar.setStyleSheet(f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        tb_row = QHBoxLayout(topbar)
        tb_row.setContentsMargins(14, 0, 12, 0)
        name_lbl = QLabel(p['name'])
        name_lbl.setStyleSheet(f"color:{COLORS['text_primary']}; font-size:14px; font-weight:bold;")
        tb_row.addWidget(name_lbl)
        tb_row.addStretch()
        close_btn = QPushButton('Close')
        close_btn.setFixedHeight(26)
        close_btn.clicked.connect(self.accept)
        tb_row.addWidget(close_btn)
        layout.addWidget(topbar)

        # Body
        body = QWidget()
        body.setStyleSheet(f"background:{COLORS['window_bg']};")
        body_row = QHBoxLayout(body)
        body_row.setContentsMargins(16, 16, 16, 16)
        body_row.setSpacing(16)

        # Left panel: personal info + CA/PA + HGP/HGC
        left = QFrame()
        left.setFixedWidth(200)
        left.setStyleSheet(f"background:{COLORS['surface']}; border:1px solid {COLORS['border']}; border-radius:3px;")
        left_vbox = QVBoxLayout(left)
        left_vbox.setContentsMargins(12, 14, 12, 14)
        left_vbox.setSpacing(6)

        nation_name = NATIONS.get(p['nation'], f"n={p['nation']}")
        age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
        pos = _primary_pos(p['positions']) if p.get('positions') else '?'

        for txt, color in [
            (pos, COLORS['text_secondary']),
            (nation_name, COLORS['text_secondary']),
            (f"Age {age}", COLORS['text_dim']),
            (f"Born {p.get('birth_year', '?')}", COLORS['text_dim']),
        ]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color:{color}; font-size:12px;")
            left_vbox.addWidget(lbl)

        left_vbox.addSpacing(8)

        # CA / PA bars
        ca = p.get('ca')
        pa = p.get('pa')
        for label, val, color in [
            ('CA', ca, COLORS['accent_hover']),
            ('PA', pa, COLORS['hgp_green']),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(26)
            lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
            val_lbl = QLabel(str(val) if val else '?')
            val_lbl.setFixedWidth(30)
            val_lbl.setStyleSheet(f"color:{color}; font-size:11px; font-weight:bold;")
            bar = QFrame()
            bar.setFixedHeight(4)
            pct = int((val or 0) / 200 * 100)
            bar.setStyleSheet(
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
                f" stop:0 {color}, stop:{pct/100:.2f} {color},"
                f" stop:{pct/100:.2f} {COLORS['border']},"
                f" stop:1 {COLORS['border']});"
                "border-radius:2px;"
            )
            row.addWidget(lbl)
            row.addWidget(val_lbl)
            row.addWidget(bar, 1)
            left_vbox.addLayout(row)

        left_vbox.addSpacing(10)

        # HGP / HGC pills
        hgp = p.get('hgp', False)
        hgc = _is_hgc(b, p, self._club_entity_id) if (b and self._club_entity_id) else None

        for label, active, color in [
            ('HGP', hgp, COLORS['hgp_green']),
            ('HGC', hgc, COLORS['hgp_green']),
        ]:
            pill = QLabel(label)
            if active:
                pill.setStyleSheet(
                    f"color:{COLORS['window_bg']}; background:{color};"
                    "border-radius:3px; padding:2px 8px; font-size:11px; font-weight:bold;")
            elif active is False:
                pill.setStyleSheet(
                    f"color:{COLORS['text_dim']}; background:{COLORS['elevated']};"
                    f"border:1px solid {COLORS['border']};"
                    "border-radius:3px; padding:2px 8px; font-size:11px;")
            else:
                pill.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
                pill.setText(f"{label}: ?")
            left_vbox.addWidget(pill)

        left_vbox.addStretch()
        body_row.addWidget(left)

        # Center: attributes
        attrs_scroll = QScrollArea()
        attrs_scroll.setWidgetResizable(True)
        attrs_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        attrs_widget = QWidget()
        attrs_widget.setStyleSheet(f"background:{COLORS['window_bg']};")
        attrs_vbox = QVBoxLayout(attrs_widget)
        attrs_vbox.setContentsMargins(0, 0, 8, 0)
        attrs_vbox.setSpacing(10)

        raw = p.get('raw_attrs', [])
        personality = p.get('personality', [])

        def _display_val(raw_v, scale=5):
            return max(1, min(20, round(raw_v / scale)))

        def _val_color(v):
            if v >= 17: return '#52C287'
            if v >= 13: return COLORS['hgp_green']
            if v >= 9:  return COLORS['text_primary']
            if v >= 5:  return COLORS['text_secondary']
            return COLORS['non_hgp_red']

        ATTR_GROUPS = [
            ('Technical', [
                ('Crossing', 0), ('Dribbling', 1), ('Finishing', 2), ('Heading', 3),
                ('Long Shots', 4), ('Marking', 5), ('Off Ball', 6), ('Passing', 7),
                ('Pen Taking', 8), ('Tackling', 9), ('Vision', 10),
                ('First Touch', 22), ('Technique', 23), ('Corners', 27),
                ('Long Throws', 30), ('Free Kick', 35),
            ]),
            ('Mental', [
                ('Anticipation', 17), ('Decisions', 18), ('Positioning', 20),
                ('Teamwork', 28), ('Work Rate', 29), ('Leadership', 40),
                ('Bravery', 43), ('Consistency', 44), ('Aggression', 45),
                ('Important Matches', 47), ('Composure', 52), ('Concentration', 53),
            ]),
            ('Physical', [
                ('Acceleration', 34), ('Pace', 38), ('Strength', 36), ('Stamina', 37),
                ('Balance', 42), ('Agility', 46), ('Jumping Reach', 39),
                ('Natural Fitness', 50),
            ]),
            ('Personality', None),  # special - uses personality[]
        ]

        PERSONALITY_ATTRS = [
            ('Adaptability', 0), ('Ambition', 1), ('Loyalty', 2), ('Pressure', 3),
            ('Professionalism', 4), ('Sportsmanship', 5), ('Temperament', 6),
        ]

        for group_name, group_attrs in ATTR_GROUPS:
            grp_frame = QFrame()
            grp_frame.setStyleSheet(
                f"background:{COLORS['surface']}; border:1px solid {COLORS['border']};"
                "border-radius:3px;")
            grp_vbox = QVBoxLayout(grp_frame)
            grp_vbox.setContentsMargins(10, 8, 10, 8)
            grp_vbox.setSpacing(3)

            grp_lbl = QLabel(group_name.upper())
            grp_lbl.setStyleSheet(
                f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:1px;")
            grp_vbox.addWidget(grp_lbl)

            if group_name == 'Personality':
                items = PERSONALITY_ATTRS
                for attr_name, idx in items:
                    if not personality or idx >= len(personality):
                        continue
                    v = personality[idx]
                    row = QHBoxLayout()
                    row.setSpacing(0)
                    n_lbl = QLabel(attr_name)
                    n_lbl.setFixedWidth(130)
                    n_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
                    v_lbl = QLabel(str(v))
                    v_lbl.setFixedWidth(28)
                    v_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    v_lbl.setStyleSheet(f"color:{_val_color(v)}; font-size:12px; font-weight:bold;")
                    row.addWidget(n_lbl)
                    row.addStretch()
                    row.addWidget(v_lbl)
                    grp_vbox.addLayout(row)
            else:
                if not raw:
                    continue
                cols_layout = QHBoxLayout()
                cols_layout.setSpacing(12)
                col1 = QVBoxLayout()
                col2 = QVBoxLayout()
                for i, (attr_name, idx) in enumerate(group_attrs):
                    if idx >= len(raw):
                        continue
                    v = _display_val(raw[idx])
                    row = QHBoxLayout()
                    row.setSpacing(0)
                    n_lbl = QLabel(attr_name)
                    n_lbl.setFixedWidth(100)
                    n_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
                    v_lbl = QLabel(str(v))
                    v_lbl.setFixedWidth(28)
                    v_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    v_lbl.setStyleSheet(f"color:{_val_color(v)}; font-size:12px; font-weight:bold;")
                    row.addWidget(n_lbl)
                    row.addStretch()
                    row.addWidget(v_lbl)
                    if i % 2 == 0:
                        col1.addLayout(row)
                    else:
                        col2.addLayout(row)
                cols_layout.addLayout(col1)
                cols_layout.addLayout(col2)
                grp_vbox.addLayout(cols_layout)

            attrs_vbox.addWidget(grp_frame)

        attrs_vbox.addStretch()
        attrs_scroll.setWidget(attrs_widget)
        body_row.addWidget(attrs_scroll, 1)

        layout.addWidget(body)

        # Footer action row
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(
            f"background:{COLORS['elevated']}; border-top:1px solid {COLORS['border']};")
        foot_row = QHBoxLayout(footer)
        foot_row.setContentsMargins(14, 0, 14, 0)
        foot_row.setSpacing(8)
        foot_row.addStretch()

        if b is not None:
            if not hgp:
                make_hgp = QPushButton('Make HGP')
                make_hgp.setObjectName('accent')
                make_hgp.clicked.connect(lambda: (self._emit_patch('hgp'), self.accept()))
                foot_row.addWidget(make_hgp)
            if hgc is False and self._club_entity_id:
                make_hgc = QPushButton('Make HGC')
                make_hgc.setObjectName('accent')
                make_hgc.clicked.connect(lambda: (self._emit_patch('hgc'), self.accept()))
                foot_row.addWidget(make_hgc)

        layout.addWidget(footer)

        self._patch_mode = None

    def _emit_patch(self, mode):
        self._patch_mode = mode


# -- Main window ---------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FM24 Homegrown Editor')
        self.setMinimumSize(1000, 660)
        self.resize(1200, 780)

        self._save_data = None
        self._squad = []
        self._club_entity_id = None
        self._worker = None
        self._current_club = None
        self._shortlist = []
        self._status_base = ''
        self._dot_phase = 0
        self._table_mode = 'squad'

        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(420)
        self._dot_timer.timeout.connect(self._tick_dots)

        self._build_ui()
        self._update_ui_state()

    # -- UI construction -------------------------------------------------------

    def _make_hline(self):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{COLORS['border']};")
        return line

    def _make_nav_btn(self, svg_tpl: str, label: str, callback) -> QPushButton:
        btn = QPushButton(f'  {label}')
        btn.setCheckable(True)
        btn.setIcon(_svg_icon(svg_tpl, COLORS['text_secondary'], 15))
        btn.setIconSize(QSize(15, 15))
        btn.clicked.connect(callback)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_secondary']};
                text-align: left;
                padding: 7px 15px;
                font-size: 12px;
                border-radius: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['border']};
                color: {COLORS['text_primary']};
            }}
            QPushButton:checked {{
                background: {COLORS['selection_bg']};
                color: {COLORS['text_primary']};
                font-weight: bold;
            }}
        """)
        return btn

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:10px; "
            "letter-spacing:1px; padding:6px 15px 4px;"
        )
        return lbl

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._make_topbar())

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background:{COLORS['elevated']}; border:none; }}
            QProgressBar::chunk {{ background:{COLORS['accent']}; }}
        """)
        vbox.addWidget(self._progress)

        shell = QWidget()
        shell_hbox = QHBoxLayout(shell)
        shell_hbox.setContentsMargins(0, 0, 0, 0)
        shell_hbox.setSpacing(0)
        shell_hbox.addWidget(self._make_sidebar())

        self._main_stack = QStackedWidget()
        self._main_stack.addWidget(self._make_view_club())       # 0
        self._main_stack.addWidget(self._make_view_squad())      # 1
        self._main_stack.addWidget(self._make_view_staff())      # 2
        self._main_stack.addWidget(self._make_view_shortlist())  # 3
        shell_hbox.addWidget(self._main_stack)
        vbox.addWidget(shell)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage('Open an FM24 save file to get started.')
        self._save_path = None

    def _make_topbar(self):
        bar = QFrame()
        bar.setObjectName('topbar')
        bar.setFixedHeight(42)
        bar.setStyleSheet(f"""
            QFrame#topbar {{
                background: {COLORS['elevated']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Centred search
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('Search players, clubs, nations...')
        self._search_box.setEnabled(False)
        self._search_box.returnPressed.connect(self._do_search)
        self._search_box.setFixedHeight(28)
        self._search_box.setMaximumWidth(440)
        self._search_box.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['window_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
                padding: 4px 10px 4px 10px;
                font-size: 12px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; outline: none; }}
            QLineEdit:disabled {{ color: {COLORS['text_dim']}; }}
        """)
        search_action = QAction(
            _svg_icon(_SVG_SEARCH, COLORS['text_dim'], 14), '', self._search_box)
        self._search_box.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)

        layout.addStretch(1)
        layout.addWidget(self._search_box, 2)
        layout.addStretch(1)

        # Load button
        self._load_btn = QPushButton('Load')
        self._load_btn.setFixedHeight(28)
        self._load_btn.setObjectName('accent')
        self._load_btn.setToolTip('Open and load an FM24 save file')
        self._load_btn.clicked.connect(self._load_file)

        # Settings cog
        self._settings_btn = QPushButton()
        self._settings_btn.setFixedSize(28, 28)
        self._settings_btn.setIcon(_svg_icon(_SVG_COG, COLORS['text_secondary'], 15))
        self._settings_btn.setIconSize(QSize(15, 15))
        self._settings_btn.setToolTip('Settings')
        self._settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['elevated']};
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['border']};
                border-color: {COLORS['border_bright']};
            }}
        """)

        layout.addWidget(self._load_btn)
        layout.addWidget(self._settings_btn)
        return bar

    def _make_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(192)
        sidebar.setObjectName('sidebar')
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        vbox = QVBoxLayout(sidebar)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Club header
        self._sb_club_name = QLabel('FM24 Editor')
        self._sb_club_name.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;"
            "padding: 13px 15px 2px; background:transparent;")
        self._sb_season = QLabel('No save loaded')
        self._sb_season.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:11px;"
            "padding:0 15px 10px; background:transparent;")
        vbox.addWidget(self._sb_club_name)
        vbox.addWidget(self._sb_season)
        vbox.addWidget(self._make_hline())

        # Save info
        save_frame = QFrame()
        save_frame.setStyleSheet("background:transparent;")
        sf_vbox = QVBoxLayout(save_frame)
        sf_vbox.setContentsMargins(15, 8, 15, 8)
        sf_vbox.setSpacing(2)
        self._sb_save_name = QLabel('')
        self._sb_save_name.setStyleSheet(
            f"color:{COLORS['hgp_green']}; font-size:12px; font-weight:bold;")
        self._sb_club_count = QLabel('')
        self._sb_club_count.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:11px;")
        sf_vbox.addWidget(self._sb_save_name)
        sf_vbox.addWidget(self._sb_club_count)
        vbox.addWidget(save_frame)
        vbox.addWidget(self._make_hline())

        # Main nav
        vbox.addWidget(self._make_section_label('MAIN'))
        self._nav_btns = {}
        for key, svg, label in [
            ('club',      _SVG_CLUB,      'Club'),
            ('squad',     _SVG_SQUAD,     'Squad'),
            ('staff',     _SVG_STAFF,     'Staff'),
            ('shortlist', _SVG_SHORTLIST, 'My Shortlist'),
        ]:
            btn = self._make_nav_btn(svg, label, lambda k=key: self._nav_to(k))
            self._nav_btns[key] = btn
            vbox.addWidget(btn)

        vbox.addWidget(self._make_hline())

        # Scouting
        vbox.addWidget(self._make_section_label('SCOUTING'))
        vbox.addWidget(self._make_section_label('Reports'))

        self._report_btns = {}
        for key, label in [
            ('prospects', 'Best Prospects'),
            ('wonderkids', 'Wonderkids'),
            ('best_pos',   'Best in Position'),
            ('best_role',  'Best by Role'),
        ]:
            btn = self._make_nav_btn(_SVG_REPORT, label, lambda k=key: self._run_report(k))
            btn.setEnabled(False)
            self._report_btns[key] = btn
            vbox.addWidget(btn)

        vbox.addStretch()
        vbox.addWidget(self._make_hline())

        # Reload button
        self._reload_btn = QPushButton()
        self._reload_btn.setEnabled(False)
        self._reload_btn.setIcon(_svg_icon(_SVG_RELOAD, COLORS['text_secondary'], 14))
        self._reload_btn.setIconSize(QSize(14, 14))
        self._reload_btn.setText('  Reload Save')
        self._reload_btn.clicked.connect(self._reload_save)
        self._reload_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_secondary']};
                text-align: left;
                padding: 9px 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['border']};
                color: {COLORS['text_primary']};
            }}
            QPushButton:disabled {{ color: {COLORS['text_dim']}; }}
        """)
        vbox.addWidget(self._reload_btn)
        return sidebar

    def _make_view_club(self):
        w = QWidget()
        w.setObjectName('view_club')
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(24, 24, 24, 24)
        vbox.setSpacing(16)

        self._club_view_name = QLabel('No club selected')
        self._club_view_name.setObjectName('header')
        self._club_view_name.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:22px; font-weight:bold;")
        vbox.addWidget(self._club_view_name)

        self._club_view_info = QLabel(
            'Search for a club in the top bar to load their squad.\n'
            'Then navigate to Squad in the sidebar to view and edit players.')
        self._club_view_info.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:13px;")
        self._club_view_info.setWordWrap(True)
        vbox.addWidget(self._club_view_info)
        vbox.addStretch()
        return w

    def _make_view_squad(self):
        w = QWidget()
        w.setObjectName('view_squad')
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Content header: club name + squad switcher
        header_bar = QFrame()
        header_bar.setFixedHeight(44)
        header_bar.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        header_row = QHBoxLayout(header_bar)
        header_row.setContentsMargins(16, 0, 16, 0)
        header_row.setSpacing(12)

        self._squad_club_label = QLabel('')
        self._squad_club_label.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:14px; font-weight:bold;")
        header_row.addWidget(self._squad_club_label)

        self._squad_switcher = QComboBox()
        self._squad_switcher.setFixedWidth(160)
        self._squad_switcher.setFixedHeight(28)
        self._squad_switcher.currentIndexChanged.connect(self._on_squad_switched)
        header_row.addWidget(self._squad_switcher)
        header_row.addStretch()

        self._squad_info = QLabel('')
        self._squad_info.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        header_row.addWidget(self._squad_info)
        vbox.addWidget(header_bar)

        # Filter tab row
        tab_bar = QFrame()
        tab_bar.setFixedHeight(36)
        tab_bar.setStyleSheet(
            f"background:{COLORS['surface']}; border-bottom:1px solid {COLORS['border']};")
        tab_row = QHBoxLayout(tab_bar)
        tab_row.setContentsMargins(12, 0, 12, 0)
        tab_row.setSpacing(0)

        self._filter_btns = {}
        for key, label in [('all', 'All'), ('non_hgp', 'Non-HGP'), ('non_hgc', 'Non-HGC')]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == 'all')
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    color: {COLORS['text_secondary']};
                    padding: 0 14px;
                    font-size: 12px;
                    border-radius: 0;
                }}
                QPushButton:hover {{ color: {COLORS['text_primary']}; }}
                QPushButton:checked {{
                    color: {COLORS['text_primary']};
                    border-bottom: 2px solid {COLORS['accent']};
                    font-weight: bold;
                }}
            """)
            btn.clicked.connect(lambda _, k=key: self._set_filter(k))
            self._filter_btns[key] = btn
            tab_row.addWidget(btn)

        tab_row.addStretch()

        # Patch action buttons in tab bar (right side)
        self._patch_hgp_btn = QPushButton('Make HGP')
        self._patch_hgp_btn.setObjectName('accent')
        self._patch_hgp_btn.setFixedHeight(26)
        self._patch_hgp_btn.setToolTip('Set selected players as Homegrown Player')
        self._patch_hgp_btn.clicked.connect(self._do_patch_hgp)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn = QPushButton('Make HGC')
        self._patch_hgc_btn.setObjectName('accent')
        self._patch_hgc_btn.setFixedHeight(26)
        self._patch_hgc_btn.setToolTip('Set selected players as Homegrown at Club')
        self._patch_hgc_btn.clicked.connect(self._do_patch_hgc)
        self._patch_hgc_btn.setEnabled(False)
        self._clear_sel_btn = QPushButton('Clear')
        self._clear_sel_btn.setFixedHeight(26)
        self._clear_sel_btn.clicked.connect(self._table.clearSelection if hasattr(self, '_table') else lambda: None)
        self._clear_sel_btn.setEnabled(False)

        tab_row.addWidget(self._patch_hgp_btn)
        tab_row.addSpacing(4)
        tab_row.addWidget(self._patch_hgc_btn)
        tab_row.addSpacing(8)
        tab_row.addWidget(self._clear_sel_btn)
        tab_row.addSpacing(4)
        vbox.addWidget(tab_bar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
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
        vbox.addWidget(self._table)

        # Fix Clear button now that table exists
        self._clear_sel_btn.clicked.disconnect()
        self._clear_sel_btn.clicked.connect(self._table.clearSelection)

        return w

    def _make_view_staff(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(24, 24, 24, 24)
        lbl = QLabel('Staff')
        lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:22px; font-weight:bold;")
        vbox.addWidget(lbl)
        coming = QLabel('Coming soon — staff search and filtering by role.')
        coming.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:13px;")
        vbox.addWidget(coming)
        vbox.addStretch()
        return w

    def _make_view_shortlist(self):
        w = QWidget()
        self._shortlist_vbox = QVBoxLayout(w)
        self._shortlist_vbox.setContentsMargins(24, 24, 24, 24)
        lbl = QLabel('My Shortlist')
        lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:22px; font-weight:bold;")
        self._shortlist_vbox.addWidget(lbl)
        self._shortlist_empty = QLabel(
            'Your shortlist is empty.\nDouble-click a player in Squad view and choose "Add to Shortlist".')
        self._shortlist_empty.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:13px;")
        self._shortlist_empty.setWordWrap(True)
        self._shortlist_vbox.addWidget(self._shortlist_empty)
        self._shortlist_vbox.addStretch()
        return w

    # -- Navigation -----------------------------------------------------------

    _VIEW_INDEX = {'club': 0, 'squad': 1, 'staff': 2, 'shortlist': 3}

    def _nav_to(self, key: str):
        idx = self._VIEW_INDEX.get(key, 0)
        self._main_stack.setCurrentIndex(idx)
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        # Uncheck scout report buttons unless we're going there via report
        if key not in ('squad',):
            for btn in self._report_btns.values():
                btn.setChecked(False)

    # -- Table configuration --------------------------------------------------

    def _configure_table_for_mode(self, mode):
        hdr = self._table.horizontalHeader()
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _TT = {
            'CA':  'Current Ability (1–200): overall quality right now',
            'PA':  'Potential Ability (1–200): maximum this player can reach',
            'Dev': 'Development rate (1–20): predicted speed of improvement\n'
                   'Based on ambition, professionalism and determination',
            'Age': 'Age at start of FM24 season',
            'HGP': 'Homegrown Player (nation) — trained in England for ≥3 years between ages 15–21',
            'HGC': 'Homegrown at Club — trained at THIS club for ≥3 years between ages 15–21',
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

    # -- State helpers --------------------------------------------------------

    def _update_ui_state(self):
        has_file = bool(self._save_path)
        has_data = self._save_data is not None
        self._reload_btn.setEnabled(has_file)
        self._search_box.setEnabled(has_data)
        has_abilities = has_data and any(
            'ca' in p for p in self._save_data.get('people', []))
        for btn in self._report_btns.values():
            btn.setEnabled(has_abilities)
        self._table.setEnabled(has_data)
        has_squad = bool(self._squad) and self._table_mode == 'squad'
        has_b = has_data and 'b' in self._save_data
        has_sel = has_squad and bool(self._table.selectedItems())
        self._patch_hgp_btn.setEnabled(has_sel)
        self._patch_hgc_btn.setEnabled(has_sel and has_b and self._club_entity_id is not None)
        self._clear_sel_btn.setEnabled(has_squad)

    # -- File loading ---------------------------------------------------------

    def _load_file(self):
        """Open file picker then immediately start loading."""
        start_dir = DEFAULT_SAVE_DIR if os.path.isdir(DEFAULT_SAVE_DIR) else os.path.expanduser('~')
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open FM24 Save File', start_dir, 'FM Save Files (*.fm);;All Files (*)')
        if not path:
            return
        self._save_path = path
        self._save_data = None
        self._squad = []
        self._current_club = None
        self._table.setRowCount(0)
        self._squad_info.setText('')
        self._sb_save_name.setText(os.path.basename(path))
        self._sb_club_count.setText('Loading...')
        self._update_ui_state()
        self._reload_save()

    def _reload_save(self):
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
        self._sb_club_count.setText(f'{n_clubs} clubs loaded')
        if self._save_path:
            self._sb_save_name.setText(os.path.basename(self._save_path))
        self._status.showMessage(
            f"Loaded {n_clubs} clubs. Search for a team to view their squad.")
        self._update_ui_state()

    # -- Search ---------------------------------------------------------------

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
        squad_counts = {}
        for cid in squads.values():
            squad_counts[cid] = squad_counts.get(cid, 0) + 1
        matches.sort(key=lambda c: squad_counts.get(c['id'], 0), reverse=True)
        from PyQt6.QtWidgets import QInputDialog
        names = [c['name'] for c in matches]
        chosen, ok = QInputDialog.getItem(
            self, 'Multiple matches',
            f'{len(matches)} clubs match "{query}" — pick one:',
            names, 0, False)
        if ok:
            self._show_squad(matches[names.index(chosen)])

    # -- Squad / table views --------------------------------------------------

    def _show_squad(self, club):
        self._configure_table_for_mode('squad')
        self._current_club = club
        squads = self._save_data.get('squads', {})
        people = self._save_data.get('people', [])

        club_pids = {pid for pid, cid in squads.items() if cid == club['id']}
        squad = [p for p in people if p.get('id', -1) in club_pids]
        squad.sort(key=lambda p: p['name'])
        self._squad = squad

        from fm_editor.patch import find_club_entity_id, is_hgc
        b = self._save_data.get('b')
        if b is not None:
            self._club_entity_id = find_club_entity_id(b, squad)
        else:
            self._club_entity_id = None

        # Update sidebar + header
        self._sb_club_name.setText(club['name'])
        self._sb_season.setText('First Team')
        self._squad_club_label.setText(club['name'])
        self._squad_switcher.blockSignals(True)
        self._squad_switcher.clear()
        self._squad_switcher.addItem('First Team')
        self._squad_switcher.blockSignals(False)

        # Update club view
        self._club_view_name.setText(club['name'])
        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        n_hgc = sum(1 for p in squad
                    if b is not None and self._club_entity_id and is_hgc(b, p, self._club_entity_id))
        self._club_view_info.setText(
            f"{len(squad)} players  ·  {n_hgp} HGP  ·  {n_hgc} HGC\n\n"
            "Navigate to Squad in the sidebar to view and edit players.")

        self._populate_squad_table(squad)
        self._nav_to('squad')
        self._nav_btns['squad'].setChecked(True)
        self._update_ui_state()
        try:
            self._table.itemSelectionChanged.disconnect()
        except Exception:
            pass
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _populate_squad_table(self, squad):
        from fm_editor.patch import is_hgc
        b = self._save_data.get('b') if self._save_data else None

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
        b = self._save_data.get('b') if self._save_data else None
        from fm_editor.patch import is_hgc
        n_hgc = sum(1 for p in squad
                    if b is not None and self._club_entity_id and is_hgc(b, p, self._club_entity_id))
        self._squad_info.setText(
            f"{len(squad)} players  ·  {n_hgp} HGP  ·  {n_hgc} HGC")
        self._status.showMessage(f"Showing {self._current_club['name']} — {len(squad)} players")

    def _set_filter(self, key: str):
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
        if not self._squad:
            return
        if key == 'non_hgp':
            self._select_all_non_hgp()
        elif key == 'non_hgc':
            self._select_all_non_hgc()
        else:
            self._table.clearSelection()

    def _on_squad_switched(self, idx):
        pass  # ponytail: no-op until sub-squad data available

    def _show_player_results(self, players):
        self._configure_table_for_mode('player')
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
            nation_name = NATIONS.get(p['nation'], f"n={p['nation']}")
            hgp = p.get('hgp', False)
            name_item = _SortItem(p['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item, _SortItem(club_name), _SortItem(nation_name),
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
        self._nav_to('squad')
        self._update_ui_state()

    def _on_row_double_clicked(self, index):
        if self._table_mode == 'squad':
            self._open_player_detail(index.row())
            return
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

    def _open_player_detail(self, row: int):
        item = self._table.item(row, 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        person = next((p for p in self._squad if p.get('id') == pid), None)
        if not person:
            return
        dlg = PlayerDetailDialog(person, self._save_data, self._club_entity_id, self)
        dlg.exec()
        if dlg._patch_mode == 'hgp':
            self._table.clearSelection()
            for r in range(self._table.rowCount()):
                if self._table.item(r, 0) and \
                   self._table.item(r, 0).data(Qt.ItemDataRole.UserRole) == pid:
                    self._table.selectRow(r)
                    break
            self._do_patch_hgp()
        elif dlg._patch_mode == 'hgc':
            self._table.clearSelection()
            for r in range(self._table.rowCount()):
                if self._table.item(r, 0) and \
                   self._table.item(r, 0).data(Qt.ItemDataRole.UserRole) == pid:
                    self._table.selectRow(r)
                    break
            self._do_patch_hgc()

    # -- Scout views ----------------------------------------------------------

    def _show_scout_results(self, players, title):
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
                name_item, _SortItem(club_name), _SortItem(pos),
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
        self._status.showMessage(f"{title} — {len(players)} players — double-click to view club squad")
        self._nav_to('squad')
        self._squad_club_label.setText(title)
        self._update_ui_state()

    def _run_report(self, key: str):
        if not self._save_data:
            return
        for k, btn in self._report_btns.items():
            btn.setChecked(k == key)
        if key == 'prospects':
            self._scout_high_potential()
        elif key == 'wonderkids':
            self._scout_wonderkids()
        elif key == 'best_pos':
            self._show_pos_menu()
        elif key == 'best_role':
            self._status.showMessage('Best by Role coming soon.')

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
        self._show_scout_results(candidates[:200], 'Best Prospects (PA≥160)')

    def _show_pos_menu(self):
        if not self._save_data:
            return
        menu = QMenu(self)
        for pos in POSITIONS:
            menu.addAction(pos)
        btn = self._report_btns.get('best_pos')
        if btn:
            action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        else:
            action = menu.exec(self.cursor().pos())
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
        item = self._table.item(row, 0)
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

    # -- Patch ----------------------------------------------------------------

    def _get_selected_persons(self):
        pid_map = {p.get('id', -1): p for p in self._squad}
        selected_rows = sorted({idx.row() for idx in self._table.selectedIndexes()})
        persons = []
        for r in selected_rows:
            pid = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole) \
                if self._table.item(r, 0) else -1
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
                                'Please click "Reload Save" before patching.')
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
                                'Please click "Reload Save" before patching.')
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

    # -- Progress / error -----------------------------------------------------

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
        self._load_btn.setEnabled(not busy)
        self._reload_btn.setEnabled(not busy and bool(self._save_path))
        self._search_box.setEnabled(not busy and self._save_data is not None)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn.setEnabled(False)
        if msg and not busy:
            self._status.showMessage(msg)
