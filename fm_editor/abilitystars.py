"""CA / PA (1-200 scale) -> star rating for display. No Qt imports."""

STAR_DIVISOR = 40  # 200 / 5 stars; adjust here (or replace the body) if a better fit to FM turns up


def ability_stars(value):
    """Stars 0.5..5.0 in half steps for a CA/PA value (None/invalid -> 0.0).

    APPROXIMATION of FM's relative star rating (which depends on the league/club context):
    stars = value / STAR_DIVISOR rounded to the nearest half step, clamped to 0.5..5.
    Adjustable in one place (STAR_DIVISOR / this function).
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.5, min(5.0, round(v / STAR_DIVISOR * 2) / 2))
