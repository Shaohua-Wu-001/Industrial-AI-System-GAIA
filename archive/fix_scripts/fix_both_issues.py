#!/usr/bin/env python3
"""
完整修復：同時解決函數調用和文本清理問題
"""

import re

print("="*80)
print("🔧 Complete Fix: Function Call + Text Cleaning")
print("="*80)

# 讀取檔案
with open('minimal_reasoning_layer.py', 'r', encoding='utf-8') as f:
    content = f.read()

fixes_applied = []

# ============================================================
# Fix 1: 函數調用 - 移除第三個參數
# ============================================================
old_call = "deterministic_answer = solve_excel_xml_deterministic(excel_result, xml_result, task_question)"
new_call = "deterministic_answer = solve_excel_xml_deterministic(excel_result, xml_result)"

if old_call in content:
    content = content.replace(old_call, new_call)
    fixes_applied.append("✅ Fixed function call (removed 3rd parameter)")
    print("\n📞 Fix 1: Function Call")
    print("   Old: solve_excel_xml_deterministic(excel_result, xml_result, task_question)")
    print("   New: solve_excel_xml_deterministic(excel_result, xml_result)")
else:
    print("\n⚠️  Fix 1: Pattern not found (might be already fixed)")

# ============================================================
# Fix 2: 文本清理 - 移除引號和逗號
# ============================================================
# 查找 text cleaning 部分
pattern1 = r"clean = text\.strip\(['\"]\\\"\\\\['\"]'\)\.strip\(\)"
replacement1 = r"clean = text.strip('\"\\\\').strip().rstrip(',').strip().rstrip('\"').strip()"

if re.search(pattern1, content):
    content = re.sub(pattern1, replacement1, content)
    fixes_applied.append("✅ Enhanced text cleaning (removes quotes and commas)")
    print("\n🧹 Fix 2: Text Cleaning (Method A)")
    print("   Added: .rstrip(',') - remove trailing commas")
    print("   Added: .rstrip('\"') - remove trailing quotes")
    print("   Added: extra .strip() - remove whitespace")
else:
    # 替代方案：尋找更廣泛的模式
    pattern2 = r"(clean = text\.strip\([^)]+\)\.strip\(\))"
    if re.search(pattern2, content):
        # 直接在這行後面添加額外的清理
        replacement2 = r"\1.rstrip(',').strip().rstrip('\"').strip()"
        content = re.sub(pattern2, replacement2, content)
        fixes_applied.append("✅ Enhanced text cleaning (alternative method)")
        print("\n🧹 Fix 2: Text Cleaning (Method B)")
        print("   Added comprehensive cleaning chain")
    else:
        print("\n⚠️  Fix 2: Pattern not found")

# 寫回檔案
with open('minimal_reasoning_layer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*80)
print("📊 Summary")
print("="*80)
for fix in fixes_applied:
    print(f"  {fix}")

if len(fixes_applied) == 0:
    print("  ⚠️  No fixes applied (patterns not found)")
    print("\n  Trying manual inspection...")
    
    # 顯示相關的行
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'solve_excel_xml_deterministic' in line and 'deterministic_answer' in line:
            print(f"\n  Line {i+1}: {line.strip()}")
        if 'clean = text.strip' in line:
            print(f"\n  Line {i+1}: {line.strip()}")

print("\n" + "="*80)
print("✅ Update Complete!")
print("="*80)
print("\nTest now:")
print("  python3 test_fixed_solver.py")
print("\nExpected:")
print("  ✨ Solver Answer: Soups and Stews")
print("  🎯 Ground Truth: Soups and Stews")
print("  Status: ✅ CORRECT!")
