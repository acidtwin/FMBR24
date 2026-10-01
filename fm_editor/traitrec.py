"""Trait recommender (no Qt): which preferred moves (PPMs) suit a player's attributes.

Data: data/trait_recommender.json, converted once from "FM Trait Recommender v1" (Google Sheet, community
author) which in turn takes the trait -> attribute lists from GuideToFM's player trait guide. Credit to
GuideToFM and the sheet author. Corrections vs the sheet: attribute-name typos/trailing spaces fixed
('determinatoin', 'balace', 'finishing ', 'agility ', 'work rate ' - the sheet silently dropped those from
its averages), a duplicate 'decisions' in Comes Deep to Get Ball removed, 'ncreases' typo in a description.

Score = average of the trait's attributes (1-20 scale). Threshold = the 'desired minimum attribute' of the
sheet (default 11 = its G12 default; ~14-15 for top clubs, 11-12 for lesser sides): a trait is *met* when
score >= threshold, and attributes below the threshold are listed as `missing`.
The sheet's 36 traits already exclude 'bad' (Dwells on Ball, Argues with Officials), most GK and situational
traits (Long Flat Throw); we keep exactly that set. Outfield only: callers should skip goalkeepers.
Display only: never feed results to patch/save code.
"""
import json
import os

from fm_editor.potential import display_value
from fm_editor.traits import TRAIT_TABLE

# attribute name (sheet spelling, lower case) -> index into person['raw_attrs'] (raw = 5 x the 1-20 value)
ATTR_IDX = {
    'corners': 27, 'crossing': 0, 'dribbling': 1, 'finishing': 2, 'first touch': 22, 'heading': 3,
    'long shots': 4, 'long throws': 30, 'marking': 5, 'passing': 7, 'tackling': 9, 'technique': 23,
    'aggression': 45, 'anticipation': 17, 'bravery': 43, 'composure': 52, 'concentration': 53,
    'decisions': 18, 'determination': 51, 'flair': 26, 'leadership': 40, 'off the ball': 6,
    'positioning': 20, 'teamwork': 28, 'vision': 10, 'work rate': 29, 'acceleration': 34, 'agility': 46,
    'balance': 42, 'jumping reach': 39, 'natural fitness': 50, 'pace': 38, 'stamina': 37, 'strength': 36,
}
_DATA = None


def _data():
    global _DATA
    if _DATA is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'trait_recommender.json'),
                  encoding='utf-8') as f:
            _DATA = json.load(f)
        # Display names come from TRAIT_TABLE (verified against in-game screenshots), not the sheet's wording
        # (e.g. bit 47: sheet 'Likes to Switch Ball to Other Flank'); the sheet name is kept as t['sheet_name'].
        ren = {}
        for t in _DATA['traits']:
            t['sheet_name'] = t['name']
            tn = TRAIT_TABLE.get(t['id'], (None,))[0]
            if tn:
                ren[t['name']] = t['name'] = tn
        _DATA['conflicts'] = [[ren.get(a, a), ren.get(b, b)] for a, b in _DATA['conflicts']]
    return _DATA


def default_threshold():
    return _data()['default_threshold']


def attrs_from_raw(raw_attrs):
    """Raw save attributes (x5) -> 1-20 ints as shown in the player window."""
    return [display_value(v / 5) for v in raw_attrs[:54]]


class Rec:
    __slots__ = ('name', 'id', 'score', 'met', 'missing', 'has', 'desc')

    def __init__(self, name, id, score, met, missing, has, desc):
        self.name, self.id, self.score, self.met, self.missing, self.has, self.desc = \
            name, id, score, met, missing, has, desc

    def __repr__(self):
        return f'Rec({self.name!r}, {self.score:.2f}, met={self.met}, has={self.has})'


def recommend(attrs, threshold=None, have_ids=(), top=None):
    """attrs: 54 values on the 1-20 scale (raw_attrs index order). have_ids: trait ids the player has.
    -> list[Rec] by score desc (ties: name). Traits that conflict with an owned trait, or with a higher-ranked
    recommendation, are dropped. `has` = player already has it; `missing` = [(attr, value)] below threshold."""
    thr = default_threshold() if threshold is None else threshold
    d = _data()
    have = set(have_ids)
    owned = {t['name'] for t in d['traits'] if t['id'] in have}
    clash = {}
    for a, b in d['conflicts']:
        clash.setdefault(a, set()).add(b)
        clash.setdefault(b, set()).add(a)
    out = []
    for t in d['traits']:
        vals = [(a, attrs[ATTR_IDX[a]]) for a in t['attrs']]
        score = sum(v for _, v in vals) / len(vals)
        out.append(Rec(t['name'], t['id'], score, score >= thr,
                       sorted(((a, v) for a, v in vals if v < thr), key=lambda x: x[1]),
                       t['name'] in owned, t['desc']))
    out.sort(key=lambda r: (-r.score, r.name))
    kept, taken = [], set(owned)
    for r in out:
        if not r.has and clash.get(r.name, set()) & taken:
            continue
        kept.append(r)
        if r.met or r.has:
            taken.add(r.name)
    return kept[:top] if top else kept
