"""CA / PA (1-200) and Dev Rate (1-20) -> star rating for display. No Qt imports."""

def half_stars(stars):
    """Float stars -> nearest half star, ties UP (Python's round() ties to even, which made uneven bins).
    Every star mapping in the app (CA/PA, Dev Rate, club reputation) rounds through here."""
    return int(stars * 2 + 0.5) / 2


STAR_DIVISOR = 40      # CA/PA: 200 / 5 stars; adjust here if a better fit to FM turns up
DEV_STAR_DIVISOR = 4   # Dev Rate: 20 / 5 stars


def ability_stars(value, divisor=STAR_DIVISOR):
    """Stars 0.5..5.0 in half steps for a CA/PA value (None/invalid -> 0.0).

    APPROXIMATION of FM's relative star rating (which depends on the league/club context):
    stars = value / STAR_DIVISOR rounded half up to a half step (half_stars), clamped to 0.5..5.
    Adjustable in one place (STAR_DIVISOR / this function). `divisor` selects another scale.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.5, min(5.0, half_stars(v / divisor)))


def dev_stars(value):
    """Stars for a Dev Rate (1-20): value / DEV_STAR_DIVISOR, same rounding/clamp. Approximation."""
    return ability_stars(value, DEV_STAR_DIVISOR)
