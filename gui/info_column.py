"""Info column painting + hover spread of the player lists (mockups/player-lists.html, variant A; recipe in its second header comment).

`paint_stack` draws the fanned tag stack for a spread factor s (0 = collapsed stack in the cell, 1 = fully spread);
`TagSpread` is the floating overlay child of the table viewport that paints it while the mouse is over the Info cell of a row
with 2+ tags; `InfoHover` is the viewport event filter that drives it with ONE reused QVariantAnimation
(enter 180 ms OutCubic to s=1, leave 120 ms InCubic to s=0, interruptible: it always continues from the current s).
No Qt widgets are created per row; tags come from the INFO_ROLE data (list of (code, label, tooltip), fm_editor.infotags)."""
from PyQt6.QtCore import Qt, QRectF, QRect, QObject, QEvent, QVariantAnimation, QEasingCurve, QPersistentModelIndex, QModelIndex
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QToolTip

from gui.people_model import INFO_ROLE, ROWQ_ROLE, ROW_TINT

INFO_W = 80                          # column width
TAG_H, TAG_R, INSET, PEEK, GAP, MAX_STACK = 18, 3, 6, 9, 4, 3
TW = {'INJ': 28, 'HGP': 28, 'HGC': 28, 'NFS': 28, 'U21': 28, '+HGP': 36, '+HGC': 36, 'LOAN': 36}
ST = {'INJ': ('#8B1A1A', '#FFFFFF'), 'HGP': ('#2B7A4B', '#FFFFFF'), 'HGC': ('#1B4D31', '#FFFFFF'),
      'LOAN': ('#2A4F86', '#D6E6FF'), 'NFS': ('#4A4636', '#E0C98A'), 'U21': ('#2C8C80', '#E6FFFA'),
      '+HGP': ('#323023', '#EAD95C'), '+HGC': ('#323023', '#EAD95C')}   # queued: opaque (= rgba(234,217,92,.14) over #14151A)
QUEUED_EDGE = QColor('#EAD95C')
BG_BASE, BG_ALT, BG_SEL = QColor('#14151A'), QColor('#161721'), QColor('#2A1B4A')
EDGE, EDGE_SEL = QColor('#343740'), QColor(154, 124, 255, 140)   # rgba(154,124,255,.55)
DIM = QColor('#8B96A8')
ENTER_MS, LEAVE_MS = 180, 120
_ST_QC = {k: (QColor(a), QColor(b)) for k, (a, b) in ST.items()}


def row_bg(row, selected, queued):
    """The row colour the QSS paints (alternate #161721 / #14151A / selected #2A1B4A), queued tint blended over it."""
    c = BG_SEL if selected else BG_ALT if row & 1 else BG_BASE
    if queued and not selected:
        a = ROW_TINT.alpha() / 255
        c = QColor(*[round(x * (1 - a) + y * a) for x, y in ((c.red(), ROW_TINT.red()), (c.green(), ROW_TINT.green()),
                                                              (c.blue(), ROW_TINT.blue()))])
    return c


def _w(code):
    return TW.get(code, 28)


def spread_lefts(tags):
    """Spread layout: left of each tag (relative to the cell) and the card width."""
    x, out = INSET, []
    for c, _l, _t in tags:
        out.append(x)
        x += _w(c) + GAP
    return out, x + GAP


def collapsed_extent(tags):
    """Width the collapsed stack (+ '+n' marker) occupies, relative to the cell."""
    k = min(MAX_STACK, len(tags))
    return INSET + _w(tags[0][0]) + PEEK * (k - 1) + (16 if len(tags) > MAX_STACK else 2) + 2


def tag_rects(tags, s, y, h=TAG_H):
    """[(x_left, width)] of every tag for spread factor s (relative to the cell's left edge)."""
    fw = _w(tags[0][0])
    l1, _w1 = spread_lefts(tags)
    out = []
    for i, (c, _l, _t) in enumerate(tags):
        l0 = INSET + fw + PEEK * min(i, MAX_STACK - 1) - _w(c)
        out.append((l0 + (l1[i] - l0) * s, _w(c)))
    return out


def _font():
    f = QFont()
    f.setPixelSize(10)
    f.setBold(True)
    return f


def paint_stack(p, x0, y0, h, tags, bg, s=0.0):
    """Draw the stack with the cell's left edge at x0 and its top at y0 (row height h), spread factor s. Back to front, front tag last."""
    if not tags:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    font = _font()
    p.setFont(font)
    ty = y0 + (h - TAG_H) / 2
    rects = tag_rects(tags, s, ty)
    base_op = p.opacity()
    for i in range(len(tags) - 1, -1, -1):
        c, label, _t = tags[i]
        a = 1.0 if i < MAX_STACK else s       # tags beyond the third sit in the third's slot and fade in
        if a <= 0:
            continue
        p.setOpacity(base_op * a)
        left, w = rects[i]
        r = QRectF(x0 + left, ty, w, TAG_H)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(r.adjusted(-1, -1, 1, 1), TAG_R + 1, TAG_R + 1)   # 1px ring in the row colour
        fill, fg = _ST_QC[c]
        queued = c[0] == '+'
        if queued:
            p.setPen(QPen(QUEUED_EDGE, 1))
            r = r.adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(fill)
        p.drawRoundedRect(r, TAG_R, TAG_R)
        la = 1.0 if i == 0 else s              # the label of a back tag is only readable when it spreads out
        if la > 0:
            p.setOpacity(base_op * a * la)
            p.setPen(fg)
            p.drawText(QRectF(x0 + left, ty, w, TAG_H), Qt.AlignmentFlag.AlignCenter, label)
    p.setOpacity(base_op)
    if len(tags) > MAX_STACK and s < 1:
        p.setOpacity(base_op * (1 - s))
        p.setPen(DIM)
        f9 = QFont(font)
        f9.setPixelSize(9)
        p.setFont(f9)
        mx = INSET + _w(tags[0][0]) + PEEK * (MAX_STACK - 1) + GAP
        p.drawText(QRectF(x0 + mx, y0, 24, h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f'+{len(tags) - MAX_STACK}')
    p.restore()


class TagSpread(QWidget):
    """Opaque floating card over the Info cell (child of the table viewport, mouse-transparent): the cell's stack plus its spread."""
    SH = 13   # room for the shadow right / below

    def __init__(self, viewport):
        super().__init__(viewport)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.s = 0.0
        self.tags = []
        self.index = QPersistentModelIndex()
        self.cell = QRect()
        self.table = None
        self.hide()

    def shift(self):
        """Leftwards shift (scaled by s) when the full spread would pass the viewport's right edge."""
        return max(0.0, self.cell.x() - 1 + spread_lefts(self.tags)[1] - self.parentWidget().width()) * self.s

    def card_rect(self):
        """Card rect in viewport coordinates for the current s."""
        w0, w1 = collapsed_extent(self.tags), spread_lefts(self.tags)[1]
        return QRectF(self.cell.x() - 1 - self.shift(), self.cell.y() - 1, w0 + (w1 - w0) * self.s, self.cell.height() + 2)

    def sync(self):
        if not self.tags:
            return
        c = self.card_rect()
        self.setGeometry(int(c.x()) - 8, int(c.y()) - 8, int(c.width()) + 8 + self.SH, int(c.height()) + 8 + self.SH)
        self.update()

    def bg(self):
        i = QModelIndex(self.index)
        sel = self.table.selectionModel().isRowSelected(i.row(), QModelIndex()) if self.table.selectionModel() else False
        return row_bg(i.row(), sel, bool(i.siblingAtColumn(0).data(ROWQ_ROLE))), sel

    def paintEvent(self, _e):
        if not self.tags or not self.index.isValid():
            return
        bg, sel = self.bg()
        s = self.s
        c = self.card_rect()
        card = QRectF(c.x() - self.x(), c.y() - self.y(), c.width(), c.height()).adjusted(0.5, 0.5, -0.5, -0.5)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        # no shadow and no outline on the hover card (user): just the row colour behind the spread tags
        p.setPen(Qt.PenStyle.NoPen)   # no outline on the hover card (user), the shadow alone lifts it
        p.setBrush(bg)
        p.drawRoundedRect(card, 4, 4)
        p.setPen(Qt.PenStyle.NoPen)
        paint_stack(p, self.cell.x() - self.shift() - self.x(), self.cell.y() - self.y(), self.cell.height(), self.tags, bg, s)
        p.end()

    def tag_at(self, pos):
        """Tooltip line of the tag under viewport point pos (fully spread only), else None."""
        if self.s < 1 or not self.tags:
            return None
        ox = self.cell.x() - self.shift()
        for (left, w), (_c, _l, tip) in zip(tag_rects(self.tags, 1.0, 0), self.tags):
            if QRectF(ox + left, self.cell.y(), w, self.cell.height()).contains(pos.x(), pos.y()):
                return tip
        return None


class InfoHover(QObject):
    """Viewport event filter: hover over the Info cell of a 2+ tag row spreads the stack in a floating TagSpread (animated)."""
    def __init__(self, table, col):
        super().__init__(table)
        self.table, self.col = table, col
        self.ov = TagSpread(table.viewport())
        self.ov.table = table
        self.anim = QVariantAnimation(self)
        self.anim.valueChanged.connect(self._set_s)
        self.anim.finished.connect(self._done)
        table.viewport().installEventFilter(self)
        table.setMouseTracking(True)
        table.verticalScrollBar().valueChanged.connect(self.hide_now)
        table.horizontalScrollBar().valueChanged.connect(self.hide_now)
        table.horizontalHeader().sortIndicatorChanged.connect(self.hide_now)
        table.horizontalHeader().sectionResized.connect(self.hide_now)
        m = table.model()
        for sig in (m.modelReset, m.layoutChanged, m.rowsInserted, m.rowsRemoved):
            sig.connect(self.hide_now)
        m.dataChanged.connect(self._data_changed)
        sm = table.selectionModel()
        if sm is not None:
            sm.selectionChanged.connect(self._sel_changed)

    def _sel_changed(self, *_):
        try:
            if self.ov.isVisible():
                self.ov.update()
        except RuntimeError:
            pass

    # -- animation ---------------------------------------------------------
    def _go(self, to):
        self.anim.stop()
        self.anim.setStartValue(self.ov.s)
        self.anim.setEndValue(float(to))
        self.anim.setDuration(ENTER_MS if to else LEAVE_MS)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic if to else QEasingCurve.Type.InCubic)
        self.anim.start()

    def _set_s(self, v):
        self.ov.s = float(v)
        self.ov.sync()

    def _done(self):
        if self.ov.s <= 0:
            self.ov.hide()

    def hide_now(self, *_):
        try:
            self.anim.stop()
            self.ov.s = 0.0
            self.ov.hide()
        except RuntimeError:   # table already being destroyed (model signals at teardown)
            pass

    def _data_changed(self, tl, br, *_):
        try:
            if self.ov.isVisible() and self.ov.index.isValid() and tl.row() <= QModelIndex(self.ov.index).row() <= br.row():
                self.hide_now()
        except RuntimeError:
            pass

    # -- mouse -------------------------------------------------------------
    def _target(self, pos):
        """(index, tags) of the 2+ tag Info cell under pos, or the card's own cell while pos is over the spread card."""
        ov = self.ov
        if ov.isVisible() and ov.index.isValid() and ov.card_rect().contains(pos.x(), pos.y()):
            return QModelIndex(ov.index), ov.tags
        i = self.table.indexAt(pos)
        if i.isValid() and i.column() == self.col:
            tags = i.data(INFO_ROLE)
            if tags and len(tags) >= 2:
                return i, tags
        return None, None

    def _show(self, i, tags):
        ov = self.ov
        if QPersistentModelIndex(i) != ov.index or not ov.isVisible():
            self.anim.stop()
            ov.s = 0.0
            ov.index = QPersistentModelIndex(i)
            ov.tags = list(tags)
            ov.cell = self.table.visualRect(i)
            ov.sync()
            ov.show()
            ov.raise_()
        if self.anim.endValue() != 1.0 or self.anim.state() != QVariantAnimation.State.Running:
            if ov.s < 1.0:
                self._go(1)

    def _leave(self):
        if self.ov.isVisible() and self.ov.s > 0 and not (self.anim.state() == QVariantAnimation.State.Running and self.anim.endValue() == 0.0):
            self._go(0)
        elif self.ov.isVisible() and self.ov.s <= 0:
            self.ov.hide()

    def eventFilter(self, obj, e):
        t = e.type()
        if t == QEvent.Type.MouseMove:
            i, tags = self._target(e.position().toPoint())
            self._show(i, tags) if i is not None else self._leave()
        elif t in (QEvent.Type.Leave, QEvent.Type.Hide, QEvent.Type.WindowDeactivate):
            self._leave()
        elif t == QEvent.Type.ToolTip and self.ov.isVisible() and self.ov.s >= 1:
            tip = self.ov.tag_at(e.pos())
            if tip:
                QToolTip.showText(e.globalPos(), tip, self.table.viewport())
                return True
        return False
