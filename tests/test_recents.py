"""Recently viewed players (fm_editor/recents.py): LRU of 8, no duplicates, exclude current, per-save persistence outside settings.json."""
import json
import os
import sys
import tempfile

os.environ['FMBR24_CONFIG_DIR'] = tempfile.mkdtemp()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fm_editor import settings as S  # noqa: E402
from fm_editor.recents import MAX_RECENT, RecentPlayers  # noqa: E402

r = RecentPlayers('/saves/a.fm')
assert MAX_RECENT == 8 and r.ids() == []
for i in range(1, 13):
    r.push(i)
assert r.ids() == [12, 11, 10, 9, 8, 7, 6, 5], r.ids()               # newest first, only the last 8
r.push(8)
assert r.ids() == [8, 12, 11, 10, 9, 7, 6, 5], 'an existing id moves to the front, no duplicate'
r.push(5)
assert r.ids()[0] == 5 and len(r.ids()) == 8 and len(set(r.ids())) == 8
assert 5 not in r.ids(exclude=5) and len(r.ids(exclude=5)) == 7, 'the current player is excluded'
r.push(-1)
r.push('x')
assert len(r.ids()) == 8, 'invalid ids ignored'
assert [p['id'] for p in r.people({5: {'id': 5}, 12: {'id': 12}})] == [5, 12], 'ids missing from the save are dropped'

# persistence per save, in recent_players.json (never settings.json)
assert RecentPlayers('/saves/a.fm').ids() == r.ids(), 'persisted'
assert RecentPlayers('/saves/b.fm').ids() == [], 'another save has its own list'
b = RecentPlayers('/saves/b.fm')
b.push(99)
assert RecentPlayers('/saves/a.fm').ids() == r.ids() and RecentPlayers('/saves/b.fm').ids() == [99]
r.set_save('/saves/b.fm')
assert r.ids() == [99]
assert not os.path.exists(S.settings_path()) or 'recent' not in open(S.settings_path()).read()
raw = json.load(open(os.path.join(S.config_dir(), 'recent_players.json')))
assert set(raw) == {'/saves/a.fm', '/saves/b.fm'}
open(os.path.join(S.config_dir(), 'recent_players.json'), 'w').write('{broken')
assert RecentPlayers('/saves/a.fm').ids() == [], 'a corrupt file is ignored'
assert RecentPlayers('x', persist=False).ids() == []
print('recents OK')
