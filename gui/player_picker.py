"""Player picker for Compare (mockups/compare-players.html '?open=a', mockups/player-window.html '?cmp'): a popup of
suggestion rows with tabs Recent | Squad | Shortlist (empty query) or a search of the WHOLE save (>= 2 characters, the main
search's ranking: fm_editor/player_search.py), plus `PlayerCombo`, the selector of the Compare page.

The popup is a plain child frame of the top-level window (like gui/search_suggest.py): it never takes keyboard focus, keys come
from the line edit it serves (the combo's own, or its built-in search box in `own_search` mode = player window), clicks outside
close it through an application event filter. Keepers are only compared with keepers: `keeper=` filters the lists and the
search and a footnote says how many players were hidden."""
from PyQt6.QtCore import QEvent, QPoint, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                             QStyledItemDelegate, QVBoxLayout, QWidget)

from fm_editor import settings as _settings
from fm_editor.abilitystars import ability_stars
from fm_editor.agecalc import person_age
from fm_editor.nations import nation_flag
from fm_editor.player_search import is_keeper, rank_hits
from gui.faces import get_service as _faces_service
from gui.stars import star_row_pixmap
from gui.theme import COLORS

ROW_H = 44
MAX_ROWS = 8
MIN_QUERY = 2          # characters before the search leaves the lists (the main search uses 3: player names are short)
TABS = (('recent', 'Recent', 'last opened first'), ('squad', 'Squad', None), ('short', 'Shortlist', 'Player Shortlist'))
FACE_W, FACE_H = 24, 30
ACCENT2 = '#735CE4'


_PERSON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#525B68" stroke-width="1.6">'
               '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></svg>')


def person_pixmap(person, w, h, dpr=1.0, radius=2):
    """Facepack picture of the person in a w x h box, or (no pack / no picture) the silhouette on the elevated tile
    (mockup `?noface`: pictogram 55 % of the box, centred)."""
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtSvg import QSvgRenderer
    px = _faces_service().pixmap(person.get('uid'), w, h, dpr, radius=radius)
    if px is not None:
        return px
    out = QPixmap(round(w * dpr), round(h * dpr))
    out.setDevicePixelRatio(dpr)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(COLORS['elevated']))
    p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)
    side = min(w, h) * 0.7
    QSvgRenderer(_PERSON_SVG.encode()).render(p, QRectF((w - side) / 2, (h - side) / 2, side, side))
    p.end()
    return out


def person_pos(p):
    from gui.main_window import _primary_pos
    return _primary_pos(p['positions']) if p.get('positions') else None


class PickerContext:
    """What the picker needs from the app: the search index, recents, the human club's squad and the Player Shortlist.
    `index` / `shortlist` are callables (the main window rebuilds both lazily), `recents` a fm_editor.recents.RecentPlayers."""

    def __init__(self, save_data, index, recents, shortlist):
        self.sd = save_data or {}
        self._index, self.recents, self._shortlist = index, recents, shortlist
        self._by_id = None

    def people_by_id(self):
        if self._by_id is None:
            self._by_id = {p.get('id'): p for p in self.sd.get('people', [])}
        return self._by_id

    def club_of(self, person):
        cid = (self.sd.get('squads') or {}).get(person.get('id'))
        return next((c for c in self.sd.get('clubs', []) if c.get('id') == cid), None) if cid is not None else None

    def recent(self):
        return self.recents.people(self.people_by_id())

    def squad(self):
        hum = self.sd.get('human_clubs') or ()
        rows = [self.people_by_id()[pid] for pid, cid in (self.sd.get('squads') or {}).items()
                if cid in hum and pid in self.people_by_id() and self.people_by_id()[pid].get('ca') is not None]
        return sorted(rows, key=lambda p: -(p.get('ca') or 0))

    def shortlist(self):
        return list(self._shortlist())

    def lists(self):
        return {'recent': self.recent(), 'squad': self.squad(), 'short': self.shortlist()}

    def search(self, text, exclude_ids=(), keeper=None):
        """(persons best first, number hidden by the keeper rule). Players only."""
        full = rank_hits(self._index(), text, 200, kinds=(2,), exclude_ids=exclude_ids)
        ok = [h for h in full if keeper is None or is_keeper(h[3]) == keeper]
        return [h[3] for h in ok], len(full) - len(ok)


class PlayerRowDelegate(QStyledItemDelegate):
    """Row (mockup .opt, 44 px): 3 px edge | face 24x30 | name 13/700 (query highlighted) over [pos badge, flag, club badge,
    club, '·', age] 11 secondary | CA stars 11 px (Settings > Ability display = Numbers: the number, raw value in the tooltip)."""
    PERSON, CLUB, QUERY, STARS = (Qt.ItemDataRole.UserRole + i for i in range(4))

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), ROW_H)

    def paint(self, p, option, index):
        from gui.main_window import _POS_BADGE_COLORS
        person, club, q, stars = (index.data(r) for r in (self.PERSON, self.CLUB, self.QUERY, self.STARS))
        r = option.rect
        dpr = p.device().devicePixelRatioF()
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sel = index.row() == self._cur(option)
        p.fillRect(r, QColor(COLORS['selection_bg']) if sel else QColor(0, 0, 0, 0))
        if sel:
            p.fillRect(QRectF(r.x(), r.y(), 3, r.height()), QColor(COLORS['accent']))
        x = r.x() + 12
        fy = r.y() + (r.height() - FACE_H) // 2
        p.drawPixmap(x, fy, person_pixmap(person, FACE_W, FACE_H, dpr))
        x += FACE_W + 10
        # right: stars / number
        rx = r.right() - 12
        if stars is None:
            ca = person.get('ca')
            nf = QFont()
            nf.setPixelSize(14)
            nf.setBold(True)
            p.setFont(nf)
            p.setPen(QColor(ACCENT2))
            txt = str(ca) if ca is not None else '?'
            w = QFontMetrics(nf).horizontalAdvance(txt)
            p.drawText(QRectF(rx - w, r.y(), w, r.height()), int(Qt.AlignmentFlag.AlignVCenter), txt)
            rx -= w
        else:
            sp = star_row_pixmap(stars, 11, 1, dpr)
            p.drawPixmap(rx - 59, r.y() + (r.height() - 11) // 2, sp)
            rx -= 59
        # line 1: name
        nf = QFont()
        nf.setPixelSize(13)
        nf.setBold(True)
        p.setFont(nf)
        name = person.get('name', '')
        fm = QFontMetrics(nf)
        name_w = max(40, rx - 12 - x)
        shown = fm.elidedText(name, Qt.TextElideMode.ElideRight, name_w)
        p.setPen(QColor('#FFFFFF'))
        ny = r.y() + 17
        p.drawText(x, ny, shown)
        i = name.lower().find(q) if q else -1
        if i >= 0 and name[:i + len(q)] == shown[:i + len(q)]:
            hx = x + fm.horizontalAdvance(name[:i])
            hw = fm.horizontalAdvance(name[i:i + len(q)])
            p.fillRect(QRectF(hx, ny - fm.ascent(), hw, fm.height()), QColor(COLORS['selection_bg'] if not sel else '#3A2570'))
            p.setPen(QColor(ACCENT2))
            p.drawText(hx, ny, name[i:i + len(q)])
            p.setPen(QPen(QColor(ACCENT2), 1))
            p.drawLine(int(hx), ny + 2, int(hx + hw), ny + 2)
        # line 2
        sf = QFont()
        sf.setPixelSize(11)
        p.setFont(sf)
        sfm = QFontMetrics(sf)
        y2 = r.y() + 24
        pos = person_pos(person)
        if pos:
            from gui.player_window import POS_CODE
            bg = _POS_BADGE_COLORS.get(pos, ('#2A2D35', '#FFFFFF'))[0]
            bf = QFont()
            bf.setPixelSize(10)
            bf.setBold(True)
            code = POS_CODE.get(pos, pos)
            bw = max(28, QFontMetrics(bf).horizontalAdvance(code) + 10)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(bg))
            p.drawRoundedRect(QRectF(x, y2, bw, 16), 2, 2)
            p.setFont(bf)
            p.setPen(QColor('#FFFFFF'))
            p.drawText(QRectF(x, y2, bw, 16), int(Qt.AlignmentFlag.AlignCenter), code)
            x2 = x + bw + 5
        else:
            x2 = x
        p.setFont(sf)
        flag_px = _faces_service().nation_pixmap(person.get('nation'), 16, dpr)
        if flag_px is not None:
            p.drawPixmap(int(x2), y2, flag_px)
            x2 += 21
        else:
            fl = nation_flag(person.get('nation'))
            if fl:
                ff = QFont('Noto Color Emoji')
                ff.setPixelSize(12)
                p.setFont(ff)
                p.setPen(QColor('#FFFFFF'))
                p.drawText(QRectF(x2, y2, 20, 16), int(Qt.AlignmentFlag.AlignVCenter), fl)
                x2 += 21
                p.setFont(sf)
        cpx = _faces_service().club_pixmap((club or {}).get('uid'), 16, dpr) if club else None
        if cpx is not None:
            p.drawPixmap(int(x2), y2, cpx)
            x2 += 21
        p.setPen(QColor(COLORS['text_secondary']))
        tail = (club or {}).get('name') or ''
        tail = (tail + '  ·  ' if tail else '') + f'{person_age(person)} years'
        p.drawText(QRectF(x2, y2, max(0, rx - 12 - x2), 16), int(Qt.AlignmentFlag.AlignVCenter),
                   sfm.elidedText(tail, Qt.TextElideMode.ElideRight, int(max(0, rx - 12 - x2))))
        p.restore()

    def _cur(self, option):
        w = option.widget
        return w.currentRow() if w is not None else -1


def fill_rows(lw, persons, ctx, query='', stars_on=True):
    """Fill a QListWidget (delegate PlayerRowDelegate) with suggestion rows for `persons`."""
    lw.clear()
    for p in persons:
        it = QListWidgetItem()
        it.setSizeHint(QSize(max(lw.width(), 200), ROW_H))
        it.setData(PlayerRowDelegate.PERSON, p)
        it.setData(PlayerRowDelegate.CLUB, ctx.club_of(p))
        it.setData(PlayerRowDelegate.QUERY, query)
        ca = p.get('ca')
        it.setData(PlayerRowDelegate.STARS, ability_stars(ca) if (stars_on and ca is not None) else None)
        if ca is not None and stars_on:
            it.setToolTip(f'CA {ca}')
        lw.addItem(it)


def make_row_list(parent=None):
    """A bare QListWidget with the row delegate (Compare empty state: recently viewed players)."""
    lw = QListWidget(parent)
    lw.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    lw.setItemDelegate(PlayerRowDelegate(lw))
    lw.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    lw.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    lw.setMouseTracking(True)
    lw.setStyleSheet('QListWidget { background:transparent; border:none; outline:none; }')
    lw.itemEntered.connect(lambda it: lw.setCurrentItem(it))
    return lw


class PlayerPicker(QFrame):
    """Popup list. `picked(person)` on Enter / click, `closed()` when it goes away. Serve a line edit with `show_for`."""
    picked = pyqtSignal(dict)
    closed = pyqtSignal()
    WIDTH = 468

    def __init__(self, window, ctx, own_search=False):
        super().__init__(window)
        self._win, self._ctx, self._own = window, ctx, own_search
        self._src, self._exclude, self._keeper, self._query = 'recent', (), None, ''
        self._edit = None
        self.setObjectName('playerPicker')
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        c = COLORS
        self.setStyleSheet(
            f"QFrame#playerPicker {{ background:{c['surface']}; border:1px solid {c['border_bright']}; border-radius:4px; }}"
            "QFrame#playerPicker QWidget { background:transparent; }"
            f"QLabel#ppTitle {{ color:{c['text_secondary']}; font-size:11px; padding:10px 12px 0 12px; }}"
            f"QLabel#ppLbl {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; padding:8px 12px 3px 12px; }}"
            f"QLabel#ppHid {{ color:{c['text_secondary']}; font-size:11px; padding:6px 12px; border-top:1px solid {c['border']}; }}"
            f"QLabel#ppNone {{ color:{c['text_secondary']}; padding:16px 12px; }}"
            f"QLabel#ppHint {{ color:{c['text_secondary']}; font-size:11px; padding:6px 12px; border-top:1px solid {c['border']}; }}"
            f"QLabel#ppNote {{ color:{c['text_secondary']}; font-size:11px; }}"
            f"QLineEdit#ppSearch {{ background:{c['window_bg']}; border:1px solid {ACCENT2}; border-radius:3px; padding:0 10px; "
            "font-size:13px; }"
            f"QFrame#ppSeg {{ background:{c['window_bg']}; border:1px solid {c['border_bright']}; border-radius:3px; }}"
            f"QPushButton#ppTab {{ background:{c['window_bg']}; color:{c['text_secondary']}; border:none; font-size:11px; "
            "font-weight:bold; padding:0 12px; }"
            f"QPushButton#ppTab:checked {{ background:{c['accent']}; color:#FFFFFF; }}"
            "QListWidget#ppList { border:none; outline:none; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self._title = QLabel()
        self._title.setObjectName('ppTitle')
        v.addWidget(self._title)
        self._search = QLineEdit()
        self._search.setObjectName('ppSearch')
        self._search.setFixedHeight(36)
        self._search.setPlaceholderText('Search any player in the save…')
        self._search.textEdited.connect(self.set_query)
        self._sw = QWidget()
        sl = QHBoxLayout(self._sw)
        sl.setContentsMargins(12, 8, 12, 8)
        sl.addWidget(self._search)
        v.addWidget(self._sw)
        self._tabs = QWidget()
        tl = QHBoxLayout(self._tabs)
        tl.setContentsMargins(12, 8, 12, 6)
        seg = QFrame()
        seg.setObjectName('ppSeg')
        sgl = QHBoxLayout(seg)
        sgl.setContentsMargins(0, 0, 0, 0)
        sgl.setSpacing(0)
        self._tab_btns = {}
        bold = QFont()
        bold.setPixelSize(11)
        bold.setBold(True)
        for key, label, _n in TABS:
            b = QPushButton(label)
            b.setObjectName('ppTab')
            b.setCheckable(True)
            b.setFixedSize(QFontMetrics(bold).horizontalAdvance(label) + 24, 24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(lambda checked, k=key: self.set_source(k))
            sgl.addWidget(b)
            self._tab_btns[key] = b
        tl.addWidget(seg)
        self._note = QLabel()
        self._note.setObjectName('ppNote')
        tl.addStretch(1)
        tl.addWidget(self._note)
        v.addWidget(self._tabs)
        self._lbl = QLabel()
        self._lbl.setObjectName('ppLbl')
        v.addWidget(self._lbl)
        self._list = QListWidget()
        self._list.setObjectName('ppList')
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.setItemDelegate(PlayerRowDelegate(self._list))
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setMouseTracking(True)
        self._list.itemEntered.connect(lambda it: self._list.setCurrentItem(it))
        self._list.itemClicked.connect(lambda it: self._pick(it))
        v.addWidget(self._list)
        self._none = QLabel()
        self._none.setObjectName('ppNone')
        self._none.setWordWrap(True)
        v.addWidget(self._none)
        self._hid = QLabel()
        self._hid.setObjectName('ppHid')
        v.addWidget(self._hid)
        hint = QLabel('↑ ↓ move    Enter pick    Esc close')
        hint.setObjectName('ppHint')
        v.addWidget(hint)
        self._sw.setVisible(own_search)
        self._search.installEventFilter(self)
        self.hide()

    # -- state -----------------------------------------------------------------------------------
    def show_for(self, edit, anchor, title='', exclude_ids=(), keeper=None, above=False, align_right=False, source=None, width=None):
        """Open for `edit` (the combo's line edit; in own_search mode the popup's own search box is used and `edit` ignored),
        placed under (or above) `anchor`. exclude_ids = people never offered; keeper True/False = only that kind."""
        self._exclude, self._keeper = tuple(exclude_ids), keeper
        self._title.setText(title)
        self._title.setVisible(bool(title))
        if self._edit is not None and self._edit is not self._search:
            self._edit.removeEventFilter(self)
        self._edit = self._search if self._own else edit
        if self._edit is not self._search:
            self._edit.installEventFilter(self)
        self._ability_stars = _settings.ability_as_stars()
        if source:
            self._src = source
        self._anchor, self._above, self._align_right, self._w = anchor, above, align_right, width or self.WIDTH
        self._search.setText('') if self._own else None
        self._query = ''
        self._fill()
        self._place()
        self.raise_()
        if not self.isVisible():
            self.show()
            QApplication.instance().installEventFilter(self)
        if self._own:
            self._search.setFocus()

    def set_source(self, key):
        self._src = key
        self._fill()
        self._place()

    def set_query(self, text):
        self._query = text.strip()
        self._fill()
        self._place()

    def current_person(self):
        it = self._list.currentItem()
        return it.data(PlayerRowDelegate.PERSON) if it is not None else None

    def rows(self):
        return [self._list.item(i).data(PlayerRowDelegate.PERSON) for i in range(self._list.count())]

    def _fill(self):
        search = len(self._query) >= MIN_QUERY
        hidden = 0
        if search:
            persons, hidden = self._ctx.search(self._query, self._exclude, self._keeper)
        else:
            persons = [p for p in self._ctx.lists()[self._src] if p.get('id') not in self._exclude
                       and (self._keeper is None or is_keeper(p) == self._keeper)]
            full = [p for p in self._ctx.lists()[self._src] if p.get('id') not in self._exclude]
            hidden = len(full) - len(persons)
        persons = persons[:MAX_ROWS]
        self._tabs.setVisible(not search)
        self._lbl.setVisible(search)
        if search:
            self._lbl.setText(f'PLAYERS MATCHING “{self._query}” · WHOLE SAVE')
        for k, b in self._tab_btns.items():
            b.setChecked(k == self._src)
        club = (self._src == 'squad' and self._ctx.sd.get('human_clubs') and
                next((c['name'] for c in self._ctx.sd.get('clubs', []) if c.get('id') in self._ctx.sd['human_clubs']), None))
        self._note.setText({'recent': 'last opened first', 'squad': club or 'human club', 'short': 'Player Shortlist'}[self._src])
        fill_rows(self._list, persons, self._ctx, self._query.lower() if search else '', self._ability_stars)
        if persons:
            self._list.setCurrentRow(0)
        self._list.setFixedHeight(len(persons) * ROW_H)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVisible(bool(persons))
        noun = 'goalkeeper' if self._keeper else 'player'
        self._none.setVisible(not persons)
        self._none.setText(f'No {noun} matches “{self._query}”.' if search else
                           {'recent': 'No players viewed yet: open a player window first.',
                            'squad': 'No squad: no human club in this save.', 'short': 'The Player Shortlist is empty.'}[self._src])
        self._hid.setVisible(bool(hidden))
        if hidden:
            self._hid.setText(f"{hidden} player{'s' if hidden > 1 else ''} not shown: goalkeepers are only compared with goalkeepers."
                              if self._keeper else
                              f"{hidden} goalkeeper{'s' if hidden > 1 else ''} not shown: goalkeepers are only compared with goalkeepers.")
        self.adjustSize()

    def _place(self):
        a = self._anchor
        w = self._w
        self.setFixedWidth(w)
        self.adjustSize()
        h = self.sizeHint().height()
        if self._above:
            top = a.mapTo(self._win, QPoint(0, 0)).y() - h - 6
            right = a.mapTo(self._win, QPoint(a.width(), 0)).x()
            pos = QPoint(right - w, max(4, top))
        else:
            bl = a.mapTo(self._win, QPoint(0, a.height() + 4))
            pos = QPoint(bl.x() + a.width() - w if self._align_right else bl.x(), bl.y())
        pos.setX(max(4, min(pos.x(), self._win.width() - w - 4)))
        if not self._above and pos.y() + h > self._win.height() - 4 and self._list.isVisible():
            # not enough room below the field: show fewer rows, the list scrolls (never covers the field, never leaves the window)
            rows = max(2, (self._list.height() - (pos.y() + h - self._win.height() + 4)) // ROW_H)
            self._list.setFixedHeight(rows * ROW_H)
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.adjustSize()
            h = self.sizeHint().height()
        self.setGeometry(pos.x(), pos.y(), w, h)

    # -- keys / mouse ----------------------------------------------------------------------------
    def _move(self, step):
        n = self._list.count()
        if n:
            self._list.setCurrentRow(max(0, min(n - 1, self._list.currentRow() + step)))

    def _pick(self, it=None):
        it = it or self._list.currentItem()
        p = it.data(PlayerRowDelegate.PERSON) if it is not None else None
        if p is not None:
            self.close_popup()
            self.picked.emit(p)

    def close_popup(self):
        was = self.isVisible()
        self.hide()
        QApplication.instance().removeEventFilter(self)
        if was:
            self.closed.emit()

    def eventFilter(self, obj, ev):
        t = ev.type()
        if t == QEvent.Type.KeyPress and obj is self._edit:
            k = ev.key()
            if k == Qt.Key.Key_Down:
                self._move(1)
                return True
            if k == Qt.Key.Key_Up:
                self._move(-1)
                return True
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._pick()
                return True
            if k in (Qt.Key.Key_Escape, Qt.Key.Key_Tab):
                self.close_popup()
                return k == Qt.Key.Key_Escape
        elif t == QEvent.Type.MouseButtonPress and self.isVisible():
            gp = ev.globalPosition().toPoint()
            # the app-level filter sees the press on the QWindow first (obj is not a QWidget), so decide by GEOMETRY:
            # a click anywhere over the popup is inside (tabs, rows, search box), whatever object receives it
            inside = self.rect().contains(self.mapFromGlobal(gp))
            on_edit = self._edit is not None and self._edit.rect().contains(self._edit.mapFromGlobal(gp)) \
                or (self._anchor is not None and self._anchor.rect().contains(self._anchor.mapFromGlobal(gp)))
            if not inside and not on_edit:
                self.close_popup()
        return False


class PlayerCombo(QFrame):
    """Selector of the Compare page (mockup .sel, 40 high): marker + letter | face 22x28 | editable text | position badge |
    clear | chevron. Click / focus opens the picker (lists for an empty query); typing searches the whole save."""
    personPicked = pyqtSignal(dict)
    cleared = pyqtSignal()
    opened = pyqtSignal()

    def __init__(self, slot, color, get_picker, parent=None):
        super().__init__(parent)
        self.slot, self._color, self._get_picker = slot, color, get_picker   # get_picker(slot) -> the shared PlayerPicker
        self._person = None
        self.setObjectName('cmpSel')
        self.setFixedHeight(40)
        self.setMinimumWidth(180)
        c = COLORS
        self.setStyleSheet(
            f"QFrame#cmpSel {{ background:{c['surface']}; border:1px solid {c['border_bright']}; border-radius:3px; }}"
            f"QFrame#cmpSel[open=\"true\"] {{ background:{c['window_bg']}; border:1px solid {ACCENT2}; }}"
            "QLineEdit#cmpSelEdit { background:transparent; border:none; padding:0; font-size:13px; font-weight:bold; }"
            f"QToolButton#cmpSelBtn {{ background:transparent; border:none; color:{c['text_secondary']}; border-radius:3px; }}"
            f"QToolButton#cmpSelBtn:hover {{ background:{c['elevated']}; color:#FFFFFF; }}")
        h = QHBoxLayout(self)
        h.setContentsMargins(10, 0, 4, 0)
        h.setSpacing(8)
        self._tag = QLabel(f'{"●" if slot == "a" else "◆"} {slot.upper()}')
        self._tag.setStyleSheet(f'color:{color}; font-weight:bold; font-size:12px; background:transparent;')
        h.addWidget(self._tag)
        self._face = QLabel()
        self._face.setFixedSize(22, 28)
        self._face.setStyleSheet(f"background:{c['elevated']}; border-radius:2px;")
        h.addWidget(self._face)
        self._edit = QLineEdit()
        self._edit.setObjectName('cmpSelEdit')
        self._edit.setPlaceholderText('Search any player in the save…')
        self._edit.setAccessibleName(f'Player {slot.upper()}')
        self._edit.installEventFilter(self)
        self._edit.textEdited.connect(self._typed)
        h.addWidget(self._edit, 1)
        self._badge = QLabel()
        self._badge.setFixedHeight(16)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(self._badge)
        from PyQt6.QtWidgets import QToolButton
        self._clear = QToolButton()
        self._clear.setObjectName('cmpSelBtn')
        self._clear.setText('×')
        self._clear.setFixedSize(26, 26)
        self._clear.setToolTip(f'Clear player {slot.upper()}')
        self._clear.clicked.connect(self._on_clear)
        h.addWidget(self._clear)
        self._chev = QToolButton()
        self._chev.setObjectName('cmpSelBtn')
        self._chev.setText('▾')
        self._chev.setFixedSize(26, 26)
        self._chev.setToolTip('Show lists')
        self._chev.clicked.connect(self._toggle)
        h.addWidget(self._chev)
        self.exclude_ids, self.keeper = (), None      # set by the page before each open
        self._set_open(False)
        self.set_person(None)

    # -- state -----------------------------------------------------------------------------------
    @property
    def person(self):
        return self._person

    def set_person(self, p):
        self._person = p
        self._edit.setText(p['name'] if p else '')
        self._clear.setVisible(p is not None)
        self._badge.setVisible(p is not None)
        self._face.setVisible(p is not None)
        if p:
            from gui.main_window import _POS_BADGE_COLORS
            from gui.player_window import POS_CODE
            pos = person_pos(p)
            self._badge.setText(POS_CODE.get(pos, pos or ''))
            bg = _POS_BADGE_COLORS.get(pos, ('#2A2D35', '#FFFFFF'))[0]
            self._badge.setStyleSheet(f'background:{bg}; color:#FFFFFF; font-size:10px; font-weight:bold; border-radius:2px; padding:0 5px;')
            self._badge.setMinimumWidth(28)
            self._face.setPixmap(person_pixmap(p, 22, 28, self.devicePixelRatioF()))
        self._edit.setCursorPosition(0)

    def _set_open(self, on):
        self.setProperty('open', bool(on))
        self.style().unpolish(self)
        self.style().polish(self)

    def open_picker(self, source=None):
        self._edit.selectAll()
        self._set_open(True)
        title = ''
        self._get_picker(self.slot).show_for(self._edit, self, title, self.exclude_ids, self.keeper, align_right=(self.slot == 'b'), source=source)
        self.opened.emit()

    def close_picker(self):
        self._get_picker(self.slot).close_popup()

    def picker_closed(self):
        self._set_open(False)
        self._edit.setText(self._person['name'] if self._person else '')
        self._edit.setCursorPosition(0)

    def _typed(self, text):
        if not self._property_open():
            self.open_picker()
            self._edit.setText(text)
        self._get_picker(self.slot).set_query(text)

    def _property_open(self):
        return bool(self.property('open'))

    def _toggle(self):
        if self._property_open():
            self._get_picker(self.slot).close_popup()
        else:
            self.open_picker()

    def _on_clear(self):
        self.cleared.emit()

    def mousePressEvent(self, e):
        if not self._property_open():
            self.open_picker()
        self._edit.setFocus()
        super().mousePressEvent(e)

    def eventFilter(self, obj, ev):
        if obj is self._edit:
            if ev.type() == QEvent.Type.MouseButtonPress and not self._property_open():
                self.open_picker()
            elif ev.type() == QEvent.Type.FocusIn and not self._property_open():
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, lambda: None if self._property_open() else self.open_picker())
        return super().eventFilter(obj, ev)
