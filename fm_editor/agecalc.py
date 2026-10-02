"""Player/staff age from the save's in-game date (no Qt).

The person record stores the birth YEAR (u16 at record end+2) and the birth DAY-OF-YEAR
(u16 at end+0, 1..366), so the exact birthday is known: age = in-game date minus birth date.
Verified on the 2 Jan 2028 save: van de Ven (19 Apr 2001) 26, Tonali (8 May 2000) 27,
Balde (18 Oct 2003) 24, Costa (19 Sep 1999) 28, Kayode (10 Jul 2004) 23, Messi (24 Jun 1987) 40,
Neymar (5 Feb 1992) 35 - all match the game.

Fallback when a person has no `birth_day` (old cache): birthday assumed 1 Jul, i.e.
age = ref.year - birth_year - (1 if ref.month < 7 else 0).
With no save loaded (no in-game date) the reference is 1 Jul 2024 (FM24 default start).
"""
from datetime import date

DEFAULT_REF = date(2024, 7, 1)
_ref = DEFAULT_REF


def parse_ref(in_game_date):
    """'YYYY-MM-DD' (saveinfo in_game_date) -> date, or DEFAULT_REF if missing/invalid."""
    try:
        return date.fromisoformat(in_game_date)
    except (TypeError, ValueError):
        return DEFAULT_REF


def set_ref(in_game_date):
    """Set the module reference date from a save's `in_game_date` (call once per load)."""
    global _ref
    _ref = parse_ref(in_game_date) if isinstance(in_game_date, str) else (in_game_date or DEFAULT_REF)
    return _ref


def get_ref():
    return _ref


def age_on(p, ref):
    """Age in whole years of person dict `p` on date `ref`."""
    by = p.get('birth_year')
    if by is None:
        return 0
    d = p.get('birth_day')
    if d:
        bd = date.fromordinal(date(by, 1, 1).toordinal() + d - 1)
        return ref.year - by - ((ref.month, ref.day) < (bd.month, bd.day))
    return ref.year - by - (ref.month < 7)


def person_age(p):
    """Age on the loaded save's in-game date."""
    return age_on(p, _ref)


def age_exact(p, ref=None):
    """Age as a float: whole years (age_on) + the part of the current year since the last birthday (int() == age_on)."""
    ref = ref or _ref
    whole = age_on(p, ref)
    by, d = p.get('birth_year'), p.get('birth_day')
    if by is None:
        return 0.0
    if d:
        bd = date.fromordinal(date(by, 1, 1).toordinal() + d - 1)
    else:
        bd = date(by, 7, 1)
    try:
        last = bd.replace(year=by + whole)
    except ValueError:                                   # 29 Feb birthday in a non-leap year
        last = date(by + whole, 3, 1)
    return whole + min((ref - last).days / 365.2425, 0.999)
