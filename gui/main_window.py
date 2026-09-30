"""FM24 Save Editor - main window."""
import os
import shutil
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QStatusBar, QFrame, QSizePolicy, QMessageBox,
    QAbstractItemView, QMenu, QStackedWidget, QDialog, QScrollArea,
    QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QSpinBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QRectF, QPoint
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QAction

from gui.theme import COLORS
from gui.roles import role_rating, role_names_by_group, FM_ROLES, _ROLE_INDEX
from fm_editor.cache import load_cache, save_cache, clear_cache
from fm_editor import weights as _weights_mod

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
    '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">'
    '<path fill="{c}" fill-rule="evenodd" d="'
    'M6.5 1.2h3l.35 1.45c.32.1.62.24.9.4l1.38-.47 1.5 2.6-1.05.96'
    'c.04.24.07.49.07.76s-.03.52-.07.76l1.05.96-1.5 2.6-1.38-.47'
    'c-.28.16-.58.3-.9.4L9.5 12.8h-3l-.35-1.45c-.32-.1-.62-.24-.9-.4'
    'l-1.38.47-1.5-2.6 1.05-.96A4.1 4.1 0 0 1 3.35 7.6l-1.05-.96 1.5-2.6'
    ' 1.38.47c.28-.16.58-.3.9-.4L6.5 1.2z'
    ' M8 10a2.4 2.4 0 1 0 0-4.8A2.4 2.4 0 0 0 8 10z"/>'
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
_SVG_LOAD = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 12V6a1 1 0 0 1 1-1h3.5L8 6.5H13a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z"/>'
    '</svg>'
)
_SVG_SAVE = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="2" width="12" height="12" rx="1"/>'
    '<path d="M5 2v4h6V2"/>'
    '<rect x="4.5" y="9" width="7" height="4" rx="0.5"/>'
    '</svg>'
)

# Growing dot cycle: . .. ... ....
_DOT_SEQ = [1, 2, 3, 4]

# Column header tooltips shared across all player tables
_COL_TT = {
    'INJ':    'Injured',
    'Pos':    'Primary playing position',
    'CA':     'Current Ability (1–200)\nOverall quality right now',
    'PA':     'Potential Ability (1–200)\nMaximum this player can reach',
    'Dev':    'Development rate (1–20)\nPredicted improvement speed, based on ambition, professionalism and determination',
    'Rating': 'Role suitability (1–20)\nMean of key attributes for the selected role',
    'HGP':    'Homegrown Player (nation)\nTrained in England for 3+ years between ages 15–21',
    'HGC':    'Homegrown at Club\nTrained at this club for 3+ years between ages 15–21',
    'CtrE':   'Contract End (YYYY-MM)',
    # Attribute abbreviations → full names (display value = max(1, min(20, round(raw/5))))
    'Cro': 'Crossing',      'Dri': 'Dribbling',      'Fin': 'Finishing',
    'Hea': 'Heading',       'Lsh': 'Long Shots',      'Mar': 'Marking',
    'OtB': 'Off The Ball',  'Pas': 'Passing',         'Pen': 'Penalties',
    'Tck': 'Tackling',      'Vis': 'Vision',          'Han': 'Handling',
    'AeR': 'Aerial Reach',  'CoA': 'Cmd of Area',     'Com': 'Communication',
    'Kic': 'Kicking',       'Thr': 'Throwing',        'Ant': 'Anticipation',
    'Dec': 'Decisions',     '1v1': 'One on Ones',     'Psn': 'Positioning',
    'Ref': 'Reflexes',      'Fir': 'First Touch',     'Tec': 'Technique',
    'LFo': 'Left Foot',     'RFo': 'Right Foot',      'Fla': 'Flair',
    'Cor': 'Corners',       'Tea': 'Teamwork',        'Wor': 'Work Rate',
    'LTh': 'Long Throws',   'Ecc': 'Eccentricity',    'RuO': 'Rushing Out',
    'Pun': 'Punching',      'Acc': 'Acceleration',    'FK':  'Free Kick',
    'Str': 'Strength',      'Sta': 'Stamina',         'Pac': 'Pace',
    'JR':  'Jumping Reach', 'Lea': 'Leadership',      'Dir': 'Dirtiness',
    'Bal': 'Balance',       'Bra': 'Bravery',         'Con': 'Consistency',
    'Agg': 'Aggression',    'Agi': 'Agility',         'BM':  'Big Matches',
    'IP':  'Injury Prone',  'Ver': 'Versatility',     'NF':  'Natural Fitness',
    'Det': 'Determination', 'Cmp': 'Composure',       'Cnc': 'Concentration',
}


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


class _HoverTable(QTableWidget):
    """QTableWidget that highlights the full hovered row."""
    _HOVER_COLOR = QColor(105, 51, 189, 26)
    _SEL_HOVER_COLOR = QColor(105, 51, 189, 64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hovered_row = -1
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.viewport():
            if event.type() == event.Type.MouseMove:
                idx = self.indexAt(event.pos())
                row = idx.row() if idx.isValid() else -1
                if row != self._hovered_row:
                    self._hovered_row = row
                    self.viewport().update()
            elif event.type() in (event.Type.Leave, event.Type.HoverLeave):
                self._hovered_row = -1
                self.viewport().update()
        return super().eventFilter(obj, event)

    def drawRow(self, painter, option, index):
        super().drawRow(painter, option, index)
        if index.row() == self._hovered_row:
            color = (self._SEL_HOVER_COLOR
                     if self.selectionModel().isRowSelected(index.row())
                     else self._HOVER_COLOR)
            painter.save()
            painter.fillRect(option.rect, color)
            painter.restore()


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
                                          find_people, match_identities, find_abilities,
                                          find_employment, find_contracts, find_club_staff,
                                          find_coaching_attrs, find_injuries,
                                          find_staff_extras)
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
            squads, sub_squads = find_squads(b, clubs, names_start)

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

            self._emit("Scanning employment records...", 91)
            employment = find_employment(b, people)

            self._emit("Scanning contract dates...", 92)
            contracts = find_contracts(b, people)
            for p in people:
                ce = contracts.get(p.get('id', -1))
                if ce:
                    p['contract_end'] = ce

            self._emit("Scanning club staff arrays...", 93)
            club_staff = find_club_staff(b, clubs, people, abilities, names_start)

            player_ids = set(abilities.keys())
            self._emit("Parsing coaching attributes...", 94)
            find_coaching_attrs(b, people, player_ids)
            self._emit("Scanning injuries...", 95)
            find_injuries(b, people, player_ids)
            self._emit("Parsing staff ability (CA/PA)...", 96)
            find_staff_extras(b, people, player_ids)

            self._emit("Caching results...", 98)
            save_cache(self.save_path, clubs, squads, sub_squads, people, employment, club_staff)

            self.pct.emit(100)
            result = {
                'clubs': clubs, 'squads': squads, 'sub_squads': sub_squads, 'people': people,
                'employment': employment, 'club_staff': club_staff,
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
            gdb_m = next((m for m in members if m['name'] == 'game_db.dat'), None)
            if gdb_m is None:
                self.error.emit('game_db.dat member not found in archive')
                return
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

_STAFF_COL_TOOLTIPS = {
    'Age': 'Age', 'Club': 'Club',
    'Atk': 'Attacking', 'Def': 'Defending', 'Fit': 'Fitness',
    'Mnt': 'Mental',    'SPc': 'Set Pieces', 'Tac': 'Tactical',
    'Tch': 'Technical', 'WwY': 'Working with Youngsters',
    'Det': 'Determination', 'Mot': 'Motivating', 'PMg': 'People Management',
    'JPA': 'Judging Player Ability', 'JSA': 'Judging Staff Ability',
    'TKn': 'Tactical Knowledge',
    'Neg': 'Negotiating', 'GKH': 'GK Handling', 'GKS': 'GK Shot Stopping',
    'Adp': 'Adaptability', 'Amb': 'Ambition', 'Loy': 'Loyalty',
    'Prs': 'Pressure',    'Pro': 'Professionalism', 'Spt': 'Sportsmanship',
    'Tmp': 'Temperament', 'Ctr': 'Controversy',
}

# Position → (background, foreground) matching mockup color scheme
_POS_BADGE_COLORS = {
    'INJ': ('#8B1A1A', '#FFFFFF'),  # dark red injury badge
    'GK':  ('#C07B2A', '#FFFFFF'),
    'SW':  ('#3A6BA8', '#FFFFFF'),
    'DL':  ('#3A6BA8', '#FFFFFF'), 'DC': ('#3A6BA8', '#FFFFFF'),
    'DR':  ('#3A6BA8', '#FFFFFF'),
    'DM':  ('#5A3A8A', '#FFFFFF'),  # purple — distinct from DC blue
    'WBL': ('#3A6BA8', '#FFFFFF'), 'WBR': ('#3A6BA8', '#FFFFFF'),
    'ML':  ('#3A8A5A', '#FFFFFF'), 'MC': ('#3A8A5A', '#FFFFFF'),
    'MR':  ('#3A8A5A', '#FFFFFF'), 'AML': ('#3A8A5A', '#FFFFFF'),
    'AMC': ('#3A8A5A', '#FFFFFF'), 'AMR': ('#3A8A5A', '#FFFFFF'),
    'ST':  ('#A83A3A', '#FFFFFF'),
}

# Default sort order for position column (lower = higher in list)
_POS_SORT_ORDER = {
    'GK': 0,
    'DR': 1, 'WBR': 2, 'DL': 3, 'WBL': 4,
    'DC': 5, 'SW': 6,
    'DM': 7, 'MC': 8,
    'MR': 9, 'AMR': 10, 'ML': 11, 'AML': 12,
    'AMC': 13, 'ST': 14,
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
        self._shortlist_added = False
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
        action_row.addStretch()
        add_shortlist = QPushButton('Add to Shortlist')
        add_shortlist.setStyleSheet(_btn_ss)
        add_shortlist.setCursor(Qt.CursorShape.PointingHandCursor)
        add_shortlist.clicked.connect(lambda: self._do_add_shortlist())
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

    def _do_add_shortlist(self):
        self._shortlist_added = True
        self.accept()


class StaffDetailDialog(QDialog):
    _PERS_LABELS = [
        ('Adaptability', 0), ('Ambition', 1), ('Loyalty', 2), ('Pressure', 3),
        ('Professionalism', 4), ('Sportsmanship', 5), ('Temperament', 6), ('Controversy', 7),
    ]

    def __init__(self, person, save_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(person.get('name', 'Staff'))
        self.setMinimumSize(680, 480)
        self.resize(780, 560)
        self._person = person
        self._save_data = save_data
        self._shortlist_added = False
        self._build()

    def _build(self):
        p = self._person
        nation_name = NATIONS.get(p.get('nation', 0), f"n={p.get('nation', 0)}")
        age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
        personality = p.get('personality', [])

        # Resolve club name
        club_name = ''
        if self._save_data:
            clubs = self._save_data.get('clubs', [])
            club_by_id = {c['id']: c['name'] for c in clubs}
            club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
            club_staff = self._save_data.get('club_staff', {})
            employment = self._save_data.get('employment', {})
            pid = p.get('id', -1)
            staff_club: dict[int, int] = {}
            for cid, pids in club_staff.items():
                for ppid in pids:
                    if ppid not in staff_club:
                        staff_club[ppid] = cid
            cid = staff_club.get(pid)
            if cid is not None:
                club_name = club_by_id.get(cid, '')
            else:
                entity_id = employment.get(pid)
                club_name = club_by_entity.get(entity_id, '') if entity_id else ''

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
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
        name_lbl = QLabel(p.get('name', ''))
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:14px; font-weight:bold;")
        sub_lbl = QLabel(f"{nation_name}  ·  Age {age}")
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

        # Body
        body = QWidget()
        body.setStyleSheet(f"background:{COLORS['window_bg']};")
        body_hbox = QHBoxLayout(body)
        body_hbox.setContentsMargins(0, 0, 0, 0)
        body_hbox.setSpacing(0)

        # Left panel
        left = QFrame()
        left.setFixedWidth(190)
        left.setStyleSheet(
            f"background:{COLORS['surface']}; border-right:1px solid {COLORS['border']};")
        left_vbox = QVBoxLayout(left)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        photo = QFrame()
        photo.setFixedSize(190, 120)
        photo.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        photo_inner = QVBoxLayout(photo)
        photo_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_icon = QLabel()
        photo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_icon.setPixmap(_svg_icon(_SVG_STAFF, COLORS['text_dim'], 48).pixmap(48, 48))
        photo_inner.addWidget(photo_icon)
        left_vbox.addWidget(photo)

        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"border-bottom:1px solid {COLORS['border']}; background:transparent;")
        info_vbox = QVBoxLayout(info_frame)
        info_vbox.setContentsMargins(12, 8, 12, 8)
        info_vbox.setSpacing(0)

        def _info_row(label: str, value: str):
            row = QHBoxLayout()
            row.setContentsMargins(0, 3, 0, 3)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            val = QLabel(value)
            val.setStyleSheet(
                f"color:{COLORS['text_primary']}; font-size:11px; font-weight:500;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            return row

        if club_name:
            info_vbox.addLayout(_info_row('Club', club_name))
        info_vbox.addLayout(_info_row('Nation', nation_name))
        info_vbox.addLayout(_info_row('Age', str(age)))
        left_vbox.addWidget(info_frame)
        left_vbox.addStretch()
        body_hbox.addWidget(left)

        coaching = p.get('coaching', {})
        _COACHING_DISPLAY = {
            'WwY': 'Working w/ Youngsters', 'People Mgt': 'People Management',
            'JPA': 'Judging Player Ability', 'JSA': 'Judging Staff Ability',
            'Tact Knowledge': 'Tactical Knowledge', 'GK Shot Stop': 'GK Shot Stopping',
        }
        _COACHING_LEFT = [
            'Attacking', 'Defending', 'Fitness', 'Mental', 'Set Pieces',
            'Tactical', 'Technical', 'WwY', 'People Mgt',
        ]
        _COACHING_RIGHT = [
            'Determination', 'Motivating', 'JPA', 'JSA',
            'Tact Knowledge', 'Negotiating', 'GK Handling', 'GK Shot Stop',
        ]

        # Center: coaching + personality
        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{COLORS['window_bg']}; }}")
        center_w = QWidget()
        center_w.setStyleSheet(f"background:{COLORS['window_bg']};")
        center_vbox = QVBoxLayout(center_w)
        center_vbox.setContentsMargins(16, 16, 16, 16)
        center_vbox.setSpacing(8)

        def _section_title(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:1px;"
                f"border-bottom:1px solid {COLORS['border']}; padding-bottom:4px; margin-bottom:2px;")
            return lbl

        def _attr_bar_row(label, v, label_w=150):
            row = QHBoxLayout()
            row.setSpacing(6)
            n = QLabel(label)
            n.setFixedWidth(label_w)
            n.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
            bar_bg = QFrame()
            bar_bg.setFixedHeight(4)
            bar_bg.setStyleSheet(f"background:{COLORS['border']}; border-radius:2px;")
            bar_fill = QFrame(bar_bg)
            bar_fill.setFixedHeight(4)
            bar_fill.setStyleSheet(f"background:{COLORS['accent']}; border-radius:2px;")
            bar_fill.setMaximumWidth(int(120 * v / 20))
            v_lbl = QLabel(str(v))
            v_lbl.setFixedWidth(24)
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            v_lbl.setStyleSheet(
                f"color:{_attr_val_color(v)}; font-size:11px; font-weight:bold;")
            row.addWidget(n)
            row.addWidget(bar_bg, 1)
            row.addWidget(v_lbl)
            return row

        if coaching:
            center_vbox.addWidget(_section_title('COACHING ATTRIBUTES'))
            cols_w = QWidget()
            cols_w.setStyleSheet("background:transparent;")
            cols_hbox = QHBoxLayout(cols_w)
            cols_hbox.setContentsMargins(0, 0, 0, 0)
            cols_hbox.setSpacing(16)

            for col_keys in (_COACHING_LEFT, _COACHING_RIGHT):
                col_w = QWidget()
                col_w.setStyleSheet("background:transparent;")
                col_vbox = QVBoxLayout(col_w)
                col_vbox.setContentsMargins(0, 0, 0, 0)
                col_vbox.setSpacing(4)
                for key in col_keys:
                    v = coaching.get(key)
                    if v is None:
                        continue
                    display = _COACHING_DISPLAY.get(key, key)
                    col_vbox.addLayout(_attr_bar_row(display, v))
                col_vbox.addStretch()
                cols_hbox.addWidget(col_w, 1)

            center_vbox.addWidget(cols_w)

        staff_ca = p.get('staff_ca')
        staff_pa = p.get('staff_pa')
        if staff_ca is not None:
            center_vbox.addWidget(_section_title('ABILITY'))
            ab_row = QHBoxLayout()
            ab_row.setSpacing(24)
            for label, val in (('CA', staff_ca), ('PA', staff_pa)):
                pair = QHBoxLayout()
                pair.setSpacing(6)
                lbl = QLabel(label)
                lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
                num = QLabel(str(val))
                num.setStyleSheet(
                    f"color:{_attr_val_color(round(val / 10))};"
                    f" font-size:13px; font-weight:bold;")
                pair.addWidget(lbl)
                pair.addWidget(num)
                ab_row.addLayout(pair)
            ab_row.addStretch()
            center_vbox.addLayout(ab_row)

        center_vbox.addWidget(_section_title('PERSONALITY'))
        if personality:
            for attr_name, idx in self._PERS_LABELS:
                v = personality[idx] if idx < len(personality) else 0
                center_vbox.addLayout(_attr_bar_row(attr_name, v))
        else:
            no_data = QLabel('No personality data available.')
            no_data.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            center_vbox.addWidget(no_data)

        center_vbox.addStretch()

        # Action strip
        action_frame = QFrame()
        action_frame.setStyleSheet(
            f"border-top:1px solid {COLORS['border']}; background:transparent;")
        action_row = QHBoxLayout(action_frame)
        action_row.setContentsMargins(0, 8, 0, 4)
        action_row.addStretch()
        _btn_ss = f"""
            QPushButton {{
                background:{COLORS['accent']}; color:#fff; border:none;
                padding:6px 16px; font-weight:bold; border-radius:2px; font-size:11px;
            }}
            QPushButton:hover {{ background:{COLORS['accent_hover']}; }}
            QPushButton:pressed {{ background:{COLORS['accent_press']}; }}
        """
        add_btn = QPushButton('Add to Shortlist')
        add_btn.setStyleSheet(_btn_ss)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda checked=False: self._do_add_shortlist())
        action_row.addWidget(add_btn)
        center_vbox.addWidget(action_frame)

        center_scroll.setWidget(center_w)
        body_hbox.addWidget(center_scroll, 1)
        layout.addWidget(body)

    def _do_add_shortlist(self):
        self._shortlist_added = True
        self.accept()


# -- Role attribute names for weight editor ------------------------------------

# Short column labels for the squad table (54 attrs, same order as raw_attrs)
_ATTR_ABBREV = [
    'Cro', 'Dri', 'Fin', 'Hea', 'Lsh', 'Mar', 'OtB', 'Pas', 'Pen', 'Tck', 'Vis', 'Han',
    'AeR', 'CoA', 'Com', 'Kic', 'Thr', 'Ant', 'Dec', '1v1', 'Psn', 'Ref', 'Fir', 'Tec',
    'LFo', 'RFo', 'Fla', 'Cor', 'Tea', 'Wor', 'LTh', 'Ecc', 'RuO', 'Pun', 'Acc', 'FK',
    'Str', 'Sta', 'Pac', 'JR',  'Lea', 'Dir', 'Bal', 'Bra', 'Con', 'Agg', 'Agi', 'BM',
    'IP',  'Ver', 'NF',  'Det', 'Cmp', 'Cnc',
]

_ATTR_DISPLAY = [
    'Crossing', 'Dribbling', 'Finishing', 'Heading', 'Long Shots', 'Marking',
    'Off The Ball', 'Passing', 'Penalties', 'Tackling', 'Vision', 'Handling',
    'Aerial Reach', 'Cmd of Area', 'Communication', 'Kicking', 'Throwing',
    'Anticipation', 'Decisions', 'One on Ones', 'Positioning', 'Reflexes',
    'First Touch', 'Technique', 'Left Foot', 'Right Foot', 'Flair', 'Corners',
    'Teamwork', 'Work Rate', 'Long Throws', 'Eccentricity', 'Rushing Out',
    'Punching', 'Acceleration', 'Free Kick', 'Strength', 'Stamina', 'Pace',
    'Jumping Reach', 'Leadership', 'Dirtiness', 'Balance', 'Bravery',
    'Consistency', 'Aggression', 'Agility', 'Big Matches', 'Injury Prone',
    'Versatility', 'Natural Fitness', 'Determination', 'Composure', 'Concentration',
]

_DIALOG_SS = lambda: f"""
    QDialog {{
        background: {COLORS['window_bg']};
        color: {COLORS['text_primary']};
    }}
    QLabel {{
        color: {COLORS['text_primary']};
        background: transparent;
    }}
    QComboBox, QSpinBox {{
        background: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 2px;
        padding: 2px 6px;
        min-height: 24px;
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background: {COLORS['elevated']};
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['selection_bg']};
        border: 1px solid {COLORS['border_bright']};
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: {COLORS['surface']}; width: 6px; border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border_bright']}; border-radius: 3px; min-height: 20px;
    }}
"""

_BTN_SS = lambda accent=False: (
    f"QPushButton {{ background: {COLORS['accent'] if accent else COLORS['surface']};"
    f" color: {'#fff' if accent else COLORS['text_primary']};"
    f" border: {'none' if accent else '1px solid ' + COLORS['border']};"
    f" border-radius: 3px; padding: 5px 14px; font-size: 12px; }}"
    f"QPushButton:hover {{ background: {COLORS['accent'] if accent else COLORS['selection_bg']}; }}"
    f"QPushButton:disabled {{ opacity: 0.4; }}"
)


# -- Weight editor dialog -------------------------------------------------------

class WeightEditorDialog(QDialog):
    """Edit per-role attribute weights. Operates on a mutable copy of a preset."""

    def __init__(self, base_preset: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Role Weight Editor')
        self.setMinimumSize(520, 580)
        self.setStyleSheet(_DIALOG_SS())
        self._edited: dict[str, dict[int, int]] = {
            role: dict(w) for role, w in base_preset.get('roles', {}).items()
        }
        self._current_role = None
        self._spinboxes: dict[int, QSpinBox] = {}
        self._saved_preset_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Role selector
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(QLabel('Role:'))
        self._role_combo = QComboBox()
        self._role_combo.setFixedWidth(260)
        for group, names in role_names_by_group():
            sep = self._role_combo.count()
            self._role_combo.addItem(f'── {group} ──')
            self._role_combo.model().item(sep).setEnabled(False)
            for name in names:
                self._role_combo.addItem(name)
        self._role_combo.setCurrentIndex(1)
        top.addWidget(self._role_combo)
        top.addStretch()
        layout.addLayout(top)

        # Info label
        self._info_lbl = QLabel('Zero = attribute not used for this role.')
        self._info_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
        layout.addWidget(self._info_lbl)

        # Attr list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner.setStyleSheet(f"background:{COLORS['surface']}; border-radius:3px;")
        self._attr_layout = QVBoxLayout(inner)
        self._attr_layout.setContentsMargins(10, 8, 10, 8)
        self._attr_layout.setSpacing(4)
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(8)
        reset_btn = QPushButton('Reset Role')
        reset_btn.setStyleSheet(_BTN_SS())
        reset_btn.clicked.connect(self._reset_current_role)
        btns.addWidget(reset_btn)
        btns.addStretch()
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setStyleSheet(_BTN_SS())
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        save_btn = QPushButton('Save as New Preset…')
        save_btn.setStyleSheet(_BTN_SS(accent=True))
        save_btn.clicked.connect(self._save_as)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

        self._role_combo.currentTextChanged.connect(self._on_role_changed)
        self._on_role_changed(self._role_combo.currentText())

    def _on_role_changed(self, role_name: str):
        if not role_name or role_name.startswith('──'):
            return
        self._flush_current()
        self._current_role = role_name

        # Clear old spinboxes
        while self._attr_layout.count():
            item = self._attr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._spinboxes.clear()

        key_indices = set(_ROLE_INDEX.get(role_name, ()))
        current_weights = self._edited.get(role_name, {})

        for idx, name in enumerate(_ATTR_DISPLAY):
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(name)
            lbl.setFixedWidth(140)
            lbl.setStyleSheet(
                f"color:{COLORS['text_primary'] if idx in key_indices else COLORS['text_dim']};"
                f"font-size:12px;")
            row.addWidget(lbl)
            spin = QSpinBox()
            spin.setRange(0, 20)
            spin.setFixedWidth(55)
            spin.setValue(current_weights.get(idx, 0))
            spin.setStyleSheet(
                f"QSpinBox {{ background:{COLORS['elevated']};"
                f" color:{COLORS['text_primary']}; border:1px solid {COLORS['border']};"
                f" border-radius:2px; padding:1px 4px; font-size:12px; }}")
            row.addWidget(spin)
            if idx in key_indices:
                kw_lbl = QLabel('key attr')
                kw_lbl.setStyleSheet(f"color:{COLORS['accent']}; font-size:10px;")
                row.addWidget(kw_lbl)
            row.addStretch()
            container = QWidget()
            container.setLayout(row)
            self._attr_layout.addWidget(container)
            self._spinboxes[idx] = spin

        self._attr_layout.addStretch()

    def _flush_current(self):
        if self._current_role and self._spinboxes:
            self._edited[self._current_role] = {
                idx: spin.value() for idx, spin in self._spinboxes.items()
                if spin.value() > 0
            }

    def _reset_current_role(self):
        if not self._current_role:
            return
        # Restore equal-weight defaults from key_indices
        key_indices = _ROLE_INDEX.get(self._current_role, ())
        for idx, spin in self._spinboxes.items():
            spin.setValue(10 if idx in key_indices else 0)

    def _save_as(self):
        self._flush_current()
        name, ok = QInputDialog.getText(self, 'Save Preset', 'Preset name:')
        if not ok or not name.strip():
            return
        name = name.strip()
        desc, ok2 = QInputDialog.getText(self, 'Save Preset', 'Description (optional):')
        if not ok2:
            return
        path = _weights_mod.save_custom_preset(name, desc.strip(), self._edited)
        self._saved_preset_path = path
        self.accept()

    def saved_preset_name(self) -> str | None:
        if not self._saved_preset_path:
            return None
        try:
            import json
            with open(self._saved_preset_path, encoding='utf-8') as f:
                return json.load(f).get('name')
        except Exception:
            return None


# -- Settings dialog ------------------------------------------------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setMinimumSize(460, 320)
        self.setStyleSheet(_DIALOG_SS())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(14)

        # Section title
        sec_lbl = QLabel('Role Weights')
        sec_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;"
            f" padding-bottom:2px; border-bottom:1px solid {COLORS['border']};")
        layout.addWidget(sec_lbl)

        # Preset row
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_row.addWidget(QLabel('Preset:'))
        self._preset_combo = QComboBox()
        self._preset_combo.setMinimumWidth(200)
        self._presets = _weights_mod.list_presets()
        active = _weights_mod.get_active_preset_name()
        active_idx = 0
        for i, p in enumerate(self._presets):
            self._preset_combo.addItem(p['name'])
            if p['name'] == active:
                active_idx = i
        self._preset_combo.setCurrentIndex(active_idx)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self._preset_combo)
        self._edit_btn = QPushButton('Edit Weights…')
        self._edit_btn.setStyleSheet(_BTN_SS())
        self._edit_btn.clicked.connect(self._edit_weights)
        preset_row.addWidget(self._edit_btn)
        layout.addLayout(preset_row)

        # Import / delete row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        import_btn = QPushButton('Import Preset…')
        import_btn.setStyleSheet(_BTN_SS())
        import_btn.clicked.connect(self._import_preset)
        action_row.addWidget(import_btn)
        self._delete_btn = QPushButton('Delete Preset')
        self._delete_btn.setStyleSheet(_BTN_SS())
        self._delete_btn.clicked.connect(self._delete_preset)
        action_row.addWidget(self._delete_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        # Description
        self._desc_lbl = QLabel()
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:11px;"
            f" background:{COLORS['surface']}; border-radius:3px; padding:8px;")
        layout.addWidget(self._desc_lbl)

        layout.addStretch()

        # OK / Cancel
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setStyleSheet(_BTN_SS())
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        ok_btn = QPushButton('Apply')
        ok_btn.setStyleSheet(_BTN_SS(accent=True))
        ok_btn.clicked.connect(self._apply)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        self._on_preset_changed(active_idx)

    def _on_preset_changed(self, idx: int):
        if 0 <= idx < len(self._presets):
            p = self._presets[idx]
            parts = []
            if p['tactical_style']:
                parts.append(f"Style: {p['tactical_style']}")
            if p['description']:
                parts.append(p['description'])
            self._desc_lbl.setText('\n'.join(parts) if parts else 'No description.')
            self._delete_btn.setEnabled(not p['bundled'])
            self._edit_btn.setEnabled(True)

    def _edit_weights(self):
        idx = self._preset_combo.currentIndex()
        if not (0 <= idx < len(self._presets)):
            return
        p = self._presets[idx]
        try:
            base_preset = _weights_mod.load_preset(p['path'])
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not load preset:\n{e}')
            return
        dlg = WeightEditorDialog(base_preset, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_name = dlg.saved_preset_name()
            if new_name:
                self._refresh_presets(select_name=new_name)

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Import Weight Preset', '', 'JSON Files (*.json)')
        if not path:
            return
        try:
            name = _weights_mod.import_preset(path)
            self._refresh_presets(select_name=name)
        except Exception as e:
            QMessageBox.warning(self, 'Import Error', f'Could not import preset:\n{e}')

    def _delete_preset(self):
        idx = self._preset_combo.currentIndex()
        if not (0 <= idx < len(self._presets)):
            return
        p = self._presets[idx]
        if p['bundled']:
            return
        if QMessageBox.question(
                self, 'Delete Preset',
                f"Delete '{p['name']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        _weights_mod.delete_user_preset(p['name'])
        self._refresh_presets()

    def _refresh_presets(self, select_name: str | None = None):
        self._presets = _weights_mod.list_presets()
        current = self._preset_combo.currentText()
        self._preset_combo.blockSignals(True)
        self._preset_combo.clear()
        select_idx = 0
        for i, p in enumerate(self._presets):
            self._preset_combo.addItem(p['name'])
            if select_name and p['name'] == select_name:
                select_idx = i
            elif not select_name and p['name'] == current:
                select_idx = i
        self._preset_combo.blockSignals(False)
        self._preset_combo.setCurrentIndex(select_idx)
        self._on_preset_changed(select_idx)

    def _apply(self):
        idx = self._preset_combo.currentIndex()
        if 0 <= idx < len(self._presets):
            _weights_mod.set_active_preset_name(self._presets[idx]['name'])
        self.accept()

    def selected_preset_name(self) -> str:
        idx = self._preset_combo.currentIndex()
        if 0 <= idx < len(self._presets):
            return self._presets[idx]['name']
        return ''


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
        self._report_ratings = {}
        self._active_preset = _weights_mod.load_active_preset()

        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(420)
        self._dot_timer.timeout.connect(self._tick_dots)

        self._shimmer_phase = 0.0
        self._progress_target = 0.0
        self._progress_displayed = 0.0
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(30)
        self._shimmer_timer.timeout.connect(self._tick_shimmer)

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
                border-left: 3px solid transparent;
                color: {COLORS['text_secondary']};
                text-align: left;
                padding: 7px 15px 7px 12px;
                font-size: 12px;
                border-radius: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['elevated']};
                color: {COLORS['text_primary']};
                border-left: 3px solid {COLORS['border_bright']};
            }}
            QPushButton:checked {{
                background: {COLORS['selection_bg']};
                color: {COLORS['text_primary']};
                font-weight: bold;
                border-left: 3px solid {COLORS['accent']};
            }}
            QPushButton:disabled {{
                color: {COLORS['text_dim']};
                background: transparent;
                border-left: 3px solid transparent;
            }}
        """)
        return btn

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:10px; font-weight:600; "
            "letter-spacing:1.2px; padding:10px 15px 3px;"
        )
        return lbl

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_hbox = QHBoxLayout(root)
        root_hbox.setContentsMargins(0, 0, 0, 0)
        root_hbox.setSpacing(0)

        # Sidebar spans full window height
        root_hbox.addWidget(self._make_sidebar())

        # Right side: topbar + progress + content
        right = QWidget()
        right_vbox = QVBoxLayout(right)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(0)

        right_vbox.addWidget(self._make_topbar())

        self._progress = QProgressBar()
        self._progress.setRange(0, 10000)
        self._progress.setValue(0)
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background:{COLORS['elevated']}; border:none; }}
            QProgressBar::chunk {{ background:{COLORS['accent']}; }}
        """)
        right_vbox.addWidget(self._progress)

        self._main_stack = QStackedWidget()
        self._main_stack.addWidget(self._make_view_club())        # 0
        self._main_stack.addWidget(self._make_view_squad())       # 1
        self._main_stack.addWidget(self._make_view_staff())       # 2
        self._main_stack.addWidget(self._make_view_shortlist())   # 3
        self._main_stack.addWidget(self._make_view_reports())     # 4
        self._main_stack.addWidget(self._make_view_players())     # 5
        self._main_stack.addWidget(self._make_view_club_staff())  # 6
        right_vbox.addWidget(self._main_stack)

        self._status = QStatusBar()
        self._status.setSizeGripEnabled(False)
        self._status_ready_lbl = QLabel('Open an FM24 save file to get started.')
        self._status_ready_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._status_ready_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        self._status.addWidget(self._status_ready_lbl, 1)
        self._status_info_lbl = QLabel('')
        self._status_info_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._status_info_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px; padding-right:8px;")
        self._status.addPermanentWidget(self._status_info_lbl)
        right_vbox.addWidget(self._status)
        root_hbox.addWidget(right)
        self.statusBar().hide()
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
        self._back_btn = QPushButton('◀')
        self._back_btn.setFixedSize(26, 26)
        self._back_btn.setEnabled(False)
        self._back_btn.setStyleSheet(_nav_ss)
        self._back_btn.clicked.connect(self._nav_back)
        self._fwd_btn = QPushButton('▶')
        self._fwd_btn.setFixedSize(26, 26)
        self._fwd_btn.setEnabled(False)
        self._fwd_btn.setStyleSheet(_nav_ss)
        self._fwd_btn.clicked.connect(self._nav_fwd)
        self._nav_history: list[tuple] = []
        self._nav_pos: int = -1
        back_btn = self._back_btn
        fwd_btn = self._fwd_btn

        self._breadcrumb = QLabel('FM Save Editor')
        self._breadcrumb.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:12px; background:transparent;")

        layout.addWidget(back_btn)
        layout.addWidget(fwd_btn)

        # Centred search
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('Search clubs, players or staff...')
        self._search_box.setEnabled(False)
        self._search_box.returnPressed.connect(self._do_search)
        self._search_box.setFixedHeight(28)
        self._search_box.setMaximumWidth(16777215)  # no cap
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

        layout.addWidget(self._search_box, 1)

        _tbtn_ss = (
            f"QPushButton {{ background:{COLORS['elevated']}; color:{COLORS['text_secondary']};"
            f" border:1px solid {COLORS['border']}; border-radius:2px;"
            f" padding:4px 10px; font-size:11px; }}"
            f"QPushButton:hover {{ background:{COLORS['border']}; color:{COLORS['text_primary']}; }}"
            f"QPushButton:disabled {{ color:{COLORS['text_dim']}; }}"
        )
        _tbtn_accent_ss = (
            f"QPushButton {{ background:{COLORS['accent']}; color:#fff;"
            f" border:none; border-radius:2px;"
            f" padding:4px 10px; font-size:11px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:{COLORS['accent_hover']}; }}"
            f"QPushButton:pressed {{ background:{COLORS['accent_press']}; }}"
            f"QPushButton:disabled {{ background:{COLORS['elevated']}; color:{COLORS['text_dim']};"
            f" border:1px solid {COLORS['border']}; font-weight:normal; }}"
        )

        # Save button (left of Load)
        self._save_btn = QPushButton('Save Changes')
        self._save_btn.setFixedHeight(28)
        self._save_btn.setEnabled(False)
        self._save_btn.setToolTip('Save current file (default: SaveName-Edited-DATE)')
        self._save_btn.setIcon(_svg_icon(_SVG_SAVE, COLORS['text_secondary'], 13))
        self._save_btn.setIconSize(QSize(13, 13))
        self._save_btn.setStyleSheet(_tbtn_ss)
        self._save_btn.clicked.connect(self._do_save)

        # Load button
        self._load_btn = QPushButton('Load')
        self._load_btn.setFixedHeight(28)
        self._load_btn.setObjectName('accent')
        self._load_btn.setToolTip('Open an FM24 save file')
        self._load_btn.setIcon(_svg_icon(_SVG_LOAD, '#fff', 13))
        self._load_btn.setIconSize(QSize(13, 13))
        self._load_btn.setStyleSheet(_tbtn_accent_ss)
        self._load_btn.clicked.connect(self._load_file)

        # Reload button (right of Load, greyed when no file)
        self._reload_btn = QPushButton('Reload')
        self._reload_btn.setFixedHeight(28)
        self._reload_btn.setEnabled(False)
        self._reload_btn.setToolTip('Re-parse the current save file')
        self._reload_btn.setIcon(_svg_icon(_SVG_RELOAD, COLORS['text_secondary'], 13))
        self._reload_btn.setIconSize(QSize(13, 13))
        self._reload_btn.setStyleSheet(_tbtn_ss)
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

        self._settings_btn.clicked.connect(self._open_settings)
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
        self._sb_season.setTextFormat(Qt.TextFormat.RichText)
        self._sb_season.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:11px;"
            "padding:0 15px 10px; background:transparent;")
        vbox.addWidget(self._sb_club_name)
        vbox.addWidget(self._sb_season)
        vbox.addWidget(self._make_hline())

        # Main nav
        vbox.addWidget(self._make_section_label('MAIN'))
        self._nav_btns = {}
        for key, svg, label in [
            ('club',       _SVG_CLUB,      'Club'),
            ('squad',      _SVG_SQUAD,     'Squads'),
            ('club_staff', _SVG_STAFF,     'Club Staff'),
            ('shortlist',  _SVG_SHORTLIST, 'My Shortlist'),
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

        self._scouting_staff_nav_btn = self._make_nav_btn(
            _SVG_STAFF, 'Staff', lambda checked: self._nav_to('staff'))
        self._scouting_staff_nav_btn.setEnabled(False)
        vbox.addWidget(self._scouting_staff_nav_btn)

        vbox.addWidget(self._make_section_label('PLAYER REPORTS'))

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

        vbox.addWidget(self._make_hline())
        vbox.addWidget(self._make_section_label('STAFF REPORTS'))
        staff_rpt_btn = self._make_nav_btn(_SVG_REPORT, 'Coming Soon', lambda checked: None)
        staff_rpt_btn.setEnabled(False)
        vbox.addWidget(staff_rpt_btn)

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
        self._squad_info.setTextFormat(Qt.TextFormat.RichText)
        self._squad_info.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        header_row.addWidget(self._squad_info)
        vbox.addWidget(header_bar)

        # Squad tab row — shows "First Team" + sub-squads when loaded
        tab_bar = QFrame()
        tab_bar.setFixedHeight(40)
        tab_bar.setStyleSheet(
            f"background:{COLORS['surface']}; border-bottom:1px solid {COLORS['border']};")
        tab_row = QHBoxLayout(tab_bar)
        tab_row.setContentsMargins(12, 3, 12, 0)
        tab_row.setSpacing(0)

        _squad_tab_ss = f"""
            QPushButton {{
                background: transparent; border: none;
                border-bottom: 2px solid transparent;
                color: {COLORS['text_secondary']};
                padding: 0px 16px; font-size: 12px; border-radius: 0;
                min-width: 80px;
            }}
            QPushButton:hover {{ color: {COLORS['text_primary']}; }}
            QPushButton:checked {{
                color: {COLORS['text_primary']};
                border-bottom: 2px solid {COLORS['accent']};
                font-weight: bold;
            }}
        """
        self._squad_tab_ss_str = _squad_tab_ss
        self._squad_tab_bar = tab_row   # keep reference to add dynamic tabs later
        self._squad_tab_frame = tab_bar
        self._squad_tab_btns = []
        self._squad_tab_dynamic_btns = []

        # First Team tab always present
        ft_btn = QPushButton('First Team')
        ft_btn.setCheckable(True)
        ft_btn.setChecked(True)
        ft_btn.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
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
        tab_row.addWidget(self._patch_hgp_btn)
        tab_row.addSpacing(4)
        tab_row.addWidget(self._patch_hgc_btn)
        tab_row.addSpacing(4)
        vbox.addWidget(tab_bar)

        # Table
        self._table = _HoverTable()
        self._table.setColumnCount(9)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setEnabled(False)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_table_context_menu)
        self._inj_delegate = _PosBadgeDelegate(self._table)
        self._pos_delegate = _PosBadgeDelegate(self._table)
        self._table.setItemDelegateForColumn(1, self._inj_delegate)
        self._table.setItemDelegateForColumn(2, self._pos_delegate)
        self._configure_table_for_mode('squad')
        vbox.addWidget(self._table)


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
        vbox.addWidget(hdr)

        self._staff_table = _HoverTable()
        self._staff_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._staff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._staff_table.setAlternatingRowColors(True)
        self._staff_table.verticalHeader().setVisible(False)
        self._staff_table.setShowGrid(False)
        self._staff_table.setSortingEnabled(True)
        shdr = self._staff_table.horizontalHeader()
        shdr.setHighlightSections(False)
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _COACHING_COLS = [
            'Atk', 'Def', 'Fit', 'Mnt', 'SPc', 'Tac', 'Tch', 'WwY',
            'Det', 'Mot', 'PMg',
            'JPA', 'JSA', 'TKn',
            'Neg', 'GKH', 'GKS',
        ]
        self._staff_coaching_cols = _COACHING_COLS
        self._coaching_col_map = {
            'Atk': 'Attacking', 'Def': 'Defending', 'Fit': 'Fitness',
            'Mnt': 'Mental',    'SPc': 'Set Pieces', 'Tac': 'Tactical',
            'Tch': 'Technical', 'WwY': 'WwY',
            'Det': 'Determination', 'Mot': 'Motivating', 'PMg': 'People Mgt',
            'JPA': 'JPA',       'JSA': 'JSA',       'TKn': 'Tact Knowledge',
            'Neg': 'Negotiating', 'GKH': 'GK Handling', 'GKS': 'GK Shot Stop',
        }
        cols = ['Name', 'Club', 'Nation', 'Age'] + _COACHING_COLS + [
            'Adp', 'Amb', 'Loy', 'Prs', 'Pro', 'Spt', 'Tmp', 'Ctr']
        self._staff_table.setColumnCount(len(cols))
        self._staff_table.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _STAFF_COL_TOOLTIPS:
                self._staff_table.horizontalHeaderItem(i).setToolTip(_STAFF_COL_TOOLTIPS[col])
        for i in range(len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        widths = {0: 200, 1: 160, 2: 50, 3: 40}
        for i in range(4, len(cols)):
            widths[i] = 35
        for i, cw in widths.items():
            self._staff_table.setColumnWidth(i, cw)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        shdr.setStretchLastSection(False)
        self._staff_table.cellDoubleClicked.connect(self._on_staff_double_click)
        vbox.addWidget(self._staff_table, 1)
        return w

    def _populate_staff_table(self):
        if not self._save_data:
            return
        people = self._save_data.get('people', [])
        employment = self._save_data.get('employment', {})
        club_staff = self._save_data.get('club_staff', {})
        clubs = self._save_data.get('clubs', [])
        club_by_id = {c['id']: c['name'] for c in clubs}
        club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
        # Build reverse map: person_id -> club_id from club_staff arrays
        staff_club: dict[int, int] = {}
        for cid, pids in club_staff.items():
            for pid in pids:
                if pid not in staff_club:
                    staff_club[pid] = cid
        staff = [p for p in people if 'ca' not in p]
        coaching_cols = getattr(self, '_staff_coaching_cols', [])
        coaching_col_map = getattr(self, '_coaching_col_map', {})
        self._staff_table.setSortingEnabled(False)
        self._staff_table.setRowCount(len(staff))
        for row, p in enumerate(staff):
            pid = p.get('id', -1)
            name = p.get('name', '')
            # club_staff array first, fall back to employment record
            cid = staff_club.get(pid)
            if cid is not None:
                club_name = club_by_id.get(cid, '')
            else:
                entity_id = employment.get(pid)
                club_name = club_by_entity.get(entity_id, '') if entity_id else ''
            nation_id = p.get('nation', 0)
            flag = _NATION_FLAG.get(nation_id, NATIONS.get(nation_id, ''))
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            coaching = p.get('coaching', {})
            coaching_items = []
            for short_label in coaching_cols:
                key = coaching_col_map.get(short_label, short_label)
                v = coaching.get(key)
                coaching_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            pers = p.get('personality', [])
            pers_items = []
            for idx in range(8):
                v = pers[idx] if idx < len(pers) else None
                pers_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            name_item = _SortItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            items = [name_item, _SortItem(club_name), _SortItem(flag), _SortItem(str(age), age)] + coaching_items + pers_items
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._staff_table.setItem(row, col, item)
        self._staff_table.setSortingEnabled(True)
        for i in range(self._staff_table.columnCount()):
            self._staff_table.resizeColumnToContents(i)
        total = len(staff)
        self._staff_count_lbl.setText(f'{total:,} staff')
        self._status_info_lbl.setText(f'{total:,} staff')

    def _make_view_club_staff(self):
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
        self._club_staff_title_lbl = QLabel('Club Staff')
        self._club_staff_title_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:13px; font-weight:bold;")
        hdr_row.addWidget(self._club_staff_title_lbl)
        hdr_row.addStretch()
        vbox.addWidget(hdr)

        self._club_staff_table = _HoverTable()
        self._club_staff_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._club_staff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._club_staff_table.setAlternatingRowColors(True)
        self._club_staff_table.verticalHeader().setVisible(False)
        self._club_staff_table.setShowGrid(False)
        self._club_staff_table.setSortingEnabled(True)
        self._club_staff_table.setStyleSheet(self._staff_table.styleSheet())
        shdr = self._club_staff_table.horizontalHeader()
        shdr.setHighlightSections(False)
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # Coaching cols (Section B confirmed + Section A extras), then personality
        _STAFF_COACHING_COLS = [
            'Atk', 'Def', 'Fit', 'Mnt', 'SPc', 'Tac', 'Tch', 'WwY',  # coaching area
            'Det', 'Mot', 'PMg',                                          # mental
            'JPA', 'JSA', 'TKn',                                          # knowledge
            'Neg', 'GKH', 'GKS',                                          # other
        ]
        self._club_staff_coaching_cols = _STAFF_COACHING_COLS
        # Map short label → coaching dict key
        self._coaching_col_map = {
            'Atk': 'Attacking', 'Def': 'Defending', 'Fit': 'Fitness',
            'Mnt': 'Mental',    'SPc': 'Set Pieces','Tac': 'Tactical',
            'Tch': 'Technical', 'WwY': 'WwY',
            'Det': 'Determination', 'Mot': 'Motivating', 'PMg': 'People Mgt',
            'JPA': 'JPA',       'JSA': 'JSA',       'TKn': 'Tact Knowledge',
            'Neg': 'Negotiating','GKH': 'GK Handling','GKS': 'GK Shot Stop',
        }
        cols = ['Name', 'Nation', 'Age'] + _STAFF_COACHING_COLS + [
            'Adp', 'Amb', 'Loy', 'Prs', 'Pro', 'Spt', 'Tmp', 'Ctr']
        self._club_staff_table.setColumnCount(len(cols))
        self._club_staff_table.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _STAFF_COL_TOOLTIPS:
                self._club_staff_table.horizontalHeaderItem(i).setToolTip(_STAFF_COL_TOOLTIPS[col])
        for i in range(len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        widths = {0: 220, 1: 45, 2: 38}
        for i in range(3, len(cols)):
            widths[i] = 35
        for i, cw in widths.items():
            self._club_staff_table.setColumnWidth(i, cw)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        shdr.setStretchLastSection(False)
        self._club_staff_table.cellDoubleClicked.connect(self._on_club_staff_double_click)
        vbox.addWidget(self._club_staff_table, 1)
        return w

    def _populate_club_staff_table(self):
        if not self._save_data or not self._current_club:
            return
        club = self._current_club
        people = self._save_data.get('people', [])
        employment = self._save_data.get('employment', {})
        club_staff = self._save_data.get('club_staff', {})

        # Primary: club-side staff array (coaches, physios, scouts, analysts).
        # Fallback: employment records for managers / ex-player coaches.
        cid = club['id']
        staff_pids = set(club_staff.get(cid, []))
        # Add any employment-linked staff not already in the array
        club_entity_id = cid + 1
        for pid, eid in employment.items():
            if eid == club_entity_id:
                staff_pids.add(pid)

        people_by_id = {p.get('id'): p for p in people}
        staff = [people_by_id[pid] for pid in staff_pids
                 if pid in people_by_id and 'ca' not in people_by_id[pid]]
        staff.sort(key=lambda p: p.get('name', ''))

        self._club_staff_title_lbl.setText(f'{club["name"]} - Club Staff')
        self._club_staff_table.setSortingEnabled(False)
        self._club_staff_table.setRowCount(len(staff))
        coaching_col_map = getattr(self, '_coaching_col_map', {})
        coaching_cols = getattr(self, '_club_staff_coaching_cols', [])
        for row, p in enumerate(staff):
            pid = p.get('id', -1)
            name = p.get('name', '')
            nation_id = p.get('nation', 0)
            flag = _NATION_FLAG.get(nation_id, NATIONS.get(nation_id, ''))
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            coaching = p.get('coaching', {})
            coaching_items = []
            for short_label in coaching_cols:
                key = coaching_col_map.get(short_label, short_label)
                v = coaching.get(key)
                coaching_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            pers = p.get('personality', [])
            pers_items = []
            for idx in range(8):
                v = pers[idx] if idx < len(pers) else None
                pers_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            name_item = _SortItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            items = [name_item, _SortItem(flag), _SortItem(str(age), age)] + coaching_items + pers_items
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._club_staff_table.setItem(row, col, item)
        self._club_staff_table.setSortingEnabled(True)
        for i in range(self._club_staff_table.columnCount()):
            self._club_staff_table.resizeColumnToContents(i)
        self._status_info_lbl.setText(f'{len(staff):,} staff')

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
        self._shortlist_count_lbl = QLabel('0 people')
        self._shortlist_count_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:11px;")
        hdr_row.addWidget(self._shortlist_count_lbl)
        vbox.addWidget(hdr)

        self._shortlist_table = _HoverTable()
        self._shortlist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._shortlist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._shortlist_table.setAlternatingRowColors(True)
        self._shortlist_table.verticalHeader().setVisible(False)
        self._shortlist_table.setShowGrid(False)
        self._shortlist_table.setSortingEnabled(True)
        shdr = self._shortlist_table.horizontalHeader()
        shdr.setHighlightSections(False)
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'Club', 'Type', 'Pos', 'CA', 'PA', 'Age', 'Nation']
        self._shortlist_table.setColumnCount(len(cols))
        self._shortlist_table.setHorizontalHeaderLabels(cols)
        for i in range(len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        for i, cw in {0: 150, 1: 160, 2: 55, 3: 55, 4: 45, 5: 45, 6: 40, 7: 50}.items():
            self._shortlist_table.setColumnWidth(i, cw)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        shdr.setStretchLastSection(True)

        self._shortlist_empty_lbl = QLabel(
            'Your shortlist is empty.\nDouble-click a player or staff member to add them.')
        self._shortlist_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._shortlist_empty_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; padding:40px;")
        self._shortlist_empty_lbl.setWordWrap(True)

        self._shortlist_stack = QStackedWidget()
        self._shortlist_stack.addWidget(self._shortlist_empty_lbl)
        self._shortlist_stack.addWidget(self._shortlist_table)
        vbox.addWidget(self._shortlist_stack, 1)
        return w

    def _add_to_shortlist(self, person):
        pid = person.get('id', -1)
        if any(p.get('id') == pid for p in self._shortlist):
            return
        self._shortlist.append(person)
        self._populate_shortlist()
        self._status.showMessage(f'Added {person.get("name", "")} to shortlist', 2000)

    def _populate_shortlist(self):
        people = self._shortlist
        self._shortlist_table.setSortingEnabled(False)
        self._shortlist_table.setRowCount(len(people))
        clubs = self._save_data.get('clubs', []) if self._save_data else []
        squads = self._save_data.get('squads', {}) if self._save_data else {}
        club_staff = self._save_data.get('club_staff', {}) if self._save_data else {}
        employment = self._save_data.get('employment', {}) if self._save_data else {}
        club_by_id = {c['id']: c['name'] for c in clubs}
        club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
        staff_club: dict[int, int] = {}
        for cid, pids in club_staff.items():
            for ppid in pids:
                if ppid not in staff_club:
                    staff_club[ppid] = cid
        for row, p in enumerate(people):
            pid = p.get('id', -1)
            is_player = 'ca' in p
            name = p.get('name', '')
            # Club
            if is_player:
                cid = squads.get(pid)
                club_name = club_by_id.get(cid, '') if cid else ''
            else:
                cid = staff_club.get(pid)
                if cid is not None:
                    club_name = club_by_id.get(cid, '')
                else:
                    eid = employment.get(pid)
                    club_name = club_by_entity.get(eid, '') if eid else ''
            ptype = 'Player' if is_player else 'Staff'
            pos = _primary_pos(p['positions']) if is_player and p.get('positions') else '-'
            ca = str(p.get('ca', '-')) if is_player else '-'
            pa = str(p.get('pa', '-')) if is_player else '-'
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            nation = NATIONS.get(p.get('nation', 0), '')
            name_item = _SortItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            row_items = [
                name_item,
                _SortItem(club_name),
                _SortItem(ptype),
                _SortItem(pos),
                _SortItem(ca, p.get('ca', -1) if is_player else -1),
                _SortItem(pa, p.get('pa', -1) if is_player else -1),
                _SortItem(str(age), age),
                _SortItem(nation),
            ]
            for col, item in enumerate(row_items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._shortlist_table.setItem(row, col, item)
        self._shortlist_table.setSortingEnabled(True)
        for c in range(self._shortlist_table.columnCount()):
            self._shortlist_table.resizeColumnToContents(c)
        n = len(people)
        self._shortlist_count_lbl.setText(f'{n} {"person" if n == 1 else "people"}')
        self._shortlist_stack.setCurrentIndex(1 if n > 0 else 0)

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
        hdr_row.addStretch()

        self._report_count_lbl = QLabel('')
        vbox.addWidget(hdr)

        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            f"background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']};")
        filter_frame.setFixedHeight(38)
        filter_row2 = QHBoxLayout(filter_frame)
        filter_row2.setContentsMargins(16, 0, 16, 0)
        filter_row2.setSpacing(12)
        vbox.addWidget(filter_frame)

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
        filter_row2.addWidget(self._report_pos_bar)

        # Role picker bar (best_role mode)
        self._report_role_bar = QWidget()
        role_row = QHBoxLayout(self._report_role_bar)
        role_row.setContentsMargins(0, 0, 0, 0)
        role_row.setSpacing(6)
        role_lbl = QLabel('Role:')
        role_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
        role_row.addWidget(role_lbl)
        self._report_role_combo = QComboBox()
        self._report_role_combo.setFixedWidth(220)
        self._report_role_combo.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px;")
        for group, names in role_names_by_group():
            sep = self._report_role_combo.count()
            self._report_role_combo.addItem(f'── {group} ──')
            self._report_role_combo.model().item(sep).setEnabled(False)
            for name in names:
                self._report_role_combo.addItem(name)
        self._report_role_combo.setCurrentIndex(1)  # first real role, skip group header
        self._report_role_combo.currentTextChanged.connect(self._on_report_role_changed)
        role_row.addWidget(self._report_role_combo)
        self._weights_lbl = QLabel()
        self._report_role_bar.setVisible(False)
        filter_row2.addWidget(self._report_role_bar)

        filter_row2.addStretch()

        # Age range filter — always visible
        _spin_ss = (
            f"QSpinBox {{ background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f" border:1px solid {COLORS['border']}; border-radius:2px;"
            f" padding:1px 2px 1px 4px; font-size:12px; }}"
            f"QSpinBox::up-button {{ subcontrol-origin:border; subcontrol-position:top right;"
            f" width:14px; height:10px; background:{COLORS['elevated']};"
            f" border-left:1px solid {COLORS['border']}; border-bottom:1px solid {COLORS['border']};"
            f" border-top-right-radius:2px; }}"
            f"QSpinBox::down-button {{ subcontrol-origin:border; subcontrol-position:bottom right;"
            f" width:14px; height:10px; background:{COLORS['elevated']};"
            f" border-left:1px solid {COLORS['border']};"
            f" border-bottom-right-radius:2px; }}"
            f"QSpinBox::up-button:hover, QSpinBox::down-button:hover"
            f" {{ background:{COLORS['border']}; }}"
        )
        age_lbl = QLabel('Age:')
        age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
        filter_row2.addWidget(age_lbl)
        self._report_age_min = QSpinBox()
        self._report_age_min.setRange(15, 60)
        self._report_age_min.setValue(15)
        self._report_age_min.setFixedWidth(52)
        self._report_age_min.setStyleSheet(_spin_ss)
        filter_row2.addWidget(self._report_age_min)
        dash_lbl = QLabel('-')
        dash_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:12px;")
        filter_row2.addWidget(dash_lbl)
        self._report_age_max = QSpinBox()
        self._report_age_max.setRange(15, 60)
        self._report_age_max.setValue(45)
        self._report_age_max.setFixedWidth(52)
        self._report_age_max.setStyleSheet(_spin_ss)
        filter_row2.addWidget(self._report_age_max)
        self._report_age_min.valueChanged.connect(self._on_report_age_changed)
        self._report_age_max.valueChanged.connect(self._on_report_age_changed)

        self._reports_table = _HoverTable()
        self._reports_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._reports_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._reports_table.setAlternatingRowColors(True)
        self._reports_table.verticalHeader().setVisible(False)
        self._reports_table.setShowGrid(False)
        self._reports_table.setSortingEnabled(True)

        self._reports_inj_delegate = _PosBadgeDelegate(self._reports_table)
        self._reports_pos_delegate = _PosBadgeDelegate(self._reports_table)
        self._reports_table.setItemDelegateForColumn(1, self._reports_inj_delegate)
        self._reports_table.setItemDelegateForColumn(2, self._reports_pos_delegate)

        rhdr = self._reports_table.horizontalHeader()
        rhdr.setHighlightSections(False)
        rhdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'INJ', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'Club', 'CtrE'] + _ATTR_ABBREV
        self._reports_table.setColumnCount(len(cols))
        self._reports_table.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _COL_TT:
                self._reports_table.horizontalHeaderItem(i).setToolTip(_COL_TT[col])
        for i in range(len(cols)):
            rhdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        fixed_widths = {0: 150, 1: 35, 2: 55, 3: 45, 4: 45, 5: 45, 6: 40, 7: 50, 8: 45, 9: 160, 10: 65}
        for i, cw in fixed_widths.items():
            self._reports_table.setColumnWidth(i, cw)
        for i in range(11, len(cols)):
            self._reports_table.setColumnWidth(i, 35)
        rhdr.setSectionsMovable(True)
        rhdr.setFirstSectionMovable(False)
        rhdr.setStretchLastSection(True)
        self._reports_table.doubleClicked.connect(self._on_reports_table_dblclick)
        self._reports_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._reports_table.customContextMenuRequested.connect(
            lambda pos: self._on_list_table_context_menu(self._reports_table, pos))
        vbox.addWidget(self._reports_table, 1)
        return w

    def _get_report_players(self, key, pos_name=None, role_name=None):
        self._report_ratings = {}
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
        elif key == 'best_role':
            rname = role_name or ''
            role_weights = _weights_mod.get_role_weights(self._active_preset, rname)
            mn_age = self._report_age_min.value()
            mx_age = self._report_age_max.value()
            rated = []
            for p in people:
                age = season_year - p.get('birth_year', season_year)
                if not (mn_age <= age <= mx_age):
                    continue
                r = role_rating(p, rname, role_weights)
                if r is not None:
                    rated.append((p, r))
            rated.sort(key=lambda x: -x[1])
            rated = rated[:200]
            self._report_ratings = {p.get('id', -1): r for p, r in rated}
            return [p for p, _ in rated]
        else:
            return []
        mn_age = self._report_age_min.value()
        mx_age = self._report_age_max.value()
        c = [p for p in c if mn_age <= (season_year - p.get('birth_year', season_year)) <= mx_age]
        return c[:200]

    def _populate_reports_table(self, players):
        if not self._save_data:
            return
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        club_by_id = {c['id']: c['name'] for c in clubs}
        is_role = self._current_report_key == 'best_role'
        ratings = getattr(self, '_report_ratings', {})
        rhdr = self._reports_table.horizontalHeader()
        col4_label = 'Rating' if is_role else 'Dev'
        self._reports_table.setHorizontalHeaderItem(5, _SortItem(col4_label))
        self._reports_table.horizontalHeaderItem(5).setToolTip(_COL_TT.get(col4_label, ''))
        rhdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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
            col4_val = ratings.get(p.get('id'), None) if is_role else _progress_rate(p)
            age = FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)
            nation_id = p.get('nation', 0)
            flag = _NATION_FLAG.get(nation_id, NATIONS.get(nation_id, ''))
            club_id = squads.get(p.get('id'))
            club_name = club_by_id.get(club_id, '') if club_id else ''
            injured = p.get('injured', False)
            injury_days = p.get('injury_days', 0)
            contract_end = p.get('contract_end', '')
            raw_attrs = p.get('raw_attrs', [])
            hgp = p.get('hgp', False)

            inj_item = _SortItem('INJ' if injured else '', 1 if injured else 0)
            if injured and injury_days > 0:
                inj_item.setToolTip(f"Out for {injury_days} days")

            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item,
                inj_item,
                _SortItem(pos, _POS_SORT_ORDER.get(pos, 99)),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(col4_val) if col4_val is not None else '?',
                          col4_val if col4_val is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                _SortItem('HGP' if hgp else '-'),
                _SortItem(club_name),
                _SortItem(contract_end),
            ]
            for raw in raw_attrs:
                dv = max(1, min(20, round(raw / 5)))
                items.append(_SortItem(str(dv), dv))
            while len(items) < 11 + 54:
                items.append(_SortItem(''))
            for col, item in enumerate(items):
                if col == 7:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    item.setFont(f)
                elif col == 8:
                    text_dim = COLORS.get('text_dim', COLORS.get('text_secondary', '#888'))
                    item.setForeground(QColor('#4caf50') if hgp else QColor(text_dim))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._reports_table.setItem(row, col, item)
        self._reports_table.setSortingEnabled(True)
        self._reports_table.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        self._report_count_lbl.setText(f'{len(players):,} players')
        info = f'{len(players):,} players'
        if self._current_report_key == 'best_role':
            preset = self._weights_lbl.text().strip('[]')
            if preset:
                info += f'  ·  {preset}'
        self._status_info_lbl.setText(info)

    def _on_report_pos_changed(self, pos):
        if self._current_report_key == 'best_pos' and self._save_data:
            players = self._get_report_players('best_pos', pos)
            self._populate_reports_table(players)

    def _on_report_role_changed(self, role):
        if self._current_report_key == 'best_role' and self._save_data:
            if not role or role.startswith('──'):
                return
            players = self._get_report_players('best_role', role_name=role)
            self._report_title_lbl.setText('Best by Role')
            self._populate_reports_table(players)

    def _on_report_age_changed(self):
        if not self._current_report_key or not self._save_data:
            return
        mn, mx = self._report_age_min.value(), self._report_age_max.value()
        if mn > mx:
            return
        key = self._current_report_key
        pos = self._report_pos_combo.currentText() if key == 'best_pos' else None
        role = self._report_role_combo.currentText() if key == 'best_role' else None
        if role and role.startswith('──'):
            return
        players = self._get_report_players(key, pos, role)
        self._populate_reports_table(players)

    def _on_reports_table_dblclick(self, index):
        item = self._reports_table.item(index.row(), 0)
        if item:
            self._open_player_detail_by_pid(item.data(Qt.ItemDataRole.UserRole))

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

        _spin_ss = (
            f"QSpinBox {{ background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f" border:1px solid {COLORS['border']}; border-radius:2px;"
            f" padding:1px 2px 1px 4px; font-size:12px; }}"
            f"QSpinBox::up-button {{ subcontrol-origin:border; subcontrol-position:top right;"
            f" width:14px; height:10px; background:{COLORS['elevated']};"
            f" border-left:1px solid {COLORS['border']}; border-bottom:1px solid {COLORS['border']};"
            f" border-top-right-radius:2px; }}"
            f"QSpinBox::down-button {{ subcontrol-origin:border; subcontrol-position:bottom right;"
            f" width:14px; height:10px; background:{COLORS['elevated']};"
            f" border-left:1px solid {COLORS['border']};"
            f" border-bottom-right-radius:2px; }}"
            f"QSpinBox::up-button:hover, QSpinBox::down-button:hover"
            f" {{ background:{COLORS['border']}; }}"
        )
        min_ca_lbl = QLabel('Min CA:')
        min_ca_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(min_ca_lbl)
        self._players_ca_filter = QSpinBox()
        self._players_ca_filter.setRange(0, 200)
        self._players_ca_filter.setValue(0)
        self._players_ca_filter.setFixedSize(56, 26)
        self._players_ca_filter.setStyleSheet(_spin_ss)
        self._players_ca_filter.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_ca_filter)

        min_pa_lbl = QLabel('Min PA:')
        min_pa_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(min_pa_lbl)
        self._players_pa_filter = QSpinBox()
        self._players_pa_filter.setRange(0, 200)
        self._players_pa_filter.setValue(0)
        self._players_pa_filter.setFixedSize(56, 26)
        self._players_pa_filter.setStyleSheet(_spin_ss)
        self._players_pa_filter.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_pa_filter)

        age_lbl = QLabel('Age:')
        age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(age_lbl)
        self._players_age_min = QSpinBox()
        self._players_age_min.setRange(15, 60)
        self._players_age_min.setValue(15)
        self._players_age_min.setFixedSize(52, 26)
        self._players_age_min.setStyleSheet(_spin_ss)
        self._players_age_min.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_age_min)
        dash = QLabel('-')
        dash.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(dash)
        self._players_age_max = QSpinBox()
        self._players_age_max.setRange(15, 60)
        self._players_age_max.setValue(60)
        self._players_age_max.setFixedSize(52, 26)
        self._players_age_max.setStyleSheet(_spin_ss)
        self._players_age_max.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_age_max)

        dev_lbl = QLabel('Min Dev:')
        dev_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(dev_lbl)
        self._players_dev_filter = QSpinBox()
        self._players_dev_filter.setRange(0, 20)
        self._players_dev_filter.setValue(0)
        self._players_dev_filter.setFixedSize(52, 26)
        self._players_dev_filter.setStyleSheet(_spin_ss)
        self._players_dev_filter.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_dev_filter)

        filter_row.addStretch()

        clear_btn = QPushButton('Clear')
        clear_btn.setFixedHeight(26)
        clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        clear_btn.clicked.connect(self._clear_players_filter)
        filter_row.addWidget(clear_btn)

        hdr_vbox.addLayout(filter_row)
        vbox.addWidget(hdr)

        # Players table
        self._players_table = _HoverTable()
        self._players_table.setColumnCount(9)
        self._players_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._players_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._players_table.setAlternatingRowColors(True)
        self._players_table.verticalHeader().setVisible(False)
        self._players_table.setShowGrid(False)
        self._players_table.setSortingEnabled(True)
        self._players_table.setStyleSheet(self._table.styleSheet() if hasattr(self, '_table') else '')
        self._players_inj_delegate = _PosBadgeDelegate(self._players_table)
        self._players_pos_delegate = _PosBadgeDelegate(self._players_table)
        self._players_table.setItemDelegateForColumn(1, self._players_inj_delegate)
        self._players_table.setItemDelegateForColumn(2, self._players_pos_delegate)

        phdr = self._players_table.horizontalHeader()
        phdr.setHighlightSections(False)
        phdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'INJ', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'Club', 'CtrE'] + _ATTR_ABBREV
        self._players_table.setColumnCount(len(cols))
        self._players_table.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _COL_TT:
                self._players_table.horizontalHeaderItem(i).setToolTip(_COL_TT[col])
        for i in range(len(cols)):
            phdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        fixed_widths = {0: 150, 1: 35, 2: 55, 3: 45, 4: 45, 5: 45, 6: 40, 7: 50, 8: 45, 9: 160, 10: 65}
        for i, cw in fixed_widths.items():
            self._players_table.setColumnWidth(i, cw)
        for i in range(11, len(cols)):
            self._players_table.setColumnWidth(i, 35)
        phdr.setStretchLastSection(True)

        self._players_table.doubleClicked.connect(self._on_players_table_dblclick)
        self._players_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._players_table.customContextMenuRequested.connect(
            lambda pos: self._on_list_table_context_menu(self._players_table, pos))
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
        self._scouting_staff_nav_btn.setChecked(False)

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
        self._players_pa_filter.blockSignals(True)
        self._players_age_min.blockSignals(True)
        self._players_age_max.blockSignals(True)
        self._players_dev_filter.blockSignals(True)
        self._players_name_filter.clear()
        self._players_pos_filter.setCurrentIndex(0)
        self._players_ca_filter.setValue(0)
        self._players_pa_filter.setValue(0)
        self._players_age_min.setValue(15)
        self._players_age_max.setValue(60)
        self._players_dev_filter.setValue(0)
        self._players_name_filter.blockSignals(False)
        self._players_pos_filter.blockSignals(False)
        self._players_ca_filter.blockSignals(False)
        self._players_pa_filter.blockSignals(False)
        self._players_age_min.blockSignals(False)
        self._players_age_max.blockSignals(False)
        self._players_dev_filter.blockSignals(False)

    def _apply_players_filter(self):
        if not self._all_players_cache:
            return
        name_q = self._players_name_filter.text().strip().lower()
        pos_q = self._players_pos_filter.currentText()
        if pos_q == 'All Positions':
            pos_q = ''
        min_ca = self._players_ca_filter.value()
        min_pa = self._players_pa_filter.value()
        age_min = self._players_age_min.value()
        age_max = self._players_age_max.value()
        min_dev = self._players_dev_filter.value()

        filtered = self._all_players_cache
        if name_q:
            filtered = [p for p in filtered if name_q in p.get('name', '').lower()]
        if pos_q and pos_q in POSITIONS:
            pos_idx = POSITIONS.index(pos_q)
            filtered = [p for p in filtered
                        if p.get('positions') and pos_idx < len(p['positions'])
                        and p['positions'][pos_idx] == max(p['positions'])]
        if min_ca:
            filtered = [p for p in filtered if (p.get('ca') or 0) >= min_ca]
        if min_pa:
            filtered = [p for p in filtered if (p.get('pa') or 0) >= min_pa]
        age_min_eff = age_min if age_min > 15 else 0
        age_max_eff = age_max if age_max < 60 else 999
        if age_min_eff or age_max_eff < 999:
            filtered = [p for p in filtered if age_min_eff <= (FM_SEASON_YEAR - p.get('birth_year', FM_SEASON_YEAR)) <= age_max_eff]
        if min_dev:
            filtered = [p for p in filtered if (_progress_rate(p) or 0) >= min_dev]

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

            injured = p.get('injured', False)
            injury_days = p.get('injury_days', 0)
            contract_end = p.get('contract_end', '')
            raw_attrs = p.get('raw_attrs', [])

            inj_item = _SortItem('INJ' if injured else '', 1 if injured else 0)
            if injured and injury_days > 0:
                inj_item.setToolTip(f"Out for {injury_days} days")

            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            items = [
                name_item,
                inj_item,
                _SortItem(pos, _POS_SORT_ORDER.get(pos, 99)),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                _SortItem('HGP' if hgp else '-'),
                _SortItem(club_name),
                _SortItem(contract_end),
            ]
            for raw in raw_attrs:
                dv = max(1, min(20, round(raw / 5)))
                items.append(_SortItem(str(dv), dv))
            while len(items) < 11 + 54:
                items.append(_SortItem(''))
            for col, item in enumerate(items):
                if col == 7:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    item.setFont(f)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 8:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgp else COLORS['text_dim']))
                self._players_table.setItem(row, col, item)

        self._players_table.setSortingEnabled(True)
        self._players_table.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        for i in range(self._players_table.columnCount()):
            self._players_table.resizeColumnToContents(i)
        shown = len(display)
        suffix = f' (showing {shown:,} of {total:,})' if total > limit else f' ({total:,})'
        count_text = f'{total:,} players' + (f' - showing {limit:,}' if total > limit else '')
        self._players_count_lbl.setText(count_text)
        info = f'{total:,} players' + (f'  ·  showing {limit:,}' if total > limit else '')
        self._status_info_lbl.setText(info)

    def _on_players_table_dblclick(self, index):
        item = self._players_table.item(index.row(), 0)
        if item:
            self._open_player_detail_by_pid(item.data(Qt.ItemDataRole.UserRole))

    # -- Navigation -----------------------------------------------------------

    _VIEW_INDEX = {'club': 0, 'squad': 1, 'staff': 2, 'shortlist': 3, 'reports': 4, 'players': 5, 'club_staff': 6}

    def _nav_to(self, key: str):
        if key == 'staff' and not getattr(self, '_staff_loaded', False):
            self._populate_staff_table()
            self._staff_loaded = True
        elif key == 'staff':
            self._status_info_lbl.setText(self._staff_count_lbl.text())
        if key == 'club_staff':
            self._populate_club_staff_table()
        if key in ('club', 'squad', 'shortlist'):
            self._status_info_lbl.setText('')
        idx = self._VIEW_INDEX.get(key, 0)
        # Push to history for non-squad views (squad is pushed by _show_squad)
        if key != 'squad':
            self._nav_push(idx, {})
        self._main_stack.setCurrentIndex(idx)
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        self._players_nav_btn.setChecked(False)
        self._scouting_staff_nav_btn.setChecked(key == 'staff')
        if key not in ('squad',):
            for btn in self._report_btns.values():
                btn.setChecked(False)

    def _nav_to_squad_view(self, checked=False):
        if self._squad:
            self._populate_squad_table(self._squad)
        else:
            self._status_info_lbl.setText('')
        self._main_stack.setCurrentIndex(self._VIEW_INDEX['squad'])
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == 'squad')
        self._players_nav_btn.setChecked(False)
        self._scouting_staff_nav_btn.setChecked(False)
        for btn in self._report_btns.values():
            btn.setChecked(False)

    def _nav_push(self, stack_idx: int, context: dict):
        """Push a nav entry, truncate forward history, update back/fwd buttons."""
        if not hasattr(self, '_nav_history'):
            self._nav_history = []
            self._nav_pos = -1
        # Truncate forward history on new push
        if self._nav_pos < len(self._nav_history) - 1:
            self._nav_history = self._nav_history[:self._nav_pos + 1]
        # Don't push duplicate of current
        if self._nav_history and self._nav_history[self._nav_pos] == (stack_idx, context):
            return
        self._nav_history.append((stack_idx, context))
        self._nav_pos = len(self._nav_history) - 1
        self._back_btn.setEnabled(self._nav_pos > 0)
        self._fwd_btn.setEnabled(False)

    def _nav_back(self, checked=False):
        if not hasattr(self, '_nav_history') or self._nav_pos <= 0:
            return
        self._nav_pos -= 1
        self._nav_back_btn_update()
        self._nav_restore(self._nav_history[self._nav_pos])

    def _nav_fwd(self, checked=False):
        if not hasattr(self, '_nav_history') or self._nav_pos >= len(self._nav_history) - 1:
            return
        self._nav_pos += 1
        self._nav_back_btn_update()
        self._nav_restore(self._nav_history[self._nav_pos])

    def _nav_back_btn_update(self):
        self._back_btn.setEnabled(self._nav_pos > 0)
        self._fwd_btn.setEnabled(self._nav_pos < len(self._nav_history) - 1)

    def _nav_restore(self, entry: tuple):
        stack_idx, context = entry
        key = next((k for k, v in self._VIEW_INDEX.items() if v == stack_idx), None)
        if key == 'squad' and 'club' in context:
            self._show_squad(context['club'])
        elif key is not None:
            self._nav_to(key)

    # -- Staff double-click handlers ------------------------------------------

    def _on_staff_double_click(self, row: int, col: int):
        item = self._staff_table.item(row, 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        people = self._save_data.get('people', []) if self._save_data else []
        person = next((p for p in people if p.get('id') == pid and 'ca' not in p), None)
        if not person:
            return
        dlg = StaffDetailDialog(person, self._save_data, self)
        dlg.exec()
        if dlg._shortlist_added:
            self._add_to_shortlist(person)

    def _on_club_staff_double_click(self, row: int, col: int):
        item = self._club_staff_table.item(row, 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        people = self._save_data.get('people', []) if self._save_data else []
        person = next((p for p in people if p.get('id') == pid and 'ca' not in p), None)
        if not person:
            return
        dlg = StaffDetailDialog(person, self._save_data, self)
        dlg.exec()
        if dlg._shortlist_added:
            self._add_to_shortlist(person)

    # -- Table configuration --------------------------------------------------

    def _configure_table_for_mode(self, mode):
        hdr = self._table.horizontalHeader()
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _TT = _COL_TT | {
            'Age': 'Age at start of FM24 season',
        }
        if mode == 'squad':
            cols = ['Name', 'INJ', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'HGC',
                    'CtrE'] + _ATTR_ABBREV
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            for i in range(len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            fixed_widths = {0: 150, 1: 35, 2: 55, 3: 45, 4: 45, 5: 45, 6: 40, 7: 50, 8: 45,
                            9: 45, 10: 65}  # 1=INJ, 10=CtrE
            for i, cw in fixed_widths.items():
                self._table.setColumnWidth(i, cw)
            # Attr columns: 35px each
            for i in range(11, len(cols)):
                self._table.setColumnWidth(i, 35)
        elif mode == 'scout':
            cols = ['Name', 'Club', 'Pos', 'CA', 'PA', 'Dev', 'Age']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            for i in range(len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            for i, cw in {0: 150, 1: 160, 2: 55, 3: 45, 4: 45, 5: 45, 6: 40}.items():
                self._table.setColumnWidth(i, cw)
        else:  # player
            cols = ['Name', 'Club', 'Nation', 'Born', 'HGP']
            self._table.setColumnCount(len(cols))
            self._table.setHorizontalHeaderLabels(cols)
            for i in range(len(cols)):
                hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            for i, cw in {0: 150, 1: 160, 2: 50, 3: 50, 4: 45}.items():
                self._table.setColumnWidth(i, cw)
        for i, col in enumerate(cols):
            if col in _TT:
                hdr_item = self._table.horizontalHeaderItem(i)
                if hdr_item is not None:
                    hdr_item.setToolTip(_TT[col])
        hdr.setSectionsMovable(True)
        hdr.setFirstSectionMovable(False)
        hdr.setStretchLastSection(True)
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
        self._nav_btns['squad'].setEnabled(has_data and self._current_club is not None)
        self._nav_btns['club_staff'].setEnabled(has_data and self._current_club is not None)
        self._nav_btns['shortlist'].setEnabled(has_data)
        self._scouting_staff_nav_btn.setEnabled(has_data)
        self._table.setEnabled(has_data)
        has_squad = bool(self._squad) and self._table_mode == 'squad'
        has_b = has_data and 'b' in self._save_data
        has_sel = has_squad and bool(self._table.selectedItems())
        self._patch_hgp_btn.setEnabled(has_sel)
        self._patch_hgc_btn.setEnabled(has_sel and has_b and self._club_entity_id is not None)

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
        self._status_ready_lbl.setText(
            f'<span style="color:{COLORS["text_dim"]};">&#9679;</span> Loading...')
        self._update_ui_state()
        self._reload_save()

    def _reload_save(self):
        if not self._save_path:
            return
        self._set_busy(True, 'Parsing save file')
        self._worker = ParseWorker(self._save_path)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._on_progress_pct)
        self._worker.done.connect(self._on_parse_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_parse_done(self, result):
        self._save_data = result
        self._save_data['save_path'] = self._save_path
        self._all_players_cache = []  # invalidate on new load
        self._set_busy(False)
        n_clubs = len(result.get('clubs', []))
        people_all = result.get('people', [])
        n_people = len([p for p in people_all if p.get('ca') is not None])
        n_staff = len([p for p in people_all if p.get('ca') is None])
        fname = os.path.basename(self._save_path) if self._save_path else ''
        if fname:
            self._sb_season.setText(fname)
        self._status_ready_lbl.setText(
            f'<span style="color:#4ade80;">&#9679;</span> Ready &nbsp;&middot;&nbsp; {fname}'
            f' &nbsp;&middot;&nbsp; {n_clubs:,} clubs, {n_people:,} players, {n_staff:,} staff')
        self._club_view_name.setText('Save loaded')
        self._club_view_info.setText(
            f"{n_clubs:,} clubs, {n_people:,} players with ability data.")
        self._club_stats_frame.setVisible(False)
        self._club_pos_frame.setVisible(False)
        self._club_top_frame.setVisible(False)
        self._club_view_squad_btn.setVisible(False)
        self._staff_loaded = False
        self._update_ui_state()

    # -- Search ---------------------------------------------------------------

    def _do_search(self):
        try:
            self._do_search_inner()
        except Exception:
            import traceback
            traceback.print_exc()
            self._status.showMessage('Search failed. See crash log.')

    def _do_search_inner(self):
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
        self._show_search_dropdown(matches)

    # -- Squad / table views --------------------------------------------------

    def _show_search_dropdown(self, matches):
        """Show floating panel below search box listing club matches."""
        if hasattr(self, '_search_dropdown') and self._search_dropdown is not None:
            try:
                self._search_dropdown.close()
            except RuntimeError:
                pass
        popup = QFrame(self, Qt.WindowType.Popup)
        popup.setStyleSheet(
            f"QFrame {{ background:{COLORS['elevated']};"
            f" border:1px solid {COLORS['border_bright']}; border-radius:4px; }}"
        )
        vbox = QVBoxLayout(popup)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(1)
        _btn_ss = (
            f"QPushButton {{ background:transparent; color:{COLORS['text_primary']};"
            f" border:none; text-align:left; padding:6px 10px; font-size:12px; border-radius:3px; }}"
            f"QPushButton:hover {{ background:{COLORS['selection_bg']}; }}"
        )
        for club in matches[:15]:
            btn = QPushButton(club['name'])
            btn.setStyleSheet(_btn_ss)
            btn.clicked.connect(
                lambda checked, c=club: (popup.close(), self._show_squad(c)))
            vbox.addWidget(btn)
        sb = self._search_box
        origin = sb.mapToGlobal(QPoint(0, sb.height() + 2))
        popup.move(origin)
        popup.setFixedWidth(max(260, sb.width()))
        popup.show()
        self._search_dropdown = popup

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
            f"<span style='color:{dim}'> &rsaquo; </span><b>Squads</b>")
        self._breadcrumb.setTextFormat(Qt.TextFormat.RichText)
        self._squad_club_label.setText(club['name'])
        # Update club view
        self._club_view_name.setText(club['name'])
        self._club_view_info.setText(f"{len(squad)} players in squad")
        self._update_club_view()

        self._populate_squad_table(squad)
        self._build_squad_tabs(club, squad)
        self._nav_push(self._VIEW_INDEX['squad'], {'club': club})
        self._nav_to('squad')
        self._nav_btns['squad'].setChecked(True)
        self._update_ui_state()
        try:
            self._table.itemSelectionChanged.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _build_squad_tabs(self, main_club, main_squad):
        """Detect sub-clubs (e.g. U21, U18, B team) and populate tab bar."""
        # Remove old dynamic tabs
        for btn in self._squad_tab_dynamic_btns:
            self._squad_tab_bar.removeWidget(btn)
            btn.deleteLater()
        self._squad_tab_dynamic_btns = []
        # Reset btn list to ft_btn only
        ft_btn = self._squad_tab_btns[0]
        self._squad_tab_btns = [ft_btn]
        ft_btn.setChecked(True)
        try:
            ft_btn.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        ft_btn.clicked.connect(lambda checked: self._switch_sub_squad(0, main_squad))

        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        people = self._save_data.get('people', [])
        prefix = main_club['name'] + ' '

        # Kind-based sub-squads (English clubs: same club_id, different kind byte)
        _KIND_LABEL = {21: 'U21', 23: 'U23', 20: 'Reserves', 19: 'U19', 18: 'U18'}
        _KIND_ORDER = {21: 1, 23: 2, 20: 3, 19: 4, 18: 5}
        sub_squads = self._save_data.get('sub_squads', {})
        people_by_id = {p['id']: p for p in people if 'id' in p}

        sub_entries = []
        kind_map = sub_squads.get(main_club['id'], {})
        for kind, pids in kind_map.items():
            sub_squad = [people_by_id[pid] for pid in pids if pid in people_by_id]
            if sub_squad:
                label = _KIND_LABEL.get(kind, f'Squad {kind}')
                order = _KIND_ORDER.get(kind, 99)
                sub_entries.append((label, sub_squad, order))

        # Prefix-based sub-clubs (German/Spanish B teams: separate club entity)
        for c in clubs:
            if not c['name'].startswith(prefix):
                continue
            club_pids = {pid for pid, cid in squads.items() if cid == c['id']}
            sub_squad = [p for p in people if p.get('id', -1) in club_pids]
            if sub_squad:
                label = c['name'][len(prefix):]
                sub_entries.append((label, sub_squad, 0))  # B teams sort first

        sub_entries.sort(key=lambda x: (x[2], x[0]))

        for i, (label, sub_squad, _order) in enumerate(sub_entries):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            btn.setStyleSheet(self._squad_tab_ss_str)
            tab_idx = i + 1
            btn.clicked.connect(
                lambda checked, idx=tab_idx, sq=sub_squad: self._switch_sub_squad(idx, sq))
            self._squad_tab_bar.insertWidget(1 + i, btn)
            self._squad_tab_dynamic_btns.append(btn)
            self._squad_tab_btns.append(btn)

    def _switch_sub_squad(self, tab_idx, sub_squad):
        """Switch squad tab: update check state, repopulate table."""
        for i, btn in enumerate(self._squad_tab_btns):
            btn.setChecked(i == tab_idx)
        self._squad = sub_squad
        self._configure_table_for_mode('squad')
        self._populate_squad_table(sub_squad)

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
            injured = p.get('injured', False)
            injury_days = p.get('injury_days', 0)

            contract_end = p.get('contract_end', '')
            raw_attrs = p.get('raw_attrs', [])

            inj_item = _SortItem('INJ' if injured else '', 1 if injured else 0)
            if injured and injury_days > 0:
                inj_item.setToolTip(f"Out for {injury_days} days")
            items = [
                name_item,
                inj_item,
                _SortItem(pos, _POS_SORT_ORDER.get(pos, 99)),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                _SortItem('HGP' if hgp else '-'),
                _SortItem(hgc_text),
                _SortItem(contract_end),
            ]
            # Append 54 attribute columns (display value = max(1, min(20, round(raw/5))))
            for raw in raw_attrs:
                dv = max(1, min(20, round(raw / 5)))
                items.append(_SortItem(str(dv), dv))
            # Pad missing attrs with empty items
            while len(items) < 11 + 54:
                items.append(_SortItem(''))

            for col, item in enumerate(items):
                if col == 7:  # Nation flag — center
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    item.setFont(f)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 8:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgp
                                              else COLORS['text_dim']))
                elif col == 9:
                    item.setForeground(QColor(COLORS['hgp_green'] if hgc
                                              else COLORS['text_dim']))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
        self._table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        for c in range(self._table.columnCount()):
            self._table.resizeColumnToContents(c)
        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        b = self._save_data.get('b') if self._save_data else None
        from fm_editor.patch import is_hgc
        n_hgc = sum(1 for p in squad
                    if b is not None and self._club_entity_id and is_hgc(b, p, self._club_entity_id))
        n_inj = sum(1 for p in squad if p.get('injured', False))
        def _stat(val, label, color=COLORS['text_secondary']):
            return (f'<span style="color:{COLORS["text_primary"]};font-weight:600;">{val}</span>'
                    f'&nbsp;<span style="color:{color};font-size:11px;">{label}</span>')
        sep = f'<span style="color:{COLORS["border"]};">&nbsp;&nbsp;·&nbsp;&nbsp;</span>'
        inj_part = (sep + _stat(n_inj, 'injured', '#C0392B')) if n_inj > 0 else ''
        self._squad_info.setText(
            _stat(len(squad), 'players') + sep
            + _stat(n_hgp, 'HGP', COLORS['hgp_green']) + sep
            + _stat(n_hgc, 'HGC', COLORS['hgp_green'])
            + inj_part)
        self._status_info_lbl.setText(f'{len(squad)} players')

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
        if dlg._shortlist_added:
            self._add_to_shortlist(person)
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

    def _open_player_detail_by_pid(self, pid):
        """Open PlayerDetailDialog for any player by ID (reports/players views)."""
        if not self._save_data or pid is None:
            return
        people = self._save_data.get('people', [])
        person = next((p for p in people if p.get('id') == pid), None)
        if not person:
            return
        squads = self._save_data.get('squads', {})
        clubs = self._save_data.get('clubs', [])
        club_id = squads.get(pid)
        club_entity_id = None
        if club_id:
            club = next((c for c in clubs if c['id'] == club_id), None)
            if club and club_id == getattr(self, '_current_club', {}).get('id') \
                    if isinstance(getattr(self, '_current_club', None), dict) else False:
                club_entity_id = self._club_entity_id
        dlg = PlayerDetailDialog(person, self._save_data, club_entity_id, self)
        dlg.exec()
        if dlg._shortlist_added:
            self._add_to_shortlist(person)

    def _on_list_table_context_menu(self, table, pos):
        """Shared context menu for reports and players tables."""
        row = table.rowAt(pos.y())
        if row < 0:
            return
        item = table.item(row, 0)
        if not item:
            return
        name = item.text()
        menu = QMenu(self)
        copy_action = menu.addAction(f'Copy name: {name}')
        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action == copy_action:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(name)
            self._status.showMessage(f'Copied: {name}')

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._active_preset = _weights_mod.load_active_preset()
            preset_name = _weights_mod.get_active_preset_name()
            self._weights_lbl.setText(f'[{preset_name}]')
            self._status.showMessage(f'Role weights: {preset_name}', 3000)
            # Re-run Best by Role if it's currently shown
            if self._current_report_key == 'best_role':
                role = self._report_role_combo.currentText()
                if role and not role.startswith('──'):
                    players = self._get_report_players('best_role', role_name=role)
                    self._populate_reports_table(players)

    def _run_report(self, key: str):
        try:
            if not self._save_data:
                return
            _labels = {
                'prospects': 'Best Prospects (PA 160+)',
                'wonderkids': 'Wonderkids (U21, PA 150+)',
                'best_pos':   'Best in Position',
                'best_role':  'Best by Role',
            }
            self._current_report_key = key
            for k, btn in self._report_btns.items():
                btn.setChecked(k == key)
            for btn in self._nav_btns.values():
                btn.setChecked(False)
            self._players_nav_btn.setChecked(False)
            self._scouting_staff_nav_btn.setChecked(False)
            self._report_pos_bar.setVisible(key == 'best_pos')
            self._report_role_bar.setVisible(key == 'best_role')
            if key == 'best_role':
                pname = _weights_mod.get_active_preset_name()
                self._weights_lbl.setText(f'[{pname}]')
            pos = self._report_pos_combo.currentText() if key == 'best_pos' else None
            role = self._report_role_combo.currentText() if key == 'best_role' else None
            players = self._get_report_players(key, pos, role)
            self._report_title_lbl.setText(_labels.get(key, key))
            self._populate_reports_table(players)
            self._main_stack.setCurrentIndex(self._VIEW_INDEX['reports'])
        except Exception:
            import traceback
            traceback.print_exc()
            self._status.showMessage('Report error. See log.')

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
        has_squad = bool(self._squad)

        if has_sel and has_squad:
            id_to_person = {p.get('id', -1): p for p in self._squad}
            sel_rows = self._table.selectionModel().selectedRows()
            sel_pids = [
                self._table.item(idx.row(), 0).data(Qt.ItemDataRole.UserRole)
                for idx in sel_rows
                if self._table.item(idx.row(), 0)
            ]
            sel_persons = [id_to_person[pid] for pid in sel_pids if pid in id_to_person]
            all_hgp = bool(sel_persons) and all(p.get('hgp', False) for p in sel_persons)
            if has_b and self._club_entity_id and sel_persons:
                from fm_editor.patch import is_hgc
                b = self._save_data['b']
                all_hgc = all(is_hgc(b, p, self._club_entity_id) for p in sel_persons)
            else:
                all_hgc = False
        else:
            all_hgp = False
            all_hgc = False

        self._patch_hgp_btn.setEnabled(has_squad and has_sel and not all_hgp)
        self._patch_hgc_btn.setEnabled(has_squad and has_sel and has_b
                                        and self._club_entity_id is not None and not all_hgc)

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
                                    'All selected players are already HGP.')
            return
        if 'b' not in self._save_data:
            QMessageBox.warning(self, 'Reload required',
                                'Click Reload before patching.')
            return
        out_path = self._confirm_patch_dialog(people_to_patch, 'HGP')
        if not out_path:
            return
        self._set_busy(True, 'Applying HGP patch')
        self._worker = PatchWorker(self._save_data, out_path, people_to_patch, mode='hgp')
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._on_progress_pct)
        self._worker.done.connect(self._on_patch_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _do_patch_hgc(self):
        if not self._save_data or not self._squad or not self._club_entity_id:
            return
        if 'b' not in self._save_data:
            QMessageBox.warning(self, 'Reload required',
                                'Click Reload before patching.')
            return
        from fm_editor.patch import is_hgc
        b = self._save_data['b']
        people_to_patch = [p for p in self._get_selected_persons()
                           if not is_hgc(b, p, self._club_entity_id)]
        if not people_to_patch:
            QMessageBox.information(self, 'Nothing to patch',
                                    'All selected players are already HGC.')
            return
        out_path = self._confirm_patch_dialog(people_to_patch, 'HGC')
        if not out_path:
            return
        self._set_busy(True, 'Applying HGC patch')
        self._worker = PatchWorker(self._save_data, out_path, people_to_patch,
                                   mode='hgc', club_entity_id=self._club_entity_id)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._on_progress_pct)
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
        orig = self._save_path
        folder = os.path.dirname(orig)
        fname = os.path.basename(orig)
        bk1 = os.path.join(folder, f'bk1-{fname}')
        bk2 = os.path.join(folder, f'bk2-{fname}')
        # Rotate: bk1 → bk2, then orig → bk1
        if os.path.exists(bk1):
            shutil.copy2(bk1, bk2)
        shutil.copy2(orig, bk1)
        self._set_busy(True, 'Writing save file')
        self._worker = PatchWorker(self._save_data, orig, [], mode='save_only')
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._on_progress_pct)
        self._worker.done.connect(self._on_save_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_save_done(self):
        self._set_busy(False)
        orig = os.path.basename(self._save_path)
        folder = os.path.dirname(self._save_path)
        bk2 = os.path.join(folder, f'bk2-{orig}')
        msg = f'Saved · bk1 created'
        if os.path.exists(bk2):
            msg += ' · bk2 rotated'
        self._status.showMessage(msg)

    # -- Progress / error -----------------------------------------------------

    def _tick_dots(self):
        self._dot_phase = (self._dot_phase + 1) % len(_DOT_SEQ)
        self._status.showMessage(self._status_base + '.' * _DOT_SEQ[self._dot_phase])

    def _on_progress_pct(self, pct: int):
        self._progress_target = float(pct)

    def _tick_shimmer(self):
        # Smooth progress: lerp toward target, constant slow creep between chunks
        target = self._progress_target
        disp = self._progress_displayed
        if target > disp:
            disp += (target - disp) * 0.10
            if target - disp < 0.005:
                disp = target
        else:
            # Always creep forward slowly — never stops, never auto-fills past 99
            disp = min(disp + 0.04, 99.0)
        self._progress_displayed = disp
        self._progress.setValue(round(disp * 100))

        self._shimmer_phase = (self._shimmer_phase + 0.017) % 1.0
        # peak sweeps -0.25 → 1.25 so shimmer fully enters and exits
        peak = -0.25 + self._shimmer_phase * 1.5
        hw = 0.18
        stops: dict[float, str] = {0.0: '#4a2290', 1.0: '#4a2290'}
        for offset, col in ((-hw, '#5a2da0'), (-hw * 0.5, '#6933bd'),
                            (0.0, '#c0a8fa'), (hw * 0.5, '#6933bd'), (hw, '#5a2da0')):
            p = round(peak + offset, 4)
            if 0.001 <= p <= 0.999:
                stops[p] = col
        s = ' '.join(f'stop:{p} {c}' for p, c in sorted(stops.items()))
        self._progress.setStyleSheet(
            f"QProgressBar {{ background:{COLORS['elevated']}; border:none; }}"
            f"QProgressBar::chunk {{ background:qlineargradient("
            f"x1:0,y1:0,x2:1,y2:0,{s}); }}"
        )

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
            self._shimmer_phase = 0.0
            self._progress_target = 0.0
            self._progress_displayed = 0.0
            self._shimmer_timer.start()
            self._dot_phase = -1
            self._status_base = msg or self._status_base
            self._status.showMessage(self._status_base)
            self._dot_timer.start()
        else:
            self._shimmer_timer.stop()
            self._progress.setStyleSheet(
                f"QProgressBar {{ background:{COLORS['elevated']}; border:none; }}"
                f"QProgressBar::chunk {{ background:{COLORS['accent']}; }}"
            )
            self._dot_timer.stop()
            self._status.clearMessage()
        self._progress.setVisible(busy)
        self._load_btn.setEnabled(not busy)
        self._reload_btn.setEnabled(not busy and bool(self._save_path))
        self._save_btn.setEnabled(not busy and bool(self._save_data) and 'b' in (self._save_data or {}))
        self._search_box.setEnabled(not busy and self._save_data is not None)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn.setEnabled(False)
        if msg and not busy:
            self._status.showMessage(msg)
