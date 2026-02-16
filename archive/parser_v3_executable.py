#!/usr/bin/env python3
"""
改進版 Parser v3.0
只產生完全具體、可直接執行的步驟
"""

import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class ExecutablePlanParser:
    """只產生可執行步驟的 Parser"""
    
    def __init__(self, gaia_tasks_file: str, data_dir: str = './data'):
        """
        Args:
            gaia_tasks_file: GAIA tasks JSON 檔案路徑
            data_dir: 資料檔案目錄
        """
        self.data_dir = Path(data_dir)
        
        # 載入任務
        with open(gaia_tasks_file, 'r', encoding='utf-8') as f:
            self.tasks = json.load(f)
        
        # 建立檔案映射表
        self.file_map = self._build_file_map()
        
        # 定義工具簽名（正確的參數名稱）
        self.tool_signatures = {
            'web_search': ['query', 'num_results'],
            'web_fetch': ['url', 'timeout'],
            'calculate': ['expression'],
            'read_pdf': ['file_path', 'page_numbers'],
            'read_csv': ['file_path', 'encoding'],
            'read_excel': ['file_path', 'sheet_name'],
            'read_json': ['file_path'],
            'read_xml': ['file_path'],
            'read_image': ['file_path'],
            'image_to_text': ['file_path', 'lang'],
            'filter_data': ['data', 'conditions'],
            'compare_values': ['value1', 'value2'],
            'find_in_text': ['text', 'search_terms'],
            'count_occurrences': ['data', 'target'],
            'extract_information': ['text', 'extract_type', 'keywords', 'pattern'],
            'deduplicate_data': ['data', 'key_fields'],
            'unit_converter': ['value', 'from_unit', 'to_unit', 'unit_type'],
        }
        
        # 參數名稱映射（錯誤 -> 正確）
        self.param_mapping = {
            'extract_information': {
                'target': 'keywords',
            },
            'deduplicate_data': {
                'key': 'key_fields',
            },
        }
        
        # unit_converter 支援的類型
        self.valid_unit_types = ['length', 'weight', 'temperature', 'time']
    
    def _build_file_map(self) -> Dict[str, str]:
        """建立 task_id -> actual_file 的映射"""
        file_map = {}
        
        if not self.data_dir.exists():
            return file_map
        
        # 掃描 data 目錄
        for task in self.tasks:
            task_id = task['task_id']
            file_name = task.get('file_name', '')
            
            if file_name:
                # 找到實際檔案
                for f in self.data_dir.iterdir():
                    if f.is_file() and f.name.startswith(file_name.split('.')[0][:8]):
                        file_map[task_id] = str(f)
                        break
        
        return file_map
    
    def is_placeholder(self, value: Any) -> bool:
        """檢查是否為佔位符"""
        if not isinstance(value, str):
            return False
        
        # 常見佔位符模式
        placeholder_patterns = [
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
            r'<conversion_constant>',  # <conversion_constant>
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def is_valid_url(self, url: str) -> bool:
        """檢查是否為有效的 URL"""
        if self.is_placeholder(url):
            return False
        
        # 必須以 http:// 或 https:// 開頭
        if not url.startswith(('http://', 'https://')):
            return False
        
        # 不能包含佔位符
        if '<' in url or '>' in url:
            return False
        
        return True
    
    def is_valid_file_path(self, file_path: str) -> bool:
        """檢查檔案路徑是否有效（檔案存在）"""
        if self.is_placeholder(file_path):
            return False
        
        # 檢查檔案是否存在
        path = Path(file_path)
        return path.exists() and path.is_file()
    
    def clean_calculate_expression(self, expression: str) -> Optional[str]:
        """清理計算表達式，移除單位"""
        if self.is_placeholder(expression):
            return None
        
        # 移除單位
        # g/mol, cm, L-atm, K-mol 等
        cleaned = re.sub(r'\s*[a-zA-Z]+(/[a-zA-Z]+)*', '', expression)
        
        # 移除 %
        cleaned = cleaned.replace('%', '/100')
        
        # 驗證是否為有效表達式
        try:
            # 測試評估
            eval(cleaned)
            return cleaned
        except:
            return None
    
    def fix_tool_params(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """修正工具參數名稱"""
        if tool_name not in self.param_mapping:
            return params
        
        mapping = self.param_mapping[tool_name]
        fixed_params = {}
        
        for key, value in params.items():
            # 如果參數名稱在映射表中，使用正確的名稱
            new_key = mapping.get(key, key)
            fixed_params[new_key] = value
        
        return fixed_params
    
    def is_step_executable(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判斷步驟是否可執行
        
        Returns:
            (is_executable, reason)
        """
        
        # 檢查每個參數
        for key, value in arguments.items():
            # 檢查佔位符
            if self.is_placeholder(value):
                return False, f"參數 {key} 包含佔位符: {value}"
        
        # 針對特定工具的檢查
        if tool_name == 'web_fetch':
            url = arguments.get('url', '')
            if not self.is_valid_url(url):
                return False, f"無效的 URL: {url}"
        
        elif tool_name in ['read_pdf', 'read_csv', 'read_excel', 'read_json', 'read_xml', 'read_image']:
            file_path = arguments.get('file_path', '')
            if not self.is_valid_file_path(file_path):
                return False, f"檔案不存在: {file_path}"
        
        elif tool_name == 'calculate':
            expression = arguments.get('expression', '')
            cleaned = self.clean_calculate_expression(expression)
            if cleaned is None:
                return False, f"無法清理的表達式: {expression}"
        
        elif tool_name == 'unit_converter':
            unit_type = arguments.get('unit_type', 'length')
            if unit_type not in self.valid_unit_types:
                return False, f"不支援的單位類型: {unit_type}"
        
        elif tool_name in ['extract_information', 'filter_data', 'find_in_text', 'count_occurrences']:
            # 這些工具通常需要從前面步驟獲取資料
            data_param = arguments.get('data') or arguments.get('text')
            if self.is_placeholder(data_param):
                return False, f"資料參數是佔位符"
        
        return True, "OK"
    
    def process_step(self, step: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
        """
        處理單個步驟，返回可執行的步驟或 None
        """
        tool_name = step.get('tool_name')
        arguments = step.get('arguments', {})
        
        # 修正檔案路徑（如果這個任務有對應的檔案）
        if task_id in self.file_map:
            if 'file_path' in arguments:
                old_path = arguments['file_path']
                if not self.is_valid_file_path(old_path):
                    # 使用映射的實際檔案
                    arguments['file_path'] = self.file_map[task_id]
        
        # 修正參數名稱
        arguments = self.fix_tool_params(tool_name, arguments)
        
        # 清理 calculate 表達式
        if tool_name == 'calculate' and 'expression' in arguments:
            cleaned = self.clean_calculate_expression(arguments['expression'])
            if cleaned:
                arguments['expression'] = cleaned
        
        # 檢查是否可執行
        is_exec, reason = self.is_step_executable(tool_name, arguments)
        
        if not is_exec:
            # 不可執行，返回 None
            return None
        
        # 可執行，返回處理後的步驟
        return {
            'step_id': step.get('step_id'),
            'tool_name': tool_name,
            'arguments': arguments,
            'description': step.get('description', ''),
            'executable': True,
            'skip_reason': None
        }
    
    def parse_task(self, task: Dict[str, Any], original_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析單個任務，產生可執行的 plan
        """
        task_id = task['task_id']
        original_steps = original_plan.get('tool_sequence', [])
        
        executable_steps = []
        skipped_steps = []
        
        for step_idx, step in enumerate(original_steps):
            processed_step = self.process_step(step, task_id)
            
            if processed_step:
                executable_steps.append(processed_step)
            else:
                # 記錄跳過的步驟
                tool_name = step.get('tool_name')
                is_exec, reason = self.is_step_executable(tool_name, step.get('arguments', {}))
                
                skipped_steps.append({
                    'step_id': step.get('step_id'),
                    'tool_name': tool_name,
                    'description': step.get('description', '')[:100],
                    'skip_reason': reason
                })
        
        return {
            'task_id': task_id,
            'question': task['Question'],
            'final_answer': task['Final answer'],
            'file_name': task.get('file_name', ''),
            'tool_sequence': executable_steps,
            'skipped_steps': skipped_steps,
            'stats': {
                'total_steps': len(original_steps),
                'executable_steps': len(executable_steps),
                'skipped_steps': len(skipped_steps),
                'executable_rate': len(executable_steps) / len(original_steps) if original_steps else 0
            }
        }
    
    def parse_all_tasks(self, original_plans_file: str, output_file: str):
        """
        解析所有任務
        """
        # 載入原始 plans
        with open(original_plans_file, 'r', encoding='utf-8') as f:
            original_plans = json.load(f)
        
        # 建立 task_id -> plan 的映射
        plans_map = {p['task_id']: p for p in original_plans}
        
        # 解析每個任務
        executable_plans = []
        
        print("=" * 80)
        print("開始解析任務...")
        print("=" * 80)
        print()
        
        for task in self.tasks:
            task_id = task['task_id']
            
            if task_id not in plans_map:
                print(f"⚠️  跳過 {task_id}: 沒有對應的 plan")
                continue
            
            original_plan = plans_map[task_id]
            executable_plan = self.parse_task(task, original_plan)
            executable_plans.append(executable_plan)
            
            # 輸出統計
            stats = executable_plan['stats']
            print(f"✅ {task_id}")
            print(f"   總步驟: {stats['total_steps']}")
            print(f"   可執行: {stats['executable_steps']} ({stats['executable_rate']*100:.1f}%)")
            print(f"   跳過: {stats['skipped_steps']}")
            print()
        
        # 儲存結果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(executable_plans, f, indent=2, ensure_ascii=False)
        
        # 輸出總統計
        total_original = sum(p['stats']['total_steps'] for p in executable_plans)
        total_executable = sum(p['stats']['executable_steps'] for p in executable_plans)
        total_skipped = sum(p['stats']['skipped_steps'] for p in executable_plans)
        
        print("=" * 80)
        print("總統計")
        print("=" * 80)
        print(f"任務數: {len(executable_plans)}")
        print(f"原始步驟數: {total_original}")
        print(f"可執行步驟數: {total_executable} ({total_executable/total_original*100:.1f}%)")
        print(f"跳過步驟數: {total_skipped}")
        print()
        print(f"✅ 已儲存到: {output_file}")
        print()


def main():
    """主程式"""
    parser = ExecutablePlanParser(
        gaia_tasks_file='gaia_output/gaia_level3_tasks.json',
        data_dir='./data'
    )
    
    parser.parse_all_tasks(
        original_plans_file='parser_output/plans_v2.1.json',
        output_file='parser_output/plans_v3_executable.json'
    )


if __name__ == '__main__':
    main()
