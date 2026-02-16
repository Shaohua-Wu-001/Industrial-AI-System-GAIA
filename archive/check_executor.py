#!/usr/bin/env python3
"""
診斷 run_executor_v3.py 讀取的文件
"""

import json
from pathlib import Path

print("="*80)
print("🔍 診斷 Executor 讀取的文件")
print("="*80)

# 檢查所有可能的計劃文件
files_to_check = [
    'plans_v3_executable.json',
    'parser_output/plans_v3.1_bugfix.json',
    'parser_output/plans_v3.2_autofix.json',
    'plans_v3.1_bugfix.json'  # 可能在根目錄
]

print("\n【1】檢查所有計劃文件的內容")

for fpath in files_to_check:
    p = Path(fpath)
    if p.exists():
        with open(p, 'r') as f:
            data = json.load(f)
        
        # 統計步驟
        total_steps = 0
        executable_steps = 0
        skipped_steps = 0
        
        for task in data:
            tool_seq = task.get('tool_sequence', [])
            total_steps += len(tool_seq)
            
            for step in tool_seq:
                if step.get('executable', True) and not step.get('skip_reason'):
                    executable_steps += 1
                else:
                    skipped_steps += 1
        
        print(f"\n✅ {fpath}")
        print(f"   總步驟: {total_steps}")
        print(f"   可執行: {executable_steps}")
        print(f"   跳過: {skipped_steps}")
        
        # 檢查 task_009 的 unit_converter
        task_009 = next((t for t in data if t['task_id'] == 'gaia_val_l3_009'), None)
        if task_009:
            unit_conv_steps = [
                s for s in task_009['tool_sequence']
                if s['tool_name'] == 'unit_converter'
            ]
            
            if unit_conv_steps:
                print(f"   task_009 unit_converter: {len(unit_conv_steps)} 個")
                for i, step in enumerate(unit_conv_steps[:2], 1):  # 只看前2個
                    params = list(step['arguments'].keys())
                    has_bad = any(k in params for k in ['operation', 'expression'])
                    status = "❌ 有錯誤參數" if has_bad else "✅ 參數正確"
                    print(f"      [{i}] {status}: {params}")
    else:
        print(f"\n❌ {fpath} - 不存在")

print("\n" + "="*80)
print("【2】檢查 run_executor_v3.py 讀取哪個文件")
print("="*80)

executor_file = 'run_executor_v3.py'
if Path(executor_file).exists():
    with open(executor_file, 'r') as f:
        content = f.read()
    
    # 查找 open() 調用
    import re
    patterns = [
        r"open\(['\"]([^'\"]+\.json)['\"]",
        r"Path\(['\"]([^'\"]+\.json)['\"]",
    ]
    
    found_files = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        found_files.update(matches)
    
    if found_files:
        print(f"\n✅ {executor_file} 讀取的文件:")
        for f in found_files:
            print(f"   - {f}")
    else:
        print(f"\n⚠️  無法從代碼中找到文件路徑")
        print("請手動檢查 run_executor_v3.py")
else:
    print(f"\n❌ {executor_file} 不存在")

print("\n" + "="*80)
print("【3】結論")
print("="*80)

print("""
根據你的執行結果:
  Executor 顯示: 36 個可執行步驟

這對應到哪個文件?
  如果是 36 + 28 = 64 總步驟 → 可能是 v3.1 或 plans_v3_executable.json
  如果是 38 個可執行步驟 → 應該是 v3.2

問題診斷:
  1. run_executor_v3.py 可能讀取 plans_v3_executable.json
  2. 或者替換沒有生效
  3. 或者 v3.2 根本沒有真的修復參數

解決方案:
  請運行上面的腳本，然後手動檢查 run_executor_v3.py 的代碼
""")
