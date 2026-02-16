#!/usr/bin/env python3
"""
最終修復：更好的文本清理
"""

import re

print("="*80)
print("🔧 Final Fix: Better Text Cleaning")
print("="*80)

# 讀取檔案
with open('minimal_reasoning_layer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到並替換 categories 過濾邏輯
old_filter = '''    # Filter for potential categories
    # Categories are usually: capitalized, contain spaces, 5-50 chars
    categories = []
    for text in all_texts:
        # Remove quotes
        clean = text.strip('"\\'').strip()
        
        # Category characteristics:
        # - Contains space or "and"
        # - First letter uppercase
        # - Length 5-50 characters
        if (' ' in clean or 'and' in clean) and \\
           clean and clean[0].isupper() and \\
           5 <= len(clean) <= 50:
            categories.append(clean)'''

new_filter = '''    # Filter for potential categories
    # Categories are usually: capitalized, contain spaces, 5-50 chars
    categories = []
    for text in all_texts:
        # Remove quotes, commas, and extra whitespace
        clean = text.strip('"\\'').strip()
        clean = clean.rstrip(',')  # Remove trailing commas
        clean = clean.strip()
        
        # Category characteristics:
        # - Contains space or "and"
        # - First letter uppercase
        # - Length 5-50 characters
        if (' ' in clean or 'and' in clean) and \\
           clean and clean[0].isupper() and \\
           5 <= len(clean) <= 50:
            categories.append(clean)'''

if old_filter in content:
    content = content.replace(old_filter, new_filter)
    print("✅ Updated text cleaning logic")
    print("   • Added: .rstrip(',') to remove trailing commas")
    print("   • Added: extra .strip() after comma removal")
    
    # 寫回
    with open('minimal_reasoning_layer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ File updated!")
else:
    print("⚠️  Pattern not found, trying alternative approach...")
    
    # 替代方案：直接用 sed 風格替換
    pattern = r"clean = text\.strip\('\"\\\\'\)\.strip\(\)"
    replacement = "clean = text.strip('\"\\\\\\\\').strip().rstrip(',').strip()"
    
    content = re.sub(pattern, replacement, content)
    
    with open('minimal_reasoning_layer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Applied alternative fix!")

print("\n" + "="*80)
print("✅ Fix Complete!")
print("="*80)
print("\nTest now:")
print("  python3 test_fixed_solver.py")
print("\nExpected:")
print("  ✨ Solver Answer: Soups and Stews")
print("  🎯 Ground Truth: Soups and Stews")
print("  Status: ✅ CORRECT!")
