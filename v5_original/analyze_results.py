#!/usr/bin/env python3
"""
分析執行結果
- 統計答對/答錯/未執行
- 分類錯誤原因
- 輸出成功/失敗案例清單

使用：
    python analyze_results.py

輸出：
    - analysis_report.json
"""

import json
from typing import Dict, List, Any
from pathlib import Path


def analyze_results():
    """分析 validation_results.json 和 plans_v3_executable.json"""

    # 載入資料
    with open("validation_results.json", 'r') as f:
        validation = json.load(f)

    with open("plans_v3_executable.json", 'r') as f:
        plans = json.load(f)

    # 建立 task_id -> plan 的映射
    plan_map = {p["task_id"]: p for p in plans}

    # 分類
    correct_tasks = []
    incorrect_tasks = []
    not_executed_tasks = []

    for v in validation:
        task_id = v["task_id"]
        plan = plan_map.get(task_id, {})

        if v["correct"] is True:
            # 答對
            correct_tasks.append({
                "task_id": task_id,
                "ground_truth": v["ground_truth"],
                "predicted": v["predicted"],
                "plan": plan,
                "num_steps": len(plan.get("tool_sequence", [])),
                "executable_rate": plan.get("stats", {}).get("executable_rate", 0)
            })

        elif v["correct"] is False:
            # 答錯
            incorrect_tasks.append({
                "task_id": task_id,
                "ground_truth": v["ground_truth"],
                "predicted": v["predicted"],
                "plan": plan,
                "num_steps": len(plan.get("tool_sequence", [])),
                "skipped_steps": len(plan.get("skipped_steps", [])),
                "error_analysis": _analyze_error(v, plan)
            })

        else:
            # 未執行（manual_needed）
            not_executed_tasks.append({
                "task_id": task_id,
                "ground_truth": v["ground_truth"],
                "method": v.get("method"),
                "plan": plan,
                "num_steps": len(plan.get("tool_sequence", [])),
                "skipped_steps": len(plan.get("skipped_steps", []))
            })

    # 統計
    total = len(validation)
    correct_count = len(correct_tasks)
    incorrect_count = len(incorrect_tasks)
    not_executed_count = len(not_executed_tasks)

    # 錯誤分類統計
    error_categories = {}
    for task in incorrect_tasks:
        err_type = task["error_analysis"]["type"]
        error_categories[err_type] = error_categories.get(err_type, 0) + 1

    # 計算可用於 augmentation 的題目（correct + manual_needed 都有完整 plan）
    augmentable_count = correct_count + not_executed_count

    # 產生報告
    report = {
        "summary": {
            "total": total,
            "correct": correct_count,
            "incorrect": incorrect_count,
            "not_executed": not_executed_count,
            "augmentable": augmentable_count,
            "accuracy": correct_count / total if total > 0 else 0,
            "executed_accuracy": correct_count / (correct_count + incorrect_count) if (correct_count + incorrect_count) > 0 else 0
        },
        "correct_tasks": correct_tasks,
        "incorrect_tasks": incorrect_tasks,
        "not_executed_tasks": not_executed_tasks,
        "error_categories": error_categories,
        "insights": {
            "可用於 augmentation 的題目數": augmentable_count,
            "需要錯誤分析的題目數": incorrect_count,
            "未執行題目數": not_executed_count,
            "說明": "manual_needed 的題目有完整 plan，可用於 data augmentation"
        }
    }

    # 儲存
    with open("analysis_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 顯示結果
    print("="*70)
    print("GAIA Level 3 執行結果分析")
    print("="*70)
    print(f"\n總題數：{total}")
    print(f"答對：{correct_count} 題")
    print(f"答錯：{incorrect_count} 題")
    print(f"未執行：{not_executed_count} 題")
    print(f"\n執行準確率：{report['summary']['executed_accuracy']*100:.1f}%")
    print(f"整體準確率：{report['summary']['accuracy']*100:.1f}%")

    print(f"\n✓ 答對題目：")
    for task in correct_tasks:
        rate = task.get('executable_rate', 0)
        if isinstance(rate, str):
            rate_pct = float(rate.rstrip('%'))
        else:
            rate_pct = float(rate) * 100 if rate else 0
        print(f"  - {task['task_id']}: {task['num_steps']} 步驟, 可執行率 {rate_pct:.0f}%")

    print(f"\n✗ 答錯題目：")
    for task in incorrect_tasks:
        err = task['error_analysis']
        print(f"  - {task['task_id']}: {err['type']} - {err['reason']}")

    print(f"\n⊘ 未執行題目：")
    for task in not_executed_tasks:
        print(f"  - {task['task_id']}: {task['method']}")

    if error_categories:
        print(f"\n錯誤分類統計：")
        for err_type, count in error_categories.items():
            print(f"  - {err_type}: {count} 題")

    print(f"\n報告已儲存至：analysis_report.json")

    return report


def _analyze_error(validation: Dict, plan: Dict) -> Dict:
    """分析單一錯誤案例"""

    task_id = validation["task_id"]
    predicted = validation.get("predicted")
    ground_truth = validation["ground_truth"]

    skipped_steps = plan.get("skipped_steps", [])

    # 錯誤分類
    if len(skipped_steps) > 0:
        # 有步驟被跳過 -> 執行錯誤
        skip_reasons = [s.get("skip_reason", "") for s in skipped_steps]

        if any("檔案不存在" in r for r in skip_reasons):
            return {
                "type": "file_missing",
                "reason": "必要檔案缺失，無法完整執行",
                "skipped_steps": len(skipped_steps),
                "details": skip_reasons
            }
        elif any("佔位符" in r for r in skip_reasons):
            return {
                "type": "parameter_missing",
                "reason": "參數包含佔位符，無法執行",
                "skipped_steps": len(skipped_steps),
                "details": skip_reasons
            }
        else:
            return {
                "type": "execution_error",
                "reason": "工具執行失敗",
                "skipped_steps": len(skipped_steps),
                "details": skip_reasons
            }

    else:
        # 沒有跳過步驟，但答案錯誤 -> 推理/計算錯誤
        try:
            pred_num = float(predicted) if predicted else None
            gt_num = float(ground_truth)

            if pred_num is not None:
                return {
                    "type": "calculation_error",
                    "reason": f"計算結果錯誤（預測 {predicted}，正確答案 {ground_truth}）",
                    "predicted": predicted,
                    "ground_truth": ground_truth,
                    "diff": abs(pred_num - gt_num) if pred_num else None
                }
        except ValueError:
            pass

        return {
            "type": "reasoning_error",
            "reason": "推理或邏輯錯誤",
            "predicted": predicted,
            "ground_truth": ground_truth
        }


if __name__ == "__main__":
    analyze_results()
