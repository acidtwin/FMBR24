"""Descriptive words for 1-20 ratings. No Qt imports.

The app's OWN wording (FM-like, deliberately not claimed to match the game). Number -> word tables live here and
nowhere else; the GUI and the tests import them. Each table is ((lowest value, word), ...) ascending: a value
gets the word of the last row whose lowest value it reaches, so every integer maps to exactly one word. Values
below the first row take the first word, values above 20 the last (clamped); None/non-numbers give ''.
Adjust a boundary by editing one number here (then the mockup legend text, see tests/test_words.py).
"""

POSITION_WORDS = ((0, 'Ineffective'), (2, 'Awkward'), (5, 'Unconvincing'), (10, 'Competent'),
                  (15, 'Accomplished'), (20, 'Natural'))
FOOT_WORDS = ((0, 'Very Weak'), (6, 'Weak'), (9, 'Reasonable'), (12, 'Fairly Strong'),
              (15, 'Strong'), (20, 'Very Strong'))


def _lookup(table, v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ''
    return next((w for lo, w in reversed(table) if v >= lo), table[0][1])


def position_word(v):
    """Position familiarity (1-20): Natural 20, Accomplished 15-19, Competent 10-14, Unconvincing 5-9, Awkward 2-4, Ineffective 0-1."""
    return _lookup(POSITION_WORDS, v)


def foot_word(v):
    """Foot strength (1-20): Very Weak 0-5, Weak 6-8, Reasonable 9-11, Fairly Strong 12-14, Strong 15-19, Very Strong 20."""
    return _lookup(FOOT_WORDS, v)


def position_legend():
    """'Natural 20 · Accomplished 15–19 ...' lines for the Positions tab key, best first, from POSITION_WORDS (1 = lowest shown)."""
    spans = []
    for i, (lo, w) in enumerate(POSITION_WORDS):
        hi = POSITION_WORDS[i + 1][0] - 1 if i + 1 < len(POSITION_WORDS) else 20
        lo = max(lo, 1)
        spans.append(f'{w} {lo}' if lo == hi else f'{w} {lo}–{hi}')
    return spans[::-1]
