#!/usr/bin/env python3
"""
自動答案驗證版本
"""
import os
import sys
import json
import re

# 使用當前目錄
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

# 載入資料
with open(os.path.join(PROJECT_DIR, 'gaia_level3_tasks.json'), 'r', encoding='utf-8') as f:
    tasks = json.load(f)

exec_results_file = os.path.join(PROJECT_DIR, 'parser_output/execution_results.json')
if not os.path.exists(exec_results_file):
    print("⚠️  執行結果檔案不存在，跳過驗證")
    sys.exit(0)

with open(exec_results_file, 'r', encoding='utf-8') as f:
    execution_results = json.load(f)

# 建立 task_id -> execution_result 映射
exec_map = {r['task_id']: r for r in execution_results}

print("="*80)
print("📊 答案驗證結果")
print("="*80)

validation_results = []

for task in tasks:
    task_id = task['task_id']
    ground_truth = task['Final answer']
    question = task['Question']
    
    exec_result = exec_map.get(task_id)
    
    print(f"\n{'='*80}")
    print(f"任務: {task_id}")
    print(f"標準答案: {ground_truth}")
    print('='*80)
    
    # 分析答案類型
    answer_type = 'text'
    if re.match(r'^\d+$', ground_truth):
        answer_type = 'integer'
    elif re.match(r'^\d+\.\d+$', ground_truth):
        answer_type = 'float'
    
    print(f"答案類型: {answer_type}")
    
    # 嘗試從執行結果中提取答案
    predicted_answer = None
    validation_status = 'unknown'
    
    if exec_result and exec_result['results']:
        # 檢查最後一步是否是計算
        last_result = exec_result['results'][-1]
        if last_result['success'] and last_result.get('result'):
            result_data = last_result['result']
            
            # 如果是 calculate 工具
            if last_result['tool_name'] == 'calculate':
                if 'result' in result_data:
                    predicted_answer = str(result_data['result'])
                    
                    # 比對答案
                    if answer_type == 'integer':
                        try:
                            pred_int = int(float(predicted_answer))
                            truth_int = int(ground_truth)
                            if pred_int == truth_int:
                                validation_status = 'correct'
                            else:
                                validation_status = 'incorrect'
                        except:
                            validation_status = 'unknown'
                    elif answer_type == 'float':
                        try:
                            pred_float = float(predicted_answer)
                            truth_float = float(ground_truth)
                            if abs(pred_float - truth_float) < 0.1:
                                validation_status = 'correct'
                            else:
                                validation_status = 'incorrect'
                        except:
                            validation_status = 'unknown'
    
    print(f"預測答案: {predicted_answer if predicted_answer else 'N/A'}")
    print(f"驗證狀態: {validation_status}")
    
    if validation_status == 'correct':
        print("✅ 答案正確")
    elif validation_status == 'incorrect':
        print("❌ 答案錯誤")
    else:
        print("⚠️  需要人工驗證")
    
    validation_results.append({
        'task_id': task_id,
        'ground_truth': ground_truth,
        'predicted_answer': predicted_answer,
        'answer_type': answer_type,
        'validation_status': validation_status,
        'success_rate': exec_result['success_rate'] if exec_result else 0
    })

# 統計
print("\n" + "="*80)
print("📈 整體統計")
print("="*80)

correct = sum(1 for v in validation_results if v['validation_status'] == 'correct')
incorrect = sum(1 for v in validation_results if v['validation_status'] == 'incorrect')
unknown = sum(1 for v in validation_results if v['validation_status'] == 'unknown')

print(f"\n答案驗證:")
print(f"  正確: {correct}/{len(validation_results)} ({correct/len(validation_results)*100:.1f}%)")
print(f"  錯誤: {incorrect}/{len(validation_results)}")
print(f"  未知: {unknown}/{len(validation_results)}")

# 儲存結果
output_file = os.path.join(PROJECT_DIR, 'parser_output/validation_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(validation_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ 驗證結果已儲存至: {output_file}")
