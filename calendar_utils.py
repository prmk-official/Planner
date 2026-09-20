from datetime import datetime, timedelta


def _parse_time(time_text):
    if not time_text:
        return 9, 0

    text = time_text.strip().upper()

    formats = [
        "%I %p",
        "%I:%M %p",
        "%I%p",
        "%I:%M%p",
        "%H:%M",
        "%H",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.hour, parsed.minute
        except ValueError:
            continue

    return 9, 0


def _escape_ics(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def create_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI Planner//EN",
        "CALSCALE:GREGORIAN",
    ]

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for index, event in enumerate(events):
        resolved_date = event.get("resolved_date")

        if not resolved_date:
            continue

        try:
            event_date = datetime.strptime(
                resolved_date,
                "%Y-%m-%d",
            )
        except ValueError:
            continue

        hour, minute = _parse_time(event.get("time_text"))

        start = event_date.replace(
            hour=hour,
            minute=minute,
        )

        end = start + timedelta(hours=1)

        uid = event.get(
            "item_id",
            f"ai-planner-{index}",
        )

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_escape_ics(uid)}",
                f"DTSTAMP:{timestamp}",
                f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{_escape_ics(event.get('title', 'Planner Event'))}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"
