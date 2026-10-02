"""Role Rating tab of the player window (mockups/player-window.html section 4.7 + the ROLE RATING TAB comment block; every
number below is copied from there). LEFT panel = the roles playable at the selected position (RoleList, custom painted),
RIGHT panel = the Positions-tab pitch with one dot per position = the best role there (RolePitch). Ratings are PERCENTS
(fm_editor.rolepos.role_score, e.g. 83.89%), tier colour = the Best by Role report's 1-20 tier of percent / 5.

Logic lives in fm_editor/rolepos.py (no Qt); this module only draws and wires. `RoleTab(win)` reads the window's person,
position ratings, Current | Full Potential state (`_pot_on`, `_projection`) and builds the two panels."""
import math

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetrics, QFontMetricsF, QImage, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QToolTip, QVBoxLayout, QWidget

from fm_editor import rolepos
from fm_editor import weights as _weights
from gui.player_window import (C_ALT, POS_CODE, POS_DISPLAY, POS_FULL, TIER_HEX, _ElideLabel, _lab, _PitchBig, _spaced,
                               tier, word)
from gui.pw_widgets import _a, _font
from gui.theme import COLORS

HEAD_H, ROW_H, GROUP_GAP = 36, 24, 4
SEL_BG, ACCENT, TRACK = QColor(COLORS['selection_bg']), QColor(COLORS['accent']), QColor(COLORS['border'])
SEC, INK, WHITE = QColor(COLORS['text_secondary']), QColor('#14151A'), QColor('#FFFFFF')
# list columns (px from the row's left edge; the right edge is `width - 12`): label text x 27 (duty rows) / 15 (family + flat rows),
# bar from x 235, number 52 wide, gaps 8
LABEL_X, FLAT_X, BAR_X, NUM_W, GAP = 27, 15, 235, 52, 8
TIER_KEY = [('0–22', 1), ('23–42', 2), ('43–57', 3), ('58–67', 4), ('68–82', 5), ('83–100', 6)]   # percent = tier boundaries x 5
HIT_R = 22
LOW_FAM = 10       # position rating below this = not familiar: the dot is dimmed (selected dot never)
FOOT = ("Rating = weighted mean of the role's key attributes, as a percentage of the maximum.")


def pct_text(v):
    return f'{v:.2f}%'


def rtier(v):
    """Colour tier of a percent: the 1-20 integer of the Best by Role report (rolepos.score_to_rating), then tier()."""
    return tier(rolepos.score_to_rating(v))


class RoleList(QWidget):
    """Role (family) header rows + one row per duty, best at the position highlighted. Rows are a flat model
    [(kind, y, ...)]; fixed 24 px rows, 4 px between groups; height = sum (the host scroll area scrolls if it ever overflows)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._empty = ''
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_groups(self, groups, best, empty=''):
        """groups = rolepos.position_roles(...); best = FM_ROLES name of the highlighted row; empty = text when no groups."""
        self._rows, y = [], 0
        for gi, (fam, rows) in enumerate(groups):
            if gi:
                y += GROUP_GAP
            if len(rows) == 1:
                duty, name, v = rows[0]
                self._rows.append(('flat', y, fam, duty, v, name == best))
                y += ROW_H
                continue
            self._rows.append(('head', y, fam))
            y += ROW_H
            for duty, name, v in rows:
                self._rows.append(('row', y, duty, v, name == best))
                y += ROW_H
        self._empty = empty if not groups else ''
        self.setFixedHeight(max(y, 0))
        self.update()

    def row_count(self):
        return len(self._rows)

    def paintEvent(self, _e):
        p = QPainter(self)
        W = self.width()
        if self._empty:
            p.setFont(_font(12))
            p.setPen(SEC)
            p.drawText(QRect(12, 8, W - 24, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._empty)
            return
        reg, bold, small = _font(12), _font(12, True), _font(11)
        num_x = W - 12 - NUM_W
        bar_w = num_x - GAP - BAR_X
        for r in self._rows:
            kind, y = r[0], r[1]
            box = QRect(0, y, W, ROW_H)
            if kind == 'head':
                p.fillRect(box, QColor(C_ALT))
                p.setFont(bold)
                p.setPen(WHITE)
                p.drawText(QRect(FLAT_X, y, W - FLAT_X, ROW_H), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, r[2])
                continue
            if kind == 'flat':
                _k, _y, fam, duty, v, best = r
                p.fillRect(box, SEL_BG if best else QColor(C_ALT))
                tx = FLAT_X
            else:
                _k, _y, duty, v, best = r
                fam = None
                if best:
                    p.fillRect(box, SEL_BG)
                tx = LABEL_X
            if best:
                p.fillRect(QRect(0, y, 3, ROW_H), ACCENT)
            col = QColor(TIER_HEX[rtier(v)])
            p.setPen(WHITE)
            if fam is not None:                       # flat: bold name, then the duty 11 secondary 6 px after it
                p.setFont(bold)
                fm = QFontMetrics(bold)
                name_w = fm.horizontalAdvance(fam)
                p.drawText(QRect(tx, y, 212, ROW_H), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, fam)
                p.setFont(small)
                p.setPen(SEC)
                p.drawText(QRect(tx + name_w + 6, y, 212, ROW_H), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, duty)
            else:
                p.setFont(reg)
                p.drawText(QRect(tx, y, 200, ROW_H), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, duty)
            p.fillRect(QRect(BAR_X, y + 9, bar_w, 6), TRACK)
            p.fillRect(QRect(BAR_X, y + 9, round(max(0.0, min(100.0, v)) / 100 * bar_w), 6), col)
            p.setFont(bold)
            p.setPen(col)
            p.drawText(QRect(num_x, y, NUM_W, ROW_H), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, pct_text(v))


class RolePitch(_PitchBig):
    """The Positions-tab pitch (field painted by _PitchBig) with its own dots: per position the best role's percent, tier
    coloured; selected = white ring; positions that cannot be rated (goalkeeper vs outfield) are dashed and not clickable;
    unfamiliar positions are dimmed. State comes from RoleTab.set_state (a dict per position); a click on a live dot emits `picked`."""
    picked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__({}, parent)
        self.setMouseTracking(True)     # hover tooltips + the hand cursor need move events without a pressed button
        self._info, self._tips, self._dim = {}, {}, {}
        self._sel = self._best = None

    def set_state(self, info, tips, dim, sel, best):
        """info {pos: (role name, percent) | None (not rated)}, tips {pos: text}, dim {pos: bool}, sel / best = position codes."""
        self._info, self._tips, self._dim, self._sel, self._best = info, tips, dim, sel, best
        self.update()

    def hit(self, pt):
        """Position whose dot centre is within 22 px of pt (nearest), else None."""
        best, bd = None, HIT_R + 1
        for q in POS_DISPLAY:
            x, y = self._pt(q)
            d = math.hypot(pt.x() - x, pt.y() - y)
            if d <= HIT_R and d < bd:
                best, bd = q, d
        return best

    def mouseMoveEvent(self, e):
        q = self.hit(e.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if q and self._info.get(q) else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e):
        q = self.hit(e.position()) if e.button() == Qt.MouseButton.LeftButton else None
        if q and self._info.get(q):
            self.picked.emit(q)

    def event(self, e):
        if e.type() == QEvent.Type.ToolTip:
            q = self.hit(e.pos())
            if q and self._tips.get(q):
                QToolTip.showText(self._tip_pos(q, self._tips[q]), self._tips[q], self)
            else:
                QToolTip.hideText()
                e.ignore()
            return True
        return super().event(e)

    def _tip_pos(self, q, text):
        """Global position of the tooltip: centred on the dot, above it for the lower 40 % of the pitch, else below (26 px away)."""
        x, y = self._pt(q)
        r = QFontMetrics(QToolTip.font()).boundingRect(QRect(0, 0, 600, 400), 0, text)
        w, h = r.width() + 8, r.height() + 6                    # QTipLabel = text + 8 x 6 px (measured)
        left = max(4, min(self.width() - w - 4, x - w / 2))
        top = y - 26 - h if y > self.height() * 0.6 else y + 26
        return self.mapToGlobal(QPoint(round(left) - 2, round(top) - 16))     # Qt adds (2, 16) to the position it is given

    def paint_dots(self, p):
        order = sorted(POS_DISPLAY, key=lambda q: 99 if q == self._sel else (self._info[q][1] if self._info.get(q) else -1))
        for q in order:
            x, y = self._pt(q)
            if self._dim.get(q) and q != self._sel:
                # SVG group opacity: dot + number + label are composited together at 0.4 (not each primitive on its own)
                img = QImage(80, 80, QImage.Format.Format_ARGB32_Premultiplied)
                img.fill(Qt.GlobalColor.transparent)
                ip = QPainter(img)
                ip.setRenderHint(QPainter.RenderHint.Antialiasing)
                self._dot(ip, q, 40, 52)
                ip.end()
                p.setOpacity(0.4)
                p.drawImage(QPointF(x - 40, y - 52), img)
                p.setOpacity(1.0)
            else:
                self._dot(p, q, x, y)

    def _dot(self, p, q, x, y):
        """One position's dot + code label centred on (x, y): rated = tier dot with the rounded percent, not rated = dashed."""
        num_f, lab_f, dash_f = _font(11, True), _font(10, True), _font(12)
        info = self._info.get(q)
        on = q == self._sel
        if info is None:                                          # not rated: dashed, dim, not clickable
            pen = QPen(QColor(255, 255, 255, _a(.22)), 1)
            pen.setDashPattern([3, 3])
            p.setPen(pen)
            p.setBrush(QColor(20, 21, 26, _a(.35)))
            p.drawEllipse(QPointF(x, y), 15, 15)
            self._text(p, x, y, '–', dash_f, QColor(255, 255, 255, _a(.35)))
            lab_col = QColor(255, 255, 255, _a(.35))
        else:
            v = info[1]
            col = QColor(TIER_HEX[rtier(v)])
            ghost = rtier(v) == 1
            if on:
                p.setPen(QPen(WHITE, 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(x, y), 21, 21)
            if ghost:
                p.setPen(QPen(col, 1))
                p.setBrush(QColor(20, 21, 26, _a(.55)))
                p.drawEllipse(QPointF(x, y), 16.5, 16.5)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(col)
                p.drawEllipse(QPointF(x, y), 17, 17)
            self._text(p, x, y, str(int(v + 0.5)), num_f, col if ghost else INK)
            lab_col = WHITE if (on or q == self._best) else QColor(255, 255, 255, _a(.72))
        p.setFont(lab_f)
        p.setPen(lab_col)
        code = POS_CODE[q]
        p.drawText(QPointF(x - QFontMetricsF(lab_f).horizontalAdvance(code) / 2, y - 26), code)

    @staticmethod
    def _text(p, x, y, text, font, color):
        """SVG dominant-baseline:central text centred on (x, y)."""
        p.setFont(font)
        p.setPen(color)
        fm = QFontMetricsF(font)
        p.drawText(QPointF(x - fm.horizontalAdvance(text) / 2, y + (fm.ascent() - fm.descent()) / 2), text)


class _TierKey(QWidget):
    """Strip under the pitch (27 px: 1 px hairline + 26): six tier swatches (percent ranges) + a ring for 'Selected'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(27)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(QRect(0, 0, self.width(), 1), TRACK)
        f = _font(11)
        fm = QFontMetricsF(f)
        cy = 1 + 26 / 2
        x = 12.0
        for label, t in TIER_KEY:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(TIER_HEX[t]))
            p.drawRoundedRect(QRectF(x, cy - 5, 10, 10), 2, 2)
            x += 15
            p.setFont(f)
            p.setPen(SEC)
            p.drawText(QPointF(x, cy + (fm.ascent() - fm.descent()) / 2), label)
            x += fm.horizontalAdvance(label) + 10
        p.setPen(QPen(WHITE, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x + 6, cy), 5, 5)
        x += 17
        p.setFont(f)
        p.setPen(SEC)
        p.drawText(QPointF(x, cy + (fm.ascent() - fm.descent()) / 2), 'Selected')


class RoleTab:
    """Builds and drives the two panels for one PlayerWindow (`win`): list_panel (left, 456 wide) + pitch_panel (right)."""

    def __init__(self, win):
        self.win = win
        self.preset = _weights.load_active_preset()
        self.is_gk = bool(win._is_gk)
        self.live = [q for q in POS_DISPLAY if (q == 'GK') == self.is_gk]
        self.best_pos = self._default_pos()
        self.sel = self.best_pos
        self.list_panel = self._build_list()
        self.pitch_panel = self._build_pitch()
        self.refresh()

    # -- data ------------------------------------------------------------------------------------
    def attrs(self):
        """54 attributes on the 0-100 raw scale for the window's Current | Full Potential mode, or None without attribute data."""
        w = self.win
        raw = w._person.get('raw_attrs')
        if not raw or len(raw) < 54:
            return None
        return [x * 5 for x in w._projection().proj] if w._pot_on else raw

    def _default_pos(self):
        """The player's best position (highest rating, then the listed one, then list order) among the rateable ones."""
        w = self.win
        return sorted(self.live, key=lambda q: (-w._ratings.get(q, 1), q != w._pos, POS_DISPLAY.index(q)))[0]

    def weights_name(self):
        return (self.preset or {}).get('name') or 'Equal Weight'

    def tip(self, pos, info, dim):
        w = self.win
        title = POS_FULL[pos] + (' (best position)' if pos == self.best_pos else '')
        if info is None:
            why = ('Not rated: no attribute data in the save' if not w._person.get('raw_attrs') or len(w._person['raw_attrs']) < 54
                   else 'Not rated: goalkeeper roles are only rated for goalkeepers' if pos == 'GK'
                   else 'Not rated: outfield roles are not rated for goalkeepers')
            return f'{title}\n{why}'
        r = w._ratings.get(pos, 1)
        t = f'{title}\nBest role: {info[0]} {pct_text(info[1])}\nPosition rating: {word(r)} ({r})'
        return t + ('\nDimmed: position rating below 10, not familiar with this position' if dim else '')

    # -- widgets ---------------------------------------------------------------------------------
    def _build_list(self):
        panel = QFrame()
        panel.setObjectName('pwPanel')
        panel.setFixedWidth(456)
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self._head = QWidget()
        self._head.setObjectName('pwHead')
        self._head.setFixedHeight(HEAD_H)
        self._hl = QHBoxLayout(self._head)
        self._hl.setContentsMargins(12, 0, 12, 0)
        self._hl.setSpacing(8)
        self._badge = self.win._badge(self.sel, True)
        self._title = _ElideLabel('', 'pwRoleT', natural=True)
        self._title.setStyleSheet('QLabel#pwRoleT { font-size:13px; font-weight:bold; color:#FFFFFF; }')
        self._note = _spaced(_lab('', 'pwNote'))     # mockup .ph: uppercase + letter-spacing .08em
        self._hl.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self._hl.addWidget(self._title, 1, Qt.AlignmentFlag.AlignVCenter)
        self._hl.addWidget(self._note, 0, Qt.AlignmentFlag.AlignVCenter)
        v.addWidget(self._head)
        self.rolelist = RoleList()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.rolelist)
        v.addWidget(scroll, 1)
        foot = QFrame()
        foot.setObjectName('pwRoleFoot')
        foot.setStyleSheet(f"QFrame#pwRoleFoot {{ border:none; border-top:1px solid {COLORS['border']}; }}")
        fv = QVBoxLayout(foot)
        fv.setContentsMargins(12, 6, 12, 8)
        self._foot = _lab('', 'pwNote')
        self._foot.setTextFormat(Qt.TextFormat.RichText)
        self._foot.setWordWrap(True)
        self._foot.setText(f'Weights: <span style="color:#FFFFFF; font-weight:500">{self.weights_name()}</span> (Settings)<br>{FOOT}')
        fv.addWidget(self._foot)
        v.addWidget(foot)
        return panel

    def _build_pitch(self):
        panel = QFrame()
        panel.setObjectName('pwPanel')
        panel.setMaximumWidth(444)
        panel.setMinimumWidth(300)
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setObjectName('pwHead')
        head.setFixedHeight(HEAD_H)
        h = QHBoxLayout(head)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)
        h.addWidget(_spaced(_lab('CHOOSE A POSITION', 'pwHeadT')))
        h.addStretch()
        h.addWidget(self.win._pot_seg(), 0, Qt.AlignmentFlag.AlignVCenter)
        v.addWidget(head)
        self.pitch = RolePitch()
        self.pitch.picked.connect(self.select)
        v.addWidget(self.pitch, 1)
        v.addWidget(_TierKey())
        return panel

    # -- state -----------------------------------------------------------------------------------
    def select(self, pos):
        """Select a position (ignored for one that cannot be rated: GK vs outfield)."""
        if pos in self.live and pos != self.sel:
            self.sel = pos
            self.refresh()

    def refresh(self):
        """Recompute everything from the window's current mode (Current | Full Potential) and the selection."""
        raw = self.attrs()
        best = rolepos.best_by_position(raw, self.preset, self.live) if raw else {}
        info = {q: (best.get(q) if q in self.live else None) for q in POS_DISPLAY}
        dim = {q: info[q] is not None and self.win._ratings.get(q, 1) < LOW_FAM for q in POS_DISPLAY}
        self.pitch.set_state(info, {q: self.tip(q, info[q], dim[q]) for q in POS_DISPLAY}, dim, self.sel, self.best_pos)
        groups = rolepos.position_roles(self.sel, raw, self.preset) if raw else []
        self.rolelist.set_groups(groups, groups[0][1][0][1] if groups else None, 'No attribute data in the save.')
        old = self._badge
        self._badge = self.win._badge(self.sel, True)
        self._hl.replaceWidget(old, self._badge)
        old.hide()
        old.deleteLater()
        self._title.setText(POS_FULL[self.sel])
        self._title._full = POS_FULL[self.sel]
        self._title._elide()
        self._title.updateGeometry()
        self._note.setText(f'{len(groups)} roles · Rating %'.upper())
