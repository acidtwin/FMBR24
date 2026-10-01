"""Plain script: python3 tests/test_core_fixes.py. Synthetic data only (patch 255-count, truncated archive)."""
import os
import sys
import tempfile
import json

_CFG = tempfile.mkdtemp(prefix='fmbr24_core_')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_editor import archive as A
from fm_editor import patch as P
from fm_editor import savefile as S
from test_savefile import build_archive, load


def test_hgc_255():
    end = 10
    b = bytearray(end + 35 + 255 * 16 + 20)
    b[end + 34] = 255
    before = bytes(b)
    assert P.patch_to_hgc(b, [{'end': end}], 7) == 0
    assert bytes(b) == before, 'buffer must be untouched'
    b2 = bytearray(end + 35 + 20)
    n = len(b2)
    assert P.patch_to_hgc(b2, [{'end': end}], 7) == 1 and len(b2) == n + 16 and b2[end + 34] == 1


def test_truncated():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'T.fm')
        build_archive(path, {'game_db.dat': os.urandom(50_000), 'other.bin': os.urandom(30_000)})
        sd = load(path)
        with open(path, 'rb') as f:
            full = f.read()
        om = next(m for m in sd['members'] if m['name'] == 'game_db.dat')
        out = os.path.join(d, 'out.fm')
        A.write_archive(out, path, sd['header'], sd['members'], sd['index_marker'], sd['archive_name'],
                        sd['subdir_count'], sd['subdirs'], {})
        S.verify_archive(out, path, sd['members'], sd['b'])  # intact original verifies
        cut = os.path.join(d, 'cut.fm')
        with open(cut, 'wb') as f:
            f.write(full[:26 + om['o'] + om['s'] // 2])
        om2 = next(m for m in sd['members'] if m['name'] == 'other.bin')
        checks = [lambda: A.get_member_raw(cut, om),
                  lambda: A.get_member_raw(cut, om2),
                  lambda: A.write_archive(os.path.join(d, 'o2.fm'), cut, sd['header'], sd['members'],
                                          sd['index_marker'], sd['archive_name'], sd['subdir_count'],
                                          sd['subdirs'], {}),
                  lambda: S.verify_archive(out, cut, sd['members'], sd['b'])]
        for fn in checks:
            try:
                fn()
                raise AssertionError('should raise')
            except ValueError as e:
                assert 'Truncated' in str(e)


def test_settings_merge():
    os.environ['FMBR24_CONFIG_DIR'] = _CFG  # set AFTER importing weights: must still be honoured
    from fm_editor import settings, weights
    os.makedirs(_CFG, exist_ok=True)
    with open(settings.settings_path(), 'w') as f:
        json.dump({'extra': 1, 'landing_page': 'players', 'show_pending': False}, f)
    assert settings.save({'default_save_dir': '/x'})
    d = json.load(open(settings.settings_path()))
    assert d['extra'] == 1 and d['landing_page'] == 'players' and d['show_pending'] is False
    assert d['default_save_dir'] == '/x'
    weights.set_active_preset_name('Mine')
    d = json.load(open(settings.settings_path()))
    assert d['role_weights_preset'] == 'Mine' and d['extra'] == 1 and d['landing_page'] == 'players'
    assert weights.get_active_preset_name() == 'Mine'
    assert str(weights._user_dir()).startswith(_CFG)
    assert not os.path.exists(settings.settings_path() + '.tmp')


if __name__ == '__main__':
    test_hgc_255()
    test_truncated()
    test_settings_merge()
    print('OK')
