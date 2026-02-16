#!/usr/bin/env python3
"""
Data Augmentation
對成功的 DAG 生成變體

策略：
1. 參數變化（改數值、路徑）
2. 步驟重排（在不違反依賴的前提下）
3. 增加驗證步驟
4. 簡化路徑（移除冗餘步驟）

使用：
    python data_augmentation.py --variants 5

輸入：
    - dags.json

輸出：
    - augmented_dags.json
"""

import json
import copy
import argparse
from typing import Dict, List, Any
import random


class DataAugmenter:
    """資料增強器"""

    def __init__(self, num_variants: int = 5):
        self.num_variants = num_variants

    def augment_dag(self, dag: Dict) -> List[Dict]:
        """對單一 DAG 生成多個變體"""

        variants = []
        task_id = dag["task_id"]

        print(f"\n生成變體：{task_id}")

        # 變體 1：參數變化（數值微調）
        if self.num_variants >= 1:
            v1 = self._variant_parameter_tweak(dag, 1)
            if v1:
                variants.append(v1)
                print(f"  ✓ 變體 1：參數微調")

        # 變體 2：增加中間驗證步驟
        if self.num_variants >= 2:
            v2 = self._variant_add_verification(dag, 2)
            if v2:
                variants.append(v2)
                print(f"  ✓ 變體 2：增加驗證")

        # 變體 3：改變 description
        if self.num_variants >= 3:
            v3 = self._variant_change_description(dag, 3)
            if v3:
                variants.append(v3)
                print(f"  ✓ 變體 3：改變描述")

        # 變體 4：模擬錯誤恢復（增加 retry 邏輯）
        if self.num_variants >= 4:
            v4 = self._variant_add_retry(dag, 4)
            if v4:
                variants.append(v4)
                print(f"  ✓ 變體 4：增加重試")

        # 變體 5：簡化版本（如果可能）
        if self.num_variants >= 5:
            v5 = self._variant_simplify(dag, 5)
            if v5:
                variants.append(v5)
                print(f"  ✓ 變體 5：簡化版本")

        # 變體 6：工具替換（新增）
        if self.num_variants >= 6:
            v6 = self._variant_tool_substitution(dag, 6)
            if v6:
                variants.append(v6)
                print(f"  ✓ 變體 6：工具替換")

        # 變體 7：順序重排（新增）
        if self.num_variants >= 7:
            v7 = self._variant_reorder(dag, 7)
            if v7:
                variants.append(v7)
                print(f"  ✓ 變體 7：順序重排")

        # 變體 8：子目標分解（新增）
        if self.num_variants >= 8:
            v8 = self._variant_decompose(dag, 8)
            if v8:
                variants.append(v8)
                print(f"  ✓ 變體 8：子目標分解")

        # 變體 9：步驟合併（新增）
        if self.num_variants >= 9:
            v9 = self._variant_merge_steps(dag, 9)
            if v9:
                variants.append(v9)
                print(f"  ✓ 變體 9：步驟合併")

        # 變體 10：增加中間輸出（新增）
        if self.num_variants >= 10:
            v10 = self._variant_add_intermediate_output(dag, 10)
            if v10:
                variants.append(v10)
                print(f"  ✓ 變體 10：增加中間輸出")

        print(f"  總共生成 {len(variants)} 個變體")

        return variants

    def _variant_parameter_tweak(self, dag: Dict, variant_id: int) -> Dict:
        """變體 1：微調參數"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "parameter_tweak"
        new_dag["variant_description"] = "微調數值參數（保持語義不變）"

        # 對 calculate 節點的參數做微調
        for node in new_dag["nodes"]:
            if node["tool"] == "calculate":
                # 例如：132 / 5 改成 (54 + 61 + 1 + 16 + 0) / 5
                expr = node["arguments"].get("expression", "")
                if "/" in expr:
                    # 保持原樣但加上括號強調
                    node["arguments"]["expression"] = f"({expr})"
                    node["description"] += " (參數格式微調)"

        return new_dag

    def _variant_add_verification(self, dag: Dict, variant_id: int) -> Dict:
        """變體 2：增加驗證步驟"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "add_verification"
        new_dag["variant_description"] = "在計算後增加驗證步驟"

        # 在 calculate 節點後增加一個驗證節點
        calc_nodes = [n for n in new_dag["nodes"] if n["tool"] == "calculate"]

        if calc_nodes:
            calc_node = calc_nodes[-1]
            verify_node = {
                "id": f"{calc_node['id']}_verify",
                "index": len(new_dag["nodes"]),
                "tool": "validate_data",
                "arguments": {
                    "data": "<result_from_calculate>",
                    "validation_type": "number_range"
                },
                "description": "驗證計算結果的合理性",
                "dependencies": [calc_node["id"]]
            }

            new_dag["nodes"].append(verify_node)
            new_dag["edges"].append({
                "from": calc_node["id"],
                "to": verify_node["id"],
                "data_type": "number"
            })

            new_dag["stats"]["num_nodes"] += 1
            new_dag["stats"]["num_edges"] += 1

        return new_dag

    def _variant_change_description(self, dag: Dict, variant_id: int) -> Dict:
        """變體 3：改變步驟描述（語意相同）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "change_description"
        new_dag["variant_description"] = "改寫步驟描述（保持語義）"

        # 改寫描述
        description_variants = {
            "Opened the JSONLD file.": "讀取 JSONLD 檔案內容",
            "Took the average": "計算平均值",
            "Calculate": "執行數學運算",
        }

        for node in new_dag["nodes"]:
            desc = node.get("description", "")
            for old, new in description_variants.items():
                if old in desc:
                    node["description"] = desc.replace(old, new)

        return new_dag

    def _variant_add_retry(self, dag: Dict, variant_id: int) -> Dict:
        """變體 4：增加重試邏輯"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "add_retry"
        new_dag["variant_description"] = "為可能失敗的步驟增加重試機制"

        # 為 read_* 和 web_* 節點增加 retry 元資料
        for node in new_dag["nodes"]:
            tool = node.get("tool")
            if tool and (tool.startswith("read_") or tool.startswith("web_")):
                node["retry_config"] = {
                    "max_retries": 3,
                    "backoff": "exponential"
                }
                if "description" in node:
                    node["description"] += " (含重試機制)"

        return new_dag

    def _variant_simplify(self, dag: Dict, variant_id: int) -> Dict:
        """變體 5：簡化版本（如果步驟數 > 3）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "simplify"
        new_dag["variant_description"] = "簡化執行路徑（合併可合併的步驟）"

        # 如果原始只有 2 步，無法簡化
        if len(new_dag["nodes"]) <= 2:
            # 改為「明確化」版本
            for node in new_dag["nodes"]:
                node["explicit_output"] = True
                node["description"] += " (明確輸出)"

        return new_dag

    def _variant_tool_substitution(self, dag: Dict, variant_id: int) -> Dict:
        """變體 6：工具替換（替換可替換的工具）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "tool_substitution"
        new_dag["variant_description"] = "替換功能相似的工具"

        # 定義可替換的工具對
        substitutions = {
            "web_search": "wikipedia_search",
            "wikipedia_search": "web_search",
            "read_json": "read_csv",  # 如果合適
            "read_csv": "read_excel",
        }

        # 嘗試替換第一個可替換的工具
        for node in new_dag["nodes"]:
            tool = node.get("tool")
            if tool in substitutions:
                new_tool = substitutions[tool]
                node["tool"] = new_tool
                node["description"] += f" (工具替換: {tool} → {new_tool})"
                break  # 只替換一個

        return new_dag

    def _variant_reorder(self, dag: Dict, variant_id: int) -> Dict:
        """變體 7：順序重排（在不違反依賴的前提下重排）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "reorder"
        new_dag["variant_description"] = "重新排列可平行的步驟"

        # 找出沒有依賴關係的節點（可以交換順序）
        nodes = new_dag["nodes"]
        if len(nodes) >= 3:
            # 尋找可以交換的相鄰節點
            for i in range(len(nodes) - 1):
                node_a = nodes[i]
                node_b = nodes[i + 1]

                # 檢查它們是否有依賴關係
                a_deps = set(node_a.get("dependencies", []))
                b_deps = set(node_b.get("dependencies", []))

                # 如果 B 不依賴 A，且 A 不依賴 B，可以交換
                if node_a["id"] not in b_deps and node_b["id"] not in a_deps:
                    # 交換
                    nodes[i], nodes[i + 1] = nodes[i + 1], nodes[i]
                    # 更新 index
                    nodes[i]["index"] = i
                    nodes[i + 1]["index"] = i + 1
                    break

        return new_dag

    def _variant_decompose(self, dag: Dict, variant_id: int) -> Dict:
        """變體 8：子目標分解（將複雜步驟拆分）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "decompose"
        new_dag["variant_description"] = "將複雜步驟拆分成子步驟"

        # 尋找 calculate 節點，在前面加入 extract_information
        for i, node in enumerate(new_dag["nodes"]):
            if node["tool"] == "calculate" and i > 0:
                # 在 calculate 之前插入 extract_information
                extract_node = {
                    "id": f"{node['id']}_extract",
                    "index": i,
                    "tool": "extract_information",
                    "arguments": {
                        "data": "<from_context>",
                        "target": "numerical_values"
                    },
                    "description": "提取數值資訊（子目標分解）",
                    "dependencies": node.get("dependencies", []).copy()
                }

                # 插入新節點
                new_dag["nodes"].insert(i, extract_node)

                # 更新 calculate 節點的依賴
                node["dependencies"] = [extract_node["id"]]

                # 更新所有後續節點的 index
                for j in range(i + 1, len(new_dag["nodes"])):
                    new_dag["nodes"][j]["index"] = j

                # 更新邊
                new_dag["edges"].append({
                    "from": extract_node["id"],
                    "to": node["id"],
                    "data_type": "extracted_data"
                })

                # 更新統計
                new_dag["stats"]["num_nodes"] += 1
                new_dag["stats"]["num_edges"] += 1

                break  # 只分解一個

        return new_dag

    def _variant_merge_steps(self, dag: Dict, variant_id: int) -> Dict:
        """變體 9：步驟合併（合併連續的相同類型操作）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "merge_steps"
        new_dag["variant_description"] = "合併連續的相同類型操作"

        # 尋找連續的 web_fetch
        nodes = new_dag["nodes"]
        i = 0
        while i < len(nodes) - 1:
            if nodes[i]["tool"] == "web_fetch" and nodes[i + 1]["tool"] == "web_fetch":
                # 合併這兩個節點
                merged_node = copy.deepcopy(nodes[i])
                merged_node["description"] += f" + {nodes[i + 1]['description']} (合併)"
                merged_node["arguments"]["batch_urls"] = True

                # 移除第二個節點
                removed_id = nodes[i + 1]["id"]
                nodes.pop(i + 1)

                # 更新所有引用到 removed_id 的依賴
                for node in nodes:
                    if removed_id in node.get("dependencies", []):
                        node["dependencies"].remove(removed_id)
                        if merged_node["id"] not in node["dependencies"]:
                            node["dependencies"].append(merged_node["id"])

                # 更新邊
                new_edges = []
                for edge in new_dag["edges"]:
                    if edge["from"] == removed_id:
                        edge["from"] = merged_node["id"]
                    if edge["to"] == removed_id:
                        continue  # 移除指向 removed_id 的邊
                    new_edges.append(edge)
                new_dag["edges"] = new_edges

                # 更新統計
                new_dag["stats"]["num_nodes"] -= 1

                break  # 只合併一次

            i += 1

        # 更新所有節點的 index
        for i, node in enumerate(nodes):
            node["index"] = i

        return new_dag

    def _variant_add_intermediate_output(self, dag: Dict, variant_id: int) -> Dict:
        """變體 10：增加中間輸出（在關鍵步驟後加入輸出）"""

        new_dag = copy.deepcopy(dag)
        new_dag["variant_id"] = variant_id
        new_dag["variant_method"] = "add_intermediate_output"
        new_dag["variant_description"] = "在關鍵步驟後加入中間輸出"

        # 為所有節點加入中間輸出標記
        for node in new_dag["nodes"]:
            # 特別標記資料轉換節點
            if node["tool"] in ["calculate", "extract_information", "filter_data", "web_fetch"]:
                node["save_intermediate"] = True
                node["description"] += " (儲存中間結果)"

        return new_dag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", type=int, default=5, help="每題生成的變體數量")
    args = parser.parse_args()

    # 載入 DAGs
    with open("dags.json", 'r') as f:
        dags = json.load(f)

    print(f"載入 {len(dags)} 個 DAG")
    print(f"每個生成 {args.variants} 個變體\n")
    print(f"{'='*70}")

    augmenter = DataAugmenter(num_variants=args.variants)

    all_variants = []

    for dag in dags:
        # 保留原始 DAG
        original = copy.deepcopy(dag)
        original["variant_id"] = 0
        original["variant_method"] = "original"
        original["variant_description"] = "原始版本"
        all_variants.append(original)

        # 生成變體
        variants = augmenter.augment_dag(dag)
        all_variants.extend(variants)

    # 儲存
    output = {
        "total_dags": len(all_variants),
        "original_count": len(dags),
        "augmented_count": len(all_variants) - len(dags),
        "dags": all_variants
    }

    with open("augmented_dags.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Augmentation 完成！")
    print(f"原始 DAG：{len(dags)} 個")
    print(f"總 DAG（含變體）：{len(all_variants)} 個")
    print(f"新增變體：{len(all_variants) - len(dags)} 個")
    print(f"已儲存至：augmented_dags.json")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
