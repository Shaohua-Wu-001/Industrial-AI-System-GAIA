#!/usr/bin/env python3
"""
GAIA Level 3 - 修復驗證腳本
測試所有修復是否成功
"""

import sys
from pathlib import Path

print("="*80)
print("🧪 GAIA Level 3 - 修復驗證")
print("="*80)

# 載入 gaia_function
try:
    import gaia_function as gf
    print("✅ gaia_function 載入成功")
except Exception as e:
    print(f"❌ 無法載入 gaia_function: {e}")
    sys.exit(1)

# ============================================================
# 測試1: xlrd 版本檢查
# ============================================================
print("\n" + "="*80)
print("📦 測試1: xlrd 版本")
print("="*80)

try:
    import xlrd
    print(f"✅ xlrd 版本: {xlrd.__version__}")
    
    # 檢查版本是否符合要求
    version_parts = xlrd.__version__.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0
    
    if major >= 2:
        print("✅ xlrd 版本符合要求 (>= 2.0.1)")
    else:
        print(f"⚠️  xlrd 版本過舊: {xlrd.__version__}")
        print("   建議執行: pip install 'xlrd>=2.0.1'")
except ImportError:
    print("❌ xlrd 未安裝")
    print("   執行: pip install 'xlrd>=2.0.1'")

# ============================================================
# 測試2: openpyxl 檢查
# ============================================================
print("\n" + "="*80)
print("📦 測試2: openpyxl")
print("="*80)

try:
    import openpyxl
    print(f"✅ openpyxl 版本: {openpyxl.__version__}")
except ImportError:
    print("⚠️  openpyxl 未安裝（非必需，但推薦）")
    print("   執行: pip install openpyxl")

# ============================================================
# 測試3: Excel 文件讀取
# ============================================================
print("\n" + "="*80)
print("📄 測試3: Excel 文件讀取")
print("="*80)

test_files = [
    ('data/food_duplicates.xls', 'read_excel'),
]

for file_path, func_name in test_files:
    if not Path(file_path).exists():
        print(f"⚠️  檔案不存在: {file_path}")
        continue
    
    try:
        func = getattr(gf, func_name)
        result = func(file_path)
        
        if result['success']:
            print(f"✅ {file_path}")
            print(f"   行數: {result.get('rows', 'N/A')}")
            print(f"   列數: {len(result.get('columns', []))}")
        else:
            print(f"❌ {file_path}")
            print(f"   錯誤: {result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"❌ {file_path}")
        print(f"   異常: {str(e)[:100]}")

# ============================================================
# 測試4: 其他文件讀取
# ============================================================
print("\n" + "="*80)
print("📄 測試4: 其他文件讀取")
print("="*80)

other_files = [
    ('data/bec74516-02fc-48dc-b202-55e78d0e17cf.jsonld', 'read_json'),
    ('data/CATEGORIES.xml', 'read_xml'),
]

for file_path, func_name in other_files:
    if not Path(file_path).exists():
        print(f"⚠️  檔案不存在: {file_path}")
        continue
    
    try:
        func = getattr(gf, func_name)
        result = func(file_path)
        
        if result['success']:
            print(f"✅ {file_path}")
            if func_name == 'read_json':
                print(f"   類型: {result.get('type', 'N/A')}")
            elif func_name == 'read_xml':
                print(f"   根標籤: {result.get('root_tag', 'N/A')}")
        else:
            print(f"❌ {file_path}")
            print(f"   錯誤: {result.get('error', 'Unknown')[:80]}")
    except Exception as e:
        print(f"❌ {file_path}")
        print(f"   異常: {str(e)[:100]}")

# ============================================================
# 測試5: User-Agent 檢查
# ============================================================
print("\n" + "="*80)
print("🌐 測試5: User-Agent 設定")
print("="*80)

# 檢查 gaia_function.py 中的 User-Agent
gaia_file = Path('gaia_function.py')
if gaia_file.exists():
    with open(gaia_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '"User-Agent": "GAIA-Tools' in content:
        print("⚠️  使用機器人風格的 User-Agent")
        print("   建議修改為真實瀏覽器 User-Agent")
    elif 'Mozilla' in content and 'Safari' in content:
        print("✅ 使用真實瀏覽器 User-Agent")
    else:
        print("ℹ️  無法判斷 User-Agent 設定")
else:
    print("❌ 找不到 gaia_function.py")

# 實際測試網站訪問
print("\n測試網站訪問:")
try:
    test_url = "https://httpbin.org/user-agent"
    result = gf.web_fetch(test_url, timeout=5)
    
    if result['success']:
        print(f"✅ 網站訪問成功")
        if 'Mozilla' in result['content']:
            print("✅ User-Agent 看起來像真實瀏覽器")
        else:
            print("⚠️  User-Agent 可能被識別為機器人")
            print(f"   內容: {result['content'][:100]}")
    else:
        print(f"❌ 網站訪問失敗: {result.get('error', 'Unknown')}")
except Exception as e:
    print(f"❌ 測試異常: {str(e)[:100]}")

# ============================================================
# 測試6: 單位轉換
# ============================================================
print("\n" + "="*80)
print("🔢 測試6: 單位轉換")
print("="*80)

test_conversions = [
    (1, 'L', 'mL', 'volume', 1000.0),
    (1000, 'mL', 'L', 'volume', 1.0),
]

for value, from_u, to_u, typ, expected in test_conversions:
    try:
        result = gf.unit_converter(value, from_u, to_u, typ)
        
        if result['success']:
            actual = result['result']
            if abs(actual - expected) < 0.01:
                print(f"✅ {value} {from_u} = {actual} {to_u}")
            else:
                print(f"⚠️  {value} {from_u} = {actual} {to_u} (預期: {expected})")
        else:
            print(f"❌ {value} {from_u} → {to_u}: {result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"❌ 轉換異常: {str(e)[:100]}")

# ============================================================
# 總結
# ============================================================
print("\n" + "="*80)
print("📊 驗證總結")
print("="*80)

print("""
✅ 已驗證的功能：
1. xlrd 版本 (應該是 >= 2.0.1)
2. Excel 文件讀取 (應該 100% 成功)
3. JSON/XML 文件讀取 (應該 100% 成功)
4. User-Agent 設定 (應該看起來像真實瀏覽器)
5. 單位轉換 (應該 100% 成功)

如果上述測試都通過，執行:
    python3 test_all_10_tasks.py

預期結果:
• 總成功率: 94-97%
• 文件讀取: 100%
• 一般網站訪問: 85-95%

如果還有問題，檢查:
1. xlrd 是否真的升級到 2.0.1+
2. User-Agent 是否修改為真實瀏覽器
3. 網路連線是否正常
""")

print("="*80)
print("✅ 驗證完成")
print("="*80)
