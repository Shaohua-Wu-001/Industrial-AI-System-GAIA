# Industrial-AI-System-GAIA

**Automated Planning and Execution Framework for Industrial-Scale LLM Reasoning**

A research framework developed in collaboration between [Academia Sinica (CITI)](https://www.citi.sinica.edu.tw/) and [Delta Electronics](https://www.deltaww.com/) for automated data synthesis, DAG-based task planning, and LLM execution pipelines. Built around the [GAIA benchmark](https://huggingface.co/datasets/gaia-benchmark/GAIA) for evaluating general AI assistants on real-world, multi-step reasoning tasks.

---

## Overview

This system addresses the challenge of decomposing complex, multi-step questions into structured execution plans that coordinate dozens of heterogeneous tools. The core contributions include:

- **DAG-based task planning** -- decompose natural language queries into directed acyclic graphs of tool invocations and reasoning steps
- **Parser v5 pipeline** -- fifth-generation planner with dependency inference, parameter checking, and strategic execution ordering
- **Data synthesis engine** -- augmentation pipeline that converts linear chains to DAGs and generates diverse training samples
- **Answer validation** -- automated verification of execution outputs against gold-standard answers across 109 integrated tasks

### Key Results

| Metric | Value |
|---|---|
| Integrated GAIA tasks | 109 (L1: 38, L2: 50, L3: 21) |
| Total execution steps | 17,661 (426 tool + 17,235 reasoning) |
| Validation rate | 100% |
| Unified tools | 50+ |
| Parser lineage | v2.1 &rarr; v3 &rarr; v3.1 &rarr; v5 |

---

## Repository Structure

```
Industrial-AI-System-GAIA/
|
|-- integrated_109/        # Integrated 109 GAIA tasks with validation results
|-- data_synthesis/        # Data augmentation and chain-to-DAG conversion
|-- v5_original/           # Original GAIA Level 3 tasks and Parser v5 outputs
|-- ta_99_tasks/           # 99 TA-provided GAIA tasks (L1: 38, L2: 50, L3: 11)
|-- tools/                 # Unified tool schema definitions (50+ tools)
|-- archive/               # Legacy parsers (v2.1, v3, v3.1) and executors
|-- docs/                  # Analysis reports and optimization logs
|-- data/                  # Task attachments (PDF, Excel, XML, ZIP, JSONLD)
|-- answer_validation_charts/  # Validation result visualizations
|-- *.py                   # Root-level pipeline and utility scripts
```

Each subdirectory contains its own README with detailed documentation.

---

## Architecture

The system follows a three-stage pipeline:

```
Query --> [Parser v5] --> DAG Plan --> [Executor] --> Tool Outputs --> [Validator] --> Answer
              |                            |
              v                            v
     Dependency Inference          50+ Unified Tools
     Parameter Checking            (web, code, file, ...)
     Step Ordering
```

**Parser v5** applies a layered dependency inference strategy:

1. **Placeholder** -- explicit `{step_N_result}` references
2. **Parameter** -- output-to-input type matching
3. **Semantic** -- natural language dependency signals
4. **Sequential** -- fallback linear ordering

**Executor** dispatches each DAG node to the appropriate tool, manages intermediate state, and handles retries and timeouts.

**Validator** compares execution outputs against gold answers using type-aware matching (exact, numeric tolerance, set equivalence, substring).

---

## Quick Start

### Prerequisites

- Python 3.9+
- Access to an LLM API (OpenAI, Anthropic, or compatible endpoint)

### Installation

```bash
git clone https://github.com/<org>/Industrial-AI-System-GAIA.git
cd Industrial-AI-System-GAIA
pip install -r requirements.txt
```

### Running the Pipeline

```bash
# Execute a single GAIA task
python run_pipeline.py --task_id <TASK_ID> --level 3

# Run validation on all 109 integrated tasks
python validate_all.py --input integrated_109/ --output results/

# Generate augmented training data
python data_synthesis/data_augmentation.py --input data/ --output augmented/
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| LLM Backend | OpenAI API / Anthropic API |
| Planning | DAG construction, topological sort |
| Tools | 50+ unified schemas (web, code, file I/O, math, NLP) |
| Data Formats | JSON, JSONL, CSV, PDF, Excel, XML, JSONLD |
| Visualization | Matplotlib, Plotly (validation charts) |

---

## Task Distribution

```
Level 1 (L1):  38 tasks  --  single-tool, direct retrieval
Level 2 (L2):  50 tasks  --  multi-tool, moderate reasoning
Level 3 (L3):  21 tasks  --  complex multi-step, cross-domain
```

Level 3 tasks typically require 5-15 tool invocations with non-trivial dependency graphs, making them the primary stress test for the planning and execution pipeline.

---

## Citation

If you use this framework in your research, please cite:

```bibtex
@misc{industrial-ai-gaia,
  title   = {Industrial-AI-System-GAIA: Automated Planning and Execution for Industrial-Scale LLM Reasoning},
  author  = {Academia Sinica CITI and Delta Electronics},
  year    = {2025},
  url     = {https://github.com/<org>/Industrial-AI-System-GAIA}
}
```

---

## License

This project is developed for research purposes. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [GAIA Benchmark](https://huggingface.co/datasets/gaia-benchmark/GAIA) -- Meta AI
- [Academia Sinica CITI](https://www.citi.sinica.edu.tw/)
- [Delta Electronics Research Center](https://www.deltaww.com/)
