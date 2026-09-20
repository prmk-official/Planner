import json
from typing import List

from pydantic import BaseModel
from strands import Agent
from strands.models.ollama import OllamaModel

from local_storage import get_all_items


class DailyPlan(BaseModel):
    summary: str
    priorities: List[str]
    reasoning: List[str]


model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.2:latest",
)


planner_agent = Agent(
    model=model,
    system_prompt="""
You are a daily planning assistant.

You receive a JSON list of already-structured planner items.

Your job is to create a concise plan for the student.

Rules:
- Do not invent tasks, dates, deadlines, or events.
- Prefer urgent and overdue tasks.
- Consider upcoming events.
- Tasks without deadlines can be suggested only after dated urgent work.
- Return ONLY valid JSON.
- Use exactly this structure:

{
  "summary": "short sentence",
  "priorities": [
    "specific planner item title",
    "specific planner item title"
  ],
  "reasoning": [
    "short reason",
    "short reason"
  ]
}

The priorities must refer to items present in the supplied data.
"""
)


def generate_daily_plan():
    items = get_all_items()

    if not items:
        return DailyPlan(
            summary="Your planner is empty.",
            priorities=[],
            reasoning=[],
        )

    compact_items = []

    for item in items:
        compact_items.append(
            {
                "type": item.get("type"),
                "title": item.get("title"),
                "resolved_date": item.get("resolved_date"),
                "days_remaining": item.get("days_remaining"),
                "priority": item.get("priority"),
                "time_text": item.get("time_text"),
            }
        )

    response = planner_agent(
        json.dumps(compact_items, ensure_ascii=False)
    )

    raw_text = str(response)

    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError(
            "Daily planning model did not return valid JSON."
        )

    data = json.loads(raw_text[start:end])

    return DailyPlan.model_validate(data)
