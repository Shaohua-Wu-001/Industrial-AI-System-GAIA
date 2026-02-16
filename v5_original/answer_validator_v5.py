#!/usr/bin/env python3
"""
GAIA Level 3 - 答案驗證系統 v5
適配 parser_v5 和 run_executor_v5
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import re

sys.path.insert(0, os.path.dirname(__file__))
import gaia_function as gf

print("="*80)
print("🎯 GAIA Level 3 - 答案驗證系統 v5")
print("="*80)

# ============================================================
# 載入資料
# ============================================================
print("\n📂 載入資料...")

# 1. 載入任務
with open('gaia_level3_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)
print(f"   ✅ 載入 {len(tasks)} 個任務")

# 2. 載入 parser v5 的輸出
plans_file = 'parser_output/plans.json'
if not Path(plans_file).exists():
    print(f"   ❌ 找不到: {plans_file}")
    print("   請先執行: python3 parser_v5.py gaia_level3_tasks.json ./data")
    sys.exit(1)

with open(plans_file, 'r', encoding='utf-8') as f:
    plans = json.load(f)
print(f"   ✅ 載入 {len(plans)} 個計劃")

# ============================================================
# 執行所有任務並收集結果
# ============================================================
print("\n🔧 執行任務並收集結果...")

execution_results = {}

for plan in plans:
    task_id = plan['task_id']
    tool_sequence = plan.get('tool_sequence', [])
    
    # 只執行可執行的步驟
    executable_steps = [s for s in tool_sequence if s.get('executable', True)]
    
    print(f"   {task_id}: {len(executable_steps)} 個可執行步驟")
    
    results = []
    for step in executable_steps:
        tool_name = step['tool_name']
        arguments = step['arguments']
        
        try:
            tool_func = getattr(gf, tool_name, None)
            if tool_func:
                result = tool_func(**arguments)
                results.append({
                    'step_id': step.get('step_id'),
                    'tool': tool_name,
                    'success': result.get('success', False),
                    'result': result
                })
        except Exception as e:
            results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'success': False,
                'error': str(e)
            })
    
    execution_results[task_id] = results

# ============================================================
# 答案驗證邏輯
# ============================================================
print("\n" + "="*80)
print("📊 答案驗證結果")
print("="*80)

validation_results = []

for task in tasks:
    task_id = task['task_id']
    ground_truth = task['Final answer']
    question = task['Question']
    results = execution_results.get(task_id, [])
    
    print(f"\n{'='*80}")
    print(f"任務: {task_id}")
    print(f"標準答案: {ground_truth}")
    print('='*80)
    
    # 分析答案類型
    answer_type = None
    if re.match(r'^\d+$', ground_truth):
        answer_type = 'integer'
    elif re.match(r'^\d+\.\d+$', ground_truth):
        answer_type = 'float'
    elif re.match(r'^\d+,\s*\d+$', ground_truth):
        answer_type = 'tuple'
    else:
        answer_type = 'text'
    
    print(f"答案類型: {answer_type}")
    
    # 嘗試自動驗證
    predicted_answer = None
    verification_method = None
    
    # 方法1: 檢查最後的 calculate 結果
    calculate_results = [r for r in results if r['tool'] == 'calculate' and r['success']]
    if calculate_results:
        last_calc = calculate_results[-1]
        calc_result = last_calc['result'].get('result')
        if calc_result is not None:
            if answer_type == 'integer':
                predicted_answer = str(round(calc_result))
            elif answer_type == 'float':
                predicted_answer = f"{calc_result:.1f}"
            else:
                predicted_answer = str(calc_result)
            verification_method = 'calculate'
    
    # 方法2: 檢查 unit_converter 結果（對於單位轉換題）
    if not predicted_answer:
        converter_results = [r for r in results if r['tool'] == 'unit_converter' and r['success']]
        if converter_results:
            last_conv = converter_results[-1]
            conv_result = last_conv['result'].get('result')
            if conv_result is not None:
                if answer_type == 'integer':
                    predicted_answer = str(round(conv_result))
                else:
                    predicted_answer = str(conv_result)
                verification_method = 'unit_converter'
    
    # 驗證
    if predicted_answer:
        # 寬鬆比較（允許小數點誤差）
        is_correct = False
        
        if answer_type in ['integer', 'float']:
            try:
                pred_num = float(predicted_answer)
                truth_num = float(ground_truth)
                # 允許 1% 誤差或絕對誤差 0.5
                is_correct = (abs(pred_num - truth_num) < 0.5) or \
                            (abs(pred_num - truth_num) / max(abs(truth_num), 1) < 0.01)
            except:
                is_correct = predicted_answer == ground_truth
        else:
            is_correct = predicted_answer.strip() == ground_truth.strip()
        
        status = "✅ 正確" if is_correct else "❌ 錯誤"
        print(f"\n驗證方法: {verification_method}")
        print(f"預測答案: {predicted_answer}")
        print(f"結果: {status}")
        
        validation_results.append({
            'task_id': task_id,
            'ground_truth': ground_truth,
            'predicted': predicted_answer,
            'correct': is_correct,
            'status': 'correct' if is_correct else 'incorrect',
            'method': verification_method
        })
    else:
        print(f"\n⚠️  無法自動驗證（需要人工檢查）")
        print(f"\n執行的步驟:")
        for i, r in enumerate(results[-3:], 1):  # 顯示最後3個步驟
            status = "✅" if r['success'] else "❌"
            print(f"  {status} {r['tool']}")
            if r['success'] and 'result' in r:
                # 顯示部分結果
                result_preview = str(r['result'])[:100]
                print(f"     結果: {result_preview}...")
        
        print(f"\n💡 人工驗證提示:")
        if 'calculate' in question.lower() or 'percentage' in question.lower():
            print(f"   → 檢查 calculate 的結果")
        elif 'average' in question.lower():
            print(f"   → 檢查 statistical_analysis 或 calculate")
        elif answer_type == 'text':
            print(f"   → 需要綜合多個步驟的結果")
        
        validation_results.append({
            'task_id': task_id,
            'ground_truth': ground_truth,
            'predicted': None,
            'correct': None,
            'status': 'unknown',
            'method': 'manual_needed'
        })

# ============================================================
# 總結
# ============================================================
print("\n" + "="*80)
print("📊 驗證總結")
print("="*80)

auto_verified = [r for r in validation_results if r['predicted'] is not None]
correct = [r for r in auto_verified if r['correct']]
incorrect = [r for r in auto_verified if not r['correct']]
manual_needed = [r for r in validation_results if r['predicted'] is None]

print(f"\n總任務數: {len(validation_results)}")
print(f"自動驗證: {len(auto_verified)} ({len(auto_verified)/len(validation_results)*100:.1f}%)")
print(f"  ✅ 正確: {len(correct)}")
print(f"  ❌ 錯誤: {len(incorrect)}")
print(f"需人工驗證: {len(manual_needed)}")

if len(auto_verified) > 0:
    print(f"\n📈 自動驗證準確率: {len(correct)}/{len(auto_verified)} ({len(correct)/len(auto_verified)*100:.1f}%)")

if len(validation_results) > 0:
    total_correct = len(correct)
    total_tasks = len(validation_results)
    print(f"📈 總體準確率: {total_correct}/{total_tasks} ({total_correct/total_tasks*100:.1f}%)")

print("\n✅ 自動驗證成功的任務:")
for r in correct:
    print(f"  {r['task_id']}: {r['ground_truth']} (via {r['method']})")

if incorrect:
    print("\n❌ 自動驗證失敗的任務:")
    for r in incorrect:
        print(f"  {r['task_id']}: 預測 {r['predicted']}, 實際 {r['ground_truth']}")

print("\n⚠️  需要人工驗證的任務:")
for r in manual_needed:
    print(f"  {r['task_id']}: {r['ground_truth']}")

# ============================================================
# 保存結果
# ============================================================
output_file = 'parser_output/validation_results_v5.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(validation_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ 已保存: {output_file}")

print("\n" + "="*80)
print("✅ 驗證完成")
print("="*80)
