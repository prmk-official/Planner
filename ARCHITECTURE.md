# Architecture

## System architecture

```text
┌──────────────────────────────┐
│        Student Input         │
│  Natural-language message    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Strands Agent          │
│  Agent orchestration layer   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      Llama 3.2 / Ollama      │
│   Natural-language parsing   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Pydantic Schema        │
│     Output validation        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│    Deterministic Safety      │
│          Rules               │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│ Date        │  │ Priority     │
│ Resolution  │  │ Calculation  │
└──────┬──────┘  └──────┬───────┘
       └───────┬────────┘
               ▼
┌──────────────────────────────┐
│      Local JSON Storage      │
│       planner_data.json      │
└──────────────────────────────┘
```

## Responsibility boundaries

### Strands Agent

Coordinates the language-model extraction step.

### Llama 3.2

Interprets unstructured natural-language input.

### Pydantic

Validates that the extracted structure matches the expected application schema.

### Deterministic Python

Handles rules where the system should not rely on probabilistic model behavior.

### Local storage

Provides persistence without requiring cloud credentials.

## AWS relationship

Strands Agents is the AWS open-source component used by this project.

The application currently runs locally:

```text
Strands Agents
       +
Ollama / Llama 3.2
       +
Local Python application
```

Cloud services such as Bedrock, Lambda, DynamoDB, and S3 are deliberately not required for the current prototype.
