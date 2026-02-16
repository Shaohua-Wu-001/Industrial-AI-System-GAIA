#!/usr/bin/env python3
"""
完整測試流程：重新 Parse → Execute → Evaluate
測試全部 10 題
"""

import os
import sys
import json
from pathlib import Path

# 設定路徑
sys.path.insert(0, os.path.dirname(__file__))
import gaia_function as gf

print("="*80)
print("🚀 GAIA Level 3 完整測試流程 - 全部 10 題")
print("="*80)

# ============================================================
# Step 1: 載入資料
# ============================================================
print("\n📂 Step 1: 載入任務資料...")

with open('gaia_level3_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

print(f"   ✅ 載入 {len(tasks)} 個任務")

# ============================================================
# Step 2: 重新檢查檔案狀態並更新路徑
# ============================================================
print("\n📋 Step 2: 檢查檔案狀態...")

file_status = {}
for task in tasks:
    task_id = task['task_id']
    file_name = task.get('file_name', '')
    
    if file_name:
        # 檢查檔案是否存在
        possible_paths = [
            file_name,  # 當前目錄
            f"data/{file_name}",  # data 目錄
            f"./{file_name}"
        ]
        
        file_exists = False
        actual_path = None
        for path in possible_paths:
            if Path(path).exists():
                file_exists = True
                actual_path = path
                break
        
        file_status[task_id] = {
            'has_file': True,
            'file_name': file_name,
            'exists': file_exists,
            'path': actual_path
        }
        
        status_icon = "✅" if file_exists else "❌"
        print(f"   {status_icon} {task_id}: {file_name}")
        if file_exists:
            print(f"      → 路徑: {actual_path}")
    else:
        file_status[task_id] = {'has_file': False}
        print(f"   🌐 {task_id}: (純網路任務)")

# ============================================================
# Step 3: 載入並檢查 Plans
# ============================================================
print("\n📋 Step 3: 載入執行計劃...")

with open('plans_v3_executable.json', 'r', encoding='utf-8') as f:
    plans = json.load(f)

print(f"   ✅ 載入 {len(plans)} 個計劃")

# 統計可執行步驟
total_executable = sum(len(p['tool_sequence']) for p in plans)
total_skipped = sum(p['stats']['skipped_steps'] for p in plans)

print(f"   📊 可執行步驟: {total_executable}")
print(f"   ⚠️  跳過步驟: {total_skipped}")

# ============================================================
# Step 4: 執行每個任務
# ============================================================
print("\n" + "="*80)
print("🔧 Step 4: 執行任務")
print("="*80)

results = []

for idx, task in enumerate(tasks, 1):
    task_id = task['task_id']
    question = task['Question']
    ground_truth = task['Final answer']
    
    print(f"\n{'='*80}")
    print(f"任務 {idx}/{len(tasks)}: {task_id}")
    print(f"問題: {question[:80]}...")
    print(f"標準答案: {ground_truth}")
    print('='*80)
    
    # 找到對應的計劃
    plan = next((p for p in plans if p['task_id'] == task_id), None)
    
    if not plan:
        print("   ❌ 找不到執行計劃")
        results.append({
            'task_id': task_id,
            'status': 'no_plan',
            'executable_steps': 0,
            'success_steps': 0
        })
        continue
    
    # 執行步驟
    tool_sequence = plan.get('tool_sequence', [])
    print(f"\n🔧 執行 {len(tool_sequence)} 個步驟:")
    
    success_count = 0
    step_results = []
    
    for step_idx, step in enumerate(tool_sequence, 1):
        tool_name = step['tool_name']
        arguments = step['arguments']
        desc = step.get('description', '')[:60]
        
        print(f"\n  [{step_idx}/{len(tool_sequence)}] {tool_name}")
        print(f"      {desc}...")
        
        try:
            # 執行工具
            tool_func = getattr(gf, tool_name, None)
            
            if tool_func is None:
                print(f"      ❌ 工具不存在")
                step_results.append({'tool': tool_name, 'success': False})
                continue
            
            result = tool_func(**arguments)
            
            if result.get('success', False):
                print(f"      ✅ 成功")
                success_count += 1
                step_results.append({'tool': tool_name, 'success': True})
                
                # 顯示部分結果
                if tool_name == 'calculate':
                    print(f"      結果: {result.get('result')}")
                elif tool_name == 'web_search':
                    print(f"      找到 {len(result.get('results', []))} 個結果")
                elif tool_name == 'read_json':
                    print(f"      資料類型: {result.get('type')}")
            else:
                print(f"      ❌ 失敗: {result.get('error', 'Unknown')[:50]}")
                step_results.append({'tool': tool_name, 'success': False})
                
        except Exception as e:
            print(f"      ❌ 錯誤: {str(e)[:50]}")
            step_results.append({'tool': tool_name, 'success': False})
    
    # 統計結果
    success_rate = success_count / len(tool_sequence) if tool_sequence else 0
    
    print(f"\n📊 任務統計:")
    print(f"   總步驟: {len(tool_sequence)}")
    print(f"   成功: {success_count}")
    print(f"   成功率: {success_rate*100:.1f}%")
    
    results.append({
        'task_id': task_id,
        'status': 'executed',
        'executable_steps': len(tool_sequence),
        'success_steps': success_count,
        'success_rate': success_rate,
        'ground_truth': ground_truth
    })

# ============================================================
# Step 5: 總結
# ============================================================
print("\n" + "="*80)
print("📊 總結報告")
print("="*80)

total_tasks = len(results)
total_steps = sum(r['executable_steps'] for r in results)
total_success = sum(r['success_steps'] for r in results)

print(f"\n任務總數: {total_tasks}")
print(f"總執行步驟: {total_steps}")
print(f"成功步驟: {total_success}")
if total_steps > 0:
    print(f"總成功率: {total_success/total_steps*100:.1f}%")

print("\n各任務詳細結果:")
for r in results:
    if r['status'] == 'executed':
        rate = r['success_rate'] * 100
        icon = "✅" if rate >= 50 else "⚠️" if rate >= 30 else "❌"
        print(f"{icon} {r['task_id']}: {r['success_steps']}/{r['executable_steps']} ({rate:.1f}%)")
    else:
        print(f"❌ {r['task_id']}: {r['status']}")

print("\n" + "="*80)
print("✅ 測試完成！")
print("="*80)
