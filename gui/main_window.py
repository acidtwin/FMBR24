"""FM24 Save Editor - main window."""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QStatusBar, QFrame, QSizePolicy, QMessageBox,
    QAbstractItemView, QMenu, QStackedWidget, QDialog, QScrollArea,
    QComboBox, QStyledItemDelegate, QStyleOptionViewItem,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QRectF
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

# Ping-pong dot counts for loading animation
_DOT_SEQ = [1, 2, 3, 4, 5, 4, 3, 2]


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
        try:
            a = self._sk if self._sk is not None else self.text()
            b = other._sk if isinstance(other, _SortItem) and other._sk is not None else other.text()
            try:
                return float(a) < float(b)
            except (ValueError, TypeError):
                return str(a) < str(b)
        except Exception:
            return False


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

            self._emit("Parsing archive...", 3)
            header, members, index_marker, archive_name, subdir_count, subdirs = \
                parse_archive(self.save_path)
            gdb_m_ref = next((m for m in members if m['name'] == 'game_db.dat'), None)

            if not gdb_m_ref:
                self.error.emit("game_db.dat not found in archive.")
                return

            self._emit(f"Extracting game_db.dat ({gdb_m_ref['p'] // 1024 // 1024} MB)...", 5)
            b = get_member(self.save_path, gdb_m_ref)

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

            if self.mode == 'save_only':
                pass  # just write current b state
            elif self.mode == 'hgp':
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

def _attr_val_color(v: int) -> str:
    if v >= 17: return '#FFD700'
    if v >= 16: return '#52C287'
    if v >= 13: return COLORS['accent_hover']
    if v >= 10: return COLORS['text_secondary']
    if v >= 7:  return COLORS['text_primary']
    return COLORS['non_hgp_red']


# Nation ID → flag emoji
_NATION_FLAG = {
    11:  '🇪🇬', 29:  '🇲🇦', 33:  '🇳🇬',
    97:  '🇨🇦', 120: '🇺🇸',
    187: '🇦🇷', 189: '🇧🇷', 195: '🇺🇾',
    61:  '🇯🇵', 80:  '🇰🇷', 177: '🇦🇺',
    126: '🇦🇱', 129: '🇦🇹', 135: '🇭🇷',
    146: '🇬🇷', 147: '🇭🇺', 161: '🇵🇱',
    165: '🇷🇺', 176: '🇷🇸', 219: '🇽🇰',
    131: '🇧🇪', 137: '🇨🇿', 138: '🇩🇰',
    139: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 143: '🇫🇷', 145: '🇩🇪',
    150: '🇮🇹', 158: '🇳🇱', 159: '🏴󠁧󠁢󠁮󠁩󠁲󠁿',
    160: '🇳🇴', 162: '🇵🇹', 163: '🇮🇪',
    167: '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 170: '🇪🇸', 171: '🇸🇪',
    172: '🇨🇭', 173: '🇹🇷', 175: '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
}

# Position → (background, foreground) matching mockup color scheme
_POS_BADGE_COLORS = {
    'GK':  ('#C07B2A', '#F5A63C'),
    'SW':  ('#3A6BA8', '#6EB3F7'),
    'DL':  ('#3A6BA8', '#6EB3F7'), 'DC': ('#3A6BA8', '#6EB3F7'),
    'DR':  ('#3A6BA8', '#6EB3F7'), 'DM': ('#3A6BA8', '#6EB3F7'),
    'WBL': ('#3A6BA8', '#6EB3F7'), 'WBR': ('#3A6BA8', '#6EB3F7'),
    'ML':  ('#3A8A5A', '#6ADE9A'), 'MC': ('#3A8A5A', '#6ADE9A'),
    'MR':  ('#3A8A5A', '#6ADE9A'), 'AML': ('#3A8A5A', '#6ADE9A'),
    'AMC': ('#3A8A5A', '#6ADE9A'), 'AMR': ('#3A8A5A', '#6ADE9A'),
    'ST':  ('#A83A3A', '#F7806A'),
}


class _PosBadgeDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        try:
            super().paint(painter, option, index)
            text = index.data(Qt.ItemDataRole.DisplayRole) or ''
            if not text or text == '?':
                return
            bg, fg = _POS_BADGE_COLORS.get(text, ('#2A2D35', COLORS['text_secondary']))
            painter.save()
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                font = QFont(painter.font())
                font.setPixelSize(10)
                font.setBold(True)
                painter.setFont(font)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(text)
                bw = tw + 10
                bh = 16
                x = option.rect.x() + 8
                y = option.rect.y() + (option.rect.height() - bh) // 2
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(bg))
                painter.drawRoundedRect(QRectF(x, y, bw, bh), 2, 2)
                painter.setPen(QColor(fg))
                painter.drawText(QRectF(x, y, bw, bh), Qt.AlignmentFlag.AlignCenter, text)
            finally:
                painter.restore()
        except Exception:
            import traceback
            traceback.print_exc()

    def sizeHint(self, option, index):
        try:
            return QSize(68, option.rect.height() or 28)
        except Exception:
            import traceback
            traceback.print_exc()
            return QSize(68, 28)


class PlayerDetailDialog(QDialog):
    def __init__(self, person, save_data, club_entity_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(person['name'])
        self.setMinimumSize(860, 560)
        self.resize(920, 640)
        self._person = person
        self._save_data = save_data
        self._club_entity_id = club_entity_id
        self._patch_mode = None
        self._build()

    def _build(self):
        p = self._person
        b = self._save_data.get('b') if self._save_data else None
        from fm_editor.patch import is_hgc as _is_hgc

        nation_name = NATIONS.get(p['nation'], f"n={p['nation']}")
        age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
        pos = _primary_pos(p['positions']) if p.get('positions') else '?'
        ca = p.get('ca')
        pa = p.get('pa')
        raw = p.get('raw_attrs', [])
        personality = p.get('personality', [])
        hgp = p.get('hgp', False)
        hgc = _is_hgc(b, p, self._club_entity_id) if (b and self._club_entity_id) else None
        dev = _progress_rate(p)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top bar ─────────────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(40)
        topbar.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        tb_row = QHBoxLayout(topbar)
        tb_row.setContentsMargins(14, 0, 10, 0)
        tb_row.setSpacing(8)

        title_wrap = QWidget()
        title_wrap.setStyleSheet("background:transparent;")
        tw_vbox = QVBoxLayout(title_wrap)
        tw_vbox.setContentsMargins(0, 4, 0, 4)
        tw_vbox.setSpacing(0)
        name_lbl = QLabel(p['name'])
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:14px; font-weight:bold;")
        sub_lbl = QLabel(f"{pos}  ·  {nation_name}  ·  Age {age}")
        sub_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        tw_vbox.addWidget(name_lbl)
        tw_vbox.addWidget(sub_lbl)
        tb_row.addWidget(title_wrap, 1)

        close_btn = QPushButton('✕')
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: none; border: none;
                color: {COLORS['text_dim']}; font-size: 16px; border-radius: 2px;
            }}
            QPushButton:hover {{ background: {COLORS['border']}; color: {COLORS['text_primary']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        tb_row.addWidget(close_btn)
        layout.addWidget(topbar)

        # ── Body (left | center | right) ────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"background:{COLORS['window_bg']};")
        body_hbox = QHBoxLayout(body)
        body_hbox.setContentsMargins(0, 0, 0, 0)
        body_hbox.setSpacing(0)

        # ── Left panel (190px) ───────────────────────────────────────────────
        left = QFrame()
        left.setFixedWidth(190)
        left.setStyleSheet(
            f"background:{COLORS['surface']}; border-right:1px solid {COLORS['border']};")
        left_vbox = QVBoxLayout(left)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        # Photo placeholder
        photo = QFrame()
        photo.setFixedSize(190, 140)
        photo.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        photo_inner = QVBoxLayout(photo)
        photo_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_icon = QLabel()
        photo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_icon.setPixmap(_svg_icon(_SVG_STAFF, COLORS['text_dim'], 56).pixmap(56, 56))
        photo_inner.addWidget(photo_icon)
        left_vbox.addWidget(photo)

        # Info rows
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']}; background:transparent;")
        info_vbox = QVBoxLayout(info_frame)
        info_vbox.setContentsMargins(12, 8, 12, 8)
        info_vbox.setSpacing(0)

        def _info_row(label: str, value: str, val_color: str = None):
            row = QHBoxLayout()
            row.setContentsMargins(0, 3, 0, 3)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            val = QLabel(value)
            val.setStyleSheet(
                f"color:{val_color or COLORS['text_primary']}; font-size:11px; font-weight:500;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            return row

        info_vbox.addLayout(_info_row('Position', pos))
        info_vbox.addLayout(_info_row('Age', str(age)))
        info_vbox.addLayout(_info_row('Nationality', nation_name))
        info_vbox.addLayout(_info_row('Born', str(p.get('birth_year', '?'))))
        left_vbox.addWidget(info_frame)

        # CA / PA section
        ca_frame = QFrame()
        ca_frame.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']}; background:transparent;")
        ca_vbox = QVBoxLayout(ca_frame)
        ca_vbox.setContentsMargins(12, 8, 12, 8)
        ca_vbox.setSpacing(4)

        ca_title = QLabel('ABILITY')
        ca_title.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:1px;")
        ca_vbox.addWidget(ca_title)

        for name, val, color in [('CA', ca, COLORS['accent']), ('PA', pa, '#52C287')]:
            bar_row = QHBoxLayout()
            bar_row.setSpacing(6)
            n_lbl = QLabel(name)
            n_lbl.setFixedWidth(24)
            n_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
            bar_bg = QFrame()
            bar_bg.setFixedHeight(4)
            bar_bg.setStyleSheet(
                f"background:{COLORS['border']}; border-radius:2px;")
            bar_fill = QFrame(bar_bg)
            bar_fill.setFixedHeight(4)
            pct = max(0, min(100, int((val or 0) / 200 * 100)))
            bar_fill.setStyleSheet(f"background:{color}; border-radius:2px;")
            bar_fill.resize(0, 4)
            bar_fill.setMaximumWidth(int(166 * pct / 100))
            num_lbl = QLabel(str(val) if val else '?')
            num_lbl.setFixedWidth(28)
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            num_lbl.setStyleSheet(f"color:{color}; font-size:12px; font-weight:bold;")
            bar_row.addWidget(n_lbl)
            bar_row.addWidget(bar_bg, 1)
            bar_row.addWidget(num_lbl)
            ca_vbox.addLayout(bar_row)

        if dev is not None:
            ca_vbox.addLayout(_info_row('Dev Rate', str(dev), COLORS['accent_hover']))

        left_vbox.addWidget(ca_frame)

        # HGP / HGC pills
        hg_frame = QFrame()
        hg_frame.setStyleSheet("background:transparent;")
        hg_vbox = QVBoxLayout(hg_frame)
        hg_vbox.setContentsMargins(12, 8, 12, 8)
        hg_vbox.setSpacing(4)
        hg_title = QLabel('HOMEGROWN')
        hg_title.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:1px;")
        hg_vbox.addWidget(hg_title)
        pills_row = QHBoxLayout()
        pills_row.setSpacing(5)

        for label, active, border_color in [
            ('HGP', hgp, COLORS['hgp_green']),
            ('HGC', hgc, '#52C287'),
        ]:
            pill = QLabel(label)
            pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if active:
                pill.setStyleSheet(
                    f"color:{border_color}; border:1px solid {border_color};"
                    f"background:rgba(82,194,135,0.12); border-radius:10px;"
                    "padding:2px 8px; font-size:10px; font-weight:bold;")
            elif active is False:
                pill.setStyleSheet(
                    f"color:{COLORS['text_dim']}; border:1px solid {COLORS['border_bright']};"
                    "background:transparent; border-radius:10px;"
                    "padding:2px 8px; font-size:10px;")
            else:
                pill.setStyleSheet(
                    f"color:{COLORS['text_dim']}; font-size:10px;")
                pill.setText(f"{label}?")
            pills_row.addWidget(pill)
        pills_row.addStretch()
        hg_vbox.addLayout(pills_row)
        left_vbox.addWidget(hg_frame)

        left_vbox.addStretch()
        body_hbox.addWidget(left)

        # ── Center: attributes + action strip ───────────────────────────────
        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{COLORS['window_bg']}; }}")
        center_w = QWidget()
        center_w.setStyleSheet(f"background:{COLORS['window_bg']};")
        center_vbox = QVBoxLayout(center_w)
        center_vbox.setContentsMargins(14, 14, 14, 14)
        center_vbox.setSpacing(14)

        def _display_val(raw_v):
            return max(1, min(20, round(raw_v / 5)))

        def _attr_col(attrs_list):
            col = QVBoxLayout()
            col.setSpacing(0)
            for attr_name, idx in attrs_list:
                if not raw or idx >= len(raw):
                    continue
                v = _display_val(raw[idx])
                row = QHBoxLayout()
                row.setContentsMargins(0, 3, 0, 2)
                n = QLabel(attr_name)
                n.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
                v_lbl = QLabel(str(v))
                v_lbl.setFixedWidth(22)
                v_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                v_lbl.setStyleSheet(
                    f"color:{_attr_val_color(v)}; font-size:12px; font-weight:bold;")
                row.addWidget(n)
                row.addStretch()
                row.addWidget(v_lbl)
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background:rgba(52,55,64,0.4);")
                col.addLayout(row)
                col.addWidget(sep)
            return col

        def _block_title(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:1px;"
                f"border-bottom:1px solid {COLORS['border']}; padding-bottom:4px;"
                "margin-bottom:4px;")
            return lbl

        # Row 1: Technical | Mental | Physical + Hidden
        top_grid = QHBoxLayout()
        top_grid.setSpacing(20)

        TECH = [
            ('Crossing', 0), ('Dribbling', 1), ('Finishing', 2), ('Heading', 3),
            ('Long Shots', 4), ('Marking', 5), ('Off Ball', 6), ('Passing', 7),
            ('Pen Taking', 8), ('Tackling', 9), ('Vision', 10),
            ('First Touch', 22), ('Technique', 23), ('Corners', 27),
            ('Long Throws', 30), ('Free Kick', 35),
        ]
        MENT = [
            ('Anticipation', 17), ('Decisions', 18), ('Positioning', 20),
            ('Teamwork', 28), ('Work Rate', 29), ('Leadership', 40),
            ('Bravery', 43), ('Consistency', 44), ('Aggression', 45),
            ('Composure', 52), ('Concentration', 53), ('Important Matches', 47),
        ]
        PHYS = [
            ('Acceleration', 34), ('Pace', 38), ('Strength', 36), ('Stamina', 37),
            ('Balance', 42), ('Agility', 46), ('Jumping Reach', 39),
            ('Natural Fitness', 50),
        ]
        HIDD = [
            ('Dirtiness', 41), ('Versatility', 49), ('Injury Prone', 48),
            ('Determination', 51),
        ]

        for title, attrs in [('Technical', TECH), ('Mental', MENT)]:
            col_w = QWidget()
            col_w.setStyleSheet("background:transparent;")
            col_vbox = QVBoxLayout(col_w)
            col_vbox.setContentsMargins(0, 0, 0, 0)
            col_vbox.setSpacing(0)
            col_vbox.addWidget(_block_title(title))
            col_vbox.addLayout(_attr_col(attrs))
            col_vbox.addStretch()
            top_grid.addWidget(col_w, 1)

        # Physical + Hidden stacked in third column
        phys_col = QWidget()
        phys_col.setStyleSheet("background:transparent;")
        phys_vbox = QVBoxLayout(phys_col)
        phys_vbox.setContentsMargins(0, 0, 0, 0)
        phys_vbox.setSpacing(0)
        phys_vbox.addWidget(_block_title('Physical'))
        phys_vbox.addLayout(_attr_col(PHYS))
        phys_vbox.addSpacing(14)
        phys_vbox.addWidget(_block_title('Hidden'))
        phys_vbox.addLayout(_attr_col(HIDD))
        phys_vbox.addStretch()
        top_grid.addWidget(phys_col, 1)
        center_vbox.addLayout(top_grid)

        # Row 2: Personality (4 columns)
        if personality:
            PERS = [
                ('Adaptability', 0), ('Ambition', 1), ('Loyalty', 2), ('Pressure', 3),
                ('Professionalism', 4), ('Sportsmanship', 5), ('Temperament', 6),
            ]
            pers_w = QWidget()
            pers_w.setStyleSheet("background:transparent;")
            pers_vbox = QVBoxLayout(pers_w)
            pers_vbox.setContentsMargins(0, 0, 0, 0)
            pers_vbox.setSpacing(0)
            pers_vbox.addWidget(_block_title('Personality'))
            pers_grid = QHBoxLayout()
            pers_grid.setSpacing(20)
            cols = [QVBoxLayout() for _ in range(4)]
            for i, (attr_name, idx) in enumerate(PERS):
                if idx >= len(personality):
                    continue
                v = personality[idx]
                row = QHBoxLayout()
                row.setContentsMargins(0, 3, 0, 2)
                n = QLabel(attr_name)
                n.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
                v_lbl = QLabel(str(v))
                v_lbl.setFixedWidth(22)
                v_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                v_lbl.setStyleSheet(
                    f"color:{_attr_val_color(v)}; font-size:12px; font-weight:bold;")
                row.addWidget(n)
                row.addStretch()
                row.addWidget(v_lbl)
                cols[i % 4].addLayout(row)
            for c in cols:
                w = QWidget()
                w.setStyleSheet("background:transparent;")
                wv = QVBoxLayout(w)
                wv.setContentsMargins(0, 0, 0, 0)
                wv.addLayout(c)
                wv.addStretch()
                pers_grid.addWidget(w, 1)
            pers_vbox.addLayout(pers_grid)
            center_vbox.addWidget(pers_w)

        center_vbox.addStretch()

        # Action strip (Make HGP / Make HGC / Add to Shortlist)
        action_frame = QFrame()
        action_frame.setStyleSheet(
            f"border-top:1px solid {COLORS['border']}; background:transparent;")
        action_row = QHBoxLayout(action_frame)
        action_row.setContentsMargins(0, 8, 0, 4)
        action_row.setSpacing(8)

        _btn_ss = f"""
            QPushButton {{
                background:{COLORS['accent']}; color:#fff; border:none;
                padding:6px 16px; font-weight:bold; border-radius:2px; font-size:11px;
            }}
            QPushButton:hover {{ background:{COLORS['accent_hover']}; }}
            QPushButton:pressed {{ background:{COLORS['accent_press']}; }}
        """
        if b is not None and not hgp:
            make_hgp = QPushButton('Make HGP')
            make_hgp.setStyleSheet(_btn_ss)
            make_hgp.setCursor(Qt.CursorShape.PointingHandCursor)
            make_hgp.clicked.connect(lambda: (self._emit_patch('hgp'), self.accept()))
            action_row.addWidget(make_hgp)
        if b is not None and hgc is False and self._club_entity_id:
            make_hgc = QPushButton('Make HGC')
            make_hgc.setStyleSheet(_btn_ss)
            make_hgc.setCursor(Qt.CursorShape.PointingHandCursor)
            make_hgc.clicked.connect(lambda: (self._emit_patch('hgc'), self.accept()))
            action_row.addWidget(make_hgc)

        action_row.addStretch()
        add_shortlist = QPushButton('Add to Shortlist')
        add_shortlist.setEnabled(False)
        add_shortlist.setToolTip('Shortlist coming soon')
        action_row.addWidget(add_shortlist)
        center_vbox.addWidget(action_frame)

        center_scroll.setWidget(center_w)
        body_hbox.addWidget(center_scroll, 1)

        # ── Right tab nav (110px) ────────────────────────────────────────────
        right_tabs = QFrame()
        right_tabs.setFixedWidth(110)
        right_tabs.setStyleSheet(
            f"background:{COLORS['surface']}; border-left:1px solid {COLORS['border']};")
        rt_vbox = QVBoxLayout(right_tabs)
        rt_vbox.setContentsMargins(0, 6, 0, 6)
        rt_vbox.setSpacing(0)

        _rtab_active = f"""
            QPushButton {{
                background: {COLORS['selection_bg']};
                border: none; border-left: 2px solid {COLORS['accent']};
                color: {COLORS['text_primary']}; text-align: left;
                padding: 8px 10px; font-size: 11px; border-radius: 0;
            }}
        """
        _rtab_future = f"""
            QPushButton {{
                background: transparent; border: none; border-left: 2px solid transparent;
                color: {COLORS['text_dim']}; text-align: left;
                padding: 8px 10px; font-size: 11px; font-style: italic; border-radius: 0;
            }}
        """
        for tab_label, active in [
            ('Profile', True), ('Transfer', False), ('Positions', False),
            ('General Rating', False), ('Positional Rating', False),
            ('Role Rating', False), ('Training Roles', False),
        ]:
            tb = QPushButton(tab_label)
            tb.setEnabled(active)
            tb.setStyleSheet(_rtab_active if active else _rtab_future)
            rt_vbox.addWidget(tb)

        rt_vbox.addStretch()
        body_hbox.addWidget(right_tabs)

        layout.addWidget(body)

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
        self._dot_phase = -1
        self._table_mode = 'squad'
        self._current_report_key = ''

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
        self._main_stack.addWidget(self._make_view_reports())    # 4
        self._main_stack.addWidget(self._make_view_players())    # 5
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
        layout.setContentsMargins(8, 0, 12, 0)
        layout.setSpacing(6)

        # Back / forward nav + breadcrumb
        _nav_ss = f"""
            QPushButton {{
                background: transparent; border: none;
                color: {COLORS['text_dim']}; font-size: 13px;
                padding: 4px 6px; border-radius: 2px;
            }}
            QPushButton:hover {{ background: {COLORS['border']}; color: {COLORS['text_secondary']}; }}
        """
        back_btn = QPushButton('◀')
        back_btn.setFixedSize(26, 26)
        back_btn.setEnabled(False)
        back_btn.setStyleSheet(_nav_ss)
        fwd_btn = QPushButton('▶')
        fwd_btn.setFixedSize(26, 26)
        fwd_btn.setEnabled(False)
        fwd_btn.setStyleSheet(_nav_ss)

        self._breadcrumb = QLabel('FM Save Editor')
        self._breadcrumb.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:12px; background:transparent;")

        layout.addWidget(back_btn)
        layout.addWidget(fwd_btn)
        layout.addWidget(self._breadcrumb)
        layout.addSpacing(4)

        # Centred search
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('Search clubs or players...')
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

        # Save button (left of Load)
        self._save_btn = QPushButton('Save Changes')
        self._save_btn.setFixedHeight(28)
        self._save_btn.setEnabled(False)
        self._save_btn.setToolTip('Save current file (default: SaveName-Edited-DATE)')
        self._save_btn.clicked.connect(self._do_save)

        # Load button
        self._load_btn = QPushButton('Load')
        self._load_btn.setFixedHeight(28)
        self._load_btn.setObjectName('accent')
        self._load_btn.setToolTip('Open and load an FM24 save file')
        self._load_btn.clicked.connect(self._load_file)

        # Reload button (right of Load, greyed when no file)
        self._reload_btn = QPushButton('Reload')
        self._reload_btn.setFixedHeight(28)
        self._reload_btn.setEnabled(False)
        self._reload_btn.setToolTip('Re-parse the current save file')
        self._reload_btn.clicked.connect(self._reload_save)

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

        layout.addWidget(self._save_btn)
        layout.addWidget(self._load_btn)
        layout.addWidget(self._reload_btn)
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

        # Club/save header
        self._sb_club_name = QLabel('FM Save Editor')
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

        # Main nav
        vbox.addWidget(self._make_section_label('MAIN'))
        self._nav_btns = {}
        for key, svg, label in [
            ('club',      _SVG_CLUB,      'Club'),
            ('squad',     _SVG_SQUAD,     'Squad'),
            ('staff',     _SVG_STAFF,     'Staff'),
            ('shortlist', _SVG_SHORTLIST, 'My Shortlist'),
        ]:
            if key == 'squad':
                btn = self._make_nav_btn(svg, label, self._nav_to_squad_view)
            else:
                btn = self._make_nav_btn(svg, label, lambda checked, k=key: self._nav_to(k))
            self._nav_btns[key] = btn
            vbox.addWidget(btn)

        vbox.addWidget(self._make_hline())

        # Scouting
        vbox.addWidget(self._make_section_label('SCOUTING'))

        self._players_nav_btn = self._make_nav_btn(
            _SVG_SQUAD, 'Players', lambda checked: self._open_players_view())
        self._players_nav_btn.setEnabled(False)
        vbox.addWidget(self._players_nav_btn)

        vbox.addWidget(self._make_section_label('Reports'))

        self._report_btns = {}
        for key, label in [
            ('prospects', 'Best Prospects'),
            ('wonderkids', 'Wonderkids'),
            ('best_pos',   'Best in Position'),
            ('best_role',  'Best by Role'),
        ]:
            btn = self._make_nav_btn(_SVG_REPORT, label, lambda checked, k=key: self._run_report(k))
            btn.setEnabled(False)
            self._report_btns[key] = btn
            vbox.addWidget(btn)

        vbox.addStretch()
        return sidebar

    def _make_view_club(self):
        w = QWidget()
        w.setObjectName('view_club')
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{COLORS['window_bg']}; }}")
        scroll.setWidget(w)

        outer = QWidget()
        outer.setObjectName('view_club_outer')
        outer_vbox = QVBoxLayout(outer)
        outer_vbox.setContentsMargins(0, 0, 0, 0)
        outer_vbox.setSpacing(0)
        outer_vbox.addWidget(scroll, 1)

        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(28, 28, 28, 28)
        vbox.setSpacing(20)

        # Club name
        self._club_view_name = QLabel('No save loaded')
        self._club_view_name.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:26px; font-weight:bold;")
        vbox.addWidget(self._club_view_name)

        self._club_view_info = QLabel('Load an FM24 save file to get started.')
        self._club_view_info.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:13px;")
        self._club_view_info.setWordWrap(True)
        vbox.addWidget(self._club_view_info)

        # Stats cards row
        self._club_stats_frame = QFrame()
        self._club_stats_frame.setVisible(False)
        stats_row = QHBoxLayout(self._club_stats_frame)
        stats_row.setContentsMargins(0, 0, 0, 0)
        stats_row.setSpacing(12)

        def _stat_card(title, attr):
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background:{COLORS['surface']}; border:1px solid {COLORS['border']};"
                "border-radius:4px; }")
            card.setFixedHeight(72)
            cvbox = QVBoxLayout(card)
            cvbox.setContentsMargins(14, 10, 14, 10)
            cvbox.setSpacing(2)
            val_lbl = QLabel('--')
            val_lbl.setStyleSheet(
                f"color:{COLORS['text_primary']}; font-size:22px; font-weight:bold;")
            ttl_lbl = QLabel(title)
            ttl_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            cvbox.addWidget(val_lbl)
            cvbox.addWidget(ttl_lbl)
            setattr(self, attr, val_lbl)
            return card

        stats_row.addWidget(_stat_card('Squad size', '_cv_squad_size'))
        stats_row.addWidget(_stat_card('Avg CA', '_cv_avg_ca'))
        stats_row.addWidget(_stat_card('HGP', '_cv_hgp'))
        stats_row.addWidget(_stat_card('HGC', '_cv_hgc'))
        stats_row.addStretch()
        vbox.addWidget(self._club_stats_frame)

        # Position breakdown
        self._club_pos_frame = QFrame()
        self._club_pos_frame.setVisible(False)
        self._club_pos_frame.setStyleSheet(
            f"QFrame {{ background:{COLORS['surface']}; border:1px solid {COLORS['border']};"
            "border-radius:4px; }")
        pos_vbox = QVBoxLayout(self._club_pos_frame)
        pos_vbox.setContentsMargins(14, 12, 14, 12)
        pos_vbox.setSpacing(6)
        pos_hdr = QLabel('SQUAD BREAKDOWN')
        pos_hdr.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:0.8px;")
        pos_vbox.addWidget(pos_hdr)
        self._club_pos_grid = QHBoxLayout()
        self._club_pos_grid.setSpacing(24)
        pos_vbox.addLayout(self._club_pos_grid)
        vbox.addWidget(self._club_pos_frame)

        # Top players
        self._club_top_frame = QFrame()
        self._club_top_frame.setVisible(False)
        self._club_top_frame.setStyleSheet(
            f"QFrame {{ background:{COLORS['surface']}; border:1px solid {COLORS['border']};"
            "border-radius:4px; }")
        top_vbox = QVBoxLayout(self._club_top_frame)
        top_vbox.setContentsMargins(14, 12, 14, 12)
        top_vbox.setSpacing(6)
        top_hdr = QLabel('TOP PLAYERS BY CA')
        top_hdr.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:0.8px;")
        top_vbox.addWidget(top_hdr)
        self._club_top_list = QVBoxLayout()
        self._club_top_list.setSpacing(2)
        top_vbox.addLayout(self._club_top_list)
        vbox.addWidget(self._club_top_frame)

        # View Squad button
        self._club_view_squad_btn = QPushButton('View Squad')
        self._club_view_squad_btn.setFixedHeight(34)
        self._club_view_squad_btn.setVisible(False)
        self._club_view_squad_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _btn_ss = (f"QPushButton {{ background:{COLORS['accent']}; color:#fff; border:none;"
                   f"padding:6px 18px; font-weight:bold; border-radius:2px; font-size:12px; }}"
                   f"QPushButton:hover {{ background:{COLORS['accent_hover']}; }}"
                   f"QPushButton:pressed {{ background:{COLORS['accent_press']}; }}")
        self._club_view_squad_btn.setStyleSheet(_btn_ss)
        self._club_view_squad_btn.clicked.connect(self._nav_to_squad_view)
        vbox.addWidget(self._club_view_squad_btn, 0, Qt.AlignmentFlag.AlignLeft)

        vbox.addStretch()
        return outer

    def _update_club_view(self):
        from fm_editor.patch import is_hgc
        squad = self._squad
        b = self._save_data.get('b') if self._save_data else None
        club = self._current_club

        has_club = bool(club and squad is not None)
        self._club_stats_frame.setVisible(has_club)
        self._club_pos_frame.setVisible(has_club)
        self._club_top_frame.setVisible(has_club)
        self._club_view_squad_btn.setVisible(has_club)

        if not has_club:
            return

        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        n_hgc = sum(1 for p in squad
                    if b is not None and self._club_entity_id
                    and is_hgc(b, p, self._club_entity_id))
        cas = [p['ca'] for p in squad if p.get('ca') is not None]
        avg_ca = round(sum(cas) / len(cas)) if cas else 0

        self._cv_squad_size.setText(str(len(squad)))
        self._cv_avg_ca.setText(str(avg_ca))
        self._cv_hgp.setText(str(n_hgp))
        self._cv_hgc.setText(str(n_hgc))

        # Position breakdown
        while self._club_pos_grid.count():
            item = self._club_pos_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        groups = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        _group_map = {
            'GK': 'GK', 'SW': 'DEF', 'DL': 'DEF', 'DC': 'DEF', 'DR': 'DEF',
            'DM': 'DEF', 'WBL': 'DEF', 'WBR': 'DEF',
            'ML': 'MID', 'MC': 'MID', 'MR': 'MID',
            'AML': 'MID', 'AMC': 'MID', 'AMR': 'MID',
            'ST': 'FWD',
        }
        for p in squad:
            if p.get('positions'):
                pos = _primary_pos(p['positions'])
                g = _group_map.get(pos, 'MID')
                groups[g] += 1

        _group_colors = {
            'GK': COLORS.get('warning', '#C07B2A'),
            'DEF': COLORS.get('accent', '#3A6BA8'),
            'MID': '#3A8A5A',
            'FWD': '#A83A3A',
        }
        for g, count in groups.items():
            grp_w = QWidget()
            grp_layout = QVBoxLayout(grp_w)
            grp_layout.setContentsMargins(0, 0, 0, 0)
            grp_layout.setSpacing(2)
            cnt_lbl = QLabel(str(count))
            cnt_lbl.setStyleSheet(
                f"color:{_group_colors.get(g, COLORS['text_primary'])};"
                "font-size:20px; font-weight:bold;")
            lbl = QLabel(g)
            lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:10px;")
            grp_layout.addWidget(cnt_lbl)
            grp_layout.addWidget(lbl)
            self._club_pos_grid.addWidget(grp_w)

        # Top 5 players
        while self._club_top_list.count():
            item = self._club_top_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        top = sorted([p for p in squad if p.get('ca')], key=lambda p: -p['ca'])[:5]
        for p in top:
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            ca = p.get('ca', '?')
            pa = p.get('pa', '?')
            row_w = QWidget()
            row_layout = QHBoxLayout(row_w)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(8)
            name_lbl = QLabel(p['name'])
            name_lbl.setStyleSheet(
                f"color:{COLORS['text_primary']}; font-size:12px;")
            pos_lbl = QLabel(pos)
            pos_lbl.setStyleSheet(
                f"color:{COLORS['text_secondary']}; font-size:11px;")
            pos_lbl.setFixedWidth(36)
            ca_lbl = QLabel(f"CA {ca}")
            ca_lbl.setStyleSheet(
                f"color:{COLORS['accent']}; font-size:11px; font-weight:bold;")
            pa_lbl = QLabel(f"PA {pa}")
            pa_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            row_layout.addWidget(name_lbl, 1)
            row_layout.addWidget(pos_lbl)
            row_layout.addWidget(ca_lbl)
            row_layout.addWidget(pa_lbl)
            self._club_top_list.addWidget(row_w)

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
        header_row.addStretch()

        self._squad_info = QLabel('')
        self._squad_info.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        header_row.addWidget(self._squad_info)
        vbox.addWidget(header_bar)

        # Squad tab row — shows "First Team" + sub-squads when loaded
        tab_bar = QFrame()
        tab_bar.setFixedHeight(36)
        tab_bar.setStyleSheet(
            f"background:{COLORS['surface']}; border-bottom:1px solid {COLORS['border']};")
        tab_row = QHBoxLayout(tab_bar)
        tab_row.setContentsMargins(12, 0, 12, 0)
        tab_row.setSpacing(0)

        _squad_tab_ss = f"""
            QPushButton {{
                background: transparent; border: none;
                border-bottom: 2px solid transparent;
                color: {COLORS['text_secondary']};
                padding: 0 14px; font-size: 12px; border-radius: 0;
            }}
            QPushButton:hover {{ color: {COLORS['text_primary']}; }}
            QPushButton:checked {{
                color: {COLORS['text_primary']};
                border-bottom: 2px solid {COLORS['accent']};
                font-weight: bold;
            }}
        """
        self._squad_tab_bar = tab_row   # keep reference to add dynamic tabs later
        self._squad_tab_frame = tab_bar
        self._squad_tab_btns = []

        # First Team tab always present
        ft_btn = QPushButton('First Team')
        ft_btn.setCheckable(True)
        ft_btn.setChecked(True)
        ft_btn.setFixedHeight(36)
        ft_btn.setStyleSheet(_squad_tab_ss)
        tab_row.addWidget(ft_btn)
        self._squad_tab_btns.append(ft_btn)

        tab_row.addStretch()

        # Patch action buttons in tab bar (right side)
        _accent_ss = (
            f"QPushButton {{ background:{COLORS['accent']}; color:#fff; border:none;"
            f" border-radius:2px; padding:4px 14px; font-size:12px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:{COLORS['accent_hover']}; }}"
            f"QPushButton:pressed {{ background:{COLORS['accent_press']}; }}"
            f"QPushButton:disabled {{ background:{COLORS['elevated']}; color:{COLORS['text_dim']}; }}"
        )
        _clear_ss = (
            f"QPushButton {{ background:transparent; color:{COLORS['text_secondary']};"
            f" border:1px solid {COLORS['border']}; border-radius:2px;"
            f" padding:3px 10px; font-size:11px; }}"
            f"QPushButton:hover {{ color:{COLORS['text_primary']}; border-color:{COLORS['border_bright']}; }}"
            f"QPushButton:disabled {{ color:{COLORS['text_dim']}; }}"
        )
        self._patch_hgp_btn = QPushButton('Make HGP')
        self._patch_hgp_btn.setStyleSheet(_accent_ss)
        self._patch_hgp_btn.setFixedHeight(28)
        self._patch_hgp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._patch_hgp_btn.setToolTip('Set selected players as Homegrown Player')
        self._patch_hgp_btn.clicked.connect(self._do_patch_hgp)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn = QPushButton('Make HGC')
        self._patch_hgc_btn.setStyleSheet(_accent_ss)
        self._patch_hgc_btn.setFixedHeight(28)
        self._patch_hgc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._patch_hgc_btn.setToolTip('Set selected players as Homegrown at Club')
        self._patch_hgc_btn.clicked.connect(self._do_patch_hgc)
        self._patch_hgc_btn.setEnabled(False)
        self._clear_sel_btn = QPushButton('Clear')
        self._clear_sel_btn.setStyleSheet(_clear_ss)
        self._clear_sel_btn.setFixedHeight(24)
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
        self._pos_delegate = _PosBadgeDelegate(self._table)
        self._table.setItemDelegateForColumn(1, self._pos_delegate)
        self._configure_table_for_mode('squad')
        vbox.addWidget(self._table)

        # Fix Clear button now that table exists
        self._clear_sel_btn.clicked.disconnect()
        self._clear_sel_btn.clicked.connect(self._table.clearSelection)

        return w

    def _make_view_staff(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        hdr = QFrame()
        hdr.setFixedHeight(44)
        hdr.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(16, 0, 16, 0)
        hdr_lbl = QLabel('Staff')
        hdr_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;")
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        self._staff_count_lbl = QLabel('')
        self._staff_count_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        hdr_row.addWidget(self._staff_count_lbl)
        vbox.addWidget(hdr)

        self._staff_table = QTableWidget()
        self._staff_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._staff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._staff_table.setAlternatingRowColors(True)
        self._staff_table.verticalHeader().setVisible(False)
        self._staff_table.setShowGrid(False)
        self._staff_table.setSortingEnabled(True)
        shdr = self._staff_table.horizontalHeader()
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'Nation', 'Age']
        self._staff_table.setColumnCount(len(cols))
        self._staff_table.setHorizontalHeaderLabels(cols)
        shdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        self._staff_table.setColumnWidth(1, 50)
        self._staff_table.setColumnWidth(2, 40)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        vbox.addWidget(self._staff_table, 1)
        return w

    _STAFF_DISPLAY_LIMIT = 2000

    def _populate_staff_table(self):
        if not self._save_data:
            return
        people = self._save_data.get('people', [])
        staff = [p for p in people if 'ca' not in p]
        display = staff[:self._STAFF_DISPLAY_LIMIT]
        self._staff_table.setSortingEnabled(False)
        self._staff_table.setRowCount(len(display))
        for row, p in enumerate(display):
            name = p.get('name', '')
            nation_id = p.get('nation', 0)
            nation_name = NATIONS.get(nation_id, str(nation_id) if nation_id else '')
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            items = [_SortItem(name), _SortItem(nation_name), _SortItem(str(age), age)]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._staff_table.setItem(row, col, item)
        self._staff_table.setSortingEnabled(True)
        total = len(staff)
        if total > self._STAFF_DISPLAY_LIMIT:
            self._staff_count_lbl.setText(
                f'showing {self._STAFF_DISPLAY_LIMIT:,} of {total:,} staff (filters coming)')
        else:
            self._staff_count_lbl.setText(f'{total:,} staff')

    def _make_view_shortlist(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        hdr = QFrame()
        hdr.setFixedHeight(44)
        hdr.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(16, 0, 16, 0)
        hdr_lbl = QLabel('My Shortlist')
        hdr_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;")
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        self._shortlist_count_lbl = QLabel('0 players')
        self._shortlist_count_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        hdr_row.addWidget(self._shortlist_count_lbl)
        vbox.addWidget(hdr)

        self._shortlist_table = QTableWidget()
        self._shortlist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._shortlist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._shortlist_table.setAlternatingRowColors(True)
        self._shortlist_table.verticalHeader().setVisible(False)
        self._shortlist_table.setShowGrid(False)
        self._shortlist_table.setSortingEnabled(True)
        shdr = self._shortlist_table.horizontalHeader()
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'Club', 'Pos', 'CA', 'PA', 'Age', 'Nation', 'HGP']
        self._shortlist_table.setColumnCount(len(cols))
        self._shortlist_table.setHorizontalHeaderLabels(cols)
        shdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        shdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        for i in range(2, len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        self._shortlist_table.setColumnWidth(1, 160)
        for i, cw in {2: 55, 3: 45, 4: 45, 5: 40, 6: 50, 7: 45}.items():
            self._shortlist_table.setColumnWidth(i, cw)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)

        self._shortlist_empty_lbl = QLabel(
            'Your shortlist is empty.\nDouble-click a player in Squad view to add them.')
        self._shortlist_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._shortlist_empty_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; padding:40px;")
        self._shortlist_empty_lbl.setWordWrap(True)

        self._shortlist_stack = QStackedWidget()
        self._shortlist_stack.addWidget(self._shortlist_empty_lbl)
        self._shortlist_stack.addWidget(self._shortlist_table)
        vbox.addWidget(self._shortlist_stack, 1)
        return w

    def _make_view_reports(self):
        from PyQt6.QtWidgets import QComboBox
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        hdr = QFrame()
        hdr.setFixedHeight(44)
        hdr.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        hdr_row = QHBoxLayout(hdr)
        hdr_row.setContentsMargins(16, 0, 16, 0)
        hdr_row.setSpacing(12)

        self._report_title_lbl = QLabel('Scouting Reports')
        self._report_title_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;")
        hdr_row.addWidget(self._report_title_lbl)

        self._report_pos_bar = QWidget()
        pos_row = QHBoxLayout(self._report_pos_bar)
        pos_row.setContentsMargins(0, 0, 0, 0)
        pos_row.setSpacing(6)
        pos_lbl = QLabel('Position:')
        pos_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
        pos_row.addWidget(pos_lbl)
        self._report_pos_combo = QComboBox()
        self._report_pos_combo.addItems(POSITIONS)
        self._report_pos_combo.setFixedWidth(130)
        self._report_pos_combo.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px;")
        self._report_pos_combo.currentTextChanged.connect(self._on_report_pos_changed)
        pos_row.addWidget(self._report_pos_combo)
        self._report_pos_bar.setVisible(False)
        hdr_row.addWidget(self._report_pos_bar)

        hdr_row.addStretch()
        self._report_count_lbl = QLabel('')
        self._report_count_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        hdr_row.addWidget(self._report_count_lbl)
        vbox.addWidget(hdr)

        self._reports_table = QTableWidget()
        self._reports_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._reports_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._reports_table.setAlternatingRowColors(True)
        self._reports_table.verticalHeader().setVisible(False)
        self._reports_table.setShowGrid(False)
        self._reports_table.setSortingEnabled(True)

        self._reports_pos_delegate = _PosBadgeDelegate(self._reports_table)
        self._reports_table.setItemDelegateForColumn(1, self._reports_pos_delegate)

        rhdr = self._reports_table.horizontalHeader()
        rhdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'Club']
        self._reports_table.setColumnCount(len(cols))
        self._reports_table.setHorizontalHeaderLabels(cols)
        rhdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        rhdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        for i in range(1, 7):
            rhdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        _col_widths = {1: 55, 2: 45, 3: 45, 4: 45, 5: 40, 6: 50}
        for i, cw in _col_widths.items():
            self._reports_table.setColumnWidth(i, cw)
        self._reports_table.setColumnWidth(7, 160)
        rhdr.setSectionsMovable(True)
        rhdr.setFirstSectionMovable(False)
        self._reports_table.doubleClicked.connect(self._on_reports_table_dblclick)
        vbox.addWidget(self._reports_table, 1)
        return w

    def _get_report_players(self, key, pos_name=None):
        if not self._save_data:
            return []
        people = self._save_data.get('people', [])
        season_year = FM_SEASON_YEAR
        if key == 'prospects':
            c = [p for p in people if p.get('pa', 0) >= 160]
            c.sort(key=lambda p: -p['pa'])
        elif key == 'wonderkids':
            c = [p for p in people
                 if p.get('ca') and p.get('birth_year', 0) >= season_year - 21
                 and p.get('pa', 0) >= 150]
            c.sort(key=lambda p: -p['pa'])
        elif key == 'best_pos':
            pname = pos_name or (POSITIONS[0] if POSITIONS else '')
            if pname not in POSITIONS:
                return []
            idx = POSITIONS.index(pname)
            c = [p for p in people if p.get('positions')
                 and p['positions'][idx] == max(p['positions'])]
            c.sort(key=lambda p: -p.get('ca', 0))
        else:
            return []
        return c[:200]

    def _populate_reports_table(self, players):
        if not self._save_data:
            return
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        club_by_id = {c['id']: c['name'] for c in clubs}
        self._reports_table.setSortingEnabled(False)
        self._reports_table.setRowCount(len(players))
        self._reports_table.clearSelection()
        for row, p in enumerate(players):
            try:
                pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            except Exception:
                pos = '?'
            ca = p.get('ca')
            pa = p.get('pa')
            dev = _progress_rate(p)
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            nation_id = p.get('nation', 0)
            flag = _NATION_FLAG.get(nation_id, NATIONS.get(nation_id, ''))
            club_id = squads.get(p.get('id'))
            club_name = club_by_id.get(club_id, '') if club_id else ''
            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item,
                _SortItem(pos),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                _SortItem(club_name),
            ]
            for col, item in enumerate(items):
                if col == 6:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    item.setFont(f)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._reports_table.setItem(row, col, item)
        self._reports_table.setSortingEnabled(True)
        self._report_count_lbl.setText(f'{len(players):,} players')

    def _on_report_pos_changed(self, pos):
        if self._current_report_key == 'best_pos' and self._save_data:
            players = self._get_report_players('best_pos', pos)
            self._populate_reports_table(players)

    def _on_reports_table_dblclick(self, index):
        item = self._reports_table.item(index.row(), 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        people = self._save_data.get('people', []) if self._save_data else []
        p = next((x for x in people if x.get('id') == pid), None)
        if not p:
            return
        squads = self._save_data.get('squads', {})
        clubs = self._save_data.get('clubs', [])
        club_id = squads.get(p['id'])
        if not club_id:
            self._status.showMessage(f"{p['name']} has no club.")
            return
        club = next((c for c in clubs if c['id'] == club_id), None)
        if club:
            self._show_squad(club)

    def _make_view_players(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Header / filter strip
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        hdr_vbox = QVBoxLayout(hdr)
        hdr_vbox.setContentsMargins(0, 0, 0, 0)
        hdr_vbox.setSpacing(0)

        # Title row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(16, 10, 16, 6)
        title_lbl = QLabel('Players')
        title_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        self._players_count_lbl = QLabel('')
        self._players_count_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:11px;")
        title_row.addWidget(self._players_count_lbl)
        hdr_vbox.addLayout(title_row)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(16, 0, 16, 10)
        filter_row.setSpacing(8)

        self._players_name_filter = QLineEdit()
        self._players_name_filter.setPlaceholderText('Filter by name...')
        self._players_name_filter.setFixedHeight(26)
        self._players_name_filter.setMaximumWidth(220)
        self._players_name_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:3px 8px; font-size:11px;")
        self._players_name_filter.returnPressed.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_name_filter)

        self._players_pos_filter = QComboBox()
        self._players_pos_filter.addItem('All Positions')
        self._players_pos_filter.addItems(POSITIONS)
        self._players_pos_filter.setFixedHeight(26)
        self._players_pos_filter.setFixedWidth(130)
        self._players_pos_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px; font-size:11px;")
        self._players_pos_filter.currentIndexChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_pos_filter)

        min_ca_lbl = QLabel('Min CA:')
        min_ca_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(min_ca_lbl)
        self._players_ca_filter = QLineEdit()
        self._players_ca_filter.setPlaceholderText('0')
        self._players_ca_filter.setFixedSize(48, 26)
        self._players_ca_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:3px 6px; font-size:11px;")
        self._players_ca_filter.returnPressed.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_ca_filter)

        nation_lbl = QLabel('Nation:')
        nation_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(nation_lbl)
        self._players_nation_filter = QComboBox()
        self._players_nation_filter.addItem('All Nations')
        for nid in sorted(NATIONS, key=lambda k: NATIONS[k]):
            self._players_nation_filter.addItem(NATIONS[nid], nid)
        self._players_nation_filter.setFixedHeight(26)
        self._players_nation_filter.setFixedWidth(120)
        self._players_nation_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px; font-size:11px;")
        self._players_nation_filter.currentIndexChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_nation_filter)

        filter_row.addStretch()

        clear_btn = QPushButton('Clear')
        clear_btn.setFixedSize(52, 26)
        clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px;")
        clear_btn.clicked.connect(self._clear_players_filter)
        filter_row.addWidget(clear_btn)

        hdr_vbox.addLayout(filter_row)
        vbox.addWidget(hdr)

        # Players table
        self._players_table = QTableWidget()
        self._players_table.setColumnCount(9)
        self._players_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._players_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._players_table.setAlternatingRowColors(True)
        self._players_table.verticalHeader().setVisible(False)
        self._players_table.setShowGrid(False)
        self._players_table.setSortingEnabled(True)
        self._players_table.setStyleSheet(self._table.styleSheet() if hasattr(self, '_table') else '')
        self._players_pos_delegate = _PosBadgeDelegate(self._players_table)
        self._players_table.setItemDelegateForColumn(1, self._players_pos_delegate)

        phdr = self._players_table.horizontalHeader()
        phdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'Club']
        self._players_table.setColumnCount(len(cols))
        self._players_table.setHorizontalHeaderLabels(cols)
        phdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        phdr.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self._players_table.setColumnWidth(8, 160)
        for i in range(1, 8):
            phdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        for i, cw in {1: 55, 2: 45, 3: 45, 4: 45, 5: 40, 6: 50, 7: 45}.items():
            self._players_table.setColumnWidth(i, cw)

        self._players_table.doubleClicked.connect(self._on_players_table_dblclick)
        vbox.addWidget(self._players_table)

        self._all_players_cache = []
        return w

    def _open_players_view(self, players=None, highlight_name=None):
        """Navigate to Players view. If players list given, show those; else load all."""
        self._main_stack.setCurrentIndex(self._VIEW_INDEX['players'])
        for btn in self._nav_btns.values():
            btn.setChecked(False)
        for btn in self._report_btns.values():
            btn.setChecked(False)
        self._players_nav_btn.setChecked(True)

        if players is not None:
            self._all_players_cache = players
        elif not self._all_players_cache and self._save_data:
            people = self._save_data.get('people', [])
            self._all_players_cache = sorted(
                [p for p in people if p.get('ca') is not None],
                key=lambda p: -(p.get('ca') or 0))

        self._clear_players_filter(silent=True)
        self._populate_players_table(self._all_players_cache)

        if highlight_name:
            for r in range(self._players_table.rowCount()):
                item = self._players_table.item(r, 0)
                if item and item.text() == highlight_name:
                    self._players_table.scrollToItem(item)
                    self._players_table.selectRow(r)
                    break

    def _clear_players_filter(self, silent=False):
        self._players_name_filter.blockSignals(True)
        self._players_pos_filter.blockSignals(True)
        self._players_ca_filter.blockSignals(True)
        self._players_nation_filter.blockSignals(True)
        self._players_name_filter.clear()
        self._players_pos_filter.setCurrentIndex(0)
        self._players_ca_filter.clear()
        self._players_nation_filter.setCurrentIndex(0)
        self._players_name_filter.blockSignals(False)
        self._players_pos_filter.blockSignals(False)
        self._players_ca_filter.blockSignals(False)
        self._players_nation_filter.blockSignals(False)

    def _apply_players_filter(self):
        if not self._all_players_cache:
            return
        name_q = self._players_name_filter.text().strip().lower()
        pos_q = self._players_pos_filter.currentText()
        if pos_q == 'All Positions':
            pos_q = ''
        try:
            min_ca = int(self._players_ca_filter.text().strip() or '0')
        except ValueError:
            min_ca = 0
        nation_idx = self._players_nation_filter.currentIndex()
        nation_id = self._players_nation_filter.itemData(nation_idx) if nation_idx > 0 else None

        filtered = self._all_players_cache
        if name_q:
            filtered = [p for p in filtered if name_q in p.get('name', '').lower()]
        if pos_q:
            pos_idx = POSITIONS.index(pos_q)
            filtered = [p for p in filtered
                        if p.get('positions') and p['positions'][pos_idx] == max(p['positions'])]
        if min_ca:
            filtered = [p for p in filtered if (p.get('ca') or 0) >= min_ca]
        if nation_id is not None:
            filtered = [p for p in filtered if p.get('nation') == nation_id]

        self._populate_players_table(filtered)

    def _populate_players_table(self, players):
        if not self._save_data:
            return
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        club_by_id = {c['id']: c['name'] for c in clubs}

        limit = 3000
        display = players[:limit]
        total = len(players)

        self._players_table.setSortingEnabled(False)
        self._players_table.setRowCount(len(display))
        self._players_table.clearSelection()

        for row, p in enumerate(display):
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            ca = p.get('ca')
            pa = p.get('pa')
            dev = _progress_rate(p)
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            nation_id = p.get('nation', 0)
            flag = _NATION_FLAG.get(nation_id, NATIONS.get(nation_id, ''))
            hgp = p.get('hgp', False)
            club_id = squads.get(p.get('id'))
            club_name = club_by_id.get(club_id, '') if club_id else ''

            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item,
                _SortItem(pos),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                _SortItem('HGP' if hgp else '-'),
                _SortItem(club_name),
            ]
            for col, item in enumerate(items):
                if col == 6:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    item.setFont(f)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 7:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgp else COLORS['text_dim']))
                self._players_table.setItem(row, col, item)

        self._players_table.setSortingEnabled(True)
        shown = len(display)
        suffix = f' (showing {shown:,} of {total:,})' if total > limit else f' ({total:,})'
        self._players_count_lbl.setText(
            f'{total:,} players' + (f' · showing {limit:,}' if total > limit else ''))
        self._status.showMessage(
            f"Players{suffix}. Double-click to view a club squad.")

    def _on_players_table_dblclick(self, index):
        item = self._players_table.item(index.row(), 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        people = self._save_data.get('people', []) if self._save_data else []
        p = next((x for x in people if x.get('id') == pid), None)
        if not p:
            return
        squads = self._save_data.get('squads', {})
        clubs = self._save_data.get('clubs', [])
        club_id = squads.get(p['id'])
        if not club_id:
            self._status.showMessage(f"{p['name']} has no club.")
            return
        club = next((c for c in clubs if c['id'] == club_id), None)
        if club:
            self._show_squad(club)

    # -- Navigation -----------------------------------------------------------

    _VIEW_INDEX = {'club': 0, 'squad': 1, 'staff': 2, 'shortlist': 3, 'reports': 4, 'players': 5}

    def _nav_to(self, key: str):
        if key == 'staff' and not getattr(self, '_staff_loaded', False):
            self._populate_staff_table()
            self._staff_loaded = True
        idx = self._VIEW_INDEX.get(key, 0)
        self._main_stack.setCurrentIndex(idx)
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        self._players_nav_btn.setChecked(False)
        if key not in ('squad',):
            for btn in self._report_btns.values():
                btn.setChecked(False)

    def _nav_to_squad_view(self, checked=False):
        if self._squad:
            self._populate_squad_table(self._squad)
        self._main_stack.setCurrentIndex(self._VIEW_INDEX['squad'])
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == 'squad')
        self._players_nav_btn.setChecked(False)
        for btn in self._report_btns.values():
            btn.setChecked(False)

    # -- Table configuration --------------------------------------------------

    def _configure_table_for_mode(self, mode):
        hdr = self._table.horizontalHeader()
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _TT = {
            'CA':  'Current Ability (1-200): overall quality right now',
            'PA':  'Potential Ability (1-200): maximum this player can reach',
            'Dev': 'Development rate (1-20): predicted speed of improvement\n'
                   'Based on ambition, professionalism and determination',
            'Age': 'Age at start of FM24 season',
            'HGP': 'Homegrown Player (nation): trained in England for 3+ years between ages 15-21',
            'HGC': 'Homegrown at Club: trained at THIS club for 3+ years between ages 15-21',
        }
        if mode == 'squad':
            cols = ['Name', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'HGC']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for i in range(1, len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            for i, cw in {1: 55, 2: 45, 3: 45, 4: 45, 5: 40, 6: 50, 7: 45, 8: 45}.items():
                self._table.setColumnWidth(i, cw)
        elif mode == 'scout':
            cols = ['Name', 'Club', 'Pos', 'CA', 'PA', 'Dev', 'Age']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            for i in range(2, len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self._table.setColumnWidth(1, 180)
            for i, cw in {2: 55, 3: 45, 4: 45, 5: 45, 6: 40}.items():
                self._table.setColumnWidth(i, cw)
        else:  # player
            cols = ['Name', 'Club', 'Nation', 'Born', 'HGP']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            for i in range(2, len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self._table.setColumnWidth(1, 200)
            for i, cw in {2: 50, 3: 50, 4: 45}.items():
                self._table.setColumnWidth(i, cw)
        for i, col in enumerate(cols):
            if col in _TT:
                self._table.horizontalHeaderItem(i).setToolTip(_TT[col])
        hdr.setSectionsMovable(True)
        hdr.setFirstSectionMovable(False)
        self._table_mode = mode

    def closeEvent(self, event):
        if self._save_path:
            clear_cache(self._save_path)
        super().closeEvent(event)

    # -- State helpers --------------------------------------------------------

    def _update_ui_state(self):
        has_file = bool(self._save_path)
        has_data = self._save_data is not None
        has_b = has_data and 'b' in self._save_data
        self._reload_btn.setEnabled(has_file)
        self._save_btn.setEnabled(has_b)
        self._search_box.setEnabled(has_data)
        has_abilities = has_data and any(
            'ca' in p for p in self._save_data.get('people', []))
        for btn in self._report_btns.values():
            btn.setEnabled(has_abilities)
        self._players_nav_btn.setEnabled(has_abilities)
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
        self._sb_season.setText(os.path.basename(path))
        self._update_ui_state()
        self._reload_save()

    def _reload_save(self):
        if not self._save_path:
            return
        self._set_busy(True, 'Parsing save file')
        self._worker = ParseWorker(self._save_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._progress.setValue)
        self._worker.done.connect(self._on_parse_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_parse_done(self, result):
        self._save_data = result
        self._save_data['save_path'] = self._save_path
        self._all_players_cache = []  # invalidate on new load
        self._set_busy(False)
        n_clubs = len(result.get('clubs', []))
        n_people = len([p for p in result.get('people', []) if p.get('ca') is not None])
        if self._save_path:
            self._sb_season.setText(os.path.basename(self._save_path))
        self._club_view_name.setText('Save loaded')
        self._club_view_info.setText(
            f"{n_clubs:,} clubs, {n_people:,} players with ability data. "
            "Search for a club or player in the top bar.")
        self._club_stats_frame.setVisible(False)
        self._club_pos_frame.setVisible(False)
        self._club_top_frame.setVisible(False)
        self._club_view_squad_btn.setVisible(False)
        self._status.showMessage(
            f"Loaded: {n_clubs:,} clubs, {n_people:,} players. "
            "Search for a club or player to get started.")
        self._staff_loaded = False
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
                              if p.get('id', -1) != -1 and query_l in p.get('name', '').lower()]
            if not player_matches:
                self._status.showMessage(f"No club or player matching '{query}'.")
                return
            player_matches.sort(key=lambda p: p.get('name', ''))
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
            f'{len(matches)} clubs match "{query}". Pick one:',
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
        dim = COLORS['text_dim']
        self._breadcrumb.setText(
            f"FM Save Editor <span style='color:{dim}'> &rsaquo; </span>"
            f"<b>{club['name']}</b>"
            f"<span style='color:{dim}'> &rsaquo; </span><b>Squad</b>")
        self._breadcrumb.setTextFormat(Qt.TextFormat.RichText)
        self._squad_club_label.setText(club['name'])
        # Update club view
        self._club_view_name.setText(club['name'])
        self._club_view_info.setText(f"{len(squad)} players in squad")
        self._update_club_view()

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
            nation_id = p.get('nation', 0)
            flag = _NATION_FLAG.get(nation_id, NATIONS.get(nation_id, '?'))
            hgp = p.get('hgp', False)
            hgc = is_hgc(b, p, self._club_entity_id) if (b is not None and self._club_entity_id) else None
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            ca = p.get('ca')
            pa = p.get('pa')
            dev = _progress_rate(p)
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)

            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            hgc_text = ('HGC' if hgc else '-') if hgc is not None else '?'

            items = [
                name_item,
                _SortItem(pos),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                _SortItem('HGP' if hgp else '-'),
                _SortItem(hgc_text),
            ]
            for col, item in enumerate(items):
                if col == 6:  # Nation flag — center
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    item.setFont(f)
                else:
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
        self._status.showMessage(f"Showing {self._current_club['name']}: {len(squad)} players")

    def _show_player_results(self, players):
        """Route player search results into the Players view."""
        highlight = players[0]['name'] if len(players) == 1 else None
        self._open_players_view(players=players, highlight_name=highlight)
        if len(players) == 1:
            self._players_name_filter.setText(players[0]['name'])

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

    def _run_report(self, key: str):
        try:
            if not self._save_data:
                return
            if key == 'best_role':
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, 'Best by Role', 'Coming soon: role-based ratings.')
                return
            _labels = {
                'prospects': 'Best Prospects (PA 160+)',
                'wonderkids': 'Wonderkids (U21, PA 150+)',
                'best_pos':   'Best in Position',
            }
            self._current_report_key = key
            for k, btn in self._report_btns.items():
                btn.setChecked(k == key)
            for btn in self._nav_btns.values():
                btn.setChecked(False)
            self._players_nav_btn.setChecked(False)
            self._report_pos_bar.setVisible(key == 'best_pos')
            pos = self._report_pos_combo.currentText() if key == 'best_pos' else None
            players = self._get_report_players(key, pos)
            self._report_title_lbl.setText(_labels.get(key, key))
            self._populate_reports_table(players)
            self._main_stack.setCurrentIndex(self._VIEW_INDEX['reports'])
        except Exception:
            import traceback
            traceback.print_exc()
            self._status.showMessage('Report error — see log.')

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
        self._set_busy(True, 'Patching HGP and writing')
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
        self._set_busy(True, 'Patching HGC and writing')
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
            "This may take 30-60 seconds to recompress.")
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

    def _do_save(self):
        if not self._save_data or 'b' not in self._save_data:
            return
        import datetime
        stem = os.path.splitext(os.path.basename(self._save_path))[0]
        date = datetime.date.today().strftime('%Y-%m-%d')
        default_name = os.path.join(
            os.path.dirname(self._save_path), f'{stem}-Edited-{date}.fm')
        out_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Changes', default_name, 'FM Save Files (*.fm)')
        if not out_path:
            return
        self._set_busy(True, 'Writing save file')
        self._worker = PatchWorker(self._save_data, out_path, [], mode='save_only')
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._progress.setValue)
        self._worker.done.connect(self._on_patch_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # -- Progress / error -----------------------------------------------------

    def _tick_dots(self):
        self._dot_phase = (self._dot_phase + 1) % len(_DOT_SEQ)
        self._status.showMessage(self._status_base + '.' * _DOT_SEQ[self._dot_phase])

    def _on_progress(self, msg):
        self._status_base = msg.rstrip('.')
        self._dot_phase = -1
        self._status.showMessage(self._status_base)

    def _on_error(self, msg):
        self._set_busy(False)
        QMessageBox.critical(self, 'Error', msg)
        self._status.showMessage(f'Error: {msg}')

    def _set_busy(self, busy, msg=''):
        if busy:
            self._progress.setValue(0)
            self._dot_phase = -1
            self._status_base = msg or self._status_base
            self._status.showMessage(self._status_base)
            self._dot_timer.start()
        else:
            self._dot_timer.stop()
        self._progress.setVisible(busy)
        self._load_btn.setEnabled(not busy)
        self._reload_btn.setEnabled(not busy and bool(self._save_path))
        self._save_btn.setEnabled(not busy and bool(self._save_data) and 'b' in (self._save_data or {}))
        self._search_box.setEnabled(not busy and self._save_data is not None)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn.setEnabled(False)
        if msg and not busy:
            self._status.showMessage(msg)
