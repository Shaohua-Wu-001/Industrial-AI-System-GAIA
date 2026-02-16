#!/usr/bin/env python3
"""
ToolScale Dataset Generator
將 augmented DAGs 轉換成 NV ToolScale 格式的訓練資料

使用：
    python toolscale_generator.py

輸入：
    - augmented_dags.json

輸出：
    - toolscale_dataset.json（ToolScale 格式的完整資料集）
"""

import json
from typing import Dict, List, Any
from pathlib import Path


class ToolScaleGenerator:
    """ToolScale 資料集生成器"""

    def __init__(self):
        pass

    def convert_dag_to_toolscale(self, dag: Dict) -> Dict:
        """將單一 DAG 轉換成 ToolScale 格式"""

        task_id = dag["task_id"]
        variant_id = dag.get("variant_id", 0)
        variant_method = dag.get("variant_method", "original")

        # 建立唯一的 ID
        unique_id = f"{task_id}_v{variant_id}"

        # 從 DAG 重建 planning steps
        planning_steps = []

        # 按 index 排序節點
        sorted_nodes = sorted(dag["nodes"], key=lambda x: x["index"])

        for i, node in enumerate(sorted_nodes, 1):
            step = {
                "step": i,
                "step_id": node["id"],
                "tool": node["tool"],
                "arguments": node["arguments"],
                "description": node["description"],
                "dependencies": node["dependencies"]
            }

            # 如果有額外的配置（retry, explicit_output 等）
            if "retry_config" in node:
                step["retry_config"] = node["retry_config"]

            if "explicit_output" in node:
                step["explicit_output"] = node["explicit_output"]

            planning_steps.append(step)

        # 建立 ToolScale 格式的資料
        toolscale_entry = {
            "id": unique_id,
            "source_task_id": task_id,
            "variant_id": variant_id,
            "variant_method": variant_method,
            "variant_description": dag.get("variant_description", ""),

            # 問題與答案
            "question": dag["question"],
            "final_answer": dag["final_answer"],

            # Planning 結構
            "planning": {
                "total_steps": len(planning_steps),
                "steps": planning_steps,
                "dag_structure": {
                    "nodes": len(dag["nodes"]),
                    "edges": len(dag["edges"]),
                    "max_depth": dag["stats"]["max_depth"],
                    "parallelizable_steps": dag["stats"]["parallelizable_steps"]
                }
            },

            # DAG 圖結構
            "dag": {
                "nodes": dag["nodes"],
                "edges": dag["edges"]
            },

            # 元資料
            "metadata": {
                "source": "GAIA_Level3",
                "augmentation_method": variant_method,
                "num_tools_used": len(planning_steps),
                "tool_sequence": [step["tool"] for step in planning_steps],
                "has_file_dependency": any(
                    "file_path" in step.get("arguments", {})
                    for step in planning_steps
                    if step.get("tool")
                ),
                "has_web_dependency": any(
                    (step.get("tool") or "").startswith("web_")
                    for step in planning_steps
                    if step.get("tool")
                ),
                "has_calculation": any(
                    step.get("tool") == "calculate"
                    for step in planning_steps
                    if step.get("tool")
                )
            }
        }

        return toolscale_entry

    def generate_dataset(self, augmented_dags: Dict) -> Dict:
        """生成完整的 ToolScale 資料集"""

        dags = augmented_dags["dags"]

        print(f"開始轉換 {len(dags)} 個 DAGs 成 ToolScale 格式...")

        dataset = []

        for i, dag in enumerate(dags, 1):
            toolscale_entry = self.convert_dag_to_toolscale(dag)
            dataset.append(toolscale_entry)

            task_id = dag["task_id"]
            variant_id = dag.get("variant_id", 0)
            variant_method = dag.get("variant_method", "original")

            print(f"  [{i}/{len(dags)}] ✓ {task_id} (v{variant_id}: {variant_method})")

        # 統計資訊
        total_steps = sum(entry["planning"]["total_steps"] for entry in dataset)
        avg_steps = total_steps / len(dataset) if dataset else 0

        tools_used = set()
        for entry in dataset:
            tool_seq = entry["metadata"]["tool_sequence"]
            # 過濾掉 None 值
            tools_used.update(t for t in tool_seq if t is not None)

        result = {
            "dataset_info": {
                "name": "GAIA_Level3_ToolScale",
                "version": "1.0",
                "description": "GAIA Level 3 成功案例的資料增強版本（ToolScale 格式）",
                "total_entries": len(dataset),
                "original_tasks": augmented_dags["original_count"],
                "augmented_entries": augmented_dags["augmented_count"],
                "statistics": {
                    "total_planning_steps": total_steps,
                    "avg_steps_per_task": round(avg_steps, 2),
                    "unique_tools_used": len(tools_used),
                    "tools_list": sorted(tools_used)
                }
            },
            "data": dataset
        }

        return result


def main():
    # 載入增強後的 DAGs
    with open("augmented_dags.json", 'r') as f:
        augmented_dags = json.load(f)

    print(f"載入 {augmented_dags['total_dags']} 個 DAG")
    print(f"  - 原始：{augmented_dags['original_count']} 個")
    print(f"  - 變體：{augmented_dags['augmented_count']} 個")
    print()

    generator = ToolScaleGenerator()

    # 生成 ToolScale 資料集
    toolscale_dataset = generator.generate_dataset(augmented_dags)

    # 儲存
    output_file = "toolscale_dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(toolscale_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"ToolScale 資料集生成完成！")
    print(f"{'='*70}")
    print(f"總條目數：{toolscale_dataset['dataset_info']['total_entries']}")
    print(f"總 Planning 步驟：{toolscale_dataset['dataset_info']['statistics']['total_planning_steps']}")
    print(f"平均步驟/任務：{toolscale_dataset['dataset_info']['statistics']['avg_steps_per_task']}")
    print(f"使用的工具數：{toolscale_dataset['dataset_info']['statistics']['unique_tools_used']}")
    print(f"\n使用的工具：")
    for tool in toolscale_dataset['dataset_info']['statistics']['tools_list']:
        print(f"  - {tool}")
    print(f"\n已儲存至：{output_file}")
    print(f"{'='*70}")

    # 顯示範例
    print(f"\n資料集範例（第 1 條）：")
    example = toolscale_dataset["data"][0]
    print(f"  ID: {example['id']}")
    print(f"  問題: {example['question'][:80]}...")
    print(f"  答案: {example['final_answer']}")
    print(f"  步驟數: {example['planning']['total_steps']}")
    print(f"  工具序列: {' → '.join(example['metadata']['tool_sequence'])}")


if __name__ == "__main__":
    main()
