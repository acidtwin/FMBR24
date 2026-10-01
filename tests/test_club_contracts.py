"""Self-check for the club page 'Contracts' panel date math
(gui.main_window._contract_expiry_counts). No test framework needed.

Run directly: python3 tests/test_club_contracts.py
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import _contract_expiry_counts  # noqa: E402


def test_contract_expiry_counts():
    today = date(2026, 9, 30)
    squad = [
        {'contract_end': '2027-02'},  # ~5 months out -> <6mo and <1yr
        {'contract_end': '2027-06'},  # ~9 months out -> <1yr only
        {'contract_end': '2030-06'},  # far out -> longest deal
        {'contract_end': '2026-01'},  # already expired -> excluded
        {},                           # no contract data -> ignored
    ]
    n6, n12, longest = _contract_expiry_counts(squad, today)
    assert n6 == 1, f"expected 1 contract expiring <6mo, got {n6}"
    assert n12 == 2, f"expected 2 contracts expiring <1yr, got {n12}"
    assert longest == '2030-06', f"expected longest deal 2030-06, got {longest!r}"

    n6, n12, longest = _contract_expiry_counts([{}, {'contract_end': None}], today)
    assert (n6, n12, longest) == (0, 0, ''), "empty squad should yield zero counts, no longest deal"


def test_uses_ingame_date():
    from fm_editor import agecalc
    agecalc.set_ref('2028-01-12')
    squad = [{'contract_end': '2028-06'}, {'contract_end': '2028-12'}, {'contract_end': '2030-06'}]
    assert _contract_expiry_counts(squad, agecalc.get_ref()) == (1, 2, '2030-06')
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'gui', 'main_window.py')).read()
    assert 'date.today()' not in src, 'wall-clock date used; use agecalc.get_ref()'


if __name__ == '__main__':
    test_contract_expiry_counts()
    test_uses_ingame_date()
    print('OK: _contract_expiry_counts')
