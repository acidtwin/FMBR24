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
st = os.stat(sv)
os.utime(sv, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000))  # mtime changed -> stale (even sub-second)
assert cache.load_cache(sv) is None
os.utime(sv, ns=(st.st_atime_ns, st.st_mtime_ns))
assert cache.load_cache(sv)  # restored -> valid again
open(sv, 'ab').write(b'y')  # size changed (same mtime restored) -> stale
os.utime(sv, ns=(st.st_atime_ns, st.st_mtime_ns))
assert cache.load_cache(sv) is None
# changed during parse: signature taken before, file rewritten, save_cache must not write
cache.clear_cache(sv)
sig = cache.file_signature(sv)
open(sv, 'ab').write(b'z')
cache.save_cache(sv, [{'id': 1}], {1: 2}, {2: {1: [1]}}, people, sig=sig)
assert not os.path.exists(cp) and cache.load_cache(sv) is None
cache.save_cache(sv, [{'id': 1}], {1: 2}, {2: {1: [1]}}, people, sig=cache.file_signature(sv))
assert cache.load_cache(sv)

open(cp, 'w').write('{corrupt')  # corrupt -> None (caller falls back to full parse)
assert cache.load_cache(sv) is None
open(cp, 'w').write('[]')
assert cache.load_cache(sv) is None
print('ok')
