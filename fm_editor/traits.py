"""FM24 player traits (Preferred Moves / PPMs).

Storage (verified): little-endian u64 at `person['offset'] - 8` in game_db.dat; bit n set = trait id n.
Staff carry the field too. See memory/fm24-binary-format.md for the evidence.

TRAIT_TABLE is the ONE place that decides what is shown. Grades:
  A = verified (fmsave enum / in-game screenshot / >=3 change-log agreements)
  B = mapped from the save's change-log PMxx tags and consistent with mutual exclusions
  X = bit is set on real players but the game shows NO trait for it (Aursnes 49, de la Cruz 62): never displayed
  C = educated guess (name kept as a candidate only)   ? = unknown (name None)
Only A/B names are displayed; C/? bits show as 'Trait #n'. To promote a bit, edit its line
(fix the name if needed, set the grade to 'A' or 'B').
"""
import struct

TRAIT_TABLE = {
    0: ('Runs With Ball Down Left', 'A'),
    1: ('Runs With Ball Down Right', 'A'),
    2: ('Runs With Ball Through Centre', 'A'),
    3: ('Gets Into Opposition Area', 'A'),
    4: ('Moves Into Channels', 'A'),
    5: ('Gets Forward Whenever Possible', 'A'),
    6: ('Plays Short Simple Passes', 'B'),
    7: ('Tries Killer Balls Often', 'A'),
    8: ('Shoots From Distance', 'A'),
    9: ('Shoots With Power', 'A'),
    10: ('Places Shots', 'A'),
    11: ('Curls Ball', 'B'),
    12: ('Likes To Round Keeper', 'A'),
    13: ('Likes To Try To Beat Offside Trap', 'A'),
    14: ('Uses Outside Of Foot', 'A'),
    15: ('Marks Opponent Tightly', 'A'),
    16: ('Winds Up Opponents', 'B'),
    17: ('Argues With Officials', 'A'),
    18: ('Plays With Back To Goal', 'A'),
    19: ('Comes Deep To Get Ball', 'A'),
    20: ('Plays One-Twos', 'A'),
    21: ('Likes To Lob Keeper', 'A'),
    22: ('Dictates Tempo', 'A'),
    23: ('Attempts Overhead Kicks', 'A'),
    24: ('Looks For Pass Rather Than Attempting To Score', 'A'),
    25: ('Plays No Through Balls', 'A'),
    26: ('Likes To Switch Ball To Other Flank', 'C'),
    27: ('Knocks Ball Past Opponent', 'A'),
    28: ('Moves Ball To Right Foot Before Dribble Attempt', 'B'),
    29: ('Moves Ball To Left Foot Before Dribble Attempt', 'B'),
    30: ('Dwells On Ball', 'B'),
    31: ('Arrives Late In Opposition Area', 'C'),
    32: (None, '?'),
    33: ('Stays Back At All Times', 'B'),
    34: ('Avoids Using Weaker Foot', 'A'),
    35: ('Tries Tricks', 'B'),
    36: ('Hits Free Kicks With Power', 'C'),
    37: ('Dives Into Tackles', 'A'),
    38: ('Does Not Dive Into Tackles', 'B'),
    39: ('Cuts Inside From Both Wings', 'A'),
    40: ('Hugs Line', 'B'),
    41: ('Gets Crowd Going', 'A'),
    42: ('Tries First Time Shots', 'A'),
    43: ('Tries Long Range Passes', 'A'),
    44: ('Likes Ball Played Into Feet', 'A'),
    45: ('Tries Long Range Free Kicks', 'C'),
    46: ('Likes To Beat Opponent Repeatedly', 'B'),
    47: (None, '?'),
    48: ('Attempts To Develop Weaker Foot', 'C'),
    49: (None, 'X'),
    50: ('Possesses Long Flat Throws', 'C'),
    51: ('Runs With Ball Often', 'A'),
    52: ('Runs With Ball Rarely', 'B'),
    53: (None, '?'),
    54: ('Does Not Move Into Channels', 'A'),
    55: ('Uses Long Throw To Start Counter Attacks', 'C'),
    56: (None, '?'),
    57: ('Cuts Inside From Left', 'B'),
    58: ('Cuts Inside From Right', 'B'),
    59: ('Crosses Early', 'A'),
    60: ('Brings Ball Out Of Defence', 'A'),
    61: (None, '?'),
    62: (None, 'X'),
    63: (None, '?'),
}

_SHOWN = ('A', 'B')


def read_trait_mask(b, person_offset):
    """u64 trait mask for the person record starting at `person_offset` (0 when there is no room)."""
    return struct.unpack_from('<Q', b, person_offset - 8)[0] if person_offset >= 8 else 0


def trait_ids(mask):
    """Set bit numbers, ascending (= in-game display order)."""
    return [i for i in range(64) if mask >> i & 1]


def trait_label(i):
    name, grade = TRAIT_TABLE[i]
    return name if grade in _SHOWN and name else f'Trait #{i}'


def trait_names(mask):
    """Display labels for a mask: A/B real names, C/? 'Trait #n'; X bits (not shown in game) are skipped."""
    return [trait_label(i) for i in trait_ids(mask) if TRAIT_TABLE[i][1] != 'X']
