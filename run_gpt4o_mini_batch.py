#!/usr/bin/env python3
"""
GPT-4o-mini 批次執行系統
用 43 個 GAIA tools 執行 GAIA Level 3 題目，記錄完整執行軌跡

使用方式：
    python run_gpt4o_mini_batch.py --limit 30 --output results_gpt4o_mini.json

需要設定：
    export OPENAI_API_KEY="your-api-key-here"
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

# 引入您的 GAIA function tools
from gaia_function import *

try:
    from openai import OpenAI
except ImportError:
    print("錯誤：請安裝 OpenAI 套件")
    print("執行：pip install openai")
    sys.exit(1)


class GPT4oMiniBatchRunner:
    """GPT-4o-mini 批次執行器"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未設定 OPENAI_API_KEY！\n"
                "請執行：export OPENAI_API_KEY='your-key'"
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.tools_schema = self._build_tools_schema()

    def _build_tools_schema(self) -> List[Dict]:
        """建構 43 個 tools 的 OpenAI function calling schema"""
        # 這裡列出您的 43 個 tools
        # 我會根據 gaia_function.py 裡的 function 自動生成

        tools = []

        # 基礎工具
        tools.append({
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "搜尋網路資訊，返回搜尋結果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜尋關鍵字"},
                        "num_results": {"type": "integer", "description": "返回結果數量", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "抓取網頁內容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "網頁 URL"}
                    },
                    "required": ["url"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "計算數學表達式",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "數學表達式"}
                    },
                    "required": ["expression"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "讀取本地檔案內容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "檔案路徑"}
                    },
                    "required": ["file_path"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "read_json",
                "description": "讀取並解析 JSON 檔案",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "JSON 檔案路徑"}
                    },
                    "required": ["file_path"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "read_csv",
                "description": "讀取 CSV 檔案",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "CSV 檔案路徑"},
                        "delimiter": {"type": "string", "description": "分隔符", "default": ","}
                    },
                    "required": ["file_path"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "read_excel",
                "description": "讀取 Excel 檔案",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Excel 檔案路徑"},
                        "sheet_name": {"type": "string", "description": "工作表名稱", "default": None}
                    },
                    "required": ["file_path"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "read_xml",
                "description": "讀取並解析 XML 檔案",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "XML 檔案路徑"}
                    },
                    "required": ["file_path"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "extract_zip",
                "description": "解壓縮 ZIP 檔案",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zip_path": {"type": "string", "description": "ZIP 檔案路徑"},
                        "extract_to": {"type": "string", "description": "解壓縮目標路徑"}
                    },
                    "required": ["zip_path"]
                }
            }
        })

        # 文字處理工具
        tools.append({
            "type": "function",
            "function": {
                "name": "text_search",
                "description": "在文字中搜尋關鍵字",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要搜尋的文字"},
                        "pattern": {"type": "string", "description": "搜尋模式"}
                    },
                    "required": ["text", "pattern"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "regex_match",
                "description": "使用正則表達式匹配文字",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要匹配的文字"},
                        "pattern": {"type": "string", "description": "正則表達式"}
                    },
                    "required": ["text", "pattern"]
                }
            }
        })

        # 統計工具
        tools.append({
            "type": "function",
            "function": {
                "name": "statistics_mean",
                "description": "計算平均值",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numbers": {"type": "array", "items": {"type": "number"}, "description": "數字陣列"}
                    },
                    "required": ["numbers"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "statistics_median",
                "description": "計算中位數",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numbers": {"type": "array", "items": {"type": "number"}, "description": "數字陣列"}
                    },
                    "required": ["numbers"]
                }
            }
        })

        tools.append({
            "type": "function",
            "function": {
                "name": "count_items",
                "description": "計算項目出現次數",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {"type": "array", "description": "項目陣列"}
                    },
                    "required": ["items"]
                }
            }
        })

        # TODO: 補完剩下的 tools（您可以從 gaia_function.py 複製）
        # 現在先用這 14 個示範

        return tools

    def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """執行單一工具，返回結果"""
        try:
            # 映射到實際的 Python function
            tool_map = {
                "web_search": web_search,
                "web_fetch": web_fetch,
                "calculate": calculate,
                "read_file": read_file,
                "read_json": read_json,
                "read_csv": read_csv,
                "read_excel": read_excel,
                "read_xml": read_xml,
                "extract_zip": extract_zip,
                "text_search": text_search,
                "regex_match": regex_match,
                "statistics_mean": statistics_mean,
                "statistics_median": statistics_median,
                "count_items": count_items,
                # TODO: 補完剩下的映射
            }

            if tool_name not in tool_map:
                return {
                    "success": False,
                    "error": f"未知工具：{tool_name}"
                }

            func = tool_map[tool_name]
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
        timeout: int = 300
    ) -> Dict:
        """執行單一題目"""
        task_id = task["task_id"]
        question = task["Question"]
        ground_truth = task["Final answer"]

        print(f"\n{'='*60}")
        print(f"執行題目：{task_id}")
        print(f"問題：{question[:100]}...")
        print(f"='*60}")

        # 準備系統提示詞
        system_prompt = """你是一個專業的問題解決助手。
你有一組工具可以使用，包括網路搜尋、檔案讀取、數學計算等。
請一步一步思考，使用合適的工具來解答問題。
最後請提供明確的最終答案。"""

        # 初始化對話
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
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
                    "turns": turn
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
                    # 沒有 tool call，代表已經給出最終答案
                    final_answer = assistant_message.content

                    execution_trace.append({
                        "turn": turn,
                        "type": "final_answer",
                        "content": final_answer
                    })

                    return {
                        "task_id": task_id,
                        "success": True,
                        "ground_truth": ground_truth,
                        "predicted": final_answer,
                        "execution_trace": execution_trace,
                        "turns": turn + 1,
                        "elapsed_time": time.time() - start_time
                    }

                # 執行 tool calls
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"  [Turn {turn}] 執行工具：{tool_name}")
                    print(f"    參數：{tool_args}")

                    # 執行工具
                    tool_result = self.execute_tool(tool_name, tool_args)

                    execution_trace.append({
                        "turn": turn,
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })

                    # 把結果傳回給模型
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

            except Exception as e:
                execution_trace.append({
                    "turn": turn,
                    "type": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

                return {
                    "task_id": task_id,
                    "success": False,
                    "error": str(e),
                    "ground_truth": ground_truth,
                    "predicted": None,
                    "execution_trace": execution_trace,
                    "turns": turn
                }

        # 達到最大輪數
        return {
            "task_id": task_id,
            "success": False,
            "error": "達到最大輪數限制",
            "ground_truth": ground_truth,
            "predicted": None,
            "execution_trace": execution_trace,
            "turns": max_turns
        }

    def run_batch(
        self,
        tasks: List[Dict],
        limit: Optional[int] = None,
        output_file: Optional[str] = None
    ) -> List[Dict]:
        """批次執行多個題目"""
        if limit:
            tasks = tasks[:limit]

        print(f"\n開始批次執行 {len(tasks)} 個題目...")
        print(f"模型：{self.model}")
        print(f"輸出檔案：{output_file or '（不儲存）'}")

        results = []

        for i, task in enumerate(tasks, 1):
            print(f"\n進度：{i}/{len(tasks)}")
            result = self.run_single_task(task)
            results.append(result)

            # 即時儲存
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

        # 統計
        success_count = sum(1 for r in results if r.get("success"))
        print(f"\n{'='*60}")
        print(f"執行完成！")
        print(f"成功：{success_count}/{len(results)}")
        print(f"成功率：{success_count/len(results)*100:.1f}%")
        print(f"='*60}")

        return results


def main():
    parser = argparse.ArgumentParser(description="GPT-4o-mini 批次執行 GAIA 題目")
    parser.add_argument("--limit", type=int, default=30, help="執行題目數量")
    parser.add_argument("--output", type=str, default="results_gpt4o_mini.json", help="輸出檔案")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI 模型")
    parser.add_argument("--max-turns", type=int, default=20, help="最大輪數")

    args = parser.parse_args()

    # 載入題目
    tasks_file = "gaia_level3_tasks.json"
    if not Path(tasks_file).exists():
        print(f"錯誤：找不到題目檔案 {tasks_file}")
        sys.exit(1)

    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    # 初始化執行器
    try:
        runner = GPT4oMiniBatchRunner(model=args.model)
    except ValueError as e:
        print(f"錯誤：{e}")
        sys.exit(1)

    # 執行
    results = runner.run_batch(
        tasks,
        limit=args.limit,
        output_file=args.output
    )

    print(f"\n結果已儲存至：{args.output}")


if __name__ == "__main__":
    main()
