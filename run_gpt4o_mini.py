#!/usr/bin/env python3
"""
GPT-4o-mini 批次執行系統（使用您的 43 個 GAIA tools）

執行 10 題 GAIA Level 3，分析答對/答錯

使用方式：
    export OPENAI_API_KEY="sk-..."
    python run_gpt4o_mini.py --limit 10

輸出：
    - results_gpt4o_mini.json（完整執行軌跡）
    - analysis_summary.json（答對/答錯分析）
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import traceback

# 引入您的 43 個 GAIA functions
import gaia_function

try:
    from openai import OpenAI
except ImportError:
    print("錯誤：請安裝 OpenAI 套件")
    print("執行：pip install openai")
    sys.exit(1)


class GAIARunner:
    """GAIA 執行器（用 GPT-4o-mini + 43 tools）"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未設定 OPENAI_API_KEY！\n"
                "請執行：export OPENAI_API_KEY='your-key'"
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

        # 載入自動生成的 tools schema
        with open("tools_schema.json", 'r') as f:
            self.tools_schema = json.load(f)

        with open("tools_mapping.json", 'r') as f:
            self.tool_map = json.load(f)

        print(f"✓ 已載入 {len(self.tools_schema)} 個 tools")

    def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """執行單一工具"""
        try:
            # 取得實際的 function
            if tool_name not in self.tool_map:
                return {
                    "success": False,
                    "error": f"未知工具：{tool_name}"
                }

            func = getattr(gaia_function, tool_name)

            # 執行
            result = func(**arguments)

            return {
                "success": True,
                "result": result,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def run_single_task(
        self,
        task: Dict,
        max_turns: int = 20,
        timeout: int = 180
    ) -> Dict:
        """執行單一題目"""
        task_id = task["task_id"]
        question = task["Question"]
        ground_truth = task["Final answer"]
        file_path = task.get("file_path", "")

        print(f"\n{'='*70}")
        print(f"題目：{task_id}")
        print(f"問題：{question[:80]}...")
        if file_path:
            print(f"檔案：{file_path}")
        print(f"{'='*70}")

        # 準備系統提示詞
        system_prompt = f"""你是專業的問題解決助手。你有 43 個工具可用。

可用工具類別：
- 檔案讀取：read_pdf, read_csv, read_excel, read_json, read_xml, read_docx, read_text_file, read_image
- 網路：web_search, web_fetch, wikipedia_search
- 計算：calculate, statistical_analysis, correlation_analysis, moving_average
- 資料處理：filter_data, sort_data, aggregate_data, join_data, pivot_table
- 字串處理：regex_search, string_transform, split_join_text, find_in_text
- 其他：extract_zip, date_calculator, currency_converter, geocoding 等

重要規則：
1. 一步一步思考，使用合適的工具
2. 如果有檔案路徑，必須先用對應的 read_* 工具讀取
3. 計算時使用 calculate 工具
4. 最後給出明確的最終答案（只回答答案本身，不要額外解釋）

檔案路徑規則：
- 如果題目提到檔案，路徑在 data/ 資料夾下
- 完整路徑：data/{file_path}
"""

        # 建構使用者問題
        user_message = question
        if file_path:
            user_message += f"\n\n檔案位於：data/{file_path}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        execution_trace = []
        start_time = time.time()

        for turn in range(max_turns):
            if time.time() - start_time > timeout:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": "執行超時",
                    "ground_truth": ground_truth,
                    "predicted": None,
                    "execution_trace": execution_trace,
                    "turns": turn,
                    "elapsed_time": time.time() - start_time
                }

            try:
                # 呼叫 GPT-4o-mini
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools_schema,
                    tool_choice="auto",
                    temperature=0.0
                )

                assistant_message = response.choices[0].message
                messages.append(assistant_message)

                # 檢查是否有 tool calls
                if not assistant_message.tool_calls:
                    # 最終答案
                    final_answer = assistant_message.content.strip()

                    execution_trace.append({
                        "turn": turn,
                        "type": "final_answer",
                        "content": final_answer
                    })

                    # 簡單的答案驗證
                    predicted = final_answer
                    correct = self._check_answer(predicted, ground_truth)

                    return {
                        "task_id": task_id,
                        "success": True,
                        "ground_truth": ground_truth,
                        "predicted": predicted,
                        "correct": correct,
                        "execution_trace": execution_trace,
                        "turns": turn + 1,
                        "elapsed_time": time.time() - start_time
                    }

                # 執行 tool calls
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"  [{turn}] 🔧 {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:60]}...)")

                    # 執行
                    tool_result = self.execute_tool(tool_name, tool_args)

                    if tool_result["success"]:
                        print(f"       ✓ 成功")
                    else:
                        print(f"       ✗ 失敗：{tool_result['error'][:50]}...")

                    execution_trace.append({
                        "turn": turn,
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })

                    # 傳回結果
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

            except Exception as e:
                print(f"  ✗ 錯誤：{str(e)}")
                execution_trace.append({
                    "turn": turn,
                    "type": "error",
                    "error": str(e)
                })

                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e),
                    "ground_truth": ground_truth,
                    "predicted": None,
                    "correct": False,
                    "execution_trace": execution_trace,
                    "turns": turn
                }

        # 達到最大輪數
        return {
            "task_id": task_id,
            "success": False,
            "error": "達到最大輪數",
            "ground_truth": ground_truth,
            "predicted": None,
            "correct": False,
            "execution_trace": execution_trace,
            "turns": max_turns
        }

    def _check_answer(self, predicted: str, ground_truth: str) -> bool:
        """簡單的答案比對"""
        pred = predicted.lower().strip()
        gt = ground_truth.lower().strip()

        # 完全匹配
        if pred == gt:
            return True

        # 包含匹配
        if gt in pred or pred in gt:
            return True

        # 數字匹配（允許小誤差）
        try:
            pred_num = float(pred)
            gt_num = float(gt)
            return abs(pred_num - gt_num) < 0.01
        except:
            pass

        return False

    def analyze_results(self, results: List[Dict]) -> Dict:
        """分析執行結果"""
        total = len(results)
        correct = sum(1 for r in results if r.get("correct"))
        incorrect = total - correct

        correct_tasks = [r["task_id"] for r in results if r.get("correct")]
        incorrect_tasks = [
            {
                "task_id": r["task_id"],
                "ground_truth": r["ground_truth"],
                "predicted": r.get("predicted"),
                "error": r.get("error")
            }
            for r in results if not r.get("correct")
        ]

        return {
            "summary": {
                "total": total,
                "correct": correct,
                "incorrect": incorrect,
                "accuracy": correct / total if total > 0 else 0
            },
            "correct_tasks": correct_tasks,
            "incorrect_tasks": incorrect_tasks
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="執行題目數量（預設 10）")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="模型")
    parser.add_argument("--max-turns", type=int, default=20, help="最大輪數")

    args = parser.parse_args()

    # 載入題目
    with open("gaia_level3_tasks.json", 'r') as f:
        tasks = json.load(f)

    print(f"\n載入 {len(tasks)} 題 GAIA Level 3")
    print(f"執行前 {args.limit} 題\n")

    # 初始化
    try:
        runner = GAIARunner(model=args.model)
    except ValueError as e:
        print(f"錯誤：{e}")
        sys.exit(1)

    # 執行
    results = []
    for i, task in enumerate(tasks[:args.limit], 1):
        print(f"\n{'#'*70}")
        print(f"# 進度：{i}/{args.limit}")
        print(f"{'#'*70}")

        result = runner.run_single_task(task, max_turns=args.max_turns)
        results.append(result)

        # 即時儲存
        with open("results_gpt4o_mini.json", 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # 分析
    analysis = runner.analyze_results(results)

    with open("analysis_summary.json", 'w') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    # 顯示結果
    print(f"\n{'='*70}")
    print(f"執行完成！")
    print(f"{'='*70}")
    print(f"總題數：{analysis['summary']['total']}")
    print(f"答對：{analysis['summary']['correct']}")
    print(f"答錯：{analysis['summary']['incorrect']}")
    print(f"正確率：{analysis['summary']['accuracy']*100:.1f}%")
    print(f"\n答對題目：{', '.join(analysis['correct_tasks'])}")
    print(f"\n結果已儲存至：results_gpt4o_mini.json")
    print(f"分析已儲存至：analysis_summary.json")


if __name__ == "__main__":
    main()
