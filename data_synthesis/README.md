# data_synthesis/

**Data Augmentation and DAG Generation Pipeline**

Automated pipeline for converting linear tool-call chains into dependency-aware DAGs and generating diverse augmented training samples. Designed to expand small seed datasets into larger, structurally varied collections suitable for training and evaluating LLM-based planners.

---

## Overview

Real-world GAIA task plans are expensive to annotate manually. This module addresses data scarcity through two mechanisms:

1. **Chain-to-DAG conversion** -- infer true dependency structure from sequential plans, exposing parallelism
2. **Data augmentation** -- apply 10 transformation strategies to produce structurally diverse variants

### Results

| Metric | Before | After | Change |
|---|---|---|---|
| Sample count | 42 | 77 | +83% |
| Structural diversity | 21.4% | 26.0% | +22% |
| Orphan node rate | 20.0% | 2.6% | -87% |

---

## Architecture

```
Sequential Chain
    |
    v
[chain_to_dag.py]  -- 4-layer dependency inference
    |
    v
Structured DAG
    |
    v
[data_augmentation.py]  -- 10 augmentation strategies
    |
    v
Augmented DAG Variants
    |
    v
[toolscale_generator.py]  -- ToolScale format export
    |
    v
Training Dataset (JSONL)
```

---

## Chain-to-DAG Conversion

`chain_to_dag.py` transforms a linear sequence of steps into a DAG by inferring dependencies through four layers, applied in priority order:

| Priority | Layer | Signal | Example |
|---|---|---|---|
| 1 | Placeholder | Explicit `{step_N_result}` references | Step 3 uses `{step_1_result}` as input |
| 2 | Parameter | Output type matches next input type | `url` output feeds `fetch_url` input |
| 3 | Semantic | NLP-based dependency detection | "summarize the above" implies prior step |
| 4 | Sequential | Fallback linear ordering | No signal detected; preserve original order |

Higher-priority layers take precedence. The result is a DAG where independent steps can execute in parallel while true dependencies are preserved.

```bash
python chain_to_dag.py --input chains.jsonl --output dags.jsonl
```

---

## Augmentation Strategies

`data_augmentation.py` implements 10 transformation strategies:

| # | Strategy | Description |
|---|---|---|
| 1 | Add reasoning step | Insert an explicit reasoning node before tool calls |
| 2 | Remove optional step | Drop steps not on the critical path |
| 3 | Simplify plan | Merge consecutive same-tool calls |
| 4 | Tool substitution | Replace a tool with a functionally equivalent alternative |
| 5 | Reorder parallel branches | Shuffle independent branches |
| 6 | Split compound step | Decompose multi-action steps into atomic nodes |
| 7 | Add error handling | Insert retry/fallback nodes |
| 8 | Parameter variation | Alter non-critical parameters (e.g., search query phrasing) |
| 9 | Branch duplication | Duplicate a branch with a different tool path |
| 10 | Depth adjustment | Flatten or deepen the DAG structure |

Each strategy preserves semantic correctness: the augmented plan must produce the same final answer as the original.

```bash
python data_augmentation.py \
  --input dags.jsonl \
  --output augmented.jsonl \
  --strategies all \
  --max_variants 3
```

---

## ToolScale Format Export

`toolscale_generator.py` converts augmented DAGs into the [ToolScale](https://github.com/ToolScale) dataset format for compatibility with external benchmarks and training pipelines.

```bash
python toolscale_generator.py --input augmented.jsonl --output toolscale_dataset/
```

---

## Scripts

| File | Purpose |
|---|---|
| `chain_to_dag.py` | Convert linear chains to DAGs via 4-layer inference |
| `data_augmentation.py` | Apply 10 augmentation strategies to DAG plans |
| `toolscale_generator.py` | Export to ToolScale-compatible format |

---

## Configuration

Key parameters in each script can be adjusted via command-line flags or a shared config file:

```yaml
# config.yaml (example)
chain_to_dag:
  semantic_threshold: 0.7    # NLP similarity threshold for layer 3
  allow_orphans: false       # Require all nodes to have at least one edge

augmentation:
  max_variants_per_sample: 3
  strategies: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  preserve_critical_path: true

toolscale:
  format_version: "1.0"
  include_metadata: true
```
