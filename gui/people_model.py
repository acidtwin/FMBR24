"""Virtualised model for the Scouting Players / Staff lists (77k + 54k rows, no cap).

No per-cell QTableWidgetItem: `rows[i]` is a tuple of precomputed base-column values for
source person `i`; attribute columns past `len(rows[i])` are read lazily from the person
dict. Sorting is done here (index array + cached key lists) because a
QSortFilterProxyModel with a Python lessThan is ~1 s per sort at this size.
"""
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex


def num_key(v):
    return -1 if v is None else v


class PeopleModel(QAbstractTableModel):
    """cols: header labels. spec[c] = (display_fn, key_fn) for base columns (fn(value));
    lazy_fn(person, col) -> int|None for columns beyond len(spec)."""

    def __init__(self, cols, spec, tips=None, lazy_fn=None, parent=None):
        super().__init__(parent)
        self.cols = cols
        self.spec = spec
        self.tips = tips or {}
        self.lazy_fn = lazy_fn
        self.src = []          # person dicts (base order)
        self.rows = []         # precomputed tuples, parallel to src
        self._base = []        # src indices passing the filter, base order
        self.view = []         # src indices in display order
        self._keys = {}        # col -> key list over all src
        self._sort = (-1, Qt.SortOrder.AscendingOrder)
        self.align_center = set()   # columns centred
        self.big_font_cols = {}     # col -> QFont
        self.fg = {}                # col -> fn(row_tuple) -> QColor | None
        self.tooltip_fn = None      # fn(person, col) -> str | None

    # -- data ---------------------------------------------------------------
    def set_data(self, src, rows):
        self.beginResetModel()
        self.src, self.rows = src, rows
        self._keys = {}
        self._base = list(range(len(src)))
        self._resort()
        self.endResetModel()

    def clear(self):
        self.set_data([], [])

    def total(self):
        return len(self.src)

    def person(self, row):
        return self.src[self.view[row]] if 0 <= row < len(self.view) else None

    def set_base(self, idx):
        """Replace the filtered set (src indices, base order); keeps the current sort."""
        self.beginResetModel()
        self._base = idx
        self._resort()
        self.endResetModel()

    def _key_list(self, col):
        k = self._keys.get(col)
        if k is None:
            if col < len(self.spec):
                kf = self.spec[col][1]
                k = [r[col] for r in self.rows] if kf is None else [kf(r[col]) for r in self.rows]
            else:
                lf = self.lazy_fn
                k = [num_key(lf(p, col)) for p in self.src]
            self._keys[col] = k
        return k

    def _resort(self):
        col, order = self._sort
        if col < 0 or not self._base:
            self.view = list(self._base)
            return
        k = self._key_list(col)
        self.view = sorted(self._base, key=k.__getitem__,
                           reverse=(order == Qt.SortOrder.DescendingOrder))

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        old = self.persistentIndexList()  # after the signal: includes the views' saved selection
        srcs = [(self.view[i.row()], i.column()) for i in old]
        self._sort = (column, order)
        self._resort()
        if old:
            pos = {s: r for r, s in enumerate(self.view)}
            self.changePersistentIndexList(
                old, [self.index(pos[s], c) if s in pos else QModelIndex() for s, c in srcs])
        self.layoutChanged.emit()

    # -- Qt model API -------------------------------------------------------
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.view)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.cols)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.cols):
            if role == Qt.ItemDataRole.DisplayRole:
                return self.cols[section]
            if role == Qt.ItemDataRole.ToolTipRole:
                return self.tips.get(self.cols[section])
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            si = self.view[r]
            row = self.rows[si]
            if c < len(self.spec):
                return self.spec[c][0](row[c])
            v = self.lazy_fn(self.src[si], c)
            return '' if v is None else str(v)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int((Qt.AlignmentFlag.AlignHCenter if c in self.align_center
                        else Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.FontRole:
            f = self.big_font_cols.get(c)
            if f is not None and str(self.rows[self.view[r]][c])[:1].isalpha():
                return None  # big font is for emoji flags; a text fallback (nation name) stays normal size
            return f
        if role == Qt.ItemDataRole.ForegroundRole:
            f = self.fg.get(c)
            return f(self.rows[self.view[r]]) if f else None
        if role == Qt.ItemDataRole.ToolTipRole and self.tooltip_fn:
            return self.tooltip_fn(self.src[self.view[r]], c)
        if role == Qt.ItemDataRole.UserRole:   # person id, as the old name item carried
            return self.src[self.view[r]].get('id', -1)
        return None
