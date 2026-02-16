#!/usr/bin/env python3
"""
分析 XML 結構，找出為什麼提取到 "no" 而不是 "Soups and Stews"
"""

import sys
sys.path.insert(0, '.')
import gaia_function as gf
import json

print("="*80)
print("🔍 XML 結構分析")
print("="*80)

# Step 1: Extract ZIP
print("\n📦 Step 1: Extracting ZIP...")
zip_result = gf.extract_zip('data/9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip')

if not zip_result['success']:
    print(f"❌ Failed to extract: {zip_result['error']}")
    exit(1)

extract_path = zip_result['extract_path']
files = zip_result['files']

print(f"✅ Extracted to: {extract_path}")
print(f"   Files: {len(files)}")

# Find XML file
xml_file = next((f for f in files if 'xml' in f['filename'].lower()), None)
if not xml_file:
    print("❌ No XML file found!")
    exit(1)

xml_path = xml_file['path']
print(f"   XML: {xml_file['filename']} ({xml_file['size']} bytes)")

# Step 2: Read XML
print("\n📄 Step 2: Reading XML...")
xml_result = gf.read_xml(xml_path)

if not xml_result['success']:
    print(f"❌ Failed: {xml_result['error']}")
    exit(1)

xml_data = xml_result['data']
root_tag = xml_result['root_tag']

print(f"✅ Root tag: {root_tag}")
print(f"   Top-level keys: {list(xml_data.keys())[:5]}")

# Step 3: Analyze structure
print("\n🔍 Step 3: Analyzing structure...")

def analyze_structure(obj, path="ROOT", depth=0, max_depth=5):
    """Recursively analyze XML structure"""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    
    if isinstance(obj, dict):
        for key, val in list(obj.items())[:10]:  # First 10 keys
            key_lower = key.lower()
            
            # Check if this might be categories
            if 'categor' in key_lower or 'cat' in key_lower:
                print(f"{indent}🎯 FOUND: {path}/{key}")
                if isinstance(val, dict):
                    print(f"{indent}   Type: dict with {len(val)} keys")
                    print(f"{indent}   Keys: {list(val.keys())[:5]}")
                elif isinstance(val, list):
                    print(f"{indent}   Type: list with {len(val)} items")
                    if val:
                        print(f"{indent}   First item type: {type(val[0]).__name__}")
                elif isinstance(val, str):
                    print(f"{indent}   Type: string")
                    print(f"{indent}   Value: {val[:100]}")
            
            analyze_structure(val, f"{path}/{key}", depth+1, max_depth)
            
    elif isinstance(obj, list) and obj:
        if depth < 3:  # Only show first few levels
            print(f"{indent}[List with {len(obj)} items]")
            analyze_structure(obj[0], f"{path}[0]", depth+1, max_depth)

analyze_structure(xml_data)

# Step 4: Try to extract categories manually
print("\n🔍 Step 4: Manual extraction attempt...")

categories = []

def extract_all_text(obj, in_category_section=False):
    """Extract all text, tracking if we're in category section"""
    if isinstance(obj, dict):
        for key, val in obj.items():
            is_cat = 'categor' in key.lower()
            extract_all_text(val, in_category_section or is_cat)
    elif isinstance(obj, list):
        for item in obj:
            extract_all_text(item, in_category_section)
    elif isinstance(obj, str) and obj.strip():
        if in_category_section:
            categories.append(("CATEGORY", obj.strip()))
        else:
            categories.append(("OTHER", obj.strip()))

extract_all_text(xml_data)

print(f"\n📊 Total text elements: {len(categories)}")

# Show categories
cat_texts = [t for typ, t in categories if typ == "CATEGORY"]
other_texts = [t for typ, t in categories if typ == "OTHER"]

print(f"\n🎯 In category sections: {len(cat_texts)}")
if cat_texts:
    print(f"   First 10: {cat_texts[:10]}")

print(f"\n📄 Other texts: {len(other_texts)}")
if other_texts:
    print(f"   First 10: {other_texts[:10]}")

# Check if "Soups and Stews" is anywhere
print("\n🔍 Searching for 'Soups and Stews'...")
found_in_cat = any('soup' in t.lower() for t in cat_texts)
found_in_other = any('soup' in t.lower() for t in other_texts)

if found_in_cat:
    print("   ✅ Found in category section!")
    soups = [t for t in cat_texts if 'soup' in t.lower()]
    print(f"   Matches: {soups}")
elif found_in_other:
    print("   ⚠️  Found in OTHER section (not category)")
    soups = [t for t in other_texts if 'soup' in t.lower()]
    print(f"   Matches: {soups[:5]}")
else:
    print("   ❌ Not found!")

print("\n" + "="*80)
print("💡 Conclusion")
print("="*80)

if found_in_cat:
    print("✅ Categories ARE in the XML")
    print("   → Need to fix extraction logic")
elif found_in_other:
    print("⚠️  Categories are there but not marked as 'category'")
    print("   → Need to extract ALL text, not just category-marked sections")
else:
    print("❌ 'Soups and Stews' not found in XML")
    print("   → Wrong XML file or data structure issue")
