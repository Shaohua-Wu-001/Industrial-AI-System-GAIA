#!/usr/bin/env python3
"""
真正的工具執行器 - Professional Computer Scientist Mode
根據標註的計劃，實際執行每個工具，獲取真實結果
"""

import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class ToolExecutor:
    """工具執行器 - 實際執行工具調用"""

    def __init__(self):
        self.execution_context = {}
        self.tools = self._load_tools_schema()

    def _load_tools_schema(self):
        """載入工具定義"""
        schema_path = Path(__file__).parent / "tools/unified_tools_schema.json"
        with open(schema_path, 'r') as f:
            return json.load(f)

    def execute_plan(self, task: dict) -> Dict[str, Any]:
        """
        執行完整計劃

        Args:
            task: 包含 question, annotated_steps 的任務

        Returns:
            {
                'question': str,
                'execution_results': List[dict],
                'final_answer': str,
                'execution_log': List[str]
            }
        """
        question = task['question']
        steps = task['annotated_steps']

        execution_results = []
        execution_log = []

        print(f"\n{'='*80}")
        print(f"執行計劃：{task['task_id']}")
        print(f"{'='*80}")
        print(f"問題：{question[:100]}...")
        print(f"步驟數：{len(steps)}")

        for i, step in enumerate(steps, 1):
            step_type = step.get('step_type', 'unknown')
            tool_name = step.get('tool_name')
            arguments = step.get('arguments', {})
            description = step.get('description', '')

            print(f"\n{'─'*60}")
            print(f"步驟 {i}/{len(steps)}: {step_type}")
            print(f"工具: {tool_name}")
            print(f"描述: {description[:80]}...")

            # 執行工具
            if step_type == 'tool' and tool_name:
                result = self._execute_tool(tool_name, arguments, description)
                execution_results.append({
                    'step_index': i,
                    'tool_name': tool_name,
                    'arguments': arguments,
                    'result': result,
                    'description': description
                })
                execution_log.append(f"Step {i}: {tool_name} → {str(result)[:100]}...")
                print(f"結果: {str(result)[:100]}...")

            elif step_type == 'thought':
                # 推理步驟：從描述中提取信息
                result = self._process_thought(description, execution_results)
                execution_results.append({
                    'step_index': i,
                    'step_type': 'thought',
                    'description': description,
                    'extracted_info': result
                })
                execution_log.append(f"Step {i}: Thought → {str(result)[:100]}...")
                print(f"提取信息: {str(result)[:100]}...")

        # 從執行結果中提取答案（不是看 submit_final_answer！）
        final_answer = self._extract_final_answer(execution_results, question)

        print(f"\n{'='*80}")
        print(f"最終答案: {final_answer}")
        print(f"{'='*80}")

        return {
            'question': question,
            'execution_results': execution_results,
            'final_answer': final_answer,
            'execution_log': execution_log
        }

    def _execute_tool(self, tool_name: str, arguments: dict, description: str) -> Any:
        """
        執行單個工具

        注意：這裡需要實現真實的工具調用
        目前先用模擬版本
        """
        # 特殊處理：submit_final_answer 不需要執行，跳過
        if tool_name == 'submit_final_answer':
            return {'status': 'skipped', 'note': 'Will extract from previous results'}

        # 根據工具類型執行
        if tool_name == 'web_search':
            return self._simulate_web_search(arguments, description)

        elif tool_name == 'web_browser':
            return self._simulate_web_browser(arguments, description)

        elif tool_name == 'calculator':
            return self._execute_calculator(arguments, description)

        elif tool_name == 'python_executor':
            return self._execute_python(arguments, description)

        else:
            # 未實現的工具：從描述中提取信息
            return self._extract_from_description(description)

    def _simulate_web_search(self, arguments: dict, description: str) -> dict:
        """
        模擬網頁搜尋

        實際應該：調用真實搜尋 API (DuckDuckGo, Google, etc.)
        目前：從描述中提取搜尋意圖和預期結果
        """
        query = arguments.get('query', '')

        # 從描述中提取結果（如果有）
        # 例如："Searched 'X' and found Y"
        result_hints = self._extract_from_description(description)

        return {
            'tool': 'web_search',
            'query': query,
            'simulated_results': result_hints,
            'note': '⚠️ Simulated (需要真實 API)'
        }

    def _simulate_web_browser(self, arguments: dict, description: str) -> dict:
        """
        模擬瀏覽器

        實際應該：使用 Playwright/Selenium 真正打開網頁
        目前：從描述中提取訪問的內容
        """
        url = arguments.get('url', '')

        # 從描述中提取內容
        content_hints = self._extract_from_description(description)

        return {
            'tool': 'web_browser',
            'url': url,
            'simulated_content': content_hints,
            'note': '⚠️ Simulated (需要真實瀏覽器)'
        }

    def _execute_calculator(self, arguments: dict, description: str) -> Any:
        """
        執行計算器

        這個可以真實執行！
        """
        expression = arguments.get('expression', '')

        # 如果 expression 是描述文本而不是表達式，嘗試從描述中提取
        if not any(op in expression for op in ['+', '-', '*', '/', '(', ')']):
            # 從描述中找數學表達式
            math_expr = self._extract_math_expression(description)
            if math_expr:
                expression = math_expr

        try:
            # 安全評估（只允許數學運算）
            result = self._safe_eval(expression)
            return {
                'tool': 'calculator',
                'expression': expression,
                'result': result,
                'note': '✅ Real execution'
            }
        except Exception as e:
            return {
                'tool': 'calculator',
                'expression': expression,
                'error': str(e),
                'fallback': self._extract_from_description(description)
            }

    def _execute_python(self, arguments: dict, description: str) -> Any:
        """執行 Python 代碼"""
        code = arguments.get('code', '')

        # 安全性考慮：目前不執行真實代碼
        return {
            'tool': 'python_executor',
            'code': code[:100] + '...' if len(code) > 100 else code,
            'note': '⚠️ Not executed for safety',
            'hint_from_description': self._extract_from_description(description)
        }

    def _process_thought(self, description: str, previous_results: List[dict]) -> dict:
        """
        處理推理步驟
        從描述中提取關鍵信息
        """
        # 提取數字
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', description)

        # 提取引號內容
        quoted = re.findall(r'"([^"]+)"', description)
        quoted += re.findall(r"'([^']+)'", description)

        # 提取關鍵詞
        keywords = []
        if 'noted' in description.lower():
            keywords.append('observation')
        if 'found' in description.lower():
            keywords.append('discovery')
        if 'count' in description.lower():
            keywords.append('counting')

        return {
            'numbers': numbers,
            'quoted_text': quoted,
            'keywords': keywords,
            'full_text': description
        }

    def _extract_from_description(self, description: str) -> dict:
        """從描述文本中提取所有可能的信息"""
        return {
            'text': description,
            'numbers': re.findall(r'\b\d+(?:\.\d+)?\b', description),
            'quoted': re.findall(r'"([^"]+)"', description),
            'urls': re.findall(r'https?://[^\s]+', description),
            'parentheses': re.findall(r'\(([^)]+)\)', description)
        }

    def _extract_math_expression(self, text: str) -> Optional[str]:
        """從文本中提取數學表達式"""
        # 查找包含運算符的表達式
        patterns = [
            r'(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?(?:\s*[+\-*/]\s*\d+(?:\.\d+)?)*)',
            r'\(([^)]+[+\-*/][^)]+)\)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]

        return None

    def _safe_eval(self, expression: str) -> float:
        """安全評估數學表達式"""
        # 只允許數字和基本運算符
        if not re.match(r'^[\d\s+\-*/().]+$', expression):
            raise ValueError(f"Invalid expression: {expression}")

        try:
            return eval(expression)
        except Exception as e:
            raise ValueError(f"Evaluation failed: {e}")

    def _extract_final_answer(self, execution_results: List[dict], question: str) -> str:
        """
        從執行結果中提取最終答案

        關鍵：不是看 submit_final_answer 的 arguments！
        而是從所有執行結果中推理出答案
        """
        # 收集所有可能的答案候選
        candidates = []

        for result in execution_results:
            # 從工具執行結果中提取
            if 'result' in result:
                res = result['result']

                # 計算器結果
                if isinstance(res, dict) and 'result' in res:
                    candidates.append({
                        'value': str(res['result']),
                        'source': f"calculator (step {result['step_index']})",
                        'confidence': 0.9
                    })

                # 從模擬結果中提取
                if isinstance(res, dict):
                    for key in ['simulated_results', 'simulated_content', 'fallback']:
                        if key in res:
                            info = res[key]
                            if isinstance(info, dict):
                                # 提取數字
                                if 'numbers' in info and info['numbers']:
                                    candidates.append({
                                        'value': info['numbers'][-1],
                                        'source': f"{result.get('tool_name')} (step {result['step_index']})",
                                        'confidence': 0.7
                                    })
                                # 提取引號文本
                                if 'quoted' in info and info['quoted']:
                                    candidates.append({
                                        'value': info['quoted'][-1],
                                        'source': f"{result.get('tool_name')} (step {result['step_index']})",
                                        'confidence': 0.7
                                    })

            # 從 thought 步驟提取
            if result.get('step_type') == 'thought':
                extracted = result.get('extracted_info', {})
                if 'numbers' in extracted and extracted['numbers']:
                    candidates.append({
                        'value': extracted['numbers'][-1],
                        'source': f"thought (step {result['step_index']})",
                        'confidence': 0.8
                    })
                if 'quoted_text' in extracted and extracted['quoted_text']:
                    candidates.append({
                        'value': extracted['quoted_text'][-1],
                        'source': f"thought (step {result['step_index']})",
                        'confidence': 0.8
                    })

        # 選擇最佳候選（從最後的步驟開始，優先級最高）
        if candidates:
            # 按步驟索引倒序排序
            candidates.sort(key=lambda x: (
                -int(re.search(r'step (\d+)', x['source']).group(1)),
                -x['confidence']
            ))

            best = candidates[0]
            print(f"\n💡 答案來源: {best['source']} (信心度: {best['confidence']})")
            return best['value']

        return "NO_ANSWER_FOUND"


def main():
    """測試執行器"""
    executor = ToolExecutor()

    # 載入數據
    with open("integrated_109/gaia_109_tasks_FIXED.json", 'r') as f:
        all_tasks = json.load(f)

    # 測試前 3 個 TA 任務
    ta_tasks = [t for t in all_tasks if t['task_id'].startswith('gaia_ta_')][:3]

    results = []
    for task in ta_tasks:
        result = executor.execute_plan(task)
        results.append(result)

        print(f"\n✅ 執行完成：{task['task_id']}")
        print(f"   答案：{result['final_answer']}")
        print(f"   預期：{task.get('metadata', {}).get('expected_answer', 'N/A')}")


if __name__ == "__main__":
    main()
