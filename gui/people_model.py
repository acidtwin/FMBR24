"""Virtualised model for the Scouting Players / Staff lists (77k + 54k rows, no cap).

No per-cell QTableWidgetItem: `rows[i]` is a tuple of precomputed base-column values for
source person `i`; attribute columns past `len(rows[i])` are read lazily from the person
dict. Sorting is done here (index array + cached key lists) because a
QSortFilterProxyModel with a Python lessThan is ~1 s per sort at this size.
"""
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor
from fm_editor import infotags

HG_ROLE = Qt.ItemDataRole.UserRole + 1       # HGP/HGC cell: 'set' | 'queued' | ''
ROWQ_ROLE = Qt.ItemDataRole.UserRole + 2     # row: True when that person has ANY queued edit
HG_BASE_ROLE = Qt.ItemDataRole.UserRole + 3  # QTableWidget HG cells: value in the save (True/False/None unknown)
MEDIA_UID_ROLE = Qt.ItemDataRole.UserRole + 4   # Name cell: the person's identity uid (face picture key)
CLUB_UID_ROLE = Qt.ItemDataRole.UserRole + 5    # Club cell: the club's parsed save uid (badge key), None = no club
NATION_ROLE = Qt.ItemDataRole.UserRole + 6      # Nation cell: our nation entity id (flag key)
INFO_ROLE = Qt.ItemDataRole.UserRole + 7        # Info cell: its tag list [(code, label, tooltip)] (fm_editor.infotags)
INFO_BASE_ROLE = Qt.ItemDataRole.UserRole + 8   # QTableWidget Info cell: (person, tags_for kwargs without the queue)
ROW_TINT = QColor(234, 217, 92, 26)          # rgba(234,217,92,.10): faint yellow under a queued row (painted by the delegates)


def nation_label(nid):
    """Nation name for our nation entity id (tooltip of the flag cell), or None."""
    from fm_editor.nations import nation_name
    return nation_name(nid) if nid is not None else None


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
        self.hg_cols = {}           # col -> 'hgp'|'hgc': badge columns (row value = set in the save)
        self.club_uid_idx = None    # index in a row tuple of the club's save uid (badge key); the tuple is longer than spec
        self.tip_text_cols = set()  # columns whose tooltip is the cell text (club name behind a badge)
        self.nation_col = None      # column whose tooltip is the nation's name
        self.blank_header = set()   # columns whose header label is hidden (the 40 px club badge column)
        self.queued = {}            # person id -> {'hgp','hgc'} queued edits (set_queue)
        self._by_id = None          # person id -> src index, built lazily
        self.info_col = None        # Info column (fm_editor.infotags): tags are computed lazily per row and cached
        self.info_fn = None         # fn(person, queued kinds) -> [(code, label, tooltip)]
        self._info = {}             # src index -> tags

    # -- data ---------------------------------------------------------------
    def set_data(self, src, rows):
        self.beginResetModel()
        self.src, self.rows = src, rows
        self._keys = {}
        self._info = {}
        self._by_id = None
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

    def info_tags(self, si):
        t = self._info.get(si)
        if t is None:
            p = self.src[si]
            t = self._info[si] = self.info_fn(p, self.queued.get(p.get('id'), ()))
        return t

    def _key_list(self, col):
        k = self._keys.get(col)
        if k is None:
            if col == self.info_col:
                k = [infotags.sort_key(self.info_tags(i)) for i in range(len(self.src))]
            elif col in self.hg_cols:   # set or queued first, then unset
                kind, q = self.hg_cols[col], self.queued
                k = [0 if r[col] or kind in q.get(p.get('id'), ()) else 1 for r, p in zip(self.rows, self.src)]
            elif col < len(self.spec):
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

    def set_queue(self, qmap):
        """qmap: person id -> set of queued kinds. Only the rows whose state changed are repainted
        (the diff is O(queue size); the first call builds an id -> row map, and a changed row costs one pass over the view); a list sorted by
        an HGP/HGC column is re-sorted."""
        old, self.queued = self.queued, qmap
        changed = [pid for pid in old.keys() | qmap.keys() if old.get(pid) != qmap.get(pid)]
        if not changed:
            return
        for c in self.hg_cols:
            self._keys.pop(c, None)
        if self.info_col is not None:
            self._keys.pop(self.info_col, None)
            if self._by_id is None:
                self._by_id = {p.get('id'): i for i, p in enumerate(self.src)}
            for pid in changed:
                self._info.pop(self._by_id.get(pid), None)
        if self._sort[0] in self.hg_cols or self._sort[0] == self.info_col:
            self.sort(*self._sort)
            return
        if self._by_id is None:
            self._by_id = {p.get('id'): i for i, p in enumerate(self.src)}
        pos = None
        last = self.columnCount() - 1
        for pid in changed:
            si = self._by_id.get(pid)
            if si is None:
                continue
            if pos is None:
                pos = {s: r for r, s in enumerate(self.view)}
            r = pos.get(si)
            if r is not None:
                self.dataChanged.emit(self.index(r, 0), self.index(r, last))

    def _hg_state(self, si, c):
        if self.rows[si][c]:
            return 'set'
        return 'queued' if self.hg_cols[c] in self.queued.get(self.src[si].get('id'), ()) else ''

    # -- Qt model API -------------------------------------------------------
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.view)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.cols)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.cols):
            if role == Qt.ItemDataRole.DisplayRole:
                return '' if section in self.blank_header else self.cols[section]
            if role == Qt.ItemDataRole.ToolTipRole:
                return self.tips.get(self.cols[section]) or (self.cols[section] if section in self.blank_header else None)
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        if c == self.info_col and role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole, INFO_ROLE,
                                            Qt.ItemDataRole.AccessibleTextRole):
            t = self.info_tags(self.view[r])
            return (t if role == INFO_ROLE else infotags.joined(t) if role == Qt.ItemDataRole.DisplayRole
                    else infotags.tooltip(t) or None)
        if role == Qt.ItemDataRole.DisplayRole:
            si = self.view[r]
            row = self.rows[si]
            if c in self.hg_cols:
                st = self._hg_state(si, c)
                return self.hg_cols[c].upper() if st == 'set' else f'+ {self.hg_cols[c].upper()}' if st else ''
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
        if role == Qt.ItemDataRole.ToolTipRole:
            tip = self.tooltip_fn(self.src[self.view[r]], c) if self.tooltip_fn else None
            if tip is None:
                if c in self.tip_text_cols:
                    si = self.view[r]
                    return self.spec[c][0](self.rows[si][c]) or None
                if c == self.nation_col:
                    return nation_label(self.src[self.view[r]].get('nation'))
            return tip
        if role == MEDIA_UID_ROLE:
            return self.src[self.view[r]].get('uid')
        if role == CLUB_UID_ROLE:
            return self.rows[self.view[r]][self.club_uid_idx] if self.club_uid_idx is not None else None
        if role == NATION_ROLE:
            return self.src[self.view[r]].get('nation')
        if role == HG_ROLE:
            return self._hg_state(self.view[r], c) if c in self.hg_cols else None
        if role == ROWQ_ROLE:
            return bool(self.queued) and self.src[self.view[r]].get('id') in self.queued
        if role == Qt.ItemDataRole.UserRole:   # person id, as the old name item carried
            return self.src[self.view[r]].get('id', -1)
        return None
