#!/usr/bin/env python3
"""
GAIA Step Parser v2.1 - Fixed Over-Filtering
修正版本：解決過度過濾問題，添加缺失的工具規則

Version: 2.1.0
Date: 2026-01-13
Changes from v2.0:
- Fixed: "Clicked" now maps to web_fetch instead of being filtered
- Added: More "Opened" variations for web_fetch
- Added: "Found" patterns for extract_information
- Added: Conversion operations (Changed, Plugged, Followed)
- Improved: filter_data patterns
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import importlib.util
from collections import defaultdict


# ============================================================
# 資料結構
# ============================================================

@dataclass
class ParsedStep:
    """解析後的步驟"""
    step_number: int
    original_text: str
    tool_name: Optional[str]
    arguments: Dict[str, Any]
    confidence: int  # 0-3
    intent_category: str
    extraction_method: str
    notes: List[str] = field(default_factory=list)
    is_reasoning: bool = False
    
    def to_dict(self):
        return {
            'step_number': self.step_number,
            'original_text': self.original_text,
            'tool_name': self.tool_name,
            'arguments': self.arguments,
            'confidence': self.confidence,
            'intent_category': self.intent_category,
            'extraction_method': self.extraction_method,
            'notes': self.notes,
            'is_reasoning': self.is_reasoning
        }


@dataclass
class ParsingContext:
    """跨步驟上下文"""
    downloaded_files: List[str] = field(default_factory=list)
    fetched_urls: List[str] = field(default_factory=list)
    data_sources: Dict[int, str] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    last_calculation: Optional[str] = None
    last_data_operation: Optional[str] = None
    opened_files: List[str] = field(default_factory=list)
    recent_searches: List[str] = field(default_factory=list)


# ============================================================
# v2.1 推理步驟過濾器 - 修正版
# ============================================================

class ReasoningFilterV21:
    """v2.1 修正版推理過濾器"""
    
    # 純推理動詞
    REASONING_VERBS = {
        'fix', 'fixes', 'fixed', 'fixing',
        'see', 'sees', 'saw', 'seeing',
        'when', 'if', 'as',
        'note', 'noted', 'noting', 'notes',  # "Note the food" 這種
        'check', 'checked', 'checking', 'checks',
        'verify', 'verified', 'verifying', 'verifies',
        'confirm', 'confirmed', 'confirming', 'confirms',
        'determine', 'determined', 'determining', 'determines',
        'conclude', 'concluded', 'concluding', 'concludes',
        'round', 'rounded', 'rounding', 'rounds',
        'consider', 'considered', 'considering', 'considers',
        'assume', 'assumed', 'assuming', 'assumes',
    }
    
    # UI 操作動詞 - 移除 'click'！
    UI_VERBS = {
        'scroll', 'scrolled', 'scrolling', 'scrolls',
        # 'click', 'clicked', 'clicking', 'clicks',  # 移除！改為 web_fetch
        'navigate', 'navigated', 'navigating', 'navigates',
        'watch', 'watched', 'watching', 'watches',
        'listen', 'listened', 'listening', 'listens',
        # 'view', 'viewed', 'viewing', 'views',  # 移除！可能是 web_fetch
    }
    
    # 狀態記錄模式
    STATE_PATTERNS = [
        r'\(running tally:?\s*\d+/\d+\)',
        r'\d+/\d+\s*(?:updated|not updated)',
        r'noted?\s+its\s+',  # "Noted its PubChem CID"
        r'repeated?\s+steps?\s+\d+',
        r'repeat(?:ed)?\s+(?:the\s+)?(?:steps?|process|procedure)',
    ]
    
    @classmethod
    def is_reasoning(cls, text: str) -> bool:
        """判斷是否為純推理步驟"""
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
# v2.1 增強版模式規則
# ============================================================

class EnhancedPatternRulesV21:
    """v2.1 增強版規則"""
    
    @staticmethod
    def get_all_rules():
        """返回所有工具的增強匹配規則"""
        return {
            # ========== File Operations ==========
            'read_pdf': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.pdf)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']([^"\']+?)\s*\(pdf\)["\']?\s*(?:pdf)?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}.pdf'}
                },
                {
                    'pattern': r'(?:read|viewed?|examined?)\s+(?:the\s+)?pdf',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: EnhancedPatternRulesV21._infer_pdf_path(ctx)
                },
                # 新增: "Opened the PDF"
                {
                    'pattern': r'opened?\s+(?:the\s+)?pdf',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/document.pdf'}
                },
                # 新增: "Clicked 'PDF/A'"
                {
                    'pattern': r'clicked?\s+["\']?pdf',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/document.pdf'}
                },
            ],
            
            'read_csv': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.csv)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'(?:read|loaded?|parsed?)\s+(?:the\s+)?csv',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: EnhancedPatternRulesV21._infer_csv_path(ctx)
                },
            ],
            
            'read_excel': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.xlsx?)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'(?:open|opened?)\s+(?:the\s+)?spreadsheet',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/spreadsheet.xlsx'}
                },
                {
                    'pattern': r'(?:read|loaded?)\s+(?:the\s+)?excel',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/data.xlsx'}
                },
            ],
            
            'read_json': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.json(?:ld)?)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'opened?\s+(?:the\s+)?(?:json|jsonld)\s+file',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/data.json'}
                },
                {
                    'pattern': r'(?:loaded?|parsed?)\s+(?:the\s+)?(?:json|jsonld)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/data.json'}
                },
            ],
            
            'read_xml': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.xml)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
                {
                    'pattern': r'(?:open|opened?)\s+(?:the\s+)?xml',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/data.xml'}
                },
                {
                    'pattern': r'(?:parsed?|loaded?)\s+(?:the\s+)?xml',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'file_path': './data/data.xml'}
                },
            ],
            
            'read_text_file': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.txt)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
            ],
            
            'read_docx': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.docx?)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
            ],
            
            'read_image': [
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\']?(.+?\.(?:png|jpg|jpeg|gif|bmp|webp))["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'file_path': f'./data/{m.group(1)}'}
                },
            ],
            
            'extract_zip': [
                {
                    'pattern': r'(?:extracted?|unzipped?|decompressed?)\s+(?:the\s+)?["\']?(.+?\.zip)["\']?',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'zip_path': f'./data/{m.group(1)}'}
                },
            ],
            
            'extract_information': [
                # "Found the X" (明確目標)
                {
                    'pattern': r'found\s+the\s+(.+?)(?:\s+(?:as|in|from|was|of|fed|\()|$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'extract_type': 'specific',
                        'target': m.group(1).strip()
                    }
                },
                # "Found all versions of"
                {
                    'pattern': r'found\s+all\s+(?:versions?|instances?)\s+of\s+(.+?)(?:\s+in|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'extract_type': 'all_instances',
                        'target': m.group(1).strip()
                    }
                },
                # "Extracted"
                {
                    'pattern': r'extracted?\s+(.+?)\s+(?:from|in)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'extract_type': 'keywords',
                        'keywords': [m.group(1).strip()]
                    }
                },
            ],
            
            # ========== Web/API Operations ==========
            'web_search': [
                {
                    'pattern': r'searched?\s+["\'](.+?)["\']',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'query': m.group(1)}
                },
                {
                    'pattern': r'^search\s+["\'](.+?)["\']',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'query': m.group(1)}
                },
                {
                    'pattern': r'(?:searched?|googled?)\s+for\s+(.+?)(?:\s+(?:in|on|and|to)|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'query': m.group(1).strip()}
                },
                {
                    'pattern': r'search\s+for\s+(?:a\s+)?(.+?)(?:\s+to|\s*,|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'query': m.group(1).strip()}
                },
                {
                    'pattern': r'(?:opened?\s+(?:a\s+)?(?:new\s+)?tab\s+and\s+)?searched?\s+(.+?)(?:\s+(?:in|on)|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'query': m.group(1).strip()}
                },
            ],
            
            'web_fetch': [
                # URL 開頭
                {
                    'pattern': r'opened?\s+(https?://[^\s\)]+)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'url': m.group(1).rstrip('.,;')}
                },
                # "Opened ... on website"
                {
                    'pattern': r'opened?\s+["\'](.+?)["\']?\s+on\s+(?:the\s+)?(.+?)\s+(?:website|page)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<{m.group(2)}:{m.group(1)}>'}
                },
                # 新增: "Clicked on ... link/page"
                {
                    'pattern': r'clicked?\s+(?:on\s+)?(?:the\s+)?["\']?(.+?)["\']?\s+(?:link|page|button)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<clicked:{m.group(1).strip()}>'}
                },
                # 新增: "Opened ... page" (沒有 "on website")
                {
                    'pattern': r'opened?\s+(?:the\s+)?["\'](.+?)["\']?\s+page',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<page:{m.group(1).strip()}>'}
                },
                # 新增: "Opened a new tab"
                {
                    'pattern': r'opened?\s+(?:a\s+)?new\s+tab',
                    'confidence': 1,
                    'extract': lambda m, text, ctx: {'url': '<new_tab>'}
                },
                # 新增: "Opened the link in"
                {
                    'pattern': r'opened?\s+(?:the\s+)?link\s+in\s+(?:the\s+)?(.+?)(?:\s+to|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<link_in:{m.group(1).strip()}>'}
                },
                # "Opened each"
                {
                    'pattern': r'opened?\s+each\s+(.+?)(?:\s+|$|\')',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<iterate:{m.group(1).strip()}>'}
                },
                # "Opened the two/three"
                {
                    'pattern': r'opened?\s+(?:the\s+)?(?:two|three|four|five)\s+(.+?)(?:\s+pages?|\s*$|\')',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<multiple:{m.group(1).strip()}>'}
                },
                # "Opened the resulting"
                {
                    'pattern': r'opened?\s+(?:the\s+)?resulting\s+["\'](.+?)["\']',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<result:{m.group(1).strip()}>'}
                },
                # 新增: "Followed the ... link"
                {
                    'pattern': r'followed?\s+(?:the\s+)?["\'](.+?)["\']?\s+link',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'url': f'<followed:{m.group(1).strip()}>'}
                },
                # Fetch/Retrieved
                {
                    'pattern': r'(?:fetched?|downloaded?|retrieved?)\s+(?:the\s+)?(?:url|page|website|content)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: EnhancedPatternRulesV21._infer_url_from_context(ctx)
                },
            ],
            
            'wikipedia_search': [
                {
                    'pattern': r'(?:searched?|looked\s+up)\s+(.+?)\s+(?:on|in)\s+wikipedia',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'query': m.group(1).strip()}
                },
                {
                    'pattern': r'went\s+(?:back\s+)?to\s+(?:the\s+)?wikipedia',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'query': ctx.recent_searches[-1] if ctx.recent_searches else '<infer>'}
                },
                # 新增: "Opened ... on Wikipedia"
                {
                    'pattern': r'opened?\s+["\'](.+?)["\']?\s+on\s+wikipedia',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'query': m.group(1).strip()}
                },
            ],
            
            'currency_converter': [
                {
                    'pattern': r'convert(?:ed)?\s+(\d+(?:\.\d+)?)\s+([A-Z]{3})\s+to\s+([A-Z]{3})',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {
                        'amount': float(m.group(1)),
                        'from_currency': m.group(2).upper(),
                        'to_currency': m.group(3).upper()
                    }
                },
            ],
            
            'geocoding': [
                {
                    'pattern': r'(?:geocoded?|located?|found\s+coordinates)\s+(?:for\s+)?(.+?)(?:\s+(?:and|to)|\s*$)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'location': m.group(1).strip()}
                },
            ],
            
            # ========== Calculation Operations ==========
            'calculate': [
                # 百分比計算
                {
                    'pattern': r'calculated?\s+the\s+percentage\s*\(([^)]+?)\s*%?\s*\)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1))}
                },
                # 標準計算
                {
                    'pattern': r'calculated?\s*[:\(]\s*\(([^)]+)\)\s*/\s*(\d+)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'expression': f'({m.group(1)}) / {m.group(2)}'}
                },
                {
                    'pattern': r'calculated?\s*[:\(]\s*\(([^)]+)\)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1))}
                },
                {
                    'pattern': r'calculated?\s*[:\(]\s*([0-9\s\+\-\*/\.\(\)]+?)\s*[=\)]',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1))}
                },
                {
                    'pattern': r'calculated?\s*:\s*(.+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1).split('=')[0])}
                },
                {
                    'pattern': r'(\d+(?:\s*[\+\-\*/]\s*\d+)+)\s*=',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1))}
                },
                # "Took the percentage"
                {
                    'pattern': r'took\s+the\s+percentage\s*\(([^)]+)\)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1))}
                },
                # 新增: "Calculated moles"
                {
                    'pattern': r'calculated?\s+moles?\s*:\s*(.+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {'expression': EnhancedPatternRulesV21._clean_expr(m.group(1).split('=')[0])}
                },
                # 新增: "Changed ... to ..."
                {
                    'pattern': r'changed?\s+([A-Z\s=]+)\s+to\s+([A-Z\s=]+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'operation': 'transform',
                        'from': m.group(1).strip(),
                        'to': m.group(2).strip()
                    }
                },
                # 新增: "Plugged numbers into"
                {
                    'pattern': r'plugged?\s+numbers?\s+into\s+(?:the\s+)?(.+?)(?:\s*:|$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'operation': 'substitute',
                        'equation': m.group(1).strip()
                    }
                },
            ],
            
            'statistical_analysis': [
                {
                    'pattern': r'(?:calculated?|computed?|found|took)\s+(?:the\s+)?(?:average|mean|median|std|variance)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'metrics': EnhancedPatternRulesV21._extract_metrics(text)
                    }
                },
            ],
            
            'date_calculator': [
                {
                    'pattern': r'(?:calculated?|computed?|found)\s+(?:the\s+)?(?:date|days|difference)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: EnhancedPatternRulesV21._extract_dates(text)
                },
                {
                    'pattern': r'(\d{4}-\d{2}-\d{2})',
                    'confidence': 1,
                    'extract': lambda m, text, ctx: {'start_date': m.group(1)}
                },
            ],
            
            'unit_converter': [
                # 明確的單位轉換
                {
                    'pattern': r'converted?\s+(\d+(?:\.\d+)?)\s+([a-z]+)\s*(?:=|to)\s*(\d+(?:\.\d+)?)\s*([a-z]+)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {
                        'value': float(m.group(1)),
                        'from_unit': m.group(2),
                        'to_unit': m.group(4),
                        'unit_type': 'length'
                    } if m.group(2).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
                # "Converted X unit to Y unit"
                {
                    'pattern': r'converted?\s+(\d+(?:\.\d+)?)\s+([a-z]+)\s+to\s+([a-z]+)',
                    'confidence': 3,
                    'extract': lambda m, text, ctx: {
                        'value': float(m.group(1)),
                        'from_unit': m.group(2),
                        'to_unit': m.group(3)
                    } if m.group(2).lower() not in ['usd', 'eur', 'gbp', 'jpy', 'cny'] else None
                },
                # 新增: "Converted ... * ... = ..."
                {
                    'pattern': r'converted?\s+(.+?)\s*[*×]\s*(.+?)\s*=\s*(.+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'operation': 'conversion_multiply',
                        'value1': m.group(1).strip(),
                        'value2': m.group(2).strip(),
                        'result': m.group(3).strip()
                    }
                },
                # 新增: "Converted to mL"
                {
                    'pattern': r'converted?\s+to\s+([a-z]+)\s*:\s*(.+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'to_unit': m.group(1),
                        'expression': m.group(2).strip()
                    }
                },
            ],
            
            'correlation_analysis': [
                {
                    'pattern': r'(?:calculated?|found|computed?)\s+(?:the\s+)?correlation',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'x_column': '<infer>',
                        'y_column': '<infer>'
                    }
                },
            ],
            
            'moving_average': [
                {
                    'pattern': r'(?:calculated?|computed?)\s+(?:the\s+)?moving\s+average',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'window_size': 3
                    }
                },
            ],
            
            'validate_data': [
                {
                    'pattern': r'validat(?:ed?|ing)\s+(?:the\s+)?data',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'rules': {}
                    }
                },
            ],
            
            # ========== Data Operations ==========
            'filter_data': [
                {
                    'pattern': r'filter(?:ed)?\s+(?:the\s+)?(?:data|rows?|records?)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'conditions': EnhancedPatternRulesV21._extract_filter_conditions(text)
                    }
                },
                # 新增: "Opened the filters and set"
                {
                    'pattern': r'opened?\s+(?:the\s+)?filters?\s+and\s+set\s+(?:them\s+)?to\s+(.+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'filter_settings': m.group(1).strip()
                    }
                },
            ],
            
            'sort_data': [
                {
                    'pattern': r'sort(?:ed)?\s+(?:the\s+)?(?:data|rows?)\s+by\s+(.+?)(?:\s+(?:in|and)|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'sort_by': m.group(1).strip()
                    }
                },
            ],
            
            'aggregate_data': [
                {
                    'pattern': r'aggregat(?:ed?|ing)\s+(?:the\s+)?(?:data|sales)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'group_by': '<infer>',
                        'aggregate_field': '<infer>',
                        'operation': 'sum'
                    }
                },
            ],
            
            'join_data': [
                {
                    'pattern': r'join(?:ed)?\s+(?:the\s+)?(?:data|tables?)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'join_type': 'inner'
                    }
                },
            ],
            
            'deduplicate_data': [
                {
                    'pattern': r'(?:deduplicated?|removed?\s+duplicates?)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'key': None
                    }
                },
                {
                    'pattern': r'go\s+through.+?eliminat(?:e|ing)\s+.+?duplicates?',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'key': None
                    }
                },
            ],
            
            'pivot_table': [
                {
                    'pattern': r'(?:created?|made)\s+(?:a\s+)?pivot\s+table',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'index': '<infer>',
                        'columns': '<infer>',
                        'values': '<infer>'
                    }
                },
            ],
            
            'fill_missing': [
                {
                    'pattern': r'fill(?:ed)?\s+(?:the\s+)?missing\s+values?',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'strategy': 'mean'
                    }
                },
            ],
            
            'sample_data': [
                {
                    'pattern': r'sampl(?:ed?|ing)\s+(\d+)\s+(?:rows?|records?)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'n': int(m.group(1))
                    }
                },
            ],
            
            'compare_data': [
                {
                    'pattern': r'compar(?:ed?|ing)\s+(?:the\s+)?(?:data|datasets?)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data1': '<from_context>',
                        'data2': '<from_context>',
                        'comparison_type': 'difference'
                    }
                },
            ],
            
            'compare_values': [
                {
                    'pattern': r'compar(?:ed?|ing)\s+(.+?)\s+(?:and|with|to)\s+(.+?)(?:\s*$|\s+(?:and|to))',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'value1': m.group(1).strip(),
                        'value2': m.group(2).strip()
                    }
                },
            ],
            
            'list_operations': [
                {
                    'pattern': r'(?:found|identified?)\s+(?:the\s+)?(?:union|intersection|difference)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'list1': '<from_context>',
                        'operation': EnhancedPatternRulesV21._extract_list_operation(text)
                    }
                },
            ],
            
            'split_join_text': [
                {
                    'pattern': r'(?:split|joined?)\s+(?:the\s+)?(?:text|string)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'operation': 'split' if 'split' in text.lower() else 'join',
                        'separator': ','
                    }
                },
            ],
            
            # ========== Text/String Operations ==========
            'image_to_text': [
                {
                    'pattern': r'(?:extracted?|read)\s+(?:the\s+)?text\s+from\s+(?:the\s+)?image',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'file_path': EnhancedPatternRulesV21._infer_image_path(ctx)
                    }
                },
            ],
            
            'analyze_image': [
                {
                    'pattern': r'analyz(?:ed?|ing)\s+(?:the\s+)?image',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'file_path': EnhancedPatternRulesV21._infer_image_path(ctx)
                    }
                },
            ],
            
            'regex_search': [
                {
                    'pattern': r'(?:searched?|found)\s+(?:using\s+)?(?:regex|pattern)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'pattern': EnhancedPatternRulesV21._extract_regex_pattern(text)
                    }
                },
            ],
            
            'string_transform': [
                {
                    'pattern': r'(?:converted?|transformed?)\s+(?:the\s+)?(?:text|string)\s+to\s+(\w+)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'operation': m.group(1).lower()
                    }
                },
            ],
            
            'encode_decode': [
                {
                    'pattern': r'(?:encoded?|decoded?)\s+(?:the\s+)?(?:text|string)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'operation': 'encode' if 'encode' in text.lower() else 'decode',
                        'encoding': 'base64'
                    }
                },
            ],
            
            'create_csv': [
                {
                    'pattern': r'created?\s+(?:a\s+)?csv\s+file',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'filename': 'output.csv'
                    }
                },
            ],
            
            'create_markdown': [
                {
                    'pattern': r'created?\s+(?:a\s+)?markdown\s+file',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'title': '<infer>',
                        'sections': [],
                        'filename': 'output.md'
                    }
                },
            ],
            
            'count_occurrences': [
                {
                    'pattern': r'counted?\s+the\s+(.+?)(?:\s+from|\s+in|\s*$)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'data': '<from_context>',
                        'target': EnhancedPatternRulesV21._extract_count_target(text)
                    }
                },
            ],
            
            'find_in_text': [
                {
                    'pattern': r'(?:found|find)\s+["\'](.+?)["\']',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'search_terms': m.group(1)
                    }
                },
                {
                    'pattern': r'find\s+the\s+(.+?)(?:\s+label|\s+element)',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'search_terms': m.group(1)
                    }
                },
                {
                    'pattern': r'search\s+for\s+(?:the\s+)?(.+?)(?:\s+in|\s*$)',
                    'confidence': 1,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'search_terms': m.group(1)
                    }
                },
                # 新增: "Scrolled to"
                {
                    'pattern': r'scrolled?\s+to\s+(.+)',
                    'confidence': 1,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'search_terms': m.group(1).strip()
                    }
                },
                # 新增: "Expanded"
                {
                    'pattern': r'expanded?\s+["\'](.+?)["\']',
                    'confidence': 2,
                    'extract': lambda m, text, ctx: {
                        'text': '<from_context>',
                        'search_terms': m.group(1)
                    }
                },
            ],
        }
    
    # ========== 輔助方法 ==========
    
    @staticmethod
    def _clean_expr(expr: str) -> str:
        """清理數學表達式"""
        expr = expr.replace('%', '')
        expr = re.sub(r'\s*[=%].*$', '', expr)
        expr = expr.strip().strip('()')
        return expr
    
    @staticmethod
    def _infer_pdf_path(ctx: ParsingContext) -> Dict[str, Any]:
        """從上下文推斷 PDF 路徑"""
        for url in reversed(ctx.fetched_urls):
            if '.pdf' in url:
                filename = url.split('/')[-1].split('?')[0]
                return {'file_path': f'./data/{filename}'}
        if ctx.opened_files:
            for file in reversed(ctx.opened_files):
                if '.pdf' in file:
                    return {'file_path': file}
        return {'file_path': './data/document.pdf'}
    
    @staticmethod
    def _infer_csv_path(ctx: ParsingContext) -> Dict[str, Any]:
        """從上下文推斷 CSV 路徑"""
        for url in reversed(ctx.fetched_urls):
            if '.csv' in url:
                filename = url.split('/')[-1].split('?')[0]
                return {'file_path': f'./data/{filename}'}
        return {'file_path': './data/data.csv'}
    
    @staticmethod
    def _infer_url_from_context(ctx: ParsingContext) -> Dict[str, Any]:
        """從上下文推斷 URL"""
        if ctx.fetched_urls:
            return {'url': ctx.fetched_urls[-1]}
        return {'url': '<infer>'}
    
    @staticmethod
    def _infer_image_path(ctx: ParsingContext) -> str:
        """從上下文推斷圖片路徑"""
        for file in reversed(ctx.downloaded_files):
            if any(ext in file for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                return file
        return './data/image.png'
    
    @staticmethod
    def _extract_metrics(text: str) -> List[str]:
        """提取統計指標"""
        metrics = []
        if 'average' in text or 'mean' in text:
            metrics.append('mean')
        if 'median' in text:
            metrics.append('median')
        if 'std' in text or 'standard deviation' in text:
            metrics.append('std')
        return metrics or ['mean']
    
    @staticmethod
    def _extract_dates(text: str) -> Dict[str, Any]:
        """提取日期"""
        dates = re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', text)
        if len(dates) >= 2:
            return {'start_date': dates[0], 'end_date': dates[1]}
        elif len(dates) == 1:
            return {'start_date': dates[0]}
        return {}
    
    @staticmethod
    def _extract_filter_conditions(text: str) -> Dict[str, Any]:
        """提取過濾條件"""
        return {'<infer>': '<infer>'}
    
    @staticmethod
    def _extract_list_operation(text: str) -> str:
        """提取列表操作"""
        if 'union' in text.lower():
            return 'union'
        elif 'intersection' in text.lower():
            return 'intersection'
        elif 'difference' in text.lower():
            return 'difference'
        return 'union'
    
    @staticmethod
    def _extract_regex_pattern(text: str) -> str:
        """提取正則表達式"""
        pattern_match = re.search(r'pattern\s+["\'](.+?)["\']', text)
        if pattern_match:
            return pattern_match.group(1)
        return r'\w+'
    
    @staticmethod
    def _extract_count_target(text: str) -> str:
        """提取計數目標"""
        target_match = re.search(r'of\s+["\'](.+?)["\']', text)
        if target_match:
            return target_match.group(1)
        target_match = re.search(r'counted?\s+the\s+(.+?)(?:\s+from)', text)
        if target_match:
            return target_match.group(1).strip()
        return '<infer>'


# ============================================================
# v2.1 解析器
# ============================================================

class GAIAStepParserV21:
    """GAIA 步驟解析器 v2.1"""
    
    def __init__(self, function_module_path: str = None):
        self.rules = EnhancedPatternRulesV21.get_all_rules()
        self.context = ParsingContext()
        self.reasoning_filter = ReasoningFilterV21()
        
        self.schemas = {}
        if function_module_path:
            self._load_schemas(function_module_path)
        
        self.tool_categories = self._build_category_mapping()
        
        self.stats = {
            'total_steps': 0,
            'reasoning_steps': 0,
            'tool_steps': 0,
            'high_confidence': 0,
        }
    
    def _load_schemas(self, module_path: str):
        """載入工具 schemas"""
        try:
            spec = importlib.util.spec_from_file_location("gaia_function", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.schemas = module.GAIA_TOOL_SCHEMAS
        except Exception as e:
            print(f"Warning: Could not load schemas: {e}")
    
    def _build_category_mapping(self) -> Dict[str, str]:
        """建立工具類別映射"""
        mapping = {}
        
        file_tools = ['read_pdf', 'read_csv', 'read_image', 'read_excel', 'read_json',
                      'read_text_file', 'read_docx', 'read_xml', 'extract_information', 'extract_zip']
        web_tools = ['web_search', 'web_fetch', 'currency_converter', 'wikipedia_search', 'geocoding']
        calc_tools = ['calculate', 'date_calculator', 'unit_converter', 'statistical_analysis',
                      'correlation_analysis', 'moving_average', 'validate_data']
        data_tools = ['filter_data', 'aggregate_data', 'sort_data', 'join_data', 'deduplicate_data',
                      'pivot_table', 'fill_missing', 'sample_data', 'split_join_text',
                      'compare_data', 'compare_values', 'list_operations']
        text_tools = ['image_to_text', 'analyze_image', 'regex_search', 'string_transform',
                      'encode_decode', 'create_csv', 'create_markdown', 'count_occurrences', 'find_in_text']
        
        for tool in file_tools:
            mapping[tool] = 'file'
        for tool in web_tools:
            mapping[tool] = 'web'
        for tool in calc_tools:
            mapping[tool] = 'calc'
        for tool in data_tools:
            mapping[tool] = 'data'
        for tool in text_tools:
            mapping[tool] = 'text'
        
        return mapping
    
    def parse_step(self, step_number: int, step_text: str) -> ParsedStep:
        """解析單個步驟"""
        self.stats['total_steps'] += 1
        
        # 首先檢查是否為推理步驟
        if self.reasoning_filter.is_reasoning(step_text):
            self.stats['reasoning_steps'] += 1
            return ParsedStep(
                step_number=step_number,
                original_text=step_text,
                tool_name=None,
                arguments={},
                confidence=0,
                intent_category='reasoning',
                extraction_method='reasoning_filter',
                is_reasoning=True,
                notes=['Filtered as reasoning step']
            )
        
        step_lower = step_text.lower()
        
        # 嘗試所有工具的所有規則
        best_match = None
        best_confidence = -1
        
        for tool_name, tool_rules in self.rules.items():
            for rule in tool_rules:
                match = re.search(rule['pattern'], step_lower)
                if match:
                    try:
                        arguments = rule['extract'](match, step_text, self.context)
                        
                        if arguments is None:
                            continue
                        
                        confidence = rule['confidence']
                        
                        if tool_name == 'calculate':
                            if not self._is_valid_calculation(step_text, arguments.get('expression', '')):
                                continue
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                'tool_name': tool_name,
                                'arguments': arguments,
                                'confidence': confidence,
                                'method': 'pattern'
                            }
                    except Exception as e:
                        continue
        
        if best_match:
            self.stats['tool_steps'] += 1
            if best_match['confidence'] >= 2:
                self.stats['high_confidence'] += 1
            
            self._update_context(step_number, best_match['tool_name'], best_match['arguments'])
            
            return ParsedStep(
                step_number=step_number,
                original_text=step_text,
                tool_name=best_match['tool_name'],
                arguments=best_match['arguments'],
                confidence=best_match['confidence'],
                intent_category=self.tool_categories.get(best_match['tool_name'], 'unknown'),
                extraction_method=best_match['method']
            )
        
        return ParsedStep(
            step_number=step_number,
            original_text=step_text,
            tool_name=None,
            arguments={},
            confidence=0,
            intent_category='unknown',
            extraction_method='none',
            notes=['No pattern matched']
        )
    
    def _is_valid_calculation(self, text: str, expr: str) -> bool:
        """驗證是否為有效計算"""
        text_lower = text.lower()
        
        if re.search(r'\d+-\d+\s+(?:years|months|days|hours)', text_lower):
            return False
        
        if re.search(r'repeated?\s+steps?\s+\d+-\d+', text_lower):
            return False
        
        if 'running tally' in text_lower and '/' in expr and '=' not in text_lower:
            return False
        
        if re.match(r'^\d+\s*-\s*\d+$', expr) and 'step' in text_lower:
            return False
        
        return True
    
    def _update_context(self, step_number: int, tool_name: str, arguments: Dict[str, Any]):
        """更新解析上下文"""
        if tool_name == 'web_fetch' and 'url' in arguments:
            url = arguments['url']
            if url and url != '<infer>' and not url.startswith('<'):
                self.context.fetched_urls.append(url)
                if '.pdf' in url or '.csv' in url:
                    filename = url.split('/')[-1].split('?')[0]
                    self.context.downloaded_files.append(f'./data/{filename}')
        
        elif tool_name == 'web_search' and 'query' in arguments:
            query = arguments['query']
            if query and query != '<infer>':
                self.context.recent_searches.append(query)
        
        elif tool_name in ['read_pdf', 'read_csv', 'read_excel', 'read_json', 'read_xml']:
            if 'file_path' in arguments:
                file_path = arguments['file_path']
                if file_path and file_path != '<infer>':
                    self.context.data_sources[step_number] = file_path
                    self.context.opened_files.append(file_path)
        
        elif tool_name == 'calculate':
            self.context.last_calculation = arguments.get('expression')
    
    def parse_steps(self, steps_text: str) -> List[ParsedStep]:
        """解析完整的步驟文本"""
        self.context = ParsingContext()
        self.stats = {
            'total_steps': 0,
            'reasoning_steps': 0,
            'tool_steps': 0,
            'high_confidence': 0,
        }
        
        steps = re.split(r'\d+\.\s+', steps_text)
        steps = [s.strip() for s in steps if s.strip()]
        
        parsed_steps = []
        for i, step_text in enumerate(steps, 1):
            parsed = self.parse_step(i, step_text)
            parsed_steps.append(parsed)
        
        return parsed_steps
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            'extraction_rate': self.stats['tool_steps'] / self.stats['total_steps'] if self.stats['total_steps'] > 0 else 0,
            'reasoning_rate': self.stats['reasoning_steps'] / self.stats['total_steps'] if self.stats['total_steps'] > 0 else 0,
        }


# ============================================================
# 計劃生成器
# ============================================================

class PlanGeneratorV21:
    """v2.1 計劃生成器"""
    
    def __init__(self, parser: GAIAStepParserV21):
        self.parser = parser
    
    def generate_plan(self, task: Dict) -> Dict:
        """為單個任務生成計劃"""
        metadata = task.get('Annotator Metadata', {})
        
        if 'Steps' not in metadata:
            return {
                'task_id': task['task_id'],
                'question': task['Question'],
                'final_answer': task['Final answer'],
                'file_name': task.get('file_name'),
                'tool_sequence': [],
                'parsed_steps': [],
                'metadata': {
                    'total_annotated_steps': 0,
                    'extracted_tools': 0,
                    'reasoning_steps': 0,
                    'extraction_rate': 0
                }
            }
        
        steps_text = metadata['Steps']
        parsed_steps = self.parser.parse_steps(steps_text)
        
        tool_sequence = []
        reasoning_count = 0
        
        for parsed in parsed_steps:
            if parsed.is_reasoning:
                reasoning_count += 1
            elif parsed.tool_name:
                tool_sequence.append({
                    'step_id': f'step_{parsed.step_number}',
                    'tool_name': parsed.tool_name,
                    'arguments': parsed.arguments,
                    'description': parsed.original_text,
                    'confidence': parsed.confidence,
                    'intent_category': parsed.intent_category,
                    'extraction_method': parsed.extraction_method
                })
        
        stats = self.parser.get_stats()
        
        return {
            'task_id': task['task_id'],
            'question': task['Question'],
            'final_answer': task['Final answer'],
            'file_name': task.get('file_name'),
            'tool_sequence': tool_sequence,
            'parsed_steps': [s.to_dict() for s in parsed_steps],
            'metadata': {
                'total_annotated_steps': len(parsed_steps),
                'extracted_tools': len(tool_sequence),
                'reasoning_steps': reasoning_count,
                'extraction_rate': len(tool_sequence) / len(parsed_steps) if parsed_steps else 0,
                'reasoning_rate': reasoning_count / len(parsed_steps) if parsed_steps else 0,
                'tools_with_params': sum(1 for t in tool_sequence if t['arguments']),
                'high_confidence_tools': sum(1 for t in tool_sequence if t['confidence'] >= 2),
                'tool_category_distribution': self._count_categories(tool_sequence),
                **stats
            }
        }
    
    def _count_categories(self, tool_sequence: List[Dict]) -> Dict[str, int]:
        """統計工具類別分布"""
        categories = defaultdict(int)
        for tool in tool_sequence:
            categories[tool['intent_category']] += 1
        return dict(categories)
    
    def generate_all(self, tasks: List[Dict]) -> List[Dict]:
        """為所有任務生成計劃"""
        return [self.generate_plan(task) for task in tasks]
    
    def save(self, plans: List[Dict], output_file: str = "parser_output/plans_v2.1.json"):
        """保存計劃"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(plans, f, indent=2, ensure_ascii=False)
        
        return output_file


# ============================================================
# 主程序
# ============================================================

def main():
    """主程序"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parser_v2.1.py <tasks_file> [function_module]")
        print("Example: python parser_v2.1.py gaia_output/gaia_level3_tasks.json gaia_function.py")
        sys.exit(1)
    
    tasks_file = sys.argv[1]
    function_module = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    parser = GAIAStepParserV21(function_module)
    generator = PlanGeneratorV21(parser)
    
    print(f"🚀 Processing {len(tasks)} tasks with v2.1 fixed extraction...")
    plans = generator.generate_all(tasks)
    
    output_file = generator.save(plans)
    print(f"\n✅ Generated: {output_file}")
    
    # 統計
    total_steps = sum(p['metadata']['total_annotated_steps'] for p in plans)
    total_extracted = sum(p['metadata']['extracted_tools'] for p in plans)
    total_reasoning = sum(p['metadata']['reasoning_steps'] for p in plans)
    total_with_params = sum(p['metadata']['tools_with_params'] for p in plans)
    high_confidence = sum(p['metadata']['high_confidence_tools'] for p in plans)
    
    print(f"\n📊 Extraction Statistics:")
    print(f"  Total steps: {total_steps}")
    print(f"  Reasoning steps: {total_reasoning} ({total_reasoning/total_steps:.1%})")
    print(f"  Tool steps extracted: {total_extracted} ({total_extracted/total_steps:.1%})")
    print(f"  With parameters: {total_with_params} ({total_with_params/total_extracted:.1%})")
    print(f"  High confidence (≥2): {high_confidence} ({high_confidence/total_extracted:.1%})")
    
    extraction_rate = total_extracted / total_steps
    if extraction_rate >= 0.80:
        print(f"\n🎉 TARGET ACHIEVED! Extraction rate: {extraction_rate:.1%} (>80%)")
    else:
        gap = 0.80 - extraction_rate
        print(f"\n⚠️  Target not met. Gap: {gap:.1%} ({gap * total_steps:.0f} more tools needed)")
    
    # v2 vs v2.1 比較
    print(f"\n📈 v2.0 vs v2.1 Comparison:")
    print(f"  v2.0: 43 tools (31.4%)")
    print(f"  v2.1: {total_extracted} tools ({extraction_rate:.1%})")
    print(f"  Improvement: +{total_extracted - 43} tools (+{(extraction_rate - 0.314)*100:.1f}%)")
    
    # 工具分布
    from collections import Counter
    all_tools = []
    for plan in plans:
        all_tools.extend(t['tool_name'] for t in plan['tool_sequence'])
    
    print(f"\n🔧 Tool Distribution:")
    for tool, count in Counter(all_tools).most_common(15):
        print(f"  {tool}: {count}")
    
    # 類別分布
    all_categories = defaultdict(int)
    for plan in plans:
        for cat, count in plan['metadata']['tool_category_distribution'].items():
            all_categories[cat] += count
    
    print(f"\n📁 Category Distribution:")
    for cat, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} ({count/total_extracted:.1%})")


if __name__ == "__main__":
    main()
