# v5_original/

**Original GAIA Level 3 Tasks and Parser v5 Outputs**

The foundational 10 Level 3 tasks from the GAIA benchmark, processed through Parser v5 with full validation. These tasks represent the most challenging tier of the benchmark and served as the primary development testbed for the parser.

---

## Overview

This directory contains the original 10 GAIA Level 3 tasks that were used to develop and validate Parser v5. Each task involves complex, multi-hop reasoning across heterogeneous tools, requiring the parser to construct accurate dependency graphs with 5-15 nodes.

These tasks are distinct from the broader 109-task integrated set in `/integrated_109` and the 99 TA-provided tasks in `/ta_99_tasks`.

---

## Directory Structure

```
v5_original/
|-- tasks/                    # 10 Level 3 task definitions (JSON)
|-- parser_v5_output/         # Generated DAG plans for each task
|-- validation/               # Answer validation results
|-- answer_validator_v5.py    # Validation script (v5-specific logic)
|-- test_parser.py            # Unit and integration tests for Parser v5
|-- analyze_results.py        # Generate analysis reports from validation output
|-- README.md
```

---

## Task Characteristics

All 10 tasks are Level 3, meaning they require:

- Multiple tool invocations (5-15 per task)
- Non-trivial dependency graphs (branching, merging)
- Cross-domain reasoning (e.g., read PDF, compute statistics, search web, synthesize)
- Precise intermediate state management

| Task ID | Tools Required | DAG Depth | DAG Width | Steps |
|---|---|---|---|---|
| L3_001 | 4 | 6 | 3 | 14 |
| L3_002 | 5 | 8 | 2 | 18 |
| L3_003 | 3 | 5 | 2 | 11 |
| L3_004 | 6 | 7 | 4 | 22 |
| L3_005 | 4 | 6 | 2 | 13 |
| L3_006 | 5 | 9 | 3 | 21 |
| L3_007 | 3 | 5 | 2 | 10 |
| L3_008 | 7 | 10 | 3 | 27 |
| L3_009 | 4 | 6 | 2 | 15 |
| L3_010 | 5 | 7 | 3 | 19 |

---

## Parser v5 Output

For each task, Parser v5 produces a DAG plan stored in JSON:

```json
{
  "task_id": "L3_001",
  "parser_version": "v5",
  "plan": {
    "nodes": [
      {
        "step_id": 1,
        "tool": "pdf_reader",
        "parameters": {"file_path": "data/annual_report.pdf"},
        "dependencies": [],
        "reasoning": "Extract financial data from the attached report"
      }
    ],
    "edges": [[1, 2], [1, 3], [2, 4], [3, 4]]
  },
  "metadata": {
    "total_steps": 14,
    "tool_steps": 6,
    "reasoning_steps": 8,
    "inference_layers_used": ["placeholder", "parameter", "semantic"]
  }
}
```

---

## Answer Validator v5

`answer_validator_v5.py` implements validation tailored to Level 3 outputs, which often involve complex answer types (lists, computed values, multi-part responses).

```bash
# Validate a single task
python v5_original/answer_validator_v5.py \
  --task v5_original/tasks/L3_001.json \
  --prediction results/L3_001_output.json

# Validate all 10 tasks
python v5_original/answer_validator_v5.py \
  --task_dir v5_original/tasks/ \
  --prediction_dir results/ \
  --output v5_original/validation/
```

Supported match types:

| Type | Description |
|---|---|
| `exact` | Normalized string equality |
| `numeric` | Numeric comparison with tolerance (default: 0.01) |
| `set` | Unordered set equivalence |
| `list` | Ordered list comparison |
| `substring` | Gold answer contained in prediction |
| `semantic` | LLM-judged equivalence (fallback) |

---

## Testing

`test_parser.py` provides both unit tests for individual parser components and integration tests that run full task-to-plan generation.

```bash
# Run all tests
python -m pytest v5_original/test_parser.py -v

# Run only integration tests
python -m pytest v5_original/test_parser.py -v -k "integration"
```

---

## Analysis

`analyze_results.py` generates summary statistics and per-task breakdowns from validation output.

```bash
python v5_original/analyze_results.py \
  --input v5_original/validation/ \
  --output v5_original/reports/
```

---

## Notes

- These 10 tasks are included in the 109-task integrated set (`/integrated_109`) but are preserved here in their original form for reproducibility.
- Parser v5 was developed iteratively against these tasks. The `/archive` directory contains earlier parser versions (v2.1, v3, v3.1) for comparison.
- Task attachments are stored in `/data` at the repository root.
