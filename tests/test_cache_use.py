"""Plain-script test: parse-cache validity rules (version, mtime, corrupt) + use_cache setting. Temp dirs only."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tmp = tempfile.mkdtemp(prefix='fmbr24_cache_')
os.environ['FMBR24_CONFIG_DIR'] = os.path.join(tmp, 'cfg')

from fm_editor import cache, settings  # noqa: E402

cache._CACHE_DIR = os.path.join(tmp, 'cache')
sv = os.path.join(tmp, 's.fm')
open(sv, 'wb').write(b'x')

assert settings.load()['use_cache'] is True  # default ON
settings.save(dict(settings.DEFAULTS, use_cache=False))
assert settings.load()['use_cache'] is False

people = [{'id': 1, 'name': 'A', 'nation': 1, 'birth_year': 2000, 'end': 5, 'offset': 1}]
cache.save_cache(sv, [{'id': 1}], {1: 2}, {2: {1: [1]}}, people, {1: 2}, {3: [1]}, {'x': 1})
d = cache.load_cache(sv)
assert d and d['squads'] == {1: 2} and d['sub_squads'] == {2: {1: [1]}} and d['club_staff'] == {3: [1]}

cp = cache._cache_path(sv)
raw = json.load(open(cp))
raw['version'] = cache._CACHE_VERSION - 1  # older schema ignored
json.dump(raw, open(cp, 'w'))
assert cache.load_cache(sv) is None

raw['version'] = cache._CACHE_VERSION
json.dump(raw, open(cp, 'w'))
assert cache.load_cache(sv)
os.utime(sv, (1, os.path.getmtime(sv) + 100))  # mtime changed -> stale
assert cache.load_cache(sv) is None

open(cp, 'w').write('{corrupt')  # corrupt -> None (caller falls back to full parse)
assert cache.load_cache(sv) is None
open(cp, 'w').write('[]')
assert cache.load_cache(sv) is None
print('ok')
