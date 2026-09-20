from datetime import date


def calculate_days_remaining(
    resolved_date: str,
    reference_date: date
) -> int:

    target_date = date.fromisoformat(resolved_date)

    return (target_date - reference_date).days


def calculate_priority(days_remaining: int) -> str:

    if days_remaining < 0:
        return "OVERDUE"

    if days_remaining <= 1:
        return "URGENT"

    if days_remaining <= 3:
        return "HIGH"

    if days_remaining <= 7:
        return "MEDIUM"

    return "LOW"