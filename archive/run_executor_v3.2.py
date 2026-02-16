#!/usr/bin/env python3
"""
Executor v3.2 - 明確讀取 v3.2 的輸出
修復版本，確保讀取正確的計劃文件
"""

import json
import sys
from pathlib import Path

# 添加當前目錄到路徑
sys.path.insert(0, '.')
import gaia_function as gf

print("="*80)
print("🚀 GAIA Executor v3.2 - 讀取 v3.2 輸出")
print("="*80)

# ============================================================
# 明確指定輸入文件
# ============================================================
INPUT_FILE = 'parser_output/plans_v3.2_autofix.json'

print(f"\n📂 讀取計劃文件: {INPUT_FILE}")

if not Path(INPUT_FILE).exists():
    print(f"❌ 錯誤: 找不到 {INPUT_FILE}")
    print("請先運行: python3 parser_v3.2_autofix.py")
    sys.exit(1)

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    plans = json.load(f)

print(f"✅ 載入 {len(plans)} 個計劃")

# 統計
total_executable = sum(len(t['tool_sequence']) for t in plans)
print(f"📊 可執行步驟: {total_executable} 個")

# ============================================================
# 選擇執行模式
# ============================================================
print("\n選擇執行模式:")
print("1. 執行所有任務 (10 個)")
print("2. 執行前 3 個任務")
print("3. 執行單一任務 (輸入編號 0-9)")

choice = input("\n請選擇 (1/2/3): ")

if choice == '1':
    tasks_to_run = plans
    print(f"\n開始執行 {len(tasks_to_run)} 個任務")
elif choice == '2':
    tasks_to_run = plans[:3]
    print(f"\n開始執行前 3 個任務")
elif choice == '3':
    idx = int(input("請輸入任務編號 (0-9): "))
    tasks_to_run = [plans[idx]]
    print(f"\n開始執行任務 {idx}")
else:
    print("無效選擇")
    sys.exit(1)

# ============================================================
# 執行任務
# ============================================================
total_calls = 0
success_calls = 0
task_results = []

for task in tasks_to_run:
    task_id = task['task_id']
    question = task.get('question', task.get('Question', ''))
    tool_sequence = task.get('tool_sequence', [])
    
    print("\n" + "="*80)
    print(f"執行任務: {task_id}")
    print(f"問題: {question[:100]}...")
    print(f"可執行步驟數: {len(tool_sequence)}")
    print("="*80)
    
    task_success = 0
    
    for i, step in enumerate(tool_sequence, 1):
        tool_name = step['tool_name']
        arguments = step['arguments']
        desc = step.get('description', '')[:100]
        
        print(f"\n  [{i}/{len(tool_sequence)}] {tool_name}")
        print(f"      描述: {desc}...")
        
        total_calls += 1
        
        try:
            tool_func = getattr(gf, tool_name, None)
            
            if tool_func is None:
                print(f"      ❌ 工具不存在")
                continue
            
            result = tool_func(**arguments)
            
            if result.get('success', False):
                print(f"      ✅ 成功")
                success_calls += 1
                task_success += 1
                
                # 顯示部分結果
                if tool_name == 'calculate':
                    print(f"      結果: {result.get('result')}")
                elif tool_name in ['read_json', 'read_excel', 'read_xml']:
                    data = result.get('data')
                    if isinstance(data, dict):
                        print(f"      結果: {str(data)[:100]}...")
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"      結果: {len(data)} 行資料")
            else:
                error_msg = result.get('error', 'Unknown')[:100]
                print(f"      ❌ 失敗: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"      ❌ 錯誤: {error_msg}")
    
    task_results.append({
        'task_id': task_id,
        'total': len(tool_sequence),
        'success': task_success,
        'rate': task_success / len(tool_sequence) if tool_sequence else 0
    })

# ============================================================
# 統計結果
# ============================================================
print("\n" + "="*80)
print("執行統計")
print("="*80)

success_rate = success_calls / total_calls if total_calls > 0 else 0

print(f"\n任務統計:")
print(f"  執行任務數: {len(tasks_to_run)}")
print(f"  總工具呼叫: {total_calls}")
print(f"  成功呼叫數: {success_calls}")
print(f"  成功率: {success_rate*100:.1f}%")

print(f"\n各任務詳細結果:")
for r in task_results:
    rate = r['rate'] * 100
    print(f"  {r['task_id']}: {r['success']}/{r['total']} ({rate:.1f}%)")

print("\n" + "="*80)
