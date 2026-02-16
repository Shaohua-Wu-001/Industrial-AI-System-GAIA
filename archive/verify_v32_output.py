#!/usr/bin/env python3
"""
檢查 v3.2 是否真的修復了參數
"""

import json
from pathlib import Path

print("="*80)
print("🔍 檢查 v3.2 輸出的實際內容")
print("="*80)

v32_file = 'parser_output/plans_v3.2_autofix.json'

if not Path(v32_file).exists():
    print(f"❌ 找不到 {v32_file}")
    print("請先運行: python3 parser_v3.2_autofix.py")
    exit(1)

with open(v32_file, 'r') as f:
    data = json.load(f)

print(f"\n✅ 載入 {len(data)} 個任務")

# 統計步驟
total = sum(len(t['tool_sequence']) for t in data)
print(f"📊 總步驟: {total}")

# ============================================================
# 檢查 task_009 的 unit_converter
# ============================================================
print("\n" + "="*80)
print("【1】檢查 task_009 的 unit_converter 參數")
print("="*80)

task_009 = next((t for t in data if t['task_id'] == 'gaia_val_l3_009'), None)

if not task_009:
    print("❌ 找不到 task_009")
else:
    print(f"\ntask_009 總步驟: {len(task_009['tool_sequence'])}")
    
    unit_conv_steps = [
        (i, s) for i, s in enumerate(task_009['tool_sequence'], 1)
        if s['tool_name'] == 'unit_converter'
    ]
    
    print(f"unit_converter 步驟: {len(unit_conv_steps)} 個\n")
    
    all_good = True
    for step_num, step in unit_conv_steps:
        params = list(step['arguments'].keys())
        desc = step.get('description', '')[:60]
        
        # 檢查是否有錯誤參數
        bad_params = [p for p in params if p in ['operation', 'expression']]
        
        print(f"步驟 {step_num}: {step['tool_name']}")
        print(f"  描述: {desc}...")
        print(f"  參數: {params}")
        
        if bad_params:
            print(f"  ❌ 發現錯誤參數: {bad_params}")
            all_good = False
        else:
            print(f"  ✅ 參數正確")
        print()
    
    if all_good:
        print("✅ task_009 的所有 unit_converter 步驟參數都正確")
    else:
        print("❌ task_009 的 unit_converter 還有錯誤參數")
        print("   這說明 v3.2 沒有真正修復！")

# ============================================================
# 檢查 task_006 的 extract_zip
# ============================================================
print("\n" + "="*80)
print("【2】檢查 task_006 的 extract_zip")
print("="*80)

task_006 = next((t for t in data if t['task_id'] == 'gaia_val_l3_006'), None)

if not task_006:
    print("❌ 找不到 task_006")
else:
    print(f"\ntask_006 總步驟: {len(task_006['tool_sequence'])}")
    
    extract_steps = [
        (i, s) for i, s in enumerate(task_006['tool_sequence'], 1)
        if s['tool_name'] == 'extract_zip'
    ]
    
    if extract_steps:
        print(f"✅ 找到 {len(extract_steps)} 個 extract_zip 步驟")
        for step_num, step in extract_steps:
            print(f"\n步驟 {step_num}:")
            print(f"  參數: {step['arguments']}")
    else:
        print("❌ 沒有 extract_zip 步驟")
        print("   這說明 v3.2 沒有插入 extract_zip！")
    
    # 顯示所有步驟
    print(f"\ntask_006 的所有步驟:")
    for i, s in enumerate(task_006['tool_sequence'], 1):
        print(f"  {i}. {s['tool_name']}")

# ============================================================
# 結論
# ============================================================
print("\n" + "="*80)
print("【結論】")
print("="*80)

print("""
如果上面顯示：
  ✅ unit_converter 參數正確
  ✅ 有 extract_zip 步驟

那麼 v3.2 確實修復了！
問題就是 run_executor_v3.py 沒有讀取這個文件。

解決方案：使用 run_executor_v3.2.py


如果上面顯示：
  ❌ unit_converter 還有錯誤參數
  ❌ 沒有 extract_zip

那麼 v3.2 本身有問題，沒有真正修復。
需要檢查 parser_v3.2_autofix.py 的代碼。
""")
