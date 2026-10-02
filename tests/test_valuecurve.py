"""Value-by-age model (fm_editor/valuecurve.py + data/value_model.json) and the Contract & Transfer tab chart.
Synthetic inputs, no save needed. Plain script: FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_valuecurve.py"""
import json
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fm_editor import agecalc  # noqa: E402
from fm_editor.valuecurve import curve  # noqa: E402

MODEL = os.path.join(os.path.dirname(__file__), '..', 'fm_editor', 'data', 'value_model.json')


def test_anchor_and_band():
    for age, ca, pa, gk, v, yl in ((20.3, 137, 169, False, 103_192_600, 3.4), (26.0, 166, 174, False, 96_525_000, 3.4),
                                   (33.5, 159, 165, False, 17_098_650, 1.4), (31.2, 141, 141, True, 15_762_842, 3.4),
                                   (19.0, 62, 88, False, 900_000, 0.4), (24.0, 120, 120, False, 5_000_000, None)):
        c = curve(age, ca, pa, gk, v, yl)
        assert not c.empty and c.expected[0] == v and c.lo[0] == v and c.hi[0] == v, (age, c.expected[:2])
        assert c.ages == list(range(int(age), int(age) + len(c.ages))) and c.ages[-1] <= 37
        assert all(lo <= e <= hi for lo, e, hi in zip(c.lo, c.expected, c.hi)), age
        assert all(x > 0 for x in c.expected + c.lo + c.hi)
        if c.full is not None:
            assert c.full[0] == v and len(c.full) == len(c.expected)
    assert len(curve(20, 137, 169, False, 1e6, 3).ages) == 12          # Now .. Now + 11
    assert curve(37, 120, 120, False, 1e6, 1).ages == [37]            # nothing past 37: single point


def test_goalkeepers_decline_later():
    out, gk = curve(28, 140, 150, False, 20e6, 3.0), curve(28, 140, 150, True, 20e6, 3.0)
    i = out.ages.index(33)
    assert gk.expected[i] / 20e6 > 2 * out.expected[i] / 20e6, (gk.expected[i], out.expected[i])


def test_empty_cases():
    assert curve(25, 140, 150, False, 0, 3).empty
    assert curve(25, 140, 150, False, None, 3).empty
    assert curve(25, 140, 150, False, 300_000_000, 3).empty          # Not for Sale
    assert curve(25, 140, 150, False, 0xFFFFFFFF, 3).empty           # sentinel
    assert curve(25, None, 150, False, 5e6, 3).empty and curve(25, 0, 150, False, 5e6, 3).empty
    assert curve(0, 140, 150, False, 5e6, 3).empty                   # unknown age


def test_full_potential_rules():
    assert curve(28, 140, 160, False, 20e6, 3).full is not None
    assert curve(29, 140, 160, False, 20e6, 3).full is None          # from age 29 on
    assert curve(25, 156, 160, False, 20e6, 3).full is None          # CA >= 97% of PA
    assert curve(25, 150, 160, False, 20e6, 3).full is not None
    c = curve(22, 120, 170, False, 20e6, 3)
    assert c.full[-1] > c.expected[-1] and c.full[3] > c.expected[3]  # at potential beats the typical path


def test_runs_out_label_state():
    assert curve(25, 140, 150, False, 5e6, 0.4).runs_out
    assert curve(25, 140, 150, False, 5e6, 0.99).runs_out
    assert not curve(25, 140, 150, False, 5e6, 1.0).runs_out
    assert not curve(25, 140, 150, False, 5e6, 3.4).runs_out
    assert not curve(25, 140, 150, False, 5e6, None).runs_out and curve(25, 140, 150, False, 5e6, None).years_left is None
    assert curve(25, 140, 150, False, 5e6, -0.5).years_left is None  # expired contract: no marker
    # the contract only shapes the first step (lines assume renewal): a short contract starts higher than a long one afterwards
    a, b = curve(25, 140, 150, False, 5e6, 0.3), curve(25, 140, 150, False, 5e6, 3.0)
    assert a.expected[1] > b.expected[1]


def test_model_file_is_aggregate_only():
    size = os.path.getsize(MODEL)
    assert 20_000 < size < 200_000, size
    m = json.load(open(MODEL))
    assert set(m) == {'version', 'h', 'contract', 'gk_by_age', 'path', 'band'}, set(m)
    assert set(m['path']) == {'outfield', 'gk'}

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                assert isinstance(k, str) and len(k) < 20, k
                yield from walk(v)
        elif isinstance(x, list):
            for v in x:
                yield from walk(v)
        else:
            yield x
    leaves = list(walk(m))
    assert all(isinstance(x, (int, float)) for x in leaves), 'only numbers (no names / ids)'
    assert len(leaves) < 40_000                                       # tables, not per-player rows


def test_contract_tab_chart():
    from PyQt6.QtCore import QPoint
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from gui.player_window import PlayerWindow
    from gui.pw_valuechart import ValueChart, fmt_m, nice_axis, tick_m, tip_text

    def person(**kw):
        pos = [1] * 15
        pos[3] = 20
        p = {'id': 1, 'name': 'Test Player', 'nation': 0, 'ca': 137, 'pa': 169, 'birth_year': 2008, 'birth_day': 2,
             'positions': pos, 'raw_attrs': [60 + (i * 7) % 40 for i in range(60)], 'personality': [10, 14, 8, 12, 15, 9, 13],
             'trait_mask': 5, 'wage_week': 100000, 'value_est': 103_192_600, 'contract_end': '2031-06-30', 'stats': {}}
        p.update(kw)
        return p
    old_ref = agecalc.get_ref()
    try:
        agecalc.set_ref('2028-01-02')
        w = PlayerWindow(person(), {'squads': {}, 'clubs': []}, 0, None, can_patch=False, data={})
        w.resize(1122, 760)
        w.show()
        w._select_tab('contract')
        for _ in range(3):
            app.processEvents()
        ch = w._vchart
        assert isinstance(ch, ValueChart) and ch.hasMouseTracking()
        assert w._stack.currentWidget().verticalScrollBar().maximum() == 0, 'Contract tab scrolls'
        c = ch.curve()
        assert c.ages[0] == 20 and c.expected[0] == 103_192_600 and abs(c.years_left - 3 - 5 / 12) < 1e-9, c.years_left
        assert c.full is not None and ch.contract_marker() == c.years_left
        assert ch.height() > 250
        # hover: nearest age column, guide + bubble; leaving clears it
        QTest.mouseMove(ch, QPoint(300, 200))
        QTest.mouseMove(ch, QPoint(420, 200))
        assert ch._hover == 5, ch._hover
        assert tip_text(c, 5).startswith('Age 25 (in 5 years)\nExpected  ') and 'At full potential' in tip_text(c, 5)
        assert tip_text(c, 0) == 'Age 20 (now)\nMarket value  £103M'
        ch.update()
        app.processEvents()
        ch.grab()
        ch.leaveEvent(None)
        assert ch._hover is None
        # in-game date (not today) drives years left
        agecalc.set_ref('2030-01-02')
        w2 = PlayerWindow(person(birth_year=2010), {'squads': {}, 'clubs': []}, 0, None, can_patch=False, data={})
        assert abs(w2._vchart.curve().years_left - (1 + 5 / 12)) < 1e-9
        w2.close()
        agecalc.set_ref('2028-01-02')
        # empty state: Not for Sale -> no curve, still no scrollbar
        w3 = PlayerWindow(person(value_est=300_000_000), {'squads': {}, 'clubs': []}, 0, None, can_patch=False, data={})
        w3.resize(1122, 760)
        w3.show()
        w3._select_tab('contract')
        app.processEvents()
        assert w3._vchart.curve().empty and w3._stack.currentWidget().verticalScrollBar().maximum() == 0
        w3._vchart.grab()
        w3.close()
        # goalkeeper window uses the goalkeeper tables
        pos = [1] * 15
        pos[0] = 20
        w4 = PlayerWindow(person(positions=pos, birth_year=1999, ca=140, pa=140), {'squads': {}, 'clubs': []}, 0, None,
                          can_patch=False, data={})
        gk = curve(29.0, 140, 140, True, 103_192_600, 3 + 5 / 12)
        assert w4._vchart.curve().expected == gk.expected and w4._vchart.curve().ages[0] == 29
        assert gk.expected[1] > curve(29.0, 140, 140, False, 103_192_600, 3 + 5 / 12).expected[1]
        w4.close()
        w.close()
    finally:
        agecalc.set_ref(old_ref)
    # helpers (mockup formulas)
    assert fmt_m(93e6) == '£93M' and fmt_m(2.84e6) == '£2.8M' and fmt_m(3.0e6) == '£3M' and fmt_m(850_400) == '£850K' and fmt_m(900) == '£900'
    assert nice_axis(104) == (50.0, 150.0)
    assert tick_m(0, 1e6) == '£0' and tick_m(2e7, 5e6) == '£20M' and tick_m(1.5e6, 5e5) == '£1.5M' and tick_m(4e5, 1e5) == '£0.4M'
    assert tick_m(2e5, 5e4) == '£200K'


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('OK', name)
