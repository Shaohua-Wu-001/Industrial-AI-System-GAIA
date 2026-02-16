#!/usr/bin/env python3
"""
測試 GAIA L3 10 題的答案提取
"""

import json
from pathlib import Path
from smart_answer_extractor import SmartAnswerExtractor


def test_gaia_l3():
    """測試 GAIA L3 10 題"""
    # 讀取數據
    data_path = Path(__file__).parent / "integrated_109/gaia_109_tasks_FIXED.json"
    with open(data_path, 'r') as f:
        all_tasks = json.load(f)

    # 只取 GAIA L3 的 10 題（索引 0-9）
    gaia_l3_tasks = [t for t in all_tasks if t['task_id'].startswith('gaia_val_l3_')]

    extractor = SmartAnswerExtractor()

    print("=" * 80)
    print("GAIA L3 答案提取測試")
    print("=" * 80)

    results = []
    for task in gaia_l3_tasks:
        task_id = task['task_id']
        expected = task.get('final_answer')
        steps = task['annotated_steps']

        # 提取答案
        extracted, confidence, method = extractor.extract(steps, expected)

        # 檢查是否正確
        is_correct = False
        if extracted and expected:
            extracted_norm = extractor._normalize(str(extracted))
            expected_norm = extractor._normalize(str(expected))
            is_correct = (extracted_norm == expected_norm)

        results.append({
            'task_id': task_id,
            'expected': expected,
            'extracted': extracted,
            'confidence': confidence,
            'method': method,
            'is_correct': is_correct
        })

        # 顯示結果
        status = "✅" if is_correct else "❌"
        print(f"\n{status} {task_id}")
        print(f"  預期: {expected}")
        print(f"  提取: {extracted}")
        print(f"  信心度: {confidence:.2f}")
        print(f"  方法: {method}")
        if not is_correct and extracted:
            print(f"  ⚠️  不匹配！")

    # 統計
    correct_count = sum(1 for r in results if r['is_correct'])
    total = len(results)
    accuracy = correct_count / total * 100 if total > 0 else 0

    print("\n" + "=" * 80)
    print("統計結果")
    print("=" * 80)
    print(f"正確: {correct_count}/{total}")
    print(f"準確率: {accuracy:.1f}%")

    # 顯示失敗的題目
    failed = [r for r in results if not r['is_correct']]
    if failed:
        print(f"\n失敗的題目 ({len(failed)} 題):")
        for r in failed:
            print(f"  - {r['task_id']}: 預期 '{r['expected']}' 提取到 '{r['extracted']}'")

    return results, accuracy


if __name__ == "__main__":
    test_gaia_l3()
