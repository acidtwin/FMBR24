"""Radar axes of the Profile radar and the Compare page: the app's OWN scouting groups (not the game's). No Qt imports.

THE one place to edit them. Each table row = (axis name, attribute names, names scored lower-is-better i.e. 21 - v); table
order = wheel order, clockwise from the top. Axis value = mean of its (inverted) attribute values.
OVERVIEW_*  six axes (the player window radar, Compare 'Overview').
DETAILED_*  Compare 'Detailed': 12 outfield / 11 goalkeeper axes (mockups/compare-players.html, comment 'RADAR AXES').
Both outfield sets are an exact partition of the 36 outfield + 5 hidden attributes (Footedness is on no axis); the goalkeeper
sets use the 11 GK attributes plus the outfield ones a keeper needs.
"""
_ATHLETICISM = ['Pace', 'Acceleration', 'Agility', 'Balance', 'Stamina', 'Strength', 'Jumping Reach', 'Natural Fitness']
_MENTALITY = ['Aggression', 'Composure', 'Concentration', 'Decisions', 'Determination', 'Leadership', 'Teamwork', 'Work Rate']
_REL_OUT = ('Reliability', ['Consistency', 'Important Matches', 'Injury Prone', 'Dirtiness', 'Versatility'], ('Injury Prone', 'Dirtiness'))
_REL_GK = ('Reliability', ['Consistency', 'Important Matches', 'Injury Prone', 'Dirtiness', 'Eccentricity'],
           ('Injury Prone', 'Dirtiness', 'Eccentricity'))

OVERVIEW_OUT = [
    ('Attacking', ['Finishing', 'Long Shots', 'Dribbling', 'Penalties', 'Free Kick', 'Off the Ball', 'Flair'], ()),
    ('Creativity', ['Passing', 'Vision', 'Technique', 'First Touch', 'Crossing', 'Corners', 'Long Throws'], ()),
    ('Athleticism', _ATHLETICISM, ()),
    ('Defending', ['Tackling', 'Marking', 'Heading', 'Positioning', 'Anticipation', 'Bravery'], ()),
    _REL_OUT,
    ('Mentality', _MENTALITY, ()),
]
OVERVIEW_GK = [
    ('Shot-stopping', ['Reflexes', 'Handling', 'One on Ones', 'Punching'], ()),
    ('Command', ['Aerial Reach', 'Command of Area', 'Communication', 'Rushing Out'], ()),
    ('Athleticism', _ATHLETICISM, ()),
    ('Distribution', ['Kicking', 'Throwing', 'Passing', 'First Touch'], ()),
    _REL_GK,
    ('Mentality', _MENTALITY + ['Anticipation', 'Positioning', 'Bravery'], ()),
]
DETAILED_OUT = [
    ('Shooting', ['Finishing', 'Long Shots', 'Penalties'], ()),
    ('Ball control', ['Dribbling', 'First Touch', 'Flair', 'Agility', 'Balance'], ()),
    ('Passing', ['Passing', 'Vision', 'Technique'], ()),
    ('Delivery', ['Crossing', 'Corners', 'Free Kick', 'Long Throws'], ()),
    ('Positioning', ['Positioning', 'Off the Ball', 'Anticipation', 'Concentration'], ()),
    ('Tackling', ['Tackling', 'Marking'], ()),
    ('Aerial', ['Heading', 'Jumping Reach'], ()),
    ('Physicality', ['Strength', 'Bravery', 'Aggression'], ()),
    ('Pace', ['Pace', 'Acceleration'], ()),
    ('Endurance', ['Stamina', 'Work Rate', 'Natural Fitness', 'Determination'], ()),
    ('Mentality', ['Composure', 'Decisions', 'Teamwork', 'Leadership'], ()),
    _REL_OUT,
]
DETAILED_GK = [
    ('Reflexes', ['Reflexes', 'Agility', 'Balance'], ()),
    ('Handling', ['Handling', 'Punching'], ()),
    ('One on Ones', ['One on Ones', 'Rushing Out', 'Anticipation'], ()),
    ('Aerial', ['Aerial Reach', 'Command of Area', 'Jumping Reach'], ()),
    ('Organisation', ['Communication', 'Leadership', 'Teamwork'], ()),
    ('Positioning', ['Positioning', 'Concentration', 'Decisions'], ()),
    ('Distribution', ['Kicking', 'Throwing'], ()),
    ('Ball playing', ['Passing', 'First Touch', 'Technique', 'Vision'], ()),
    ('Athleticism', ['Acceleration', 'Pace', 'Strength', 'Stamina', 'Natural Fitness'], ()),
    ('Mentality', ['Composure', 'Determination', 'Bravery', 'Aggression'], ()),
    _REL_GK,
]
MODES = ('overview', 'detailed')


def axis_table(gk, mode='overview'):
    """The axis table for a keeper / outfield player in 'overview' or 'detailed' mode."""
    if mode == 'detailed':
        return DETAILED_GK if gk else DETAILED_OUT
    return OVERVIEW_GK if gk else OVERVIEW_OUT


def axis_values(values, gk, mode='overview'):
    """values {attribute name: shown 1-20 value} -> [(axis name, mean 1-20, tooltip text)] in wheel order. Attributes missing
    from `values` are skipped; an axis with none is dropped."""
    out = []
    for name, attrs, inv in axis_table(gk, mode):
        have = [a for a in attrs if a in values]
        if not have:
            continue
        mean = sum(21 - values[a] if a in inv else values[a] for a in have) / len(have)
        tip = f"{name} = mean of {len(have)}: " + ', '.join(a + (' (21-v)' if a in inv else '') for a in have)
        out.append((name, mean, tip))
    return out
