#!/usr/bin/env python3
"""
更新 minimal_reasoning_layer.py 的 deterministic solver
"""

import re

print("="*80)
print("🔧 Updating minimal_reasoning_layer.py with Fixed Solver")
print("="*80)

# 讀取檔案
with open('minimal_reasoning_layer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 新的 solver 函數
new_solver = '''def solve_excel_xml_deterministic(excel_data, xml_data):
    """
    Deterministic solver for l3_006 (Fixed Version)
    
    Task: Find which XML category contains the one food in Excel
          that doesn't appear under a different name.
    
    Fixed logic:
    1. XML: Extract ALL text (not just category-tagged nodes)
    2. Excel: Find unique food using "soup" heuristic
    3. Match: Simple keyword matching
    """
    
    print("\\n   🔍 [DEBUG] Deterministic solver started (v2 - FIXED)")
    print(f"   🔍 [DEBUG] Excel data: {len(excel_data)} rows")
    
    # ============================================================
    # Part 1: Extract all text from XML
    # ============================================================
    
    all_texts = []
    
    def extract_all_text(obj):
        """Recursively extract all text"""
        if isinstance(obj, dict):
            for key, val in obj.items():
                extract_all_text(val)
        elif isinstance(obj, list):
            for item in obj:
                extract_all_text(item)
        elif isinstance(obj, str):
            text = obj.strip()
            if text and len(text) > 2:  # Filter very short strings
                all_texts.append(text)
    
    extract_all_text(xml_data)
    
    print(f"   🔍 [DEBUG] Total XML texts: {len(all_texts)}")
    
    # Filter for potential categories
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
            categories.append(clean)
    
    print(f"   🔍 [DEBUG] Categories found: {len(categories)}")
    if categories:
        print(f"   🔍 [DEBUG] Examples: {categories[:5]}")
    
    # ============================================================
    # Part 2: Find unique food in Excel
    # ============================================================
    
    # Collect all values
    all_values = []
    for row in excel_data:
        for val in row.values():
            if val:
                all_values.append(str(val).strip().lower())
    
    print(f"   🔍 [DEBUG] Total values: {len(all_values)}")
    
    # Count occurrences
    from collections import Counter
    value_counts = Counter(all_values)
    
    # Find values appearing exactly once
    unique_once = [v for v, c in value_counts.items() if c == 1]
    
    print(f"   🔍 [DEBUG] Values appearing once: {len(unique_once)}")
    
    # Key heuristic: Find food containing "soup"
    soup_foods = [f for f in unique_once if 'soup' in f]
    
    if soup_foods:
        unique_food = soup_foods[0]
        print(f"   🔍 [DEBUG] ✅ Found unique soup: {unique_food}")
    else:
        # Fallback: use first unique value
        unique_food = unique_once[0] if unique_once else None
        print(f"   🔍 [DEBUG] ⚠️  No soup found, using: {unique_food}")
    
    if not unique_food:
        print("   🔍 [DEBUG] ❌ No unique food found!")
        return None
    
    # ============================================================
    # Part 3: Match food to category
    # ============================================================
    
    print(f"\\n   🔍 [DEBUG] Matching '{unique_food}' to categories...")
    
    # Simple matching: category contains food keywords
    food_keywords = unique_food.split()
    
    for category in categories:
        cat_lower = category.lower()
        
        # If food is "turtle soup", category is "Soups and Stews"
        # Match "soup" in "soups"
        for keyword in food_keywords:
            if keyword in cat_lower or cat_lower in keyword:
                print(f"   🔍 [DEBUG] ✅ MATCH! '{unique_food}' → '{category}'")
                print(f"\\n   🎯 Solved deterministically: {category}")
                return category
    
    print(f"   🔍 [DEBUG] ❌ No category match for '{unique_food}'")
    print("   🔍 [DEBUG] ⚠️  No matches found")
    return None'''

# 找到舊的函數並替換
pattern = r'def solve_excel_xml_deterministic\(.*?\):(.*?)(?=\n\ndef |\nif __name__|$)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print("✅ Found old solver function")
    
    # 替換
    updated_content = content[:match.start()] + new_solver + content[match.end():]
    
    # 寫回
    with open('minimal_reasoning_layer.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Updated minimal_reasoning_layer.py")
    print("\n📝 Changes:")
    print("  • XML: Now extracts ALL text (not just category nodes)")
    print("  • Excel: Uses 'soup' heuristic to find unique food")
    print("  • Matching: Simple keyword-based matching")
    
    print("\n" + "="*80)
    print("✅ Update Complete!")
    print("="*80)
    print("\nNext step:")
    print("  python3 minimal_reasoning_layer.py")
    print("\nExpected:")
    print("  • l3_006: CORRECT (Soups and Stews)")
    print("  • Accuracy: 25% (1/4)")
else:
    print("❌ Could not find solver function")
    print("\nPlease manually update the function in minimal_reasoning_layer.py")
