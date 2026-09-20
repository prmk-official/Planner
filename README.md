# AI Planner — Agentic Student Planning System

AI Planner converts messy, natural-language student information into structured tasks and events.

Instead of forcing users to manually create separate tasks, deadlines, and calendar entries, the system lets them write naturally:

> I have a GDG meeting Thursday at 5 PM. Submit the registration form by Wednesday. Bring the event report.

The system extracts the actionable information, distinguishes tasks from events, resolves simple natural-language dates, calculates urgency, validates the result with deterministic Python rules, and stores the resulting planner items locally.

## Why this project?

Students receive obligations through many different forms: messages, announcements, meetings, assignments, applications, and events. The difficult part is often not storing a task — it is converting unstructured information into reliable structured actions.

AI Planner focuses on that conversion step.

## Core workflow

```text
Natural-language input
        ↓
Strands Agent
        ↓
Llama 3.2 via Ollama
        ↓
Structured tasks/events
        ↓
Pydantic validation
        ↓
Deterministic safety rules
        ↓
Date resolution
        ↓
Priority calculation
        ↓
Local persistent storage
```

## Technology

- Python
- Strands Agents
- Ollama
- Llama 3.2
- Pydantic
- Local JSON storage

### AWS / open-source component

The project uses **Strands Agents**, an open-source agent SDK from AWS, locally with Ollama.

The current implementation intentionally does not require an AWS account, AWS credentials, or paid cloud services.

We do **not** claim to use Amazon Bedrock, DynamoDB, Lambda, or other AWS cloud services in the current implementation.

## Architecture

The system separates probabilistic language understanding from deterministic application logic.

### LLM responsibilities

The language model handles:

- identifying tasks
- identifying events
- extracting titles
- extracting explicitly stated dates
- extracting explicitly stated times
- extracting meaningful context

### Python responsibilities

Python handles:

- schema validation
- null normalization
- task safety rules
- date resolution
- days remaining
- priority calculation
- duplicate detection
- persistence

This separation reduces the risk of allowing the language model to make decisions that should be deterministic.

## Example

### Input

```text
I have a club meeting tomorrow at 4 PM.
I need to submit my ML assignment by Monday.
Bring my project report to the meeting.
Complete the internship application by Friday.
```

### Extracted result

```text
EVENT
Club meeting
Date: tomorrow
Time: 4 PM

TASK
Submit ML assignment
Deadline: Monday
Priority: URGENT

TASK
Bring project report
No deadline

TASK
Complete internship application
Deadline: Friday
Priority: MEDIUM
```

A task associated with an event does not automatically inherit that event's date or time. Deterministic safety rules are applied after model extraction to enforce this behavior.

## Project structure

```text
AI_PLANNER_AWS/
│
├── agent.py
├── date_utils.py
├── priority_utils.py
├── local_storage.py
├── planner_data.json
├── requirements.txt
├── .gitignore
├── README.md
└── ARCHITECTURE.md
```

## Setup

### 1. Create a Python environment

Python 3.12 is recommended.

```powershell
uv venv --python 3.12
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```powershell
uv pip install -r requirements.txt
```

### 3. Install and start Ollama

Install Ollama separately and make sure it is running.

Pull the model:

```powershell
ollama pull llama3.2
```

Verify:

```powershell
ollama list
```

You should see:

```text
llama3.2:latest
```

### 4. Run the planner

```powershell
python agent.py
```

## Priority logic

Priority is calculated deterministically from the number of days remaining:

| Days remaining | Priority |
|---:|---|
| < 0 | OVERDUE |
| 0–1 | URGENT |
| 2–3 | HIGH |
| 4–7 | MEDIUM |
| > 7 | LOW |

## Date resolution

The current implementation supports:

- today
- tomorrow
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday

Unsupported date expressions are retained as text rather than being guessed.

## Persistence

Planner items are stored in:

```text
planner_data.json
```

The local storage layer also prevents duplicate items based on:

- type
- title
- resolved date
- time

## Design principle

> **LLM for ambiguity. Code for certainty.**

The model interprets natural language. Deterministic code performs operations where correctness can be explicitly defined.

## Current limitations

This version is intentionally lightweight.

It currently does not provide:

- cloud synchronization
- calendar integration
- email/WhatsApp ingestion
- authentication
- multi-user storage
- full natural-language date parsing
- production deployment

These are outside the scope of the current hackathon prototype.

## Demo

A good demonstration should show:

1. A single messy student message containing multiple obligations.
2. Extraction into tasks and events.
3. Correct separation of deadlines from event times.
4. Automatic priority calculation.
5. Persistence.
6. Re-entering the same information and showing that duplicates are not created.

## License

This project is intended as an open-source hackathon prototype.
