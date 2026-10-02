"""Rating words (fm_editor/words.py): every value maps to one word, boundaries, order, old outputs unchanged, mockup legend in sync."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fm_editor.words import FOOT_WORDS, POSITION_WORDS, foot_word, position_legend, position_word  # noqa: E402


def old_word(v):
    return ('Natural' if v >= 20 else 'Accomplished' if v >= 15 else 'Competent' if v >= 10
            else 'Unconvincing' if v >= 5 else 'Awkward' if v >= 2 else 'Ineffective')


def old_foot(v):
    return ('Very Weak' if v <= 5 else 'Weak' if v <= 8 else 'Reasonable' if v <= 11
            else 'Fairly Strong' if v <= 14 else 'Strong' if v <= 19 else 'Very Strong')


for v in range(0, 21):                       # unchanged vs the pre-consolidation implementations
    assert position_word(v) == old_word(v), v
    assert foot_word(v) == old_foot(v), v

# boundaries (first value of each word)
assert [position_word(v) for v in (1, 2, 4, 5, 9, 10, 14, 15, 19, 20)] == [
    'Ineffective', 'Awkward', 'Awkward', 'Unconvincing', 'Unconvincing', 'Competent', 'Competent',
    'Accomplished', 'Accomplished', 'Natural']
assert [foot_word(v) for v in (1, 5, 6, 8, 9, 11, 12, 14, 15, 19, 20)] == [
    'Very Weak', 'Very Weak', 'Weak', 'Weak', 'Reasonable', 'Reasonable', 'Fairly Strong', 'Fairly Strong',
    'Strong', 'Strong', 'Very Strong']

# out of range clamps, junk gives ''
assert position_word(-3) == position_word(0) == 'Ineffective' and position_word(25) == 'Natural'
assert foot_word(-3) == 'Very Weak' and foot_word(25) == 'Very Strong'
assert position_word(None) == foot_word(None) == position_word('x') == ''

# tables: ascending thresholds, unique words, words follow the table order across 1..20 (monotonic, no gaps)
for table, fn in ((POSITION_WORDS, position_word), (FOOT_WORDS, foot_word)):
    los = [lo for lo, _ in table]
    words = [w for _, w in table]
    assert los == sorted(set(los)) and len(set(words)) == len(words)
    seq = [words.index(fn(v)) for v in range(1, 21)]
    assert seq == sorted(seq) and set(seq) == set(range(len(words))), seq

# Positions legend (generated) matches the mockup text and the app: best first
assert position_legend() == ['Natural 20', 'Accomplished 15–19', 'Competent 10–14', 'Unconvincing 5–9',
                             'Awkward 2–4', 'Ineffective 1']
html = open(os.path.join(os.path.dirname(__file__), '..', 'mockups', 'player-window.html'), encoding='utf-8').read()
leg = re.search(r'White ring = Natural \(20\)[^`]*', html).group(0)
leg = re.sub(r'<br>', ' · ', leg)
leg = re.sub(r'<[^>]+>', '', leg)
assert ' · '.join(position_legend()[:3] + position_legend()[3:]) in leg, leg   # mockup legend text mirrors the table
print('OK')
