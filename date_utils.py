from datetime import date, timedelta


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def resolve_date(
    date_text: str | None,
    reference_date: date
) -> date | None:
    """
    Convert simple natural-language date expressions into
    an actual calendar date.

    Supported:
    - today
    - tomorrow
    - Monday-Sunday

    Returns None when the expression is not supported.
    """

    if not date_text:
        return None

    text = date_text.strip().lower()

    # -------------------------------
    # Today
    # -------------------------------

    if text == "today":
        return reference_date

    # -------------------------------
    # Tomorrow
    # -------------------------------

    if text == "tomorrow":
        return reference_date + timedelta(days=1)

    # -------------------------------
    # Weekday
    # -------------------------------

    if text in WEEKDAYS:

        target_weekday = WEEKDAYS[text]
        current_weekday = reference_date.weekday()

        days_ahead = (
            target_weekday - current_weekday
        ) % 7

        return reference_date + timedelta(
            days=days_ahead
        )

    # -------------------------------
    # Unsupported expression
    # -------------------------------

    return None


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    reference_date = date(2026, 9, 20)

    print("Reference date:", reference_date)
    print()

    test_dates = [
        "today",
        "tomorrow",
        "Monday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Sunday",
    ]

    for text in test_dates:

        resolved = resolve_date(
            text,
            reference_date
        )

        print(
            f"{text:10} → {resolved}"
        )