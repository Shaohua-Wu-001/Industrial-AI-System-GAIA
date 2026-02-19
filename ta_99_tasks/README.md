# ta_99_tasks/

**99 GAIA Tasks from Teaching Assistant Annotations**

A curated set of 99 tasks sourced from the GAIA inference dataset, annotated by teaching assistants with structured metadata, tool environments, and gold-standard answers.

---

## Overview

These tasks were extracted from the GAIA benchmark inference split and formatted for use with the project's execution pipeline. Each task includes a natural language query, a predefined tool environment, and a verified gold answer.

### Level Distribution

| Level | Count | Description |
|---|---|---|
| L1 | 38 | Single-tool, direct retrieval |
| L2 | 50 | Multi-tool, moderate reasoning chains |
| L3 | 11 | Complex multi-hop, cross-domain reasoning |
| **Total** | **99** | |

---

## Data Format

Tasks are stored in JSONL format (one JSON object per line):

```json
{
  "task_id": "ta_001",
  "level": 2,
  "meta": {
    "source": "gaia_inference",
    "annotator": "TA",
    "difficulty": "medium"
  },
  "query": "Find the population of the capital city mentioned in the attached document.",
  "tool_environment": [
    "web_search",
    "pdf_reader",
    "python_executor"
  ],
  "gold_answer": "8,336,817",
  "attachments": []
}
```

### Field Descriptions

| Field | Type | Description |
|---|---|---|
| `task_id` | string | Unique identifier |
| `level` | int | GAIA difficulty level (1, 2, or 3) |
| `meta` | object | Source, annotator, and difficulty metadata |
| `query` | string | Natural language question |
| `tool_environment` | array | List of tools available for this task |
| `gold_answer` | string | Verified correct answer |
| `attachments` | array | Paths to any attached files |

---

## Available Tools

The tool environment for these tasks draws from 16 predefined tools:

| Tool | Category | Description |
|---|---|---|
| `web_search` | Retrieval | Search the web for information |
| `python_executor` | Computation | Execute Python code snippets |
| `pdf_reader` | File I/O | Extract text from PDF documents |
| `excel_reader` | File I/O | Read and parse Excel spreadsheets |
| `csv_reader` | File I/O | Parse CSV files |
| `image_reader` | File I/O | Extract text/data from images (OCR) |
| `json_reader` | File I/O | Parse JSON/JSONLD files |
| `xml_reader` | File I/O | Parse XML documents |
| `text_reader` | File I/O | Read plain text files |
| `calculator` | Computation | Evaluate mathematical expressions |
| `unit_converter` | Computation | Convert between units |
| `date_calculator` | Computation | Date arithmetic and formatting |
| `string_processor` | Text | String manipulation (regex, split, etc.) |
| `translator` | Text | Translate between languages |
| `summarizer` | Text | Summarize long documents |
| `reasoning` | Logic | Multi-step logical reasoning |

---

## Directory Structure

```
ta_99_tasks/
|-- tasks.jsonl              # All 99 tasks in JSONL format
|-- tasks/                   # Individual task JSON files (optional)
|-- tool_definitions/        # Tool schemas used by these tasks
|-- README.md
```

---

## Usage

### Load tasks

```python
import json

tasks = []
with open("ta_99_tasks/tasks.jsonl", "r") as f:
    for line in f:
        tasks.append(json.loads(line.strip()))

print(f"Loaded {len(tasks)} tasks")
# Loaded 99 tasks
```

### Filter by level

```python
l3_tasks = [t for t in tasks if t["level"] == 3]
print(f"Level 3 tasks: {len(l3_tasks)}")
# Level 3 tasks: 11
```

### Run through the pipeline

```bash
python run_pipeline.py --input ta_99_tasks/tasks.jsonl --output results/ta99/
```

---

## Notes

- These tasks are a subset of the full GAIA inference dataset; they do not overlap with the 10 original Level 3 tasks in `/v5_original`.
- Tool environments are task-specific: not all 16 tools are available for every task.
- Gold answers have been verified by at least one annotator and cross-checked against GAIA reference answers.
