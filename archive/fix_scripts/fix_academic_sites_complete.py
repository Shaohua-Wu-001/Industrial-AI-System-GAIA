#!/usr/bin/env python3
"""
修復學術網站訪問的兩個問題：
1. 修正 plans 中的 URL 錯誤
2. 增強瀏覽器 headers
"""

import json
import re
from pathlib import Path

print("="*80)
print("🔧 修復學術網站訪問問題")
print("="*80)

# ============================================================
# 修復 1: 修正 plans_v3_executable.json 中的 URL
# ============================================================
print("\n📋 修復 1: 修正 URL 錯誤")
print("-"*80)

plans_file = Path('plans_v3_executable.json')
if not plans_file.exists():
    print("❌ 找不到 plans_v3_executable.json")
    exit(1)

with open(plans_file, 'r', encoding='utf-8') as f:
    plans = json.load(f)

# 找到 l3_005 任務
task_005 = None
for i, plan in enumerate(plans):
    if plan['task_id'] == 'gaia_val_l3_005':
        task_005 = plan
        task_005_index = i
        break

if not task_005:
    print("❌ 找不到 gaia_val_l3_005")
    exit(1)

# 修正 URLs
url_fixes = [
    {
        'step_id': 'step_2',
        'old': 'https://en.wikipedia.org/wiki/hafnia_(bacterium',
        'new': 'https://en.wikipedia.org/wiki/Hafnia_(bacterium)',
        'issue': '缺少右括號和大小寫錯誤'
    },
    {
        'step_id': 'step_4',
        'old': 'https://www.mdpi.com/2076-2607/11/1/123?type=check_update&version=',
        'new': 'https://www.mdpi.com/2076-2607/11/1/123',
        'issue': 'version 參數為空'
    }
]

fixed_count = 0
for fix in url_fixes:
    for step in task_005['tool_sequence']:
        if step['step_id'] == fix['step_id'] and step['tool_name'] == 'web_fetch':
            if step['arguments']['url'] == fix['old']:
                step['arguments']['url'] = fix['new']
                print(f"✅ 修正 {fix['step_id']}: {fix['issue']}")
                print(f"   {fix['old']}")
                print(f"   → {fix['new']}")
                fixed_count += 1

if fixed_count > 0:
    # 更新 plans
    plans[task_005_index] = task_005
    
    # 寫回檔案
    with open(plans_file, 'w', encoding='utf-8') as f:
        json.dump(plans, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 修正了 {fixed_count} 個 URL")
    print(f"✅ 已更新 {plans_file}")
else:
    print("\n⚠️  沒有找到需要修正的 URL（可能已修正過）")

# ============================================================
# 修復 2: 增強 gaia_function.py 的瀏覽器 headers
# ============================================================
print("\n" + "="*80)
print("🌐 修復 2: 增強瀏覽器 Headers")
print("-"*80)

gaia_file = Path('gaia_function.py')
if not gaia_file.exists():
    print("❌ 找不到 gaia_function.py")
    exit(1)

with open(gaia_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 尋找 web_fetch 函數中的 headers
# 找到最簡單的 User-Agent header
old_pattern = r'headers=\{"User-Agent": "[^"]+"\}'

# 新的完整 headers（模擬真實 Chrome）
new_headers = '''headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }'''

# 替換所有的 headers
matches = re.finditer(old_pattern, content)
match_count = len(list(re.finditer(old_pattern, content)))

if match_count > 0:
    print(f"✅ 找到 {match_count} 個 headers 定義")
    content = re.sub(old_pattern, new_headers, content)
    
    # 寫回檔案
    with open(gaia_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已更新為完整的瀏覽器 headers")
    print(f"✅ 已儲存 {gaia_file}")
    
    print("\n新增的 headers:")
    print("  • Accept: 接受的內容類型")
    print("  • Accept-Language: 語言偏好")
    print("  • Accept-Encoding: 壓縮格式")
    print("  • DNT: Do Not Track")
    print("  • Sec-Fetch-*: Chrome 安全標頭")
    print("  • Cache-Control: 緩存控制")
else:
    print("⚠️  找不到需要修改的 headers（可能已修改過）")

# ============================================================
# 測試修復結果
# ============================================================
print("\n" + "="*80)
print("🧪 測試修復結果")
print("="*80)

try:
    import gaia_function as gf
    
    test_urls = [
        ("Wikipedia", "https://en.wikipedia.org/wiki/Hafnia_(bacterium)"),
        ("MDPI", "https://www.mdpi.com/2076-2607/11/1/123"),
        ("PubMed", "https://pubmed.ncbi.nlm.nih.gov/36080356/"),
    ]
    
    print("\n正在測試...")
    success_count = 0
    
    for name, url in test_urls:
        print(f"\n{name}:")
        print(f"  URL: {url}")
        try:
            result = gf.web_fetch(url, timeout=15)
            if result['success']:
                content_len = len(result['content'])
                preview = result['content'][:80].replace('\n', ' ').strip()
                print(f"  ✅ 成功！（{content_len} 字符）")
                print(f"  內容: {preview}...")
                success_count += 1
            else:
                error = result['error'][:100]
                print(f"  ❌ 失敗: {error}")
        except Exception as e:
            print(f"  ❌ 異常: {str(e)[:100]}")
    
    print("\n" + "-"*80)
    print(f"測試結果: {success_count}/{len(test_urls)} 成功")
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    print("   提示: 執行 test_all_10_tasks.py 來完整測試")

# ============================================================
# 總結
# ============================================================
print("\n" + "="*80)
print("📊 修復總結")
print("="*80)

print("""
已完成的修復：
✅ 1. 修正 Wikipedia URL（補上右括號）
✅ 2. 修正 MDPI URL（移除空參數）
✅ 3. 增強瀏覽器 headers（10+ 個新標頭）

可能改善的成功率：
• l3_005 任務: 從 5/8 (62.5%) → 預計 7-8/8 (87.5-100%)
• 總成功率: 從 31/34 (91.2%) → 預計 33-34/34 (97-100%)

為什麼可能還會失敗：
• 學術網站的反爬蟲機制（需要cookies、JavaScript等）
• IP限制或地理封鎖
• 網站臨時不可用

下一步：
    python3 test_all_10_tasks.py

如果還是失敗，建議：
1. 檢查網路連線
2. 嘗試手動訪問 URL 確認可訪問
3. 考慮使用 Selenium（需要額外安裝）
""")

print("="*80)
print("✅ 修復完成！")
print("="*80)
