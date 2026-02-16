#!/usr/bin/env python3
"""
分析 Excel，找出哪個 food 只出現一次
"""

import sys
sys.path.insert(0, '.')
import gaia_function as gf
from collections import Counter

print("="*80)
print("🔍 Excel 結構分析")
print("="*80)

# Step 1: Extract ZIP
print("\n📦 Step 1: Extracting ZIP...")
zip_result = gf.extract_zip('data/9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip')

if not zip_result['success']:
    print(f"❌ Failed: {zip_result['error']}")
    exit(1)

extract_path = zip_result['extract_path']
files = zip_result['files']

print(f"✅ Extracted to: {extract_path}")

# Find Excel file
excel_file = next((f for f in files if 'xls' in f['filename'].lower()), None)
if not excel_file:
    print("❌ No Excel file found!")
    exit(1)

excel_path = excel_file['path']
print(f"   Excel: {excel_file['filename']}")

# Step 2: Read Excel
print("\n📄 Step 2: Reading Excel...")
excel_result = gf.read_excel(excel_path)

if not excel_result['success']:
    print(f"❌ Failed: {excel_result['error']}")
    exit(1)

data = excel_result['data']
columns = excel_result['columns']

print(f"✅ Rows: {len(data)}")
print(f"   Columns: {columns}")

# Step 3: Show data
print("\n📊 Step 3: Data preview...")
for i, row in enumerate(data[:3], 1):
    print(f"\nRow {i}:")
    for col, val in row.items():
        print(f"  {col}: {val}")

# Step 4: Count ALL occurrences
print("\n🔍 Step 4: Counting occurrences...")

all_values = []
for row in data:
    for val in row.values():
        if val:
            all_values.append(str(val).strip().lower())

value_counts = Counter(all_values)

print(f"\n📊 Total values: {len(all_values)}")
print(f"   Unique values: {len(value_counts)}")

# Find foods that appear only once
unique_once = {v: c for v, c in value_counts.items() if c == 1}
print(f"\n🎯 Foods appearing EXACTLY once: {len(unique_once)}")

if len(unique_once) <= 20:
    for food in sorted(unique_once.keys()):
        print(f"  • {food}")
else:
    print(f"  First 20:")
    for food in sorted(unique_once.keys())[:20]:
        print(f"  • {food}")

# Step 5: Check for "turtle soup"
print("\n🔍 Step 5: Looking for 'turtle soup'...")
has_turtle = any('turtle' in v for v in all_values)
turtle_count = sum(1 for v in all_values if 'turtle' in v)

if has_turtle:
    print(f"   ✅ Found 'turtle' - appears {turtle_count} times")
    turtles = [v for v in all_values if 'turtle' in v]
    print(f"   Values: {set(turtles)}")
else:
    print("   ❌ No 'turtle' found")

# Step 6: Find the actual unique food
print("\n🎯 Step 6: Finding THE unique food (appears once, no duplicate under different name)...")

# According to the question, need to find food that "does not appear a second time under a different name"
# This is different from just appearing once!

# Strategy: Look for foods with unique identifiers
print("\nLooking for distinctive foods...")

distinctive = []
for food in unique_once.keys():
    # Check if it's something very specific
    if len(food) > 5:  # Not too short
        distinctive.append(food)

print(f"\nDistinctive unique foods ({len(distinctive)}):")
for f in sorted(distinctive)[:20]:
    print(f"  • {f}")

# Special check for soup-related
soups = [f for f in distinctive if 'soup' in f]
if soups:
    print(f"\n🍲 Soup-related unique foods:")
    for s in soups:
        print(f"  • {s}")

print("\n" + "="*80)
print("💡 Conclusion")
print("="*80)

if len(unique_once) == 1:
    print(f"✅ Perfect! Only 1 unique food: {list(unique_once.keys())[0]}")
elif soups:
    print(f"✅ Found soup in unique foods: {soups[0]}")
elif len(unique_once) < 10:
    print(f"⚠️  Found {len(unique_once)} unique foods (expected 1)")
    print("   → Need to refine matching logic")
else:
    print(f"❌ Too many unique foods ({len(unique_once)})")
    print("   → Problem: algorithm counts ALL unique values, not unique FOODS")
    print("   → Many duplicates exist under different names")
    print("   → Need to identify semantic duplicates (clam=geoduck, etc)")
