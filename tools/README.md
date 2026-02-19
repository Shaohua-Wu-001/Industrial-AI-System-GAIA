# tools/

**Unified Tool Schema Definitions**

Centralized registry of 50+ tool definitions used across the GAIA execution pipeline. Merges TA-provided tool schemas with custom-built tools into a single, consistent format.

---

## Overview

The GAIA pipeline orchestrates dozens of heterogeneous tools -- from web search and code execution to specialized file parsers and statistical analyzers. This directory maintains the canonical schema for every tool, ensuring consistent parameter naming, type checking, and documentation across the system.

### Tool Inventory

| Category | TA Tools | Custom Tools | Total |
|---|---|---|---|
| File I/O | 7 | 5 | 12 |
| Computation | 3 | 8 | 11 |
| Data Processing | 2 | 7 | 9 |
| Text Processing | 2 | 6 | 8 |
| Retrieval | 1 | 4 | 5 |
| Statistical Analysis | 0 | 4 | 4 |
| Conversion | 1 | 2 | 3 |
| **Total** | **16** | **~36** | **~52** |

---

## Schema Format

Each tool is defined as a JSON object following a consistent schema:

```json
{
  "tool_name": "pdf_reader",
  "category": "file_io",
  "description": "Extract text content from a PDF document.",
  "parameters": [
    {
      "name": "file_path",
      "type": "string",
      "required": true,
      "description": "Path to the PDF file"
    },
    {
      "name": "pages",
      "type": "string",
      "required": false,
      "description": "Page range to extract (e.g., '1-5', '3,7,10')"
    }
  ],
  "returns": {
    "type": "string",
    "description": "Extracted text content"
  },
  "source": "ta",
  "aliases": ["read_pdf", "parse_pdf"]
}
```

---

## Tool Categories

### File I/O

Read and parse various file formats.

| Tool | Formats | Source |
|---|---|---|
| `pdf_reader` | PDF | TA |
| `excel_reader` | XLSX, XLS | TA |
| `csv_reader` | CSV, TSV | TA |
| `json_reader` | JSON, JSONL, JSONLD | TA |
| `xml_reader` | XML | TA |
| `text_reader` | TXT, LOG, MD | TA |
| `image_reader` | PNG, JPG (OCR) | TA |
| `zip_extractor` | ZIP, TAR, GZ | Custom |
| `html_parser` | HTML | Custom |
| `yaml_reader` | YAML | Custom |
| `docx_reader` | DOCX | Custom |
| `pptx_reader` | PPTX | Custom |

### Computation

Execute code and evaluate expressions.

| Tool | Description | Source |
|---|---|---|
| `python_executor` | Run Python code in a sandboxed environment | TA |
| `calculator` | Evaluate mathematical expressions | TA |
| `unit_converter` | Convert between measurement units | TA |
| `regex_evaluator` | Test and apply regular expressions | Custom |
| `date_calculator` | Date arithmetic and formatting | Custom |
| `statistics_calculator` | Descriptive statistics (mean, median, std) | Custom |
| `matrix_calculator` | Matrix operations | Custom |
| `equation_solver` | Symbolic equation solving | Custom |

### Data Processing

Transform and aggregate structured data.

| Tool | Description | Source |
|---|---|---|
| `data_filter` | Filter rows by condition | Custom |
| `data_aggregator` | Group-by and aggregate operations | Custom |
| `data_sorter` | Sort by one or more columns | Custom |
| `data_merger` | Join/merge multiple datasets | Custom |
| `pivot_table` | Pivot and unpivot operations | Custom |
| `deduplicator` | Remove duplicate records | Custom |
| `schema_validator` | Validate data against a schema | Custom |

### Text Processing

String manipulation and NLP operations.

| Tool | Description | Source |
|---|---|---|
| `string_processor` | Regex, split, replace, format | TA |
| `translator` | Language translation | TA |
| `summarizer` | Document summarization | Custom |
| `entity_extractor` | Named entity recognition | Custom |
| `sentiment_analyzer` | Sentiment classification | Custom |
| `keyword_extractor` | Extract key terms from text | Custom |
| `text_comparator` | Diff and similarity scoring | Custom |
| `tokenizer` | Text tokenization and counting | Custom |

### Retrieval

Fetch information from external sources.

| Tool | Description | Source |
|---|---|---|
| `web_search` | General web search | TA |
| `url_fetcher` | Fetch content from a URL | Custom |
| `api_caller` | Make HTTP API requests | Custom |
| `database_query` | Execute SQL queries | Custom |
| `knowledge_lookup` | Query a knowledge base | Custom |

---

## Merging Strategy

When TA tools and custom tools overlap in functionality, the following merge rules apply:

1. **TA schema takes precedence** for parameter naming and types
2. **Custom extensions** are added as optional parameters
3. **Aliases** map legacy or alternative names to the canonical tool name
4. **Deprecation** -- superseded tools are moved to `/archive` with a redirect note

```bash
# Extract and merge schemas from multiple sources
python tools/merge_schemas.py \
  --ta tools/ta_definitions/ \
  --custom tools/custom_definitions/ \
  --output tools/unified_schema.json
```

---

## Directory Structure

```
tools/
|-- unified_schema.json       # Merged schema for all 50+ tools
|-- ta_definitions/           # Original 16 TA tool schemas
|-- custom_definitions/       # 35+ custom tool schemas
|-- merge_schemas.py          # Schema merging script
|-- extract_schemas.py        # Extract schemas from code annotations
|-- validate_schemas.py       # Schema consistency checker
|-- README.md
```

---

## Usage

### Load the unified schema

```python
import json

with open("tools/unified_schema.json", "r") as f:
    tools = json.load(f)

print(f"Total tools: {len(tools)}")
for tool in tools:
    print(f"  {tool['tool_name']} ({tool['category']})")
```

### Validate all schemas

```bash
python tools/validate_schemas.py --schema tools/unified_schema.json
```

### Extract schemas from annotated source code

```bash
python tools/extract_schemas.py --source src/ --output tools/custom_definitions/
```

---

## Notes

- The Parser v5 parameter checker uses `unified_schema.json` to validate tool inputs at plan time, before execution begins.
- Tool availability is task-specific. Not all 50+ tools are exposed to every task; the `tool_environment` field in each task definition controls which tools the executor may invoke.
