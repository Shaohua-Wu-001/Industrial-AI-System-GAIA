# archive/

**Legacy Parsers, Executors, and Historical Artifacts**

This directory preserves earlier iterations of the planning and execution pipeline. These versions are retained for reproducibility and to document the evolution of the system architecture.

---

## Version History

| Version | Component | Description |
|---|---|---|
| v2.1 | Parser | Initial chain-based planner; linear step sequences only |
| v3 | Parser | Introduced DAG support and basic dependency inference |
| v3 | Executor | First executor with parallel node dispatch |
| v3.1 | Parser | Bugfix release -- corrected cycle detection and parameter passing |
| v3.2 | Executor | Improved retry logic and timeout handling |
| v5 | Parser (old) | Early draft of v5 before refactoring into current pipeline |

### Evolution Timeline

```
v2.1 (chain-only)
  |
  v
v3 (DAG support)
  |
  +--> v3.1 (parser bugfix)
  |
  +--> v3.2 (executor improvements)
  |
  v
v5 (current -- moved to /v5_original and root pipeline)
```

---

## Directory Contents

```
archive/
|-- parser_v2.1/           # Chain-based parser, linear plans only
|-- parser_v3/             # First DAG-capable parser
|-- parser_v3.1/           # Bugfix: cycle detection, parameter edge cases
|-- parser_v5_old/         # Early v5 draft (superseded)
|-- executor_v3/           # Parallel executor, basic retry
|-- executor_v3.2/         # Enhanced timeout and error handling
|-- data/                  # Historical test data and intermediate outputs
|-- tests/                 # Legacy test scripts for validation
```

---

## Key Differences Across Versions

### Parser

| Feature | v2.1 | v3 | v3.1 | v5 |
|---|:---:|:---:|:---:|:---:|
| Linear chain plans | Yes | Yes | Yes | Yes |
| DAG plans | -- | Yes | Yes | Yes |
| Dependency inference | -- | Basic | Basic | 4-layer |
| Cycle detection | -- | -- | Yes | Yes |
| Parameter type checking | -- | -- | Partial | Full |
| Strategic ordering | -- | -- | -- | Yes |

### Executor

| Feature | v3 | v3.2 |
|---|:---:|:---:|
| Parallel dispatch | Yes | Yes |
| Retry on failure | Basic | Configurable |
| Per-tool timeout | -- | Yes (2s budget) |
| State management | In-memory | In-memory + checkpoint |

---

## Usage

These modules are not actively maintained. To run legacy versions for comparison:

```bash
# Run parser v3 on a sample task
python archive/parser_v3/parse.py --input sample_task.json

# Run executor v3.2
python archive/executor_v3.2/execute.py --plan plan.json --tools tools/
```

---

## Notes

- The current production pipeline lives at the repository root and in `/v5_original`.
- Legacy data files may reference tool schemas that have since been renamed or merged. See `/tools/` for the current unified schema.
- Test scripts in this directory may have broken imports due to restructuring. They are preserved as-is for historical reference.
