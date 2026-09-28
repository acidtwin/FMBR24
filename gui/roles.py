"""FM24 role definitions and role suitability rating.

Each role is (display_name, group, key_attr_indices).
key_attr_indices are indices into the 54-byte raw_attrs array (0-100 scale).
Rating = mean of key attrs scaled to 1-20 (round(raw/5)).

Attribute index reference:
 0 crossing   1 dribbling  2 finishing  3 heading    4 longShots  5 marking
 6 offTheBall 7 passing    8 penalties  9 tackling  10 vision    11 handling
12 aerialReach 13 commandArea 14 communication 15 kicking 16 throwing
17 anticipation 18 decisions 19 oneOnOnes 20 positioning 21 reflexes
22 firstTouch  23 technique  24 leftFoot  25 rightFoot  26 flair   27 corners
28 teamwork    29 workRate   30 longThrows 31 eccentricity 32 rushingOut
33 punching    34 acceleration 35 freeKick 36 strength  37 stamina
38 pace        39 jumpingReach 40 leadership 41 dirtiness 42 balance
43 bravery     44 consistency  45 aggression 46 agility  47 bigMatches
48 injuryProne 49 versatility  50 naturalFitness 51 determination
52 composure   53 concentration
"""

# (name, group, key_attr_indices)
FM_ROLES: list[tuple[str, str, tuple[int, ...]]] = [

    # ── Goalkeeper (5) ───────────────────────────────────────────────────────
    ('Goalkeeper (D)',      'GK', (11, 21, 19, 12, 13, 15, 20, 17, 18, 53)),
    ('Goalkeeper (S)',      'GK', (11, 21, 19, 12, 13, 15, 20, 17, 18, 53)),
    ('Sweeper Keeper (D)',  'GK', (11, 21, 15, 17, 20, 18, 53, 46, 52, 22)),
    ('Sweeper Keeper (S)',  'GK', (11, 21, 15, 17, 20, 18, 53, 46, 52, 22, 7)),
    ('Sweeper Keeper (A)',  'GK', (11, 21, 15, 17, 20, 18, 53, 46, 52, 22, 7, 23, 10, 1)),

    # ── Central Defender (9) ─────────────────────────────────────────────────
    ('Ball-Playing Defender (D)',  'CB', (17, 53, 18, 3, 5, 20, 9, 7, 23, 36, 39, 43, 52)),
    ('Ball-Playing Defender (S)',  'CB', (17, 53, 18, 3, 5, 20, 9, 7, 23, 10, 36, 39, 43, 52)),
    ('Central Defender (D)',       'CB', (17, 53, 18, 3, 5, 20, 9, 36, 39, 43, 52)),
    ('Central Defender (S)',       'CB', (17, 53, 18, 3, 5, 20, 9, 36, 39, 43, 52)),
    ('Central Defender (Cover)',   'CB', (34, 17, 53, 18, 3, 5, 20, 9, 36, 39, 43, 52, 38)),
    ('Libero (D)',                 'CB', (34, 17, 52, 53, 18, 3, 5, 7, 20, 9, 23, 10)),
    ('Libero (S)',                 'CB', (34, 17, 52, 53, 18, 3, 5, 7, 20, 9, 23, 10, 1)),
    ('No-Nonsense Centre-Back',    'CB', (17, 53, 3, 5, 20, 9, 43, 45, 36, 39)),
    ('Stopper (D)',                'CB', (34, 17, 43, 53, 3, 5, 20, 9, 45, 36)),

    # ── Full Back / Wing-Back (14) ────────────────────────────────────────────
    ('Complete Wing-Back (S)',   'FB/WB', (34, 0, 18, 1, 22, 38, 37, 23, 29, 7, 6)),
    ('Complete Wing-Back (A)',   'FB/WB', (34, 0, 18, 1, 22, 38, 37, 23, 29, 7, 6, 10)),
    ('Full Back (D)',            'FB/WB', (17, 53, 18, 5, 20, 9, 28, 29, 36, 43)),
    ('Full Back (S)',            'FB/WB', (17, 53, 18, 5, 20, 9, 28, 29, 0, 22)),
    ('Full Back (A)',            'FB/WB', (34, 17, 53, 18, 5, 20, 9, 29, 0, 1, 38)),
    ('Inverted Wing-Back (D)',   'FB/WB', (17, 52, 53, 18, 22, 5, 9, 23, 10, 20)),
    ('Inverted Wing-Back (S)',   'FB/WB', (17, 52, 53, 18, 22, 5, 7, 9, 23, 10)),
    ('Inverted Wing-Back (A)',   'FB/WB', (34, 17, 52, 53, 18, 22, 5, 7, 9, 23, 10, 38)),
    ('No-Nonsense Full Back',    'FB/WB', (5, 9, 43, 53, 17, 20, 45, 36)),
    ('Wide Centre-Back (D)',     'FB/WB', (17, 53, 18, 3, 5, 20, 9, 7, 23)),
    ('Wide Centre-Back (S)',     'FB/WB', (17, 53, 18, 3, 5, 20, 9, 7, 23, 29)),
    ('Wide Centre-Back (A)',     'FB/WB', (34, 17, 53, 18, 3, 5, 20, 9, 29, 0)),
    ('Wing-Back (D)',            'FB/WB', (17, 0, 18, 5, 20, 37, 9, 28, 29)),
    ('Wing-Back (S)',            'FB/WB', (17, 0, 18, 22, 5, 20, 37, 9, 28, 29)),

    # ── Defensive Midfielder (10) ─────────────────────────────────────────────
    ('Anchor (D)',                  'DM', (5, 9, 53, 17, 20, 52, 18, 28, 29)),
    ('Ball-Winning Midfielder (D)', 'DM', (45, 17, 43, 5, 37, 9, 29, 28)),
    ('Ball-Winning Midfielder (S)', 'DM', (45, 17, 43, 5, 37, 9, 29, 28)),
    ('Deep-Lying Playmaker (D)',    'DM', (52, 18, 22, 7, 23, 10, 17, 53)),
    ('Deep-Lying Playmaker (S)',    'DM', (52, 18, 22, 7, 23, 10, 17, 53)),
    ('Defensive Midfielder (D)',    'DM', (17, 53, 18, 5, 7, 20, 9, 28)),
    ('Defensive Midfielder (S)',    'DM', (17, 53, 18, 5, 7, 20, 9, 28)),
    ('Half-Back (D)',               'DM', (17, 52, 53, 18, 3, 5, 7, 20, 9)),
    ('Segundo Volante (S)',         'DM', (17, 18, 4, 5, 7, 20, 9, 29)),
    ('Segundo Volante (A)',         'DM', (34, 17, 18, 4, 5, 6, 20, 38, 7, 9, 29)),

    # ── Central Midfielder (8) ────────────────────────────────────────────────
    ('Box-to-Box Midfielder (S)', 'CM', (18, 22, 4, 7, 37, 9, 28, 10, 29)),
    ('Carrilero (S)',             'CM', (17, 52, 18, 22, 7, 20, 9, 28, 10)),
    ('Central Midfielder (D)',    'CM', (17, 52, 18, 22, 7, 9, 28, 10, 29)),
    ('Central Midfielder (S)',    'CM', (17, 52, 18, 22, 7, 9, 28, 10, 29)),
    ('Central Midfielder (A)',    'CM', (18, 22, 4, 6, 7, 23, 10)),
    ('Mezzala (S)',               'CM', (18, 1, 22, 4, 6, 7, 23, 10)),
    ('Mezzala (A)',               'CM', (34, 18, 1, 22, 4, 6, 7, 23, 10, 38)),
    ('Roaming Playmaker (S)',     'CM', (52, 18, 1, 22, 4, 6, 7, 23, 10)),

    # ── Attacking Midfielder (7) ──────────────────────────────────────────────
    ('Advanced Playmaker (S)', 'AM', (52, 18, 22, 6, 7, 23, 10, 26)),
    ('Advanced Playmaker (A)', 'AM', (52, 18, 22, 6, 7, 23, 10, 26)),
    ('Attacking Midfielder (D)', 'AM', (17, 52, 18, 22, 6, 7, 23, 10)),
    ('Attacking Midfielder (S)', 'AM', (52, 18, 22, 6, 7, 23, 10)),
    ('Attacking Midfielder (A)', 'AM', (52, 18, 22, 2, 6, 7, 23, 10)),
    ('Enganche (S)',           'AM', (52, 18, 1, 22, 26, 6, 7, 23, 10)),
    ('Shadow Striker (A)',     'AM', (17, 52, 18, 22, 6, 38, 7, 23)),
    ('Trequartista (A)',       'AM', (52, 1, 26, 2, 6, 7, 23, 10)),

    # ── Winger / Wide Midfielder (15) ────────────────────────────────────────
    ('Defensive Winger (D)',  'Winger', (34, 0, 18, 38, 37, 28, 29, 5, 9)),
    ('Defensive Winger (S)',  'Winger', (34, 0, 18, 38, 37, 28, 29)),
    ('Inside Forward (S)',    'Winger', (34, 1, 2, 22, 6, 38, 23, 52)),
    ('Inside Forward (A)',    'Winger', (34, 1, 2, 22, 6, 38, 23, 52, 4)),
    ('Inverted Winger (S)',   'Winger', (0, 1, 22, 6, 38, 7, 23, 10)),
    ('Inverted Winger (A)',   'Winger', (34, 0, 1, 22, 6, 38, 7, 23, 10)),
    ('Raumdeuter (A)',        'Winger', (34, 17, 52, 18, 6, 38)),
    ('Wide Midfielder (D)',   'Winger', (0, 18, 22, 7, 37, 28, 29)),
    ('Wide Midfielder (S)',   'Winger', (0, 18, 22, 6, 7, 37, 28, 29)),
    ('Wide Midfielder (A)',   'Winger', (0, 18, 22, 4, 6, 7, 37, 28, 29)),
    ('Wide Playmaker (D)',    'Winger', (18, 22, 7, 23, 10, 6, 52)),
    ('Wide Playmaker (S)',    'Winger', (18, 22, 7, 23, 10, 6, 52)),
    ('Wide Playmaker (A)',    'Winger', (18, 22, 6, 7, 23, 10, 52)),
    ('Winger (S)',            'Winger', (34, 46, 0, 1, 6, 38, 23, 29)),
    ('Winger (A)',            'Winger', (34, 46, 0, 1, 2, 6, 38, 23, 29)),

    # ── Striker (13) ─────────────────────────────────────────────────────────
    ('Advanced Forward (A)',   'Striker', (34, 17, 52, 18, 2, 22, 6, 38, 23)),
    ('Complete Forward (S)',   'Striker', (34, 17, 52, 18, 1, 2, 22, 3, 4, 6, 38, 7, 23)),
    ('Complete Forward (A)',   'Striker', (34, 17, 52, 18, 1, 2, 22, 3, 4, 6, 26, 38, 7, 23)),
    ('Deep-Lying Forward (S)', 'Striker', (17, 52, 18, 22, 7, 23, 10, 6)),
    ('Deep-Lying Forward (A)', 'Striker', (17, 52, 18, 22, 7, 23, 10, 6, 2)),
    ('False Nine (S)',          'Striker', (17, 52, 18, 1, 22, 7, 23, 10, 6, 26)),
    ('Poacher (A)',             'Striker', (34, 17, 52, 18, 2, 6, 38, 20)),
    ('Pressing Forward (D)',    'Striker', (34, 45, 17, 43, 18, 38, 37, 28, 29)),
    ('Pressing Forward (S)',    'Striker', (34, 45, 17, 43, 18, 38, 37, 28, 29)),
    ('Pressing Forward (A)',    'Striker', (34, 45, 17, 43, 18, 2, 38, 37, 28, 29)),
    ('Target Man (S)',          'Striker', (43, 3, 39, 36, 45, 17, 52, 22, 23)),
    ('Target Man (A)',          'Striker', (43, 3, 39, 36, 45, 17, 52, 22, 23, 6)),
    ('Trequartista (A)',        'Striker', (52, 1, 26, 2, 6, 7, 23, 10)),
]

# Ordered groups for the combo box display
ROLE_GROUPS = ['GK', 'CB', 'FB/WB', 'DM', 'CM', 'AM', 'Winger', 'Striker']

# Fast lookup: name → key_attr_indices
_ROLE_INDEX: dict[str, tuple[int, ...]] = {name: attrs for name, _, attrs in FM_ROLES}

# Grouped: group → list of names (in definition order)
_ROLE_BY_GROUP: dict[str, list[str]] = {}
for _name, _group, _attrs in FM_ROLES:
    _ROLE_BY_GROUP.setdefault(_group, []).append(_name)


def role_rating(person: dict, role_name: str) -> int | None:
    """Return role suitability 1-20, or None if attrs missing."""
    key_indices = _ROLE_INDEX.get(role_name)
    if not key_indices:
        return None
    raw = person.get('raw_attrs', [])
    if len(raw) < 54:
        return None
    vals = [max(1, min(20, round(raw[i] / 5))) for i in key_indices]
    return round(sum(vals) / len(vals))


def all_role_names() -> list[str]:
    return [name for name, _, _ in FM_ROLES]


def role_names_by_group() -> list[tuple[str, list[str]]]:
    return [(g, _ROLE_BY_GROUP.get(g, [])) for g in ROLE_GROUPS]
