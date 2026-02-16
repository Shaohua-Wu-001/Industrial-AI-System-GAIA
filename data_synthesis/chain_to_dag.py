#!/usr/bin/env python3
"""
Chain-to-DAG 轉換器
把線性的 tool_sequence 轉換成 DAG（有向無環圖）

使用：
    python chain_to_dag.py

輸入：
    - analysis_report.json（只處理答對的題目）

輸出：
    - dags.json（每題的 DAG 結構）
"""

import json
import re
from typing import Dict, List, Any, Set, Tuple


class ChainToDAGConverter:
    """Chain 轉 DAG 轉換器"""

    def __init__(self):
        pass

    def convert_task(self, task: Dict) -> Dict:
        """轉換單一題目的 chain 成 DAG"""

        task_id = task["task_id"]
        plan = task["plan"]
        tool_sequence = plan.get("tool_sequence", [])

        print(f"\n處理：{task_id}")
        print(f"  原始步驟數：{len(tool_sequence)}")

        # 建立節點（過濾掉 tool_name=None 的推理步驟）
        nodes = []
        for i, step in enumerate(tool_sequence):
            tool_name = step["tool_name"]

            # 跳過 None tool（推理步驟、元描述）
            if tool_name is None:
                continue

            node = {
                "id": step["step_id"],
                "index": len(nodes),  # 使用過濾後的索引
                "tool": tool_name,
                "arguments": step["arguments"],
                "description": step.get("description", ""),
                "dependencies": []  # 後面計算
            }
            nodes.append(node)

        # 分析依賴關係
        edges = self._analyze_dependencies(nodes, tool_sequence)

        # 建立 DAG
        dag = {
            "task_id": task_id,
            "question": plan.get("question", ""),
            "final_answer": plan.get("final_answer", ""),
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "max_depth": self._compute_depth(nodes, edges),
                "parallelizable_steps": self._count_parallelizable(nodes, edges)
            }
        }

        print(f"  DAG 節點數：{dag['stats']['num_nodes']}")
        print(f"  DAG 邊數：{dag['stats']['num_edges']}")
        print(f"  最大深度：{dag['stats']['max_depth']}")
        print(f"  可平行步驟：{dag['stats']['parallelizable_steps']}")

        return dag

    def _analyze_dependencies(
        self,
        nodes: List[Dict],
        tool_sequence: List[Dict]
    ) -> List[Dict]:
        """分析節點間的依賴關係"""

        edges = []
        node_outputs = {}  # node_id -> 輸出資料

        for i, node in enumerate(nodes):
            tool_name = node.get("tool")
            args = node.get("arguments", {})
            node_id = node.get("id")

            # 跳過無效節點
            if not tool_name or not node_id:
                continue

            # 判斷此節點的輸出類型
            if tool_name.startswith("read_"):
                # 讀取類工具：輸出檔案內容
                node_outputs[node_id] = {"type": "file_content", "format": tool_name.replace("read_", "")}

            elif tool_name == "web_search":
                # 搜尋：輸出搜尋結果
                node_outputs[node_id] = {"type": "search_results"}

            elif tool_name == "web_fetch":
                # 抓取：輸出網頁內容
                node_outputs[node_id] = {"type": "web_content"}

            elif tool_name == "calculate":
                # 計算：輸出數值
                node_outputs[node_id] = {"type": "number"}

            elif tool_name == "extract_zip":
                # 解壓縮：輸出檔案列表
                node_outputs[node_id] = {"type": "file_list"}

            else:
                # 其他：通用資料
                node_outputs[node_id] = {"type": "data"}

            # 檢查參數是否依賴前面的節點
            dependencies = self._find_dependencies(node_id, args, nodes[:i], node_outputs)

            for dep_id, data_type in dependencies:
                edges.append({
                    "from": dep_id,
                    "to": node_id,
                    "data_type": data_type
                })
                # 更新節點的依賴列表
                node["dependencies"].append(dep_id)

        return edges

    def _find_dependencies(
        self,
        current_id: str,
        args: Dict,
        previous_nodes: List[Dict],
        node_outputs: Dict
    ) -> List[Tuple[str, str]]:
        """
        找出當前節點依賴哪些前面的節點（改進版）

        依賴推斷規則（按優先級）：
        1. Placeholder 規則（最高優先級）
        2. 參數名稱規則
        3. 工具語義規則
        4. 順序規則（最後採用）
        """

        dependencies = []
        current_tool = None

        # 獲取當前工具名稱
        for node in previous_nodes:
            if node["id"] == current_id:
                current_tool = node.get("tool")
                break

        # 如果在當前節點列表中找不到，從外部獲取
        if not current_tool:
            # 嘗試從 step_id 推斷 (例如 step_4 可能在後面會被處理)
            pass

        # ========== 規則 1：Placeholder 分析（最精確） ==========
        for key, value in args.items():
            if not isinstance(value, str):
                continue

            # 1.1: <from_previous_X> - 依賴前一個 X 類型工具
            if "<from_previous_" in value.lower():
                import re
                match = re.search(r'<from_previous_(\w+)>', value, re.IGNORECASE)
                if match:
                    target_tool = match.group(1).lower()
                    for prev_node in reversed(previous_nodes):
                        prev_tool = prev_node.get("tool", "")
                        if prev_tool and target_tool in prev_tool.lower():
                            dependencies.append((prev_node["id"], f"output_from_{target_tool}"))
                            break

            # 1.2: <from_context> - 依賴最近的資料源
            elif "<from_context>" in value.lower():
                for prev_node in reversed(previous_nodes):
                    prev_tool = prev_node.get("tool", "")
                    if prev_tool and (prev_tool.startswith("read_") or
                                     prev_tool.startswith("web_") or
                                     prev_tool == "extract_information"):
                        dependencies.append((prev_node["id"], "context_data"))
                        break

            # 1.3: <iterate:field> - 依賴包含該 field 的工具
            elif "<iterate:" in value.lower():
                import re
                match = re.search(r'<iterate:(\w+)>', value, re.IGNORECASE)
                if match:
                    field = match.group(1).lower()
                    # 尋找可能產生該 field 的工具
                    for prev_node in reversed(previous_nodes):
                        prev_tool = prev_node.get("tool", "")
                        # read_json/read_excel 可能產生結構化資料
                        if prev_tool in ["read_json", "read_excel", "read_xml", "web_fetch"]:
                            dependencies.append((prev_node["id"], f"field_{field}"))
                            break

        # ========== 規則 2：參數名稱分析 ==========

        # 2.1: file_path 參數 - 依賴檔案來源
        if "file_path" in args:
            file_path = args["file_path"]
            if isinstance(file_path, str):
                # 如果包含 placeholder，已經在規則 1 處理
                if "<" not in file_path:
                    # 檢查是否依賴 extract_zip
                    for prev_node in reversed(previous_nodes):
                        if prev_node["tool"] == "extract_zip":
                            dependencies.append((prev_node["id"], "extracted_file"))
                            break

        # 2.2: url 參數 - 依賴 web_search
        if "url" in args:
            url = args["url"]
            if isinstance(url, str) and "<" not in url:
                for prev_node in reversed(previous_nodes):
                    if prev_node["tool"] == "web_search":
                        dependencies.append((prev_node["id"], "search_url"))
                        break

        # 2.3: data 參數 - 依賴資料源
        if "data" in args:
            data = args["data"]
            if isinstance(data, str) and "<" not in data:
                for prev_node in reversed(previous_nodes):
                    prev_tool = prev_node.get("tool", "")
                    if prev_tool and (prev_tool.startswith("read_") or prev_tool == "extract_information"):
                        dependencies.append((prev_node["id"], "source_data"))
                        break

        # ========== 規則 3：工具語義分析 ==========

        # 找出當前節點的工具類型（如果還沒找到）
        if not current_tool:
            # 從 node list 中尋找
            for node in previous_nodes:
                if node["id"] == current_id:
                    current_tool = node.get("tool")
                    break

        if current_tool:
            # 3.1: calculate - 依賴所有前面的資料提取工具
            if current_tool == "calculate":
                # 尋找最近的資料來源
                for prev_node in reversed(previous_nodes):
                    prev_tool = prev_node.get("tool", "")
                    if prev_tool and (prev_tool.startswith("read_") or
                                     prev_tool == "web_fetch" or
                                     prev_tool == "extract_information" or
                                     prev_tool == "count_occurrences"):
                        dependencies.append((prev_node["id"], "calculation_input"))
                        break

            # 3.2: compare_values - 依賴前面的 calculate
            elif current_tool == "compare_values":
                for prev_node in reversed(previous_nodes):
                    if prev_node.get("tool") == "calculate":
                        dependencies.append((prev_node["id"], "comparison_value"))
                        break

            # 3.3: filter_data, sort_data 等 - 依賴資料源
            elif current_tool in ["filter_data", "sort_data", "deduplicate_data", "aggregate_data"]:
                for prev_node in reversed(previous_nodes):
                    prev_tool = prev_node.get("tool", "")
                    if prev_tool and prev_tool.startswith("read_"):
                        dependencies.append((prev_node["id"], "data_source"))
                        break

            # 3.4: count_occurrences, find_in_text - 依賴文字/資料源
            elif current_tool in ["count_occurrences", "find_in_text", "extract_information"]:
                for prev_node in reversed(previous_nodes):
                    prev_tool = prev_node.get("tool", "")
                    if prev_tool and (prev_tool.startswith("read_") or prev_tool == "web_fetch"):
                        dependencies.append((prev_node["id"], "text_source"))
                        break

            # 3.5: unit_converter - 依賴提供數值的工具
            elif current_tool == "unit_converter":
                for prev_node in reversed(previous_nodes):
                    prev_tool = prev_node.get("tool", "")
                    if prev_tool in ["calculate", "extract_information", "read_json"]:
                        dependencies.append((prev_node["id"], "value_source"))
                        break

        # ========== 規則 4：順序依賴（最後採用，只有在完全無法判斷時） ==========

        # 如果仍然沒有找到依賴，且不是起始節點
        if not dependencies and previous_nodes:
            # 判斷是否為起始節點（通常是 web_search, read_*, extract_zip）
            is_starting_node = False
            if current_tool:
                is_starting_node = (
                    current_tool == "web_search" or
                    current_tool == "wikipedia_search" or
                    current_tool == "extract_zip" or
                    (current_tool.startswith("read_") and "file_path" in args and "<" not in str(args["file_path"]))
                )

            # 如果不是起始節點，依賴最近的一個節點
            if not is_starting_node and len(previous_nodes) > 0:
                last_node = previous_nodes[-1]
                if last_node.get("id"):
                    dependencies.append((last_node["id"], "sequential"))

        return dependencies

    def _compute_depth(self, nodes: List[Dict], edges: List[Dict]) -> int:
        """計算 DAG 的最大深度"""

        if not nodes:
            return 0

        # 建立鄰接表
        adj = {n["id"]: [] for n in nodes}
        for edge in edges:
            adj[edge["from"]].append(edge["to"])

        # DFS 計算最大深度
        visited = set()
        max_depth = 0

        def dfs(node_id, depth):
            nonlocal max_depth
            visited.add(node_id)
            max_depth = max(max_depth, depth)

            for next_id in adj.get(node_id, []):
                if next_id not in visited:
                    dfs(next_id, depth + 1)

        # 從沒有入邊的節點開始
        roots = [n["id"] for n in nodes if not any(e["to"] == n["id"] for e in edges)]

        for root in roots:
            dfs(root, 1)

        return max_depth

    def _count_parallelizable(self, nodes: List[Dict], edges: List[Dict]) -> int:
        """計算可平行執行的步驟數"""

        # 簡單計算：沒有依賴的節點可以平行執行
        independent_nodes = [
            n for n in nodes
            if len(n["dependencies"]) == 0
        ]

        return len(independent_nodes)


def main():
    # 載入分析報告
    with open("analysis_report.json", 'r') as f:
        report = json.load(f)

    # 處理所有可用於 augmentation 的題目（correct + manual_needed）
    correct_tasks = report["correct_tasks"]
    manual_tasks = report["not_executed_tasks"]
    all_augmentable_tasks = correct_tasks + manual_tasks

    if not all_augmentable_tasks:
        print("沒有可用於 augmentation 的題目，無法生成 DAG")
        return

    print(f"開始轉換 {len(all_augmentable_tasks)} 個可用案例...")
    print(f"  - 答對：{len(correct_tasks)} 題")
    print(f"  - Manual needed：{len(manual_tasks)} 題")

    converter = ChainToDAGConverter()
    dags = []
    skipped_empty = []

    for task in all_augmentable_tasks:
        dag = converter.convert_task(task)

        # 過濾掉空 plan（0 個步驟）
        if dag["stats"]["num_nodes"] == 0:
            skipped_empty.append(task["task_id"])
            print(f"  ⊘ 跳過空 plan：{task['task_id']}（0 個步驟）")
            continue

        dags.append(dag)

    # 儲存
    with open("dags.json", 'w', encoding='utf-8') as f:
        json.dump(dags, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"轉換完成！")
    print(f"總共生成 {len(dags)} 個 DAG")
    if skipped_empty:
        print(f"跳過空 plan：{len(skipped_empty)} 個（{', '.join(skipped_empty)}）")
    print(f"已儲存至：dags.json")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
