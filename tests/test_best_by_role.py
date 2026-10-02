"""Best by Role report: the position-familiarity filter (a centre-back must not top an attacking-role list).
Plain script: FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_best_by_role.py
The last section runs on the real save's parse cache (read-only) and prints the top 10 for six roles; SKIPPED if absent."""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])
import gui.main_window as M  # noqa: E402
from fm_editor.rolepos import POS_CODES, role_positions  # noqa: E402
from gui.roles import FM_ROLES  # noqa: E402

POS = M.POSITIONS


def person(i, name, base, positions, **attrs):
    raw = [base] * 54
    for k, v in attrs.items():
        raw[int(k[1:])] = v
    pos = [1] * 15
    for code, v in positions.items():
        pos[POS.index(code)] = v
    return {'id': i, 'name': name, 'ca': 120, 'pa': 140, 'nation': 0, 'birth_year': 2000, 'birth_day': 1,
            'positions': pos, 'raw_attrs': raw, 'personality': [10] * 7, 'trait_mask': 0}


# every attribute the winger / forward roles use (pace 38, accel 34, dribbling 1, finishing 2, off-ball 6, ...) maxed on the CB
CB_ATTRS = {f'a{i}': 98 for i in (0, 1, 2, 6, 22, 23, 34, 38, 42, 46, 52, 29)}
people = [
    person(1, 'Natural Forward', 70, {'ST': 20, 'AMR': 14}, a2=90, a6=85, a34=80, a38=80),
    person(2, 'Fast Centre-Back', 60, {'DC': 20, 'ST': 3}, **CB_ATTRS),
    person(3, 'Natural Winger', 72, {'AML': 20, 'AMR': 20, 'ST': 12, 'ML': 16}, a0=90, a1=88, a38=85),
    person(4, 'Keeper', 75, {'GK': 20}),
    person(5, 'Weak Winger', 40, {'AMR': 15}),
]
w = M.MainWindow()
w._save_data = {'b': b'x', 'people': people, 'squads': {}, 'clubs': [], 'human_clubs': set()}


def report(role, minpos=None):
    w._report_minpos.setValue(M._MIN_POS_DEFAULT if minpos is None else minpos)
    return [p['name'] for p in w._get_report_players('best_role', role_name=role)], dict(w._report_ratings)


# --- default threshold hides the CB, threshold 1 shows it (and the GK) -------------------------------------------------------
assert M._MIN_POS_DEFAULT == 12 and w._report_minpos.value() == 12
for role in ('Winger (A)', 'Advanced Forward (A)'):
    names, ratings = report(role)
    order = [p['id'] for p in people if p['name'] in names]
    order = sorted(order, key=lambda i: names.index(next(p['name'] for p in people if p['id'] == i)))
    assert 'Fast Centre-Back' not in names and 'Keeper' not in names, (role, names)
    assert 'Natural Forward' in names or role == 'Winger (A)', names
    names1, ratings1 = report(role, 1)
    assert 'Fast Centre-Back' in names1 and 'Keeper' in names1, (role, names1)
    assert ratings1[2] >= ratings1[1], 'fixture: the CB must out-rate the forward on attributes'
    # displayed rating unchanged by the filter, survivors still ordered by it
    assert all(ratings[i] == ratings1[i] for i in ratings)
    assert [ratings[i] for i in order] == sorted(ratings.values(), reverse=True) and len(order) == len(ratings)
assert 'Natural Forward' in report('Winger (A)')[0]          # AMR 14 >= 12
assert 'Natural Forward' not in report('Winger (A)', 15)[0]  # raising the bar drops it
assert 'Natural Winger' in report('Advanced Forward (A)')[0]  # ST 12 passes at exactly 12
assert 'Natural Winger' not in report('Advanced Forward (A)', 13)[0]
assert 'Weak Winger' in report('Winger (A)')[0] and 'Weak Winger' not in report('Advanced Forward (A)')[0]

# --- goalkeepers only in GK roles ---------------------------------------------------------------------------------------
for role in ('Goalkeeper (D)', 'Sweeper Keeper (A)'):
    assert report(role)[0] == ['Keeper'], report(role)
for name, group, _ in FM_ROLES:
    if group != 'GK':
        assert 'Keeper' not in report(name)[0], name

# --- every role maps to at least one position; positions are real ------------------------------------------------------
for name, group, _ in FM_ROLES:
    ps = role_positions(name)
    assert ps and all(x in POS_CODES and x in POS for x in ps), (name, ps)
assert role_positions('Wide Centre-Back (D)')[-1] == 'DC' and role_positions('Not A Role') == ()
assert sorted(role_positions('Goalkeeper (S)')) == ['GK']

# --- header subtitle names role + filter; Clear resets the spinbox ------------------------------------------------------
w._current_report_key = 'best_role'
w._report_role_combo.setCurrentText('Winger (A)')
w._report_minpos.setValue(12)
w._populate_reports_table(w._get_report_players('best_role', role_name='Winger (A)'))
w._main_stack.setCurrentIndex(w._VIEW_INDEX['reports'])
w._update_header_for_view('reports')
sub = w._header_subtitle_lbl.text()
assert 'Best by Role' in sub and 'Winger (A)' in sub and '≥ 12' in sub, sub
w._report_minpos.setValue(1)
w._clear_report_filter()
assert w._report_minpos.value() == 12
print('synthetic OK, header subtitle:', sub)

# --- real save, read-only, via the parse cache --------------------------------------------------------------------------
SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/2026-27 START - Acid Twin Spurs.fm')
if not os.path.exists(SAVE):
    print('SKIPPED real-save check (save absent)')
    sys.exit(0)
from fm_editor.cache import load_cache  # noqa: E402
cache = load_cache(SAVE)
if not cache:
    print('SKIPPED real-save check (no valid parse cache)')
    sys.exit(0)
w._save_data = cache
n = len(cache['people'])
for role in ('Winger (A)', 'Advanced Forward (A)', 'Full Back (A)', 'Central Defender (D)',
             'Defensive Midfielder (D)', 'Goalkeeper (D)'):
    for mp in (M._MIN_POS_DEFAULT, 1):
        w._report_minpos.setValue(mp)
        top = w._get_report_players('best_role', role_name=role)[:10]
        pidx = [POS.index(x) for x in role_positions(role)]
        print(f'\n== {role}  min position {mp}  ({w._report_total:,} of {n:,} qualify)')
        for p in top:
            best = max(p['positions'])
            print(f"  {p['name'][:26]:26} rating {w._report_ratings[p['id']]:2}  pos@role {max(p['positions'][i] for i in pidx):2}"
                  f"  primary {M._primary_pos(p['positions'])}({best})")
        if mp == 1:
            w._report_minpos.setValue(1)
            top50 = w._get_report_players('best_role', role_name=role)[:50]
            print(f'  -> top 50 without the filter: {sum(max(p["positions"][i] for i in pidx) < M._MIN_POS_DEFAULT for p in top50)} '
                  f'cannot play the role (position < {M._MIN_POS_DEFAULT})')
        if mp == M._MIN_POS_DEFAULT:
            assert all(max(p['positions'][i] for i in pidx) >= mp for p in top)
