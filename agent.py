import json
from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ValidationError
from strands import Agent
from strands.models.ollama import OllamaModel

from date_utils import resolve_date
from priority_utils import (
    calculate_days_remaining,
    calculate_priority,
)
from local_storage import (
    save_items,
    get_all_items,
)


class ItemType(str, Enum):
    TASK = "TASK"
    EVENT = "EVENT"


class PlannerItem(BaseModel):
    type: ItemType
    title: str

    date_text: Optional[str] = None
    resolved_date: Optional[str] = None

    days_remaining: Optional[int] = None
    priority: Optional[str] = None

    time_text: Optional[str] = None
    context: Optional[str] = None


class PlannerItemList(BaseModel):
    items: List[PlannerItem]


model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.2:latest",
)


agent = Agent(
    model=model,
    system_prompt="""
You are an information extraction component for a student
productivity system.

Your ONLY job is to extract tasks and events from the user's message.

Return ONLY valid JSON.

Do not use markdown.
Do not explain your answer.

The JSON must have exactly this structure:

{
  "items": [
    {
      "type": "TASK or EVENT",
      "title": "string",
      "date_text": "string or null",
      "time_text": "string or null",
      "context": "string or null"
    }
  ]
}

IMPORTANT:

- Missing values MUST be JSON null.
- NEVER write "null" as a quoted string.
- Do not invent information.

TASK vs EVENT:

1. EVENT means something that happens at a scheduled time.
   Examples:
   - club meeting
   - research meeting
   - class
   - interview
   - appointment

2. TASK means something the student needs to do.
   Examples:
   - submit assignment
   - complete application
   - bring report
   - finish literature review

3. A TASK can have a deadline.
   A deadline does NOT turn a TASK into an EVENT.

DATE AND TIME ASSOCIATION:

4. A date or time belongs ONLY to the task/event
   that explicitly has that date or time.

5. NEVER copy a date or time from an EVENT to a TASK.

6. NEVER copy a date or time from one TASK to another TASK.

7. If the user says:
   "meeting tomorrow at 4 PM"
   then the meeting gets:
   date_text = "tomorrow"
   time_text = "4 PM"

8. If the user says:
   "submit assignment by Monday"
   then the assignment gets:
   date_text = "Monday"

9. If the user says:
   "bring my report to the meeting"
   then the report task gets:
   date_text = null
   time_text = null

10. If a TASK merely references another EVENT,
    that does NOT give the TASK the EVENT's date or time.

11. If a task says:
    "finish the literature review before the meeting"
    and the meeting has a date,
    DO NOT assign the meeting's date to the task.

12. Only assign a TASK a date when the user explicitly
    gives a deadline or date for that TASK.

CONTEXT:

13. Only include meaningful additional context.

14. Do not use generic context such as:
    "meeting"
    "assignment"
    "event"

15. Do not repeat information already contained
    in the title.

IRRELEVANT INPUT:

16. If the user's message contains no identifiable
    tasks or events, return:

{
  "items": []
}
"""
)


def normalize_null_strings(
    item_list: PlannerItemList
):
    """
    Protect the application from models that occasionally
    return the string "null" instead of JSON null.
    """

    for item in item_list.items:

        if item.date_text == "null":
            item.date_text = None

        if item.time_text == "null":
            item.time_text = None

        if item.context == "null":
            item.context = None


def apply_task_safety_rules(
    item_list: PlannerItemList,
    original_input: str
):
    """
    Apply deterministic rules after LLM extraction.

    The LLM handles semantic interpretation.
    Python enforces rules that must not be violated.
    """

    text = original_input.lower()

    for item in item_list.items:

        if item.type != ItemType.TASK:
            continue

        title = item.title.lower()

        # A task that says it should be brought/taken
        # to a meeting should not inherit the meeting's
        # date or time.
        meeting_reference = (
            "to the meeting" in text
            or "for the meeting" in text
            or "at the meeting" in text
        )

        bring_or_prepare_task = (
            "bring" in title
            or "take" in title
            or "prepare" in title
        )

        if (
            meeting_reference
            and bring_or_prepare_task
            and (
                "meeting" in title
                or "report" in title
                or "document" in title
                or "file" in title
            )
        ):
            item.date_text = None
            item.time_text = None
            item.resolved_date = None
            item.days_remaining = None
            item.priority = None


def process_input(
    user_input: str
) -> PlannerItemList:

    response = agent(user_input)

    raw_text = str(response)

    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError(
            "The model did not return a JSON object."
        )

    json_text = raw_text[start:end]

    data = json.loads(json_text)

    item_list = PlannerItemList.model_validate(
        data
    )

    normalize_null_strings(
        item_list
    )

    apply_task_safety_rules(
        item_list,
        user_input
    )

    reference_date = date.today()

    for item in item_list.items:

        if item.date_text:

            resolved = resolve_date(
                item.date_text,
                reference_date
            )

            if resolved:

                item.resolved_date = (
                    resolved.isoformat()
                )

                item.days_remaining = (
                    calculate_days_remaining(
                        item.resolved_date,
                        reference_date
                    )
                )

                item.priority = (
                    calculate_priority(
                        item.days_remaining
                    )
                )

    return item_list


def display_planner(
    item_list: PlannerItemList
):

    print("\n")
    print("=" * 60)
    print("                 AI PLANNER")
    print("=" * 60)

    print(
        f"\nToday: {date.today()}\n"
    )

    events = [
        item
        for item in item_list.items
        if item.type == ItemType.EVENT
    ]

    if events:

        print("EVENTS")
        print("-" * 60)

        for event in events:

            event_date = (
                event.resolved_date
                or event.date_text
                or "No date"
            )

            event_time = (
                event.time_text
                or "No time"
            )

            print(
                f"• {event.title}"
            )

            print(
                f"  Date: {event_date}"
            )

            print(
                f"  Time: {event_time}"
            )

            print()

    dated_tasks = [
        item
        for item in item_list.items
        if (
            item.type == ItemType.TASK
            and item.resolved_date is not None
        )
    ]

    dated_tasks.sort(
        key=lambda item: item.days_remaining
    )

    if dated_tasks:

        print("PRIORITIZED TASKS")
        print("-" * 60)

        for task in dated_tasks:

            print(
                f"[{task.priority}] "
                f"{task.title}"
            )

            print(
                f"  Due: {task.resolved_date}"
            )

            print(
                f"  Days remaining: "
                f"{task.days_remaining}"
            )

            print()

    undated_tasks = [
        item
        for item in item_list.items
        if (
            item.type == ItemType.TASK
            and item.resolved_date is None
        )
    ]

    if undated_tasks:

        print("TASKS WITHOUT DEADLINES")
        print("-" * 60)

        for task in undated_tasks:

            print(
                f"• {task.title}"
            )

            if task.context:

                print(
                    f"  Context: {task.context}"
                )

            print()


def display_saved_items():

    saved_items = get_all_items()

    if not saved_items:
        return

    print("\n")
    print("=" * 60)
    print("                 SAVED PLANNER")
    print("=" * 60)

    print(
        f"\nStored items: {len(saved_items)}\n"
    )

    events = [
        item
        for item in saved_items
        if item.get("type") == "EVENT"
    ]

    tasks = [
        item
        for item in saved_items
        if item.get("type") == "TASK"
    ]

    if events:

        print("SAVED EVENTS")
        print("-" * 60)

        for event in events:

            event_date = (
                event.get("resolved_date")
                or event.get("date_text")
                or "No date"
            )

            event_time = (
                event.get("time_text")
                or "No time"
            )

            print(
                f"• {event.get('title')}"
            )

            print(
                f"  Date: {event_date}"
            )

            print(
                f"  Time: {event_time}"
            )

            print()

    dated_tasks = [
        task
        for task in tasks
        if task.get("resolved_date")
    ]

    dated_tasks.sort(
        key=lambda item: (
            item.get("days_remaining", 999999)
        )
    )

    if dated_tasks:

        print("SAVED TASKS")
        print("-" * 60)

        for task in dated_tasks:

            print(
                f"[{task.get('priority', 'NONE')}] "
                f"{task.get('title')}"
            )

            print(
                f"  Due: "
                f"{task.get('resolved_date')}"
            )

            print()


def main():

    print("\n")
    print("=" * 60)
    print("                    AI PLANNER")
    print("=" * 60)

    display_saved_items()

    print(
        "\nPaste any message containing tasks, "
        "deadlines, meetings, etc."
    )

    print("\nCommands:")

    print(
        "  exit  → close the application"
    )

    print(
        "  clear → clear the current input prompt"
    )

    print(
        "  saved → show saved planner items"
    )

    print("\nExample:")

    print(
        "I have a GDG meeting Thursday at 5 PM. "
        "Submit the registration form by Wednesday."
    )

    while True:

        print("\n" + "-" * 60)

        try:

            user_input = input(
                "\nEnter your information:\n> "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\n\nExiting AI Planner."
            )

            break

        if user_input.lower() == "exit":

            print(
                "\nExiting AI Planner."
            )

            break

        if user_input.lower() == "clear":

            print(
                "\nInput cleared."
            )

            continue

        if user_input.lower() == "saved":

            display_saved_items()

            continue

        if not user_input:

            print(
                "\nNo input entered. "
                "Please enter a message."
            )

            continue

        try:

            planner_items = process_input(
                user_input
            )

            if not planner_items.items:

                print(
                    "\nNo tasks or events were detected."
                )

                continue

            display_planner(
                planner_items
            )

            saved_ids = save_items(
                planner_items
            )

            print(
                f"Saved {len(saved_ids)} "
                f"item(s) to planner_data.json."
            )

        except json.JSONDecodeError as error:

            print(
                "\nERROR: Invalid JSON returned "
                "by model."
            )

            print(
                f"Details: {error}"
            )

        except ValidationError as error:

            print(
                "\nERROR: Model output failed "
                "validation."
            )

            print(
                error
            )

        except ValueError as error:

            print(
                f"\nERROR: {error}"
            )

        except Exception as error:

            print(
                "\nUNEXPECTED ERROR:"
            )

            print(
                f"{type(error).__name__}: {error}"
            )


if __name__ == "__main__":
    main()