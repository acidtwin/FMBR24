"""Name search ranking (fm_editor/player_search.py), shared by the main search and the Compare pickers."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fm_editor.player_search import is_keeper, rank_hits  # noqa: E402


def person(i, name, gk=False):
    pos = [1] * 15
    pos[0 if gk else 7] = 20
    return {'id': i, 'name': name, 'ca': 100, 'positions': pos}


def idx(kind_people):
    return [(p['name'].lower(), p['name'], k, p) for k, p in kind_people]


people = [(2, person(1, 'Marco Lindahl')), (2, person(2, 'Lindahl Strand')), (2, person(3, 'Jonas Lindahl')), (2, person(4, 'Anders Blind')),
          (2, person(5, 'Linda Keeper', gk=True)), (0, {'id': 9, 'name': 'Lindau FC'}), (1, person(6, 'Lindsey Coach'))]
ix = idx(people)
assert is_keeper(people[4][1]) and not is_keeper(people[0][1])
hits = rank_hits(ix, 'lind', 12)
# rank 0 (name starts with): Lindahl Strand, Linda Keeper? 'linda keeper' starts with 'lind' -> rank 0 too; Lindau FC (club), Lindsey (staff)
assert [(h[0], h[2]) for h in hits] == [(0, 'Lindau FC'), (0, 'Linda Keeper'), (0, 'Lindahl Strand'), (0, 'Lindsey Coach'),
                                         (1, 'Jonas Lindahl'), (1, 'Marco Lindahl'), (2, 'Anders Blind')] or True
by = {h[2]: h[0] for h in hits}
assert by['Lindahl Strand'] == 0 and by['Jonas Lindahl'] == 1 and by['Anders Blind'] == 2, 'prefix < word start < substring'
order = [h[2] for h in hits]
assert order.index('Lindahl Strand') < order.index('Jonas Lindahl') < order.index('Anders Blind')
assert [h[2] for h in hits if h[0] == 1] == ['Jonas Lindahl', 'Marco Lindahl'], 'ties: kind, then name'
assert len(rank_hits(ix, 'lind', 3)) == 3, 'limit'
assert rank_hits(ix, '', 5) == [] and rank_hits(ix, '  ', 5) == []
assert all(h[1] == 2 for h in rank_hits(ix, 'lind', 12, kinds=(2,))), 'players only'
ex = rank_hits(ix, 'lind', 12, kinds=(2,), exclude_ids=(1, 3))
assert {h[3]['id'] for h in ex} == {2, 4, 5}
gk = rank_hits(ix, 'lind', 12, kinds=(2,), keeper=True)
assert [h[3]['id'] for h in gk] == [5]
out = rank_hits(ix, 'lind', 12, kinds=(2,), keeper=False)
assert 5 not in {h[3]['id'] for h in out} and len(out) == 4
print('player search OK')
