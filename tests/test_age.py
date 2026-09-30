"""Age-from-in-game-date rule (plain script). Ground truth = in-game ages on 2 Jan 2028."""
import os, sys
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor.agecalc import age_on, parse_ref, DEFAULT_REF

def doy(y, m, d):
    return (date(y, m, d) - date(y, 1, 1)).days + 1

ref = parse_ref('2028-01-02')
GT = [('van de Ven', (2001, 4, 19), 26), ('Costa', (1999, 9, 19), 28), ('Kayode', (2004, 7, 10), 23),
      ('Balde', (2003, 10, 18), 24), ('Tonali', (2000, 5, 8), 27), ('Messi', (1987, 6, 24), 40),
      ('Neymar', (1992, 2, 5), 35)]
for name, (y, m, d), want in GT:
    exact = age_on({'birth_year': y, 'birth_day': doy(y, m, d)}, ref)
    year_only = age_on({'birth_year': y}, ref)  # fallback (no day stored)
    assert exact == want, (name, exact, want)
    assert year_only == want, (name, year_only, want)
# birthday boundary, incl. leap-year birthdays
p = {'birth_year': 2000, 'birth_day': doy(2000, 3, 1)}  # leap year: day 61
assert age_on(p, date(2028, 2, 29)) == 27 and age_on(p, date(2028, 3, 1)) == 28
p = {'birth_year': 2000, 'birth_day': doy(2000, 2, 29)}
assert age_on(p, date(2029, 2, 28)) == 28 and age_on(p, date(2029, 3, 1)) == 29
assert parse_ref(None) == DEFAULT_REF and parse_ref('garbage') == DEFAULT_REF
print('OK')
