"""Plain-script test for fm_editor/settings.py and the cache-clear helpers. Uses a temp dir only."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

tmp = tempfile.mkdtemp(prefix='fmbr24_test_')
os.environ['FMBR24_CONFIG_DIR'] = os.path.join(tmp, 'cfg')  # dir does not exist yet

from fm_editor import settings, cache  # noqa: E402

# defaults when file missing
assert settings.load() == settings.DEFAULTS
assert settings.settings_path().startswith(tmp)

# round trip + unknown keys preserved
os.makedirs(settings.config_dir(), exist_ok=True)
with open(settings.settings_path(), 'w') as f:
    json.dump({'other_key': 7}, f)
vals = dict(settings.DEFAULTS, default_save_dir='/x/y', landing_page='players', show_pending=False)
assert settings.save(vals)
assert settings.load() == vals
assert json.load(open(settings.settings_path()))['other_key'] == 7

# corrupt file / wrong types / bad landing value -> defaults, no crash
open(settings.settings_path(), 'w').write('{not json')
assert settings.load() == settings.DEFAULTS
json.dump({'landing_page': 'nope', 'show_pending': 'yes', 'default_save_dir': 5},
          open(settings.settings_path(), 'w'))
assert settings.load() == settings.DEFAULTS
json.dump({'trait_threshold': 99}, open(settings.settings_path(), 'w'))
assert settings.load()['trait_threshold'] == 11 == settings.DEFAULTS['trait_threshold']
json.dump({'trait_threshold': 14}, open(settings.settings_path(), 'w'))
assert settings.load()['trait_threshold'] == 14
open(settings.settings_path(), 'w').write('[1,2]')
assert settings.load() == settings.DEFAULTS
assert settings.save(vals) and settings.load() == vals  # save recovers from a corrupt file

# ability_display: default stars, bad value -> default, accessor
assert settings.DEFAULTS['ability_display'] == 'stars'
json.dump({'ability_display': 'bogus'}, open(settings.settings_path(), 'w'))
assert settings.load()['ability_display'] == 'stars' and settings.ability_as_stars()
json.dump({'ability_display': 'numbers'}, open(settings.settings_path(), 'w'))
assert settings.load()['ability_display'] == 'numbers' and not settings.ability_as_stars()
assert settings.save(vals) and settings.load() == vals

# player_theme: default steel, bad value / wrong type -> default, valid ids kept, merge-save keeps other keys
assert settings.DEFAULTS['player_theme'] == 'steel'
for bad in ('nope', 5, None):
    json.dump({'player_theme': bad}, open(settings.settings_path(), 'w'))
    assert settings.load()['player_theme'] == 'steel'
for tid in settings.PLAYER_THEMES:
    assert settings.save({'player_theme': tid}) and settings.load()['player_theme'] == tid
json.dump({'other_key': 7}, open(settings.settings_path(), 'w'))
assert settings.save({'player_theme': 'plain'}) and json.load(open(settings.settings_path()))['other_key'] == 7
assert settings.save(vals) and settings.load() == vals

# folder_status
saves = os.path.join(tmp, 'saves')
os.makedirs(saves)
for n in ('a.fm', 'b.FM', 'c.txt'):
    open(os.path.join(saves, n), 'w').close()
assert settings.folder_status('') == ('unset', 0)
assert settings.folder_status(saves) == ('ok', 2)
assert settings.folder_status(os.path.join(saves, 'a.fm')) == ('notdir', 0)
assert settings.folder_status(os.path.join(tmp, 'nope')) == ('missing', 0)
settings.save(dict(settings.DEFAULTS, default_save_dir=saves))
assert settings.save_dialog_dir('fb') == saves
settings.save(dict(settings.DEFAULTS, default_save_dir=os.path.join(tmp, 'nope')))
assert settings.save_dialog_dir('fb') == 'fb'

# cache helpers only touch *.json in the cache dir
cdir = os.path.join(tmp, 'cache')
os.makedirs(os.path.join(cdir, 'sub'))
cache._CACHE_DIR = cdir
for n in ('a.json', 'b.json', 'keep.txt', os.path.join('sub', 'c.json')):
    open(os.path.join(cdir, n), 'w').write('{}')
assert cache.cache_info() == (2, 4)
assert cache.clear_all_caches() == 2
assert sorted(os.listdir(cdir)) == ['keep.txt', 'sub'] and os.path.exists(os.path.join(cdir, 'sub', 'c.json'))
assert cache.cache_info() == (0, 0)

print('OK')
