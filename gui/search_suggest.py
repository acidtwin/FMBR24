"""Search-box autocomplete popup (kind-tagged rows: Club / Staff / Player)."""
from PyQt6.QtWidgets import (QApplication, QStyle, QListWidget, QListWidgetItem, QFrame, QVBoxLayout,
                             QStyledItemDelegate)
from PyQt6.QtCore import Qt, QSize, QPoint, QRectF
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter
from gui.theme import COLORS

_SUGGEST_KINDS = ('Club', 'Staff', 'Player')  # kind index -> tag text
_SG_MAX = 12  # max suggestion rows


class _SuggestDelegate(QStyledItemDelegate):
    """Row = name (left), muted club (after name), muted type tag (right-aligned)."""

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), _SearchSuggest.ROW_H)

    def paint(self, p, option, index):
        r = option.rect
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        sel = bool(option.state & QStyle.StateFlag.State_Selected)
        if sel:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(COLORS['selection_bg']))
            p.drawRoundedRect(QRectF(r).adjusted(1, 0, -1, 0), 3, 3)
        name = index.data(Qt.ItemDataRole.UserRole + 1) or ''
        sub = index.data(Qt.ItemDataRole.UserRole + 2) or ''
        kind = index.data(Qt.ItemDataRole.UserRole)[0]
        pad = 10
        f = QFont(option.font)
        f.setPixelSize(12)
        p.setFont(f)
        tag_f = QFont(f)
        tag_f.setPixelSize(11)
        tag = _SUGGEST_KINDS[kind]
        tag_w = QFontMetrics(tag_f).horizontalAdvance(tag)
        # type tag, right-aligned in a fixed column
        p.setFont(tag_f)
        p.setPen(QColor(COLORS['text_secondary']))
        p.drawText(r.adjusted(0, 0, -pad, 0),
                   int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), tag)
        # name, then optional club
        p.setFont(f)
        fm = QFontMetrics(f)
        avail = r.width() - 2 * pad - tag_w - 12
        nm = fm.elidedText(name, Qt.TextElideMode.ElideRight, avail)
        p.setPen(QColor(COLORS['text_primary']))
        p.drawText(r.adjusted(pad, 0, 0, 0),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), nm)
        rest = avail - fm.horizontalAdvance(nm) - 10
        if sub and rest > 40:
            p.setPen(QColor(COLORS['text_dim']))
            x = pad + fm.horizontalAdvance(nm) + 10
            p.drawText(r.adjusted(x, 0, 0, 0),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       fm.elidedText(sub, Qt.TextElideMode.ElideRight, rest))
        p.restore()


class _SearchSuggest(QFrame):
    """Autocomplete dropdown under the top search box.

    A plain child widget of the main window (not a Popup window), so it never steals
    keyboard focus and positions reliably on X11 and Wayland. Key handling is done by
    filtering the search box; clicks outside close it via an application event filter.
    """
    ROW_H = 28

    def __init__(self, window, box, on_pick, flush=None):
        super().__init__(window)
        self._win, self._box, self._on_pick, self._flush = window, box, on_pick, flush
        self.setObjectName('searchDropdown')
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            f"QFrame#searchDropdown {{ background:{COLORS['elevated']};"
            f" border:1px solid {COLORS['border_bright']}; border-radius:4px; }}"
            "QListWidget#searchList { background:transparent; border:none; outline:none; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(3, 3, 3, 3)
        self._list = QListWidget()
        self._list.setObjectName('searchList')
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.setItemDelegate(_SuggestDelegate(self._list))
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setMouseTracking(True)
        self._list.itemEntered.connect(lambda it: self._list.setCurrentItem(it))
        self._list.itemClicked.connect(self._clicked)
        lay.addWidget(self._list)
        box.installEventFilter(self)
        self.hide()

    def set_rows(self, rows):
        """rows: [(kind, obj, name, sub)]. Shows below the box, or hides if empty."""
        self._list.clear()
        if not rows:
            self._close()
            return
        for kind, obj, name, sub in rows:
            it = QListWidgetItem()
            it.setData(Qt.ItemDataRole.UserRole, (kind, obj))
            it.setData(Qt.ItemDataRole.UserRole + 1, name)
            it.setData(Qt.ItemDataRole.UserRole + 2, sub)
            self._list.addItem(it)
        self._list.setCurrentRow(0)
        b = self._box
        pos = b.mapTo(self._win, QPoint(0, b.height() + 2))
        self.setGeometry(pos.x(), pos.y(), max(280, b.width()),
                         len(rows) * self.ROW_H + 8)
        self.raise_()
        if not self.isVisible():
            self.show()
            QApplication.instance().installEventFilter(self)

    def _close(self):
        if self.isVisible():
            QApplication.instance().removeEventFilter(self)
            self.hide()

    def close_popup(self):
        self._close()

    def _clicked(self, item):
        kind, obj = item.data(Qt.ItemDataRole.UserRole)
        self._close()
        self._on_pick(kind, obj, item.data(Qt.ItemDataRole.UserRole + 1))

    def _move(self, step):
        n = self._list.count()
        if n:
            self._list.setCurrentRow((self._list.currentRow() + step) % n)

    def eventFilter(self, obj, ev):
        t = ev.type()
        if obj is self._box:
            if t == ev.Type.FocusOut:
                self._close()
            elif t == ev.Type.KeyPress:
                k = ev.key()
                if k == Qt.Key.Key_Escape and self.isVisible():
                    self._close()
                    return True
                if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if self._flush:
                        self._flush()  # apply a pending debounced query first
                    if self.isVisible() and self._list.currentItem():
                        self._clicked(self._list.currentItem())
                        return True
                elif k in (Qt.Key.Key_Down, Qt.Key.Key_Up) and self.isVisible():
                    self._move(1 if k == Qt.Key.Key_Down else -1)
                    return True
            return False
        # application-level: click outside / window change closes
        if t == ev.Type.MouseButtonPress:
            gp = ev.globalPosition().toPoint()
            if not self.rect().contains(self.mapFromGlobal(gp)) \
                    and not self._box.rect().contains(self._box.mapFromGlobal(gp)):
                self._close()
        elif t in (ev.Type.WindowDeactivate, ev.Type.Resize) and obj is self._win:
            self._close()
        return False
