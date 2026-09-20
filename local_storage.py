import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STORAGE_FILE = Path("planner_data.json")


def _load_data():
    """
    Load planner items from the local JSON file.
    """

    if not STORAGE_FILE.exists():
        return []

    try:
        with STORAGE_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (
        json.JSONDecodeError,
        OSError
    ):
        return []


def _save_data(items):
    """
    Save planner items to the local JSON file.
    """

    with STORAGE_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            items,
            file,
            indent=2,
            ensure_ascii=False
        )


def _is_duplicate(existing_item, new_item):
    """
    Determine whether a newly extracted item already exists.

    Two items are considered duplicates when their:
    - type
    - title
    - resolved date
    - time

    are identical.
    """

    existing_type = existing_item.get("type")
    existing_title = (
        existing_item.get("title", "")
        .strip()
        .lower()
    )
    existing_date = (
        existing_item.get("resolved_date")
    )
    existing_time = (
        existing_item.get("time_text")
    )

    new_type = new_item.get("type")
    new_title = (
        new_item.get("title", "")
        .strip()
        .lower()
    )
    new_date = new_item.get("resolved_date")
    new_time = new_item.get("time_text")

    return (
        existing_type == new_type
        and existing_title == new_title
        and existing_date == new_date
        and existing_time == new_time
    )


def save_item(item):
    """
    Save one PlannerItem locally.

    If an identical item already exists,
    do not create another copy.

    Returns:
    - item ID when a new item is created
    - existing item ID when a duplicate is found
    """

    items = _load_data()

    record = {
        "item_id": str(uuid.uuid4()),

        "type": item.type.value,

        "title": item.title,

        "date_text": item.date_text,

        "resolved_date": item.resolved_date,

        "days_remaining": item.days_remaining,

        "priority": item.priority,

        "time_text": item.time_text,

        "context": item.context,

        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    for existing_item in items:

        if _is_duplicate(
            existing_item,
            record
        ):

            return existing_item["item_id"]

    items.append(record)

    _save_data(items)

    return record["item_id"]


def save_items(item_list):
    """
    Save all items from a PlannerItemList.

    Duplicate items are ignored.
    """

    item_ids = []

    for item in item_list.items:

        item_id = save_item(item)

        item_ids.append(item_id)

    return item_ids


def get_all_items():
    """
    Return every stored planner item.
    """

    return _load_data()


def delete_item(item_id):
    """
    Delete a planner item by ID.
    """

    items = _load_data()

    remaining_items = [
        item
        for item in items
        if item.get("item_id") != item_id
    ]

    _save_data(remaining_items)


def clear_all_items():
    """
    Delete all stored planner items.
    """

    _save_data([])


if __name__ == "__main__":

    print("=" * 60)
    print("             LOCAL STORAGE TEST")
    print("=" * 60)

    items = get_all_items()

    print(
        f"\nStored items: {len(items)}"
    )

    print(
        f"Storage file: {STORAGE_FILE}"
    )

    print(
        "\nLocal storage is ready."
    )