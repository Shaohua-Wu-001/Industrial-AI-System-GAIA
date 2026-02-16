#!/usr/bin/env python3
"""
測試完整 109 題的答案提取
包含：99 題 TA + 10 題 GAIA L3
"""

import json
from pathlib import Path
from smart_answer_extractor import SmartAnswerExtractor


def load_ta_answers():
    """載入 TA 的 99 題答案"""
    ta_path = Path.home() / "Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl"

    ta_answers = {}
    with open(ta_path, 'r') as f:
        for line in f:
            task = json.loads(line)
            task_id = task['meta']['id']
            answer = task['gold']['final_answer']['answer']
            ta_answers[task_id] = answer

    return ta_answers


def test_full_109():
    """測試完整 109 題"""
    # 讀取整合後的數據
    data_path = Path(__file__).parent / "integrated_109/gaia_109_tasks_FIXED.json"
    with open(data_path, 'r') as f:
        all_tasks = json.load(f)

    # 載入 TA 答案
    print("載入 TA 的答案...")
    ta_answers = load_ta_answers()
    print(f"✓ 載入 {len(ta_answers)} 個 TA 答案")

    extractor = SmartAnswerExtractor()

    print("\n" + "=" * 80)
    print("完整 109 題答案提取測試")
    print("=" * 80)

    results = {
        'gaia_l3': [],
        'ta': [],
    }

    # 測試所有題目
    for task in all_tasks:
        task_id = task['task_id']
        steps = task['annotated_steps']

        # 判斷來源
        if task_id.startswith('gaia_val_l3_'):
            source = 'gaia_l3'
            expected = task.get('final_answer')
        else:
            source = 'ta'
            # 從 metadata 中獲取原始 ID
            original_id = task['metadata'].get('original_id')
            expected = ta_answers.get(original_id)

        if not expected:
            continue

        # 提取答案
        extracted, confidence, method = extractor.extract(steps, expected)

        # 檢查是否正確
        is_correct = False
        if extracted and expected:
            extracted_norm = extractor._normalize(str(extracted))
            expected_norm = extractor._normalize(str(expected))
            is_correct = (extracted_norm == expected_norm)

        result = {
            'task_id': task_id,
            'expected': expected,
            'extracted': extracted,
            'confidence': confidence,
            'method': method,
            'is_correct': is_correct
        }

        results[source].append(result)

    # 統計 GAIA L3
    gaia_correct = sum(1 for r in results['gaia_l3'] if r['is_correct'])
    gaia_total = len(results['gaia_l3'])
    gaia_accuracy = gaia_correct / gaia_total * 100 if gaia_total > 0 else 0

    print(f"\n【GAIA L3 結果】")
    print(f"  正確: {gaia_correct}/{gaia_total}")
    print(f"  準確率: {gaia_accuracy:.1f}%")

    # 統計 TA
    ta_correct = sum(1 for r in results['ta'] if r['is_correct'])
    ta_total = len(results['ta'])
    ta_accuracy = ta_correct / ta_total * 100 if ta_total > 0 else 0

    print(f"\n【TA 99 題結果】")
    print(f"  正確: {ta_correct}/{ta_total}")
    print(f"  準確率: {ta_accuracy:.1f}%")

    # 總計
    total_correct = gaia_correct + ta_correct
    total = gaia_total + ta_total
    overall_accuracy = total_correct / total * 100 if total > 0 else 0

    print(f"\n" + "=" * 80)
    print("【總計 109 題】")
    print("=" * 80)
    print(f"正確: {total_correct}/{total}")
    print(f"準確率: {overall_accuracy:.1f}%")

    # 顯示失敗案例（前 20 個）
    all_failed = results['gaia_l3'] + results['ta']
    failed = [r for r in all_failed if not r['is_correct']]

    if failed:
        print(f"\n失敗的題目 ({len(failed)} 題，顯示前 20 個):")
        for r in failed[:20]:
            task_id_short = r['task_id'][:30] + '...' if len(r['task_id']) > 30 else r['task_id']
            expected_short = str(r['expected'])[:30] + '...' if len(str(r['expected'])) > 30 else str(r['expected'])
            extracted_short = str(r['extracted'])[:30] + '...' if r['extracted'] and len(str(r['extracted'])) > 30 else str(r['extracted'])
            print(f"  - {task_id_short}: 預期 '{expected_short}' 提取到 '{extracted_short}'")

    # 儲存詳細結果
    output_path = Path(__file__).parent / "extraction_results_109.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'gaia_l3': {
                    'correct': gaia_correct,
                    'total': gaia_total,
                    'accuracy': gaia_accuracy
                },
                'ta': {
                    'correct': ta_correct,
                    'total': ta_total,
                    'accuracy': ta_accuracy
                },
                'overall': {
                    'correct': total_correct,
                    'total': total,
                    'accuracy': overall_accuracy
                }
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 詳細結果已儲存至：{output_path}")

    return results, overall_accuracy


if __name__ == "__main__":
    test_full_109()
