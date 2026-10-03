"""Info column tags of the player lists (mockups/player-lists.html, recipe in its second header comment). No Qt.

Only tags derivable from data we already parse: INJ, queued +HGP/+HGC, HGP, HGC, LOAN, NFS, U21. Other FM tags
(Spt, Amg, PR, Ask, Wnt, Unh, Slt ...) are a FUTURE ADD (docs/DESIGN-BACKLOG.md: needs data we cannot read yet).
A tag is (code, label, tooltip); `code` is one of PRI, the label is the text painted on the tag.
"""
NOT_FOR_SALE = 300_000_000   # stored value marker (same as fm_editor.valuecurve.NOT_FOR_SALE)
U21_MAX_AGE = 21
PRI = ('INJ', '+HGP', '+HGC', 'HGP', 'HGC', 'LOAN', 'NFS', 'U21')   # priority = stack order, front first


def tags_for(person, *, queued_hgp=False, queued_hgc=False, hgp=False, hgc=False, age=None, injured_days=0,
             loan_parent=None, value_est=None, loan_club=None):
    """Ordered [(code, label, tooltip)], front tag first. person: the person dict (reads 'injured'); hgp / hgc =
    value in the save (hgc None = unknown); a queued kind replaces the plain tag only while it is not set yet.
    LOAN and NFS never coexist (a loanee who is also Not for sale shows LOAN only, HANDOVER). loan_club = parent club name."""
    t = []
    if person.get('injured'):
        t.append(('INJ', 'INJ', f'Injured, {injured_days} days' if injured_days and injured_days > 0 else 'Injured'))
    if queued_hgp and not hgp:
        t.append(('+HGP', '+HGP', 'Queued: Homegrown player (nation), written on Save Changes'))
    if queued_hgc and not hgc:
        t.append(('+HGC', '+HGC', 'Queued: Homegrown player (club), written on Save Changes'))
    if hgp:
        t.append(('HGP', 'HGP', 'Homegrown player (nation)'))
    if hgc:
        t.append(('HGC', 'HGC', 'Homegrown player (club)'))
    if loan_parent is not None:
        t.append(('LOAN', 'LOAN', f'On loan from {loan_club}' if loan_club else 'On loan'))
    elif value_est is not None and value_est >= NOT_FOR_SALE:
        t.append(('NFS', 'NFS', 'Not for sale'))
    if age is not None and age <= U21_MAX_AGE:
        t.append(('U21', 'U21', 'Under 21'))
    return t


def sort_key(tags):
    """Header-sort key: injured first (old INJ column meaning), then more tags, then the front tag's priority, then the rest."""
    r = [PRI.index(c) for c, _l, _t in tags]
    return (bool(r and r[0] == 0)) * 10**7 + len(r) * 10**6 + sum((9 - x) * 10 ** (5 - i) for i, x in enumerate(r[:6]))


def joined(tags):
    """Cell text (Ctrl+C, type-ahead, accessibility): the short labels."""
    return ' '.join(l for _c, l, _t in tags)


def tooltip(tags):
    """Collapsed cell tooltip: every tag's line."""
    return '\n'.join(t for _c, _l, t in tags)
