import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict

# 工具 Schema 定義 (43 種工具)

TOOL_SCHEMAS = {
    # File Operations (10 種)
    'read_pdf': {'required': ['file_path'], 'optional': ['page_numbers']},
    'read_csv': {'required': ['file_path'], 'optional': ['encoding']},
    'read_excel': {'required': ['file_path'], 'optional': ['sheet_name']},
    'read_json': {'required': ['file_path'], 'optional': ['encoding']},
    'read_xml': {'required': ['file_path'], 'optional': ['encoding']},
    'read_text_file': {'required': ['file_path'], 'optional': ['encoding']},
    'read_docx': {'required': ['file_path'], 'optional': []},
    'read_image': {'required': ['file_path'], 'optional': []},
    'extract_zip': {'required': ['zip_path'], 'optional': ['extract_to', 'password']},
    'image_to_text': {'required': ['file_path'], 'optional': ['lang']},
    
    # Web Operations (3 種)
    'web_search': {'required': ['query'], 'optional': ['num_results']},
    'web_fetch': {'required': ['url'], 'optional': ['timeout']},
    'wikipedia_search': {'required': ['query'], 'optional': ['language', 'sentences']},
    
    # Data Processing (15 種)
    'filter_data': {'required': ['data', 'conditions'], 'optional': []},
    'compare_values': {'required': ['value1', 'value2'], 'optional': ['comparison', 'tolerance']},
    'find_in_text': {'required': ['text', 'search_terms'], 'optional': ['context_chars', 'max_results']},
    'count_occurrences': {'required': ['data', 'target'], 'optional': ['case_sensitive', 'count_type']},
    'extract_information': {'required': ['text', 'extract_type'], 'optional': ['keywords', 'pattern']},
    'deduplicate_data': {'required': ['data'], 'optional': ['key_fields']},
    'join_data': {'required': ['data1', 'data2', 'join_key'], 'optional': ['join_type']},
    'sort_data': {'required': ['data', 'sort_by'], 'optional': ['reverse']},
    'aggregate_data': {'required': ['data', 'group_by', 'aggregate_field'], 'optional': ['operation']},
    'pivot_table': {'required': ['data', 'index', 'values'], 'optional': ['aggfunc']},
    'fill_missing': {'required': ['data', 'columns'], 'optional': ['method']},
    'sample_data': {'required': ['data', 'n'], 'optional': ['random_seed']},
    'compare_data': {'required': ['data1', 'data2'], 'optional': ['comparison_type']},
    'list_operations': {'required': ['list1', 'operation'], 'optional': ['list2']},
    'validate_data': {'required': ['data', 'rules'], 'optional': []},
    
    # Calculation & Conversion (8 種)
    'calculate': {'required': ['expression'], 'optional': []},
    'unit_converter': {'required': ['value', 'from_unit', 'to_unit'], 'optional': ['unit_type']},
    'currency_converter': {'required': ['amount', 'from_currency', 'to_currency'], 'optional': []},
    'date_calculator': {'required': ['start_date'], 'optional': ['days_to_add', 'end_date', 'date_format']},
    'statistical_analysis': {'required': ['data', 'metrics'], 'optional': []},
    'correlation_analysis': {'required': ['data', 'x_column', 'y_column'], 'optional': ['method']},
    'moving_average': {'required': ['data', 'window_size'], 'optional': []},
    'geocoding': {'required': ['location', 'return_info'], 'optional': []},
    
    # Text Operations (7 種)
    'regex_search': {'required': ['text', 'pattern'], 'optional': ['return_all']},
    'string_transform': {'required': ['text', 'operation'], 'optional': []},
    'encode_decode': {'required': ['text', 'operation'], 'optional': []},
    'split_join_text': {'required': ['text', 'operation'], 'optional': ['separator']},
    'create_csv': {'required': ['data', 'filename'], 'optional': ['include_header']},
    'create_markdown': {'required': ['title', 'sections'], 'optional': ['filename']},
    'analyze_image': {'required': ['file_path'], 'optional': []},
}

# 支援的 unit_type
VALID_UNIT_TYPES = ['length', 'weight', 'volume', 'temperature', 'time', 'pressure']

# 參數名稱映射（錯誤 -> 正確）
PARAM_NAME_MAPPING = {
    'extract_information': {
        'target': 'keywords',
    },
    'deduplicate_data': {
        'key': 'key_fields',
    },
}


# ============================================================
# 資料結構
# ============================================================

@dataclass
class ParsedStep:
    step_number: int
    original_text: str
    tool_name: Optional[str]
    arguments: Dict[str, Any]
    confidence: int  # 0-3
    intent_category: str
    extraction_method: str
    notes: List[str] = field(default_factory=list)
    is_reasoning: bool = False
    executable: bool = True
    skip_reason: Optional[str] = None
    
    def to_dict(self):
        return {
            'step_id': f'step_{self.step_number}',
            'original_text': self.original_text,
            'tool_name': self.tool_name,
            'arguments': self.arguments,
            'confidence': self.confidence,
            'intent_category': self.intent_category,
            'extraction_method': self.extraction_method,
            'notes': self.notes,
            'is_reasoning': self.is_reasoning,
            'executable': self.executable,
            'skip_reason': self.skip_reason,
            'description': self.original_text[:200]
        }


@dataclass
class ParsingContext:
    downloaded_files: List[str] = field(default_factory=list)
    fetched_urls: List[str] = field(default_factory=list)
    data_sources: Dict[int, str] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    last_calculation: Optional[str] = None
    last_data_operation: Optional[str] = None
    opened_files: List[str] = field(default_factory=list)
    recent_searches: List[str] = field(default_factory=list)


# ============================================================
# Phase 1: 推理過濾器 (from v2.1)
# ============================================================

class ReasoningFilterV5:    
    # 純推理動詞
    REASONING_VERBS = {
        'fix', 'fixes', 'fixed', 'fixing',
        'see', 'sees', 'saw', 'seeing',
        'when', 'if', 'as',
        'note', 'noted', 'noting', 'notes',
        'check', 'checked', 'checking', 'checks',
        'verify', 'verified', 'verifying', 'verifies',
        'confirm', 'confirmed', 'confirming', 'confirms',
        'determine', 'determined', 'determining', 'determines',
        'conclude', 'concluded', 'concluding', 'concludes',
        'round', 'rounded', 'rounding', 'rounds',
        'consider', 'considered', 'considering', 'considers',
        'assume', 'assumed', 'assuming', 'assumes',
    }
    
    # UI 操作動詞（已移除 'click'）
    UI_VERBS = {
        'scroll', 'scrolled', 'scrolling', 'scrolls',
        'navigate', 'navigated', 'navigating', 'navigates',
        'watch', 'watched', 'watching', 'watches',
        'listen', 'listened', 'listening', 'listens',
    }
    
    # 狀態記錄模式
    STATE_PATTERNS = [
        r'\(running tally:?\s*\d+/\d+\)',
        r'\d+/\d+\s*(?:updated|not updated)',
        r'noted?\s+its\s+',
        r'repeated?\s+steps?\s+\d+',
        r'repeat(?:ed)?\s+(?:the\s+)?(?:steps?|process|procedure)',
    ]
    
    @classmethod
    def is_reasoning(cls, text: str) -> bool:
        text_lower = text.lower().strip()
        first_word = text_lower.split()[0] if text_lower.split() else ''
        
        # 檢查首字是否為推理動詞
        if first_word in cls.REASONING_VERBS:
            return True
        
        # 檢查是否為 UI 操作
        if first_word in cls.UI_VERBS:
            return True
        
        # 檢查狀態記錄模式
        for pattern in cls.STATE_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        # 檢查是否為條件句
        if text_lower.startswith(('when ', 'if ', 'as ')):
            return True
        
        # 檢查是否為數學推理
        if '"fix"' in text_lower and ('column' in text_lower or 'number' in text_lower):
            return True
        
        # 檢查 "we checked" 模式
        if text_lower.startswith('we ') and any(v in text_lower for v in ['checked', 'found', 'verified']):
            return True
        
        return False


# ============================================================
# Phase 2: Placeholder & URL 驗證器 (from v3)
# ============================================================

class ValidationUtilsV5:
    
    PLACEHOLDER_PATTERNS = [
        r'^<.*>$',              # <anything>
        r'<from_context>',      # <from_context>
        r'<iterate:',           # <iterate:something>
        r'<clicked:',           # <clicked:something>
        r'<link_in:',           # <link_in:something>
        r'<result:',            # <result:something>
        r'<multiple:',          # <multiple:something>
        r'<infer>',             # <infer>
        r'<new_tab>',           # <new_tab>
        r'<page:',              # <page:something>
        r'<followed:',          # <followed:something>
        r'<conversion_constant>',
    ]
    
    @staticmethod
    def is_placeholder(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        
        for pattern in ValidationUtilsV5.PLACEHOLDER_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        if ValidationUtilsV5.is_placeholder(url):
            return False
        
        # 必須以 http:// 或 https:// 開頭
        if not url.startswith(('http://', 'https://')):
            return False
        
        # 不能包含 placeholder 標記
        if '<' in url or '>' in url:
            return False
        
        return True
    
    @staticmethod
    def is_valid_file_path(file_path: str, data_dir: Path) -> bool:
        if ValidationUtilsV5.is_placeholder(file_path):
            return False
        
        # 檢查多個可能的路徑
        paths_to_check = [
            Path(file_path),
            data_dir / file_path,
            data_dir / Path(file_path).name,
        ]
        
        for path in paths_to_check:
            if path.exists() and path.is_file():
                return True
        
        return False
    
    @staticmethod
    def clean_calculate_expression(expression: str) -> Optional[str]:
        if ValidationUtilsV5.is_placeholder(expression):
            return None
        
        # 移除單位 (g/mol, L-atm, K-mol 等)
        cleaned = re.sub(r'\s*[a-zA-Z]+(/[a-zA-Z]+)*', '', expression)
        
        # 移除 %
        cleaned = cleaned.replace('%', '/100')
        
        # 移除多餘空格
        cleaned = re.sub(r'\s+', '', cleaned)
        
        # 驗證是否為有效表達式
        try:
            eval(cleaned)
            return cleaned
        except:
            return None
    
    @staticmethod
    def fix_wikipedia_url(url: str) -> str:
        if 'wikipedia.org' not in url:
            return url
        
        # 修復不完整的括號
        open_count = url.count('(')
        close_count = url.count(')')
        
        if open_count > close_count:
            url += ')' * (open_count - close_count)
        
        return url
    
    @staticmethod
    def infer_unit_type(from_unit: str, to_unit: str) -> str:
        units_lower = (from_unit + to_unit).lower()
        
        # 重量
        if any(u in units_lower for u in ['kg', 'g', 'lb', 'oz', 'ton', 'gram', 'kilogram']):
            return 'weight'
        
        # 長度
        if any(u in units_lower for u in ['m', 'km', 'cm', 'mm', 'mile', 'ft', 'inch', 'meter']):
            return 'length'
        
        # 體積
        if any(u in units_lower for u in ['l', 'ml', 'gallon', 'liter', 'litre']):
            return 'volume'
        
        # 溫度
        if any(u in units_lower for u in ['c', 'f', 'k', 'celsius', 'fahrenheit', 'kelvin']):
            return 'temperature'
        
        # 壓力（gaia_function 不支援，但標記出來）
        if any(u in units_lower for u in ['psi', 'atm', 'pa', 'bar', 'pascal']):
            return 'pressure'
        
        # 預設
        return 'length'


# ============================================================
# Phase 3: 檔案映射管理器 (from v3.1)
# ============================================================

class FileMapperV5:
    
    def __init__(self, tasks: List[Dict], data_dir: Path):
        self.tasks = tasks
        self.data_dir = data_dir
        self.file_map = self._build_file_map()
    
    def _build_file_map(self) -> Dict[str, str]:
        file_map = {}
        
        if not self.data_dir.exists():
            return file_map
        
        for task in self.tasks:
            task_id = task['task_id']
            file_name = task.get('file_name', '')
            
            if not file_name:
                continue
            
            # 方法 1: 精確匹配
            exact_path = self.data_dir / file_name
            if exact_path.exists():
                file_map[task_id] = str(exact_path)
                continue
            
            # 方法 2: 前綴匹配（前 8 個字元）
            prefix = file_name.split('.')[0][:8]
            for f in self.data_dir.iterdir():
                if f.is_file() and f.name.startswith(prefix):
                    file_map[task_id] = str(f)
                    break
            
            # 方法 3: ZIP 檔案記錄
            if task_id not in file_map and file_name.endswith('.zip'):
                zip_path = self.data_dir / file_name
                if zip_path.exists():
                    file_map[task_id] = str(zip_path)
        
        return file_map
    
    def get_file_path(self, task_id: str) -> Optional[str]:
        return self.file_map.get(task_id)
    
    def has_file(self, task_id: str) -> bool:
        return task_id in self.file_map


# ============================================================
# Phase 4: 工具提取器 - 完整 v2.1 規則
# ============================================================

class ToolExtractorV5:

    def __init__(self):
        self.rules = self._build_extraction_rules()
    
    def _build_extraction_rules(self) -> Dict[str, List[Dict]]:

        return {
            'read_pdf': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.pdf)["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'opened?\s+(?:the\s+)?pdf',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/document.pdf'}
                },
                {
                    'pattern': r'clicked?\s+["\']?pdf',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/document.pdf'}
                },
            ],
            
            'read_csv': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.csv)["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'(?:read|loaded?|parsed?)\s+(?:the\s+)?csv',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/data.csv'}
                },
            ],
            
            'read_excel': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.xlsx?)["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'file_path': f'./data/{m.group(1)}', 'sheet_name': 'Sheet1'}
                },
                {
                    'pattern': r'(?:open|opened?)\s+(?:the\s+)?spreadsheet',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/spreadsheet.xlsx', 'sheet_name': 'Sheet1'}
                },
            ],
            
            'read_json': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.json(?:ld)?)["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'opened?\s+(?:the\s+)?(?:json|jsonld)\s+file',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/data.json'}
                },
            ],
            
            'read_xml': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.xml)["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'(?:open|opened?)\s+(?:the\s+)?xml',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/data.xml'}
                },
            ],
            
            'read_image': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.(?:png|jpg|jpeg|gif|bmp|webp))["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'file_path': f'./data/{m.group(1)}'}
                },
            ],
            
            'image_to_text': [
                {
                    'pattern': r'(?:extracted?|read)\s+(?:the\s+)?text\s+from\s+(?:the\s+)?image',
                    'confidence': 2,
                    'extract': lambda m: {'file_path': './data/image.png'}
                },
            ],
            
            'extract_zip': [
                {
                    'pattern': r'(?:extracted?|unzipped?|decompressed?)\s+(?:the\s+)?["\']?(.+?\.zip)["\']?',
                    'confidence': 3,
                    'extract': lambda m: {'zip_path': f'./data/{m.group(1)}'}
                },
            ],
            
            # ========== Web Operations ==========
            'web_search': [
                {
                    'pattern': r'searched?\s+["\'](.+?)["\']',
                    'confidence': 3,
                    'extract': lambda m: {'query': m.group(1)}
                },
                {
                    'pattern': r'searched?\s+(.+?)\s+on\s+(?:google|the\s+web|internet)',
                    'confidence': 3,
                    'extract': lambda m: {'query': m.group(1).strip().strip('"\')')}
                },
                {
                    'pattern': r'searched?\s+for\s+(.+?)(?:\s+(?:in|on|and|to)|\s*$)',
                    'confidence': 2,
                    'extract': lambda m: {'query': m.group(1).strip()}
                },
                {
                    'pattern': r'^search\s+(.+?)(?:\s+and\s+open|\s*$)',
                    'confidence': 2,
                    'extract': lambda m: {'query': m.group(1).strip()}
                },
            ],
            
            'web_fetch': [
                {
                    'pattern': r'opened?\s+(https?://[^\s\)]+)',
                    'confidence': 3,
                    'extract': lambda m: {'url': m.group(1).rstrip('.,;')}
                },
                {
                    'pattern': r'clicked?\s+(?:on\s+)?(?:the\s+)?["\']?(.+?)["\']?\s+(?:link|page|button)',
                    'confidence': 2,
                    'extract': lambda m: {'url': f'<clicked:{m.group(1).strip()}>'}
                },
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\'](.+?)["\']?\s+page',
                    'confidence': 2,
                    'extract': lambda m: {'url': f'<page:{m.group(1).strip()}>'}
                },
                {
                    'pattern': r'opened?\s+(?:a\s+)?new\s+tab',
                    'confidence': 1,
                    'extract': lambda m: {'url': '<new_tab>'}
                },
                {
                    'pattern': r'opened?\s+each\s+(.+?)(?:\s+|$)',
                    'confidence': 2,
                    'extract': lambda m: {'url': f'<iterate:{m.group(1).strip()}>'}
                },
                {
                    'pattern': r'(?:followed?|navigated?\s+to)\s+(?:the\s+)?(?:link|url)',
                    'confidence': 2,
                    'extract': lambda m: {'url': '<from_context>'}
                },
            ],
            
            'wikipedia_search': [
                {
                    'pattern': r'(?:searched?|looked\s+up)\s+(.+?)\s+(?:on|in)\s+wikipedia',
                    'confidence': 3,
                    'extract': lambda m: {'query': m.group(1).strip()}
                },
                {
                    'pattern': r'went\s+(?:back\s+)?to\s+(?:the\s+)?wikipedia',
                    'confidence': 2,
                    'extract': lambda m: {'query': '<infer>'}
                },
                {
                    'pattern': r'opened?\s+["\'](.+?)["\']?\s+on\s+wikipedia',
                    'confidence': 3,
                    'extract': lambda m: {'query': m.group(1).strip()}
                },
            ],
            
            # ========== Calculation Operations ==========
            'calculate': [
                {
                    'pattern': r'calculated?\s+the\s+percentage\s*\(([^)]+?)\s*%?\s*\)',
                    'confidence': 3,
                    'extract': lambda m: {'expression': self._clean_expression(m.group(1))}
                },
                {
                    'pattern': r'calculated?\s*[:\(]\s*(.+?)(?:\s*=|\s*\)|$)',
                    'confidence': 3,
                    'extract': lambda m: {'expression': self._clean_expression(m.group(1))}
                },
                {
                    'pattern': r'took\s+the\s+(?:percentage|average|sum)\s*[:\(]\s*(.+?)(?:\s*=|\s*\)|$)',
                    'confidence': 3,
                    'extract': lambda m: {'expression': self._clean_expression(m.group(1))}
                },
                {
                    'pattern': r'calculated?\s+(?:moles?|value|result)\s*:\s*(.+?)(?:\s*=|$)',
                    'confidence': 2,
                    'extract': lambda m: {'expression': self._clean_expression(m.group(1).split('=')[0])}
                },
            ],
            
            'unit_converter': [
                # Rule 1: "Converted X unit to Y unit"
                {
                    'pattern': r'converted?\s+(\d+(?:\.\d+)?)\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)',
                    'confidence': 3,
                    'extract': lambda m: {
                        'value': float(m.group(1)),
                        'from_unit': m.group(2),
                        'to_unit': m.group(3),
                        'unit_type': '<infer>'
                    } if m.group(2).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
                # Rule 2: "Converted X unit = Y unit" (with result shown)
                {
                    'pattern': r'converted?\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s+([a-zA-Z]+)\s*(?:=|to)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*([a-zA-Z]+)',
                    'confidence': 3,
                    'extract': lambda m: {
                        'value': float(m.group(1).replace(',', '')),
                        'from_unit': m.group(2),
                        'to_unit': m.group(4),
                        'unit_type': '<infer>'
                    } if m.group(2).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
                # Rule 3: "Converted to X: Y Z = result" (e.g., "Converted to mL: 0.05473 L = 54")
                {
                    'pattern': r'converted?\s+to\s+([a-zA-Z]+)\s*:\s*(\d+(?:\.\d+)?)\s+([a-zA-Z]+)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'value': float(m.group(2)),
                        'from_unit': m.group(3),
                        'to_unit': m.group(1),
                        'unit_type': '<infer>'
                    } if m.group(3).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
                # Rule 4: "Converted X to Y: value * factor" (e.g., "Converted psi to atm: 15,750 * 0.068046")
                {
                    'pattern': r'converted?\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)\s*:\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'value': float(m.group(3).replace(',', '')),
                        'from_unit': m.group(1),
                        'to_unit': m.group(2),
                        'unit_type': '<infer>'
                    } if m.group(1).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
                # Rule 5: "Converted X.X unit = Y.Y unit" (decimal numbers with result)
                {
                    'pattern': r'converted?\s+(\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s*=\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]+)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'value': float(m.group(1)),
                        'from_unit': m.group(2),
                        'to_unit': m.group(4),
                        'unit_type': '<infer>'
                    } if m.group(2).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
            ],
            
            # ========== Data Operations ==========
            'compare_values': [
                {
                    'pattern': r'compar(?:ed?|ing)\s+(.+?)\s+(?:and|with|to)\s+(.+?)(?:\s*$|\s+(?:and|to))',
                    'confidence': 2,
                    'extract': lambda m: {
                        'value1': m.group(1).strip(),
                        'value2': m.group(2).strip()
                    }
                },
                {
                    'pattern': r'compar(?:ed?|ing)\s+(?:the\s+)?(\w+)',
                    'confidence': 1,
                    'extract': lambda m: {
                        'value1': '<from_context>',
                        'value2': '<from_context>'
                    }
                },
            ],
            
            'filter_data': [
                {
                    'pattern': r'filter(?:ed)?\s+(?:the\s+)?(?:data|rows?|records?)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'conditions': {}
                    }
                },
                {
                    'pattern': r'opened?\s+(?:the\s+)?filters?\s+and\s+set',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'conditions': {}
                    }
                },
            ],
            
            'extract_information': [
                {
                    'pattern': r'found\s+(?:the\s+)?(.+?)(?:\s+(?:as|in|from|was|of)|$)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'text': '<from_context>',
                        'extract_type': 'specific',
                        'keywords': [m.group(1).strip()]
                    }
                },
                {
                    'pattern': r'found\s+all\s+(?:the\s+)?(.+?)(?:\s+in|\s*$)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'text': '<from_context>',
                        'extract_type': 'all',
                        'keywords': [m.group(1).strip()]
                    }
                },
                {
                    'pattern': r'extracted?\s+(.+?)\s+from',
                    'confidence': 2,
                    'extract': lambda m: {
                        'text': '<from_context>',
                        'extract_type': 'extract',
                        'keywords': [m.group(1).strip()]
                    }
                },
            ],
            
            'deduplicate_data': [
                {
                    'pattern': r'(?:deduplicated?|removed?\s+duplicates?)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'key_fields': None
                    }
                },
                {
                    'pattern': r'go\s+through.+?eliminat(?:e|ing)\s+.+?duplicates?',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'key_fields': None
                    }
                },
            ],
            
            'count_occurrences': [
                {
                    'pattern': r'counted?\s+(?:the\s+)?(.+?)(?:\s+from|\s+in|\s*$)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'target': m.group(1).strip()
                    }
                },
            ],
            
            'find_in_text': [
                {
                    'pattern': r'(?:found|find)\s+["\'](.+?)["\']',
                    'confidence': 2,
                    'extract': lambda m: {
                        'text': '<from_context>',
                        'search_terms': m.group(1)
                    }
                },
                {
                    'pattern': r'find\s+(?:the\s+)?(.+?)(?:\s+label|\s+element)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'text': '<from_context>',
                        'search_terms': m.group(1)
                    }
                },
            ],
            
            'sort_data': [
                {
                    'pattern': r'sort(?:ed)?\s+(?:the\s+)?(?:data|rows?)\s+by\s+(.+?)(?:\s+|$)',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'sort_by': m.group(1).strip()
                    }
                },
            ],
            
            'aggregate_data': [
                {
                    'pattern': r'aggregat(?:ed?|ing)\s+(?:the\s+)?data',
                    'confidence': 2,
                    'extract': lambda m: {
                        'data': '<from_context>',
                        'group_by': '<infer>',
                        'aggregate_field': '<infer>'
                    }
                },
            ],
        }
    
    def _clean_expression(self, expr: str) -> str:

        # 移除百分號
        expr = expr.replace('%', '/100')
        # 移除多餘空格
        expr = re.sub(r'\s+', '', expr)
        return expr
    
    def extract_tools(self, text: str) -> List[Tuple[str, Dict, int]]:

        results = []
        
        for tool_name, patterns in self.rules.items():
            for rule in patterns:
                pattern = rule['pattern']
                confidence = rule['confidence']
                extract_func = rule['extract']
                
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        arguments = extract_func(match)
                        if arguments:  # 某些 extract 可能返回 None
                            results.append((tool_name, arguments, confidence))
                            break  # 只取第一個匹配
                    except Exception as e:
                        continue
        
        return results


# ============================================================
# Phase 5: 參數驗證器
# ============================================================

class ParameterValidatorV5:
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.utils = ValidationUtilsV5
    
    def validate_step(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, List[str]]:

        errors = []
        
        # 檢查所有參數是否包含 placeholder
        # 特殊情況：unit_converter 的 unit_type 允許 <infer>（稍後會自動推斷）
        for key, value in arguments.items():
            # unit_converter 的 unit_type 允許 <infer>
            if tool_name == 'unit_converter' and key == 'unit_type' and value == '<infer>':
                continue  # 跳過，稍後會處理
            
            if self.utils.is_placeholder(value):
                errors.append(f"參數 {key} 包含 placeholder: {value}")
        
        # 針對特定工具的驗證
        if tool_name == 'web_fetch':
            url = arguments.get('url', '')
            if not self.utils.is_valid_url(url):
                errors.append(f"無效的 URL: {url}")
        
        elif tool_name in ['read_pdf', 'read_csv', 'read_excel', 'read_json', 'read_xml', 'read_image']:
            file_path = arguments.get('file_path', '')
            if not self.utils.is_valid_file_path(file_path, self.data_dir):
                errors.append(f"檔案不存在: {file_path}")
        
        elif tool_name == 'calculate':
            expression = arguments.get('expression', '')
            cleaned = self.utils.clean_calculate_expression(expression)
            if cleaned is None:
                errors.append(f"無法清理的表達式: {expression}")
            else:
                # 更新表達式為清理後的版本
                arguments['expression'] = cleaned
        
        elif tool_name == 'unit_converter':
            # 檢查是否有錯誤的參數（v2.1 的 bug）
            invalid_params = {'operation', 'value1', 'value2', 'result', 'expression'}
            if any(p in arguments for p in invalid_params):
                errors.append(f"包含無效參數: {', '.join(invalid_params & arguments.keys())}")
                # 這些錯誤是致命的，直接返回
                return False, errors
            
            # Phase 1.5 優化：放寬參數檢查，允許部分參數缺失並使用 fallback
            # 只有當參數「完全不存在」且「無法推斷」時才拒絕
            
            # 檢查 value（最關鍵）
            has_value = 'value' in arguments and arguments['value'] != '<infer>'
            
            # 檢查 from_unit 和 to_unit
            has_from = 'from_unit' in arguments and arguments['from_unit'] != '<infer>'
            has_to = 'to_unit' in arguments and arguments['to_unit'] != '<infer>'
            
            # Phase 1.5 寬鬆策略：
            # 如果至少有 value 和 其中一個單位，就嘗試執行
            if not has_value:
                errors.append("缺少 value 參數且無法推斷")
                return False, errors
            
            # 如果缺少 from_unit，嘗試從上下文推斷或使用預設
            if not has_from:
                # 檢查描述文字是否包含單位線索
                description = arguments.get('description', '')
                # 常見單位模式
                common_units = ['kg', 'g', 'lb', 'm', 'cm', 'km', 'l', 'ml', 'c', 'f', 'k']
                found_unit = None
                for unit in common_units:
                    if unit in description.lower():
                        found_unit = unit
                        break
                
                if found_unit:
                    arguments['from_unit'] = found_unit
                    has_from = True
                else:
                    # 仍然缺失，但不立即拒絕，標記警告
                    pass
            
            # 如果缺少 to_unit，同樣嘗試推斷
            if not has_to:
                description = arguments.get('description', '')
                # 查找 "to X" 模式
                import re
                to_pattern = re.search(r'to\s+([a-zA-Z]+)', description, re.IGNORECASE)
                if to_pattern:
                    arguments['to_unit'] = to_pattern.group(1)
                    has_to = True
            
            # 最終檢查：至少需要 from 或 to 其中之一
            if not has_from and not has_to:
                errors.append("缺少 from_unit 和 to_unit，無法執行轉換")
                return False, errors
            
            # 如果只有一個單位，記錄警告但仍嘗試
            if not has_from:
                errors.append("警告: 缺少 from_unit，可能執行失敗")
            if not has_to:
                errors.append("警告: 缺少 to_unit，可能執行失敗")
            
            # 處理 unit_type
            unit_type = arguments.get('unit_type', 'length')
            
            # 如果是 <infer>，嘗試自動推斷
            if unit_type == '<infer>':
                from_unit = arguments.get('from_unit', '')
                to_unit = arguments.get('to_unit', '')
                unit_type = self.utils.infer_unit_type(from_unit, to_unit)
                arguments['unit_type'] = unit_type
            
            # Phase 1 優化：對 pressure 採取寬容態度，讓它嘗試執行
            if unit_type == 'pressure':
                # 使用 'length' 作為 fallback（有些函數可能接受）
                arguments['unit_type'] = 'length'
            elif unit_type not in VALID_UNIT_TYPES:
                # 不支援的類型，使用 length 作為 fallback
                arguments['unit_type'] = 'length'
        
        elif tool_name in ['extract_information', 'filter_data', 'find_in_text', 'count_occurrences']:
            # 這些工具需要從上下文獲取資料
            data_param = arguments.get('data') or arguments.get('text')
            if self.utils.is_placeholder(data_param):
                errors.append(f"資料參數是 placeholder，需要前置步驟")
        
        return len(errors) == 0, errors
    
    def fix_parameters(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """修正參數（應用映射規則）"""
        if tool_name not in PARAM_NAME_MAPPING:
            return arguments
        
        mapping = PARAM_NAME_MAPPING[tool_name]
        fixed_args = {}
        
        for key, value in arguments.items():
            new_key = mapping.get(key, key)
            fixed_args[new_key] = value
        
        return fixed_args


# ============================================================
# Phase 6: ZIP 處理器 (from v3.2)
# ============================================================

class ZipHandlerV5:

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def should_extract(self, task: Dict) -> bool:
        """判斷是否需要解壓 ZIP"""
        file_name = task.get('file_name', '')
        return file_name.endswith('.zip')
    
    def create_extract_step(self, task: Dict) -> ParsedStep:
        """創建 extract_zip 步驟"""
        file_name = task.get('file_name', '')
        zip_path = str(self.data_dir / file_name)
        
        return ParsedStep(
            step_number=0,
            original_text=f"Extract {file_name} before processing",
            tool_name='extract_zip',
            arguments={'zip_path': zip_path},
            confidence=3,
            intent_category='file_operation',
            extraction_method='auto_zip_handler',
            executable=True,
            skip_reason=None
        )


# ============================================================
# Phase 7: 主 Parser 類別
# ============================================================

class GAIAParserV5Ultimate:
    
    def __init__(self, tasks_file: str, data_dir: str = './data'):
        self._print_header()
        
        # 載入任務
        print(f"\n📂 載入任務: {tasks_file}")
        with open(tasks_file, 'r', encoding='utf-8') as f:
            self.tasks = json.load(f)
        print(f"   ✅ {len(self.tasks)} 個任務")
        
        # 初始化組件
        self.data_dir = Path(data_dir)
        self.file_mapper = FileMapperV5(self.tasks, self.data_dir)
        self.extractor = ToolExtractorV5()
        self.validator = ParameterValidatorV5(self.data_dir)
        self.zip_handler = ZipHandlerV5(self.data_dir)
        self.reasoning_filter = ReasoningFilterV5
        
        # 統計
        self.stats = {
            'total_tasks': len(self.tasks),
            'steps_extracted': 0,
            'steps_executable': 0,
            'steps_skipped': 0,
            'steps_reasoning': 0,
            'zip_added': 0,
        }
    
    def _print_header(self):
        """打印標題"""
        print("=" * 80)
        print("🚀 GAIA Parser v5.0 Ultimate - 終極整合版本")
        print("=" * 80)
        print("\n✅ 整合功能:")
        print("  • v2.1 完整工具提取（43 種工具）")
        print("  • v2.1 推理過濾器")
        print("  • v2.1 上下文追蹤")
        print("  • v3 驗證邏輯（placeholder, URL, 檔案）")
        print("  • v3.1 參數修正")
        print("  • v3.2 自動修復（ZIP, unit_type, URL）")
    
    def parse_task(self, task: Dict) -> Dict:
        """解析單一任務"""
        task_id = task['task_id']
        steps_text = task.get('Annotator Metadata', {}).get('Steps', '')
        
        if not steps_text:
            return self._empty_result(task)
        
        # 解析步驟 - 使用 v2.1 的分割方式
        steps = re.split(r'\d+\.\s+', steps_text)
        steps = [s.strip() for s in steps if s.strip()]
        
        parsed_steps = []
        context = ParsingContext()
        
        for i, step_text in enumerate(steps, 1):
            # 跳過空步驟
            if not step_text:
                continue
            
            # 檢查是否為推理步驟
            if self.reasoning_filter.is_reasoning(step_text):
                step = ParsedStep(
                    step_number=i,
                    original_text=step_text,
                    tool_name=None,
                    arguments={},
                    confidence=0,
                    intent_category='reasoning',
                    extraction_method='reasoning_filter',
                    is_reasoning=True,
                    executable=False,
                    skip_reason='純推理步驟'
                )
                parsed_steps.append(step)
                self.stats['steps_reasoning'] += 1
                continue
            
            # 提取工具
            tool_matches = self.extractor.extract_tools(step_text)
            
            if not tool_matches:
                # 無法提取工具
                step = ParsedStep(
                    step_number=i,
                    original_text=step_text,
                    tool_name=None,
                    arguments={},
                    confidence=0,
                    intent_category='unknown',
                    extraction_method='none',
                    executable=False,
                    skip_reason='無法識別工具'
                )
                parsed_steps.append(step)
                self.stats['steps_skipped'] += 1
                continue
            
            # 取信心度最高的工具
            tool_name, arguments, confidence = max(tool_matches, key=lambda x: x[2])
            
            # 修正參數名稱
            arguments = self.validator.fix_parameters(tool_name, arguments)
            
            # 修正檔案路徑（如果需要）
            if 'file_path' in arguments:
                file_path = self.file_mapper.get_file_path(task_id)
                if file_path:
                    arguments['file_path'] = file_path
            
            # 修正 URL（如果是 Wikipedia）
            if tool_name == 'web_fetch' and 'url' in arguments:
                url = arguments['url']
                if 'wikipedia.org' in url:
                    arguments['url'] = ValidationUtilsV5.fix_wikipedia_url(url)
            
            # 驗證
            is_valid, errors = self.validator.validate_step(tool_name, arguments)
            
            step = ParsedStep(
                step_number=i,
                original_text=step_text,
                tool_name=tool_name,
                arguments=arguments,
                confidence=confidence,
                intent_category='tool_call',
                extraction_method='pattern_matching',
                executable=is_valid,
                skip_reason='; '.join(errors) if not is_valid else None
            )
            
            parsed_steps.append(step)
            
            if is_valid:
                self.stats['steps_executable'] += 1
            else:
                self.stats['steps_skipped'] += 1
            
            self.stats['steps_extracted'] += 1
        
        # 處理 ZIP
        if self.zip_handler.should_extract(task):
            zip_step = self.zip_handler.create_extract_step(task)
            parsed_steps.insert(0, zip_step)
            self.stats['steps_executable'] += 1
            self.stats['zip_added'] += 1
        
        # 轉換為輸出格式
        tool_sequence = [s.to_dict() for s in parsed_steps]
        executable_count = sum(1 for s in parsed_steps if s.executable)
        
        return {
            'task_id': task_id,
            'question': task.get('Question', ''),
            'final_answer': task.get('Final answer', ''),
            'file_name': task.get('file_name', ''),
            'tool_sequence': tool_sequence,
            'stats': {
                'total_steps': len(parsed_steps),
                'executable_steps': executable_count,
                'skipped_steps': len(parsed_steps) - executable_count,
                'executable_rate': f"{executable_count/len(parsed_steps)*100:.1f}%" if parsed_steps else "0.0%"
            }
        }
    
    def _empty_result(self, task: Dict) -> Dict:
        """空結果"""
        return {
            'task_id': task['task_id'],
            'question': task.get('Question', ''),
            'final_answer': task.get('Final answer', ''),
            'file_name': task.get('file_name', ''),
            'tool_sequence': [],
            'stats': {
                'total_steps': 0,
                'executable_steps': 0,
                'skipped_steps': 0,
                'executable_rate': "0.0%"
            }
        }
    
    def parse_all(self) -> str:
        """解析所有任務"""
        print("\n" + "=" * 80)
        print("🔧 開始處理")
        print("=" * 80)
        
        results = []
        
        for task in self.tasks:
            task_id = task['task_id']
            print(f"\n處理: {task_id}")
            
            result = self.parse_task(task)
            results.append(result)
            
            # 顯示統計
            stats = result['stats']
            if stats['total_steps'] > 0:
                print(f" ✅ {stats['executable_steps']}/{stats['total_steps']} ({stats['executable_rate']})")
            else:
                print(f"無步驟")
        
        # 儲存結果
        output_dir = Path('./parser_output')
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / 'plans.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 打印最終統計
        self._print_final_stats(results)
        
        print(f"\n✅ 儲存至: {output_file}")
        return str(output_file)
    
    def _print_final_stats(self, results: List[Dict]):
        """打印最終統計"""
        print("\n" + "=" * 80)
        print("📊 最終統計")
        print("=" * 80)
        
        total_steps = sum(r['stats']['total_steps'] for r in results)
        executable_steps = sum(r['stats']['executable_steps'] for r in results)
        skipped_steps = sum(r['stats']['skipped_steps'] for r in results)
        
        print(f"\n任務數: {self.stats['total_tasks']}")
        print(f"提取步驟: {self.stats['steps_extracted']}")
        print(f"推理步驟: {self.stats['steps_reasoning']} (已過濾)")
        print(f"可執行步驟: {executable_steps} ({executable_steps/total_steps*100:.1f}%)" if total_steps > 0 else "可執行步驟: 0")
        print(f"跳過步驟: {skipped_steps}")
        print(f"ZIP 自動處理: {self.stats['zip_added']} 個")
        
        # 各工具統計
        tool_counts = defaultdict(int)
        for result in results:
            for step in result['tool_sequence']:
                tool_name = step.get('tool_name')
                if tool_name:
                    tool_counts[tool_name] += 1
        
        print(f"\n工具使用統計:")
        for tool_name, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f" • {tool_name}: {count}")

def main():
    import sys
    
    # 檢查參數
    if len(sys.argv) < 2:
        print("使用方式: python3 parser_v5_ultimate.py <tasks_file> [data_dir]")
        print("範例: python3 parser_v5_ultimate.py gaia_level3_tasks.json ./data")
        sys.exit(1)
    
    tasks_file = sys.argv[1]
    data_dir = sys.argv[2] if len(sys.argv) > 2 else './data'
    
    # 檢查檔案是否存在
    if not Path(tasks_file).exists():
        print(f"找不到任務檔案: {tasks_file}")
        sys.exit(1)
    
    # 執行解析
    parser = GAIAParserV5Ultimate(tasks_file, data_dir)
    output_file = parser.parse_all()
    
if __name__ == '__main__':
    main()

