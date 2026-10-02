"""Role Rating tab logic (no Qt): which roles each pitch position offers (POS_ROLES) and the role rating as a PERCENT.

Percent = weighted mean of the role's key attributes on the 0-100 raw scale (the unit of `raw_attrs`), e.g. 83.89. The old
1-20 rating of the Best by Role report is `score_to_rating(percent)` = clamp(round(percent / 5)): `gui.roles.role_rating`
is a thin wrapper over `role_score`, so the two can never drift apart. Key attributes come from `gui.roles.FM_ROLES`
(pure data, no Qt); weights from the active Settings preset (`fm_editor.weights`).

POS_ROLES is FROM MEMORY OF FM24 and must be verified in game (screens of the real position role lists needed):
unsure are SW, Defensive Winger / Advanced Playmaker on AM(L/R), Wide Playmaker (D) on M(L/R), Wing-Back / Wide Centre-Back
on D(L/R). `gui.roles.FM_ROLES` itself lacks Wing-Back (A), Stopper (S/Cover), Inverted Full-Back, Regista, Target Forward,
so those cannot show.
"""
import re

from gui.roles import _ROLE_INDEX, FM_ROLES
from fm_editor.weights import get_role_weights

POS_CODES = ('GK', 'SW', 'DL', 'DC', 'DR', 'WBL', 'WBR', 'DM', 'ML', 'MC', 'MR', 'AML', 'AMC', 'AMR', 'ST')


def _rl(family, *duties):
    """_rl('Winger', 'S', 'A') -> ['Winger (S)', 'Winger (A)']; no duty = the role name alone (FM_ROLES spelling)."""
    return [f'{family} ({d})' for d in duties] if duties else [family]


def _build():
    cd = (_rl('Ball-Playing Defender', 'D', 'S') + _rl('Central Defender', 'D', 'S', 'Cover') + _rl('Libero', 'D', 'S')
          + _rl('No-Nonsense Centre-Back') + _rl('Stopper', 'D'))
    wbs = _rl('Wing-Back', 'D', 'S') + _rl('Complete Wing-Back', 'S', 'A') + _rl('Inverted Wing-Back', 'D', 'S', 'A')
    fb = (_rl('Full Back', 'D', 'S', 'A') + wbs + _rl('No-Nonsense Full Back') + _rl('Wide Centre-Back', 'D', 'S', 'A'))
    wm = (_rl('Defensive Winger', 'D', 'S') + _rl('Wide Midfielder', 'D', 'S', 'A') + _rl('Winger', 'S', 'A')
          + _rl('Wide Playmaker', 'D', 'S', 'A') + _rl('Inverted Winger', 'S', 'A'))
    aw = (_rl('Winger', 'S', 'A') + _rl('Inside Forward', 'S', 'A') + _rl('Inverted Winger', 'S', 'A')
          + _rl('Raumdeuter', 'A') + _rl('Wide Playmaker', 'S', 'A') + _rl('Advanced Playmaker', 'S', 'A'))
    return {
        'GK': _rl('Goalkeeper', 'D', 'S') + _rl('Sweeper Keeper', 'D', 'S', 'A'),
        'SW': _rl('Libero', 'D', 'S') + _rl('Central Defender', 'Cover') + _rl('Ball-Playing Defender', 'D'),
        'DL': fb, 'DC': cd, 'DR': fb,
        'WBL': wbs, 'WBR': wbs,
        'DM': (_rl('Anchor', 'D') + _rl('Ball-Winning Midfielder', 'D', 'S') + _rl('Deep-Lying Playmaker', 'D', 'S')
               + _rl('Defensive Midfielder', 'D', 'S') + _rl('Half-Back', 'D') + _rl('Segundo Volante', 'S', 'A')),
        'ML': wm,
        'MC': (_rl('Box-to-Box Midfielder', 'S') + _rl('Carrilero', 'S') + _rl('Central Midfielder', 'D', 'S', 'A')
               + _rl('Mezzala', 'S', 'A') + _rl('Roaming Playmaker', 'S') + _rl('Ball-Winning Midfielder', 'D', 'S')
               + _rl('Deep-Lying Playmaker', 'D', 'S') + _rl('Advanced Playmaker', 'S', 'A')),
        'MR': wm,
        'AML': aw,
        'AMC': (_rl('Advanced Playmaker', 'S', 'A') + _rl('Attacking Midfielder', 'D', 'S', 'A') + _rl('Enganche', 'S')
                + _rl('Shadow Striker', 'A') + _rl('Trequartista', 'A')),
        'AMR': aw,
        'ST': (_rl('Advanced Forward', 'A') + _rl('Complete Forward', 'S', 'A') + _rl('Deep-Lying Forward', 'S', 'A')
               + _rl('False Nine', 'S') + _rl('Poacher', 'A') + _rl('Pressing Forward', 'D', 'S', 'A')
               + _rl('Target Man', 'S', 'A') + _rl('Trequartista', 'A')),
    }


POS_ROLES: dict[str, list[str]] = _build()

# FALLBACK for a role that POS_ROLES does not list (none today: all 81 FM_ROLES are listed; kept so a future role added to
# FM_ROLES alone still gets a position filter): FM_ROLES group code -> pitch positions where that group plays. ONE place.
GROUP_POSITIONS = {
    'GK': ('GK',), 'CB': ('DC', 'SW'), 'FB/WB': ('DL', 'DR', 'WBL', 'WBR'), 'DM': ('DM',), 'CM': ('MC',),
    'AM': ('AMC',), 'Winger': ('ML', 'MR', 'AML', 'AMR'), 'Striker': ('ST',),
}
# Role families FM also lets you field on other slots than POS_ROLES (from memory, unverified): Wide Centre-Back is a D(C)
# role in a back three, listed above only on DL/DR.
_EXTRA_POSITIONS = {'Wide Centre-Back': ('DC',)}

_ROLE_POSITIONS: dict = {}   # role -> positions, filled on first use


def role_positions(role: str) -> tuple[str, ...]:
    """Pitch positions (POS_CODES, = gui.main_window.POSITIONS names) where `role` can be played: the inverse of
    POS_ROLES (+ _EXTRA_POSITIONS), else the role's FM_ROLES group via GROUP_POSITIONS; () for an unknown role."""
    if not _ROLE_POSITIONS:
        for pos, names in POS_ROLES.items():
            for n in names:
                _ROLE_POSITIONS.setdefault(n, []).append(pos)
        for n in list(_ROLE_POSITIONS):
            _ROLE_POSITIONS[n] = tuple(dict.fromkeys(_ROLE_POSITIONS[n] + list(_EXTRA_POSITIONS.get(split_role(n)[0], ()))))
        for n, group, _ in FM_ROLES:
            _ROLE_POSITIONS.setdefault(n, GROUP_POSITIONS.get(group, ()))
    return _ROLE_POSITIONS.get(role, ())


DUTY_WORD = {'D': 'Defend', 'S': 'Support', 'A': 'Attack', 'Cover': 'Cover', '': 'Defend'}   # '' = unsuffixed No-Nonsense roles
_SPLIT = re.compile(r'^(.*) \((D|S|A|Cover)\)$')


def split_role(name: str) -> tuple[str, str]:
    """'Winger (S)' -> ('Winger', 'Support'); 'No-Nonsense Full Back' -> ('No-Nonsense Full Back', 'Defend')."""
    m = _SPLIT.match(name)
    return (m.group(1), DUTY_WORD[m.group(2)]) if m else (name, DUTY_WORD[''])


def role_score(raw_attrs, role: str, weights: dict[int, int] | None = None) -> float | None:
    """Percent (0-100 scale of raw_attrs) = weighted mean of the role's key attributes; None if the role is unknown or
    the attributes are missing. weights = {attr_idx: weight} of the active preset; None / all-zero = equal weight."""
    key = _ROLE_INDEX.get(role)
    if not key or raw_attrs is None or len(raw_attrs) < 54:
        return None
    if weights:
        total = sum(weights.get(i, 0) for i in key)
        if total > 0:
            return sum(raw_attrs[i] * weights.get(i, 0) for i in key) / total
    return sum(raw_attrs[i] for i in key) / len(key)


def score_to_rating(score: float) -> int:
    """Percent -> the 1-20 integer of the Best by Role report (Python round, half to even)."""
    return max(1, min(20, round(score / 5)))


def position_roles(pos: str, raw_attrs, preset: dict | None = None) -> list[tuple[str, list[tuple[str, str, float]]]]:
    """Roles playable at `pos` grouped by role family: [(family, [(duty word, FM_ROLES name, percent), ...])].
    Rows by percent desc (ties: name), groups by their best row (ties: family). The first row of the first group is the best role."""
    groups: dict[str, list[tuple[str, str, float]]] = {}
    for name in POS_ROLES.get(pos, ()):
        s = role_score(raw_attrs, name, get_role_weights(preset, name))
        if s is None:
            continue
        fam, duty = split_role(name)
        groups.setdefault(fam, []).append((duty, name, s))
    out = [(fam, sorted(rows, key=lambda r: (-r[2], r[1]))) for fam, rows in groups.items()]
    out.sort(key=lambda g: (-g[1][0][2], g[0]))
    return out


def best_by_position(raw_attrs, preset: dict | None = None, positions=None) -> dict[str, tuple[str, float]]:
    """{pos: (best role name, percent)} for `positions` (default all 15); a position without a rateable role is left out."""
    out = {}
    for pos in positions or POS_CODES:
        g = position_roles(pos, raw_attrs, preset)
        if g:
            out[pos] = (g[0][1][0][1], g[0][1][0][2])
    return out
