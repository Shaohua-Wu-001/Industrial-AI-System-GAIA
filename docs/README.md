# docs/

**Analysis Reports and Optimization Logs**

This directory contains technical reports documenting system performance, parser behavior analysis, and iterative optimization results across the GAIA task suite.

---

## Contents

| Document | Description |
|---|---|
| `gaia_l3_analysis.md` | In-depth analysis of Level 3 task execution patterns, failure modes, and bottlenecks |
| `parser_parameter_check_report.md` | Audit of Parser v5 parameter validation -- coverage, false positives, edge cases |
| `improvement_optimization_report.md` | Log of iterative improvements to parser accuracy and executor throughput |
| `109_task_summary_report.md` | Aggregate statistics and per-task breakdowns for all 109 integrated GAIA tasks |

---

## Report Summaries

### GAIA L3 Analysis

Examines the 21 Level 3 tasks, which represent the most challenging subset of the benchmark. Key findings:

- Average DAG depth: 6.2 steps (vs. 2.1 for L1)
- Most common failure mode: incorrect dependency inference at the semantic layer
- Tool categories most frequently involved: file readers, web search, Python executor
- Recommendations for parser improvements that informed the v3.1 and v5 iterations

### Parser Parameter Check Report

Systematic audit of the parameter validation module introduced in Parser v5:

- Coverage: 94% of tool parameters checked before execution
- False positive rate: 3.2% (parameters flagged as missing but actually optional)
- Identified 7 tool schemas with ambiguous parameter specifications
- Led to schema corrections in the unified tool definitions

### Improvement and Optimization Report

Chronological log of optimizations applied to the pipeline:

- Dependency inference accuracy: 78% (v3) to 94% (v5)
- Orphan node rate: 20% (v3) to 2.6% (v5 + augmentation)
- Executor timeout reduction: 15s to 2s per-directory budget
- End-to-end validation rate progression across parser versions

### 109-Task Summary Report

Comprehensive statistics across all integrated tasks:

- 17,661 total steps (426 tool invocations, 17,235 reasoning steps)
- Breakdown by level, tool type, and step category
- Per-task execution time distribution
- Validation results: 100% pass rate on gold answers

---

## Usage

These documents are standalone Markdown files intended for human review. No scripts or build steps are required.

```bash
# View a report
less docs/gaia_l3_analysis.md

# Or open in any Markdown viewer
open docs/109_task_summary_report.md
```

---

## Contributing

When adding new reports to this directory:

1. Use Markdown format with clear section headings
2. Include quantitative results in tables where possible
3. Reference specific task IDs when discussing individual examples
4. Date the report in the document header
