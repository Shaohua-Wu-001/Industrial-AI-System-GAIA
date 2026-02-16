#!/usr/bin/env python3
"""
GAIA Level 3 - 完整評估框架
評估維度：
1. Function Calling 正確性
2. 答案準確性
3. Planning 質量
4. 研究 Insights
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
import re

sys.path.insert(0, os.path.dirname(__file__))
import gaia_function as gf

print("="*80)
print("📊 GAIA Level 3 - 完整評估框架")
print("="*80)

# ============================================================
# 載入資料
# ============================================================
with open('gaia_level3_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

with open('plans_v3_executable.json', 'r', encoding='utf-8') as f:
    plans = json.load(f)

# ============================================================
# 評估維度 1: Function Calling 正確性
# ============================================================
print("\n" + "="*80)
print("📋 評估 1: Function Calling 正確性")
print("="*80)

function_calling_results = []

for plan in plans:
    task_id = plan['task_id']
    tool_sequence = plan.get('tool_sequence', [])
    
    for step in tool_sequence:
        tool_name = step['tool_name']
        arguments = step['arguments']
        
        # 檢查工具是否存在
        tool_exists = hasattr(gf, tool_name)
        
        # 檢查參數是否有效
        valid_args = True
        arg_issues = []
        
        for key, value in arguments.items():
            if isinstance(value, str):
                # 檢查是否包含佔位符
                if re.search(r'<[^>]+>', value):
                    valid_args = False
                    arg_issues.append(f"{key} 包含佔位符")
        
        function_calling_results.append({
            'task_id': task_id,
            'step_id': step['step_id'],
            'tool_name': tool_name,
            'tool_exists': tool_exists,
            'valid_args': valid_args,
            'arg_issues': arg_issues
        })

# 統計
total_calls = len(function_calling_results)
valid_calls = sum(1 for r in function_calling_results if r['tool_exists'] and r['valid_args'])
invalid_tools = sum(1 for r in function_calling_results if not r['tool_exists'])
invalid_args = sum(1 for r in function_calling_results if not r['valid_args'])

print(f"\n總 Function Calls: {total_calls}")
print(f"有效調用: {valid_calls} ({valid_calls/total_calls*100:.1f}%)")
print(f"無效工具: {invalid_tools}")
print(f"無效參數: {invalid_args}")

print("\n⚠️  無效調用範例:")
for r in function_calling_results[:5]:
    if not r['tool_exists'] or not r['valid_args']:
        print(f"  {r['task_id']}/{r['step_id']}: {r['tool_name']}")
        if r['arg_issues']:
            print(f"    問題: {', '.join(r['arg_issues'])}")

# ============================================================
# 評估維度 2: 答案準確性
# ============================================================
print("\n" + "="*80)
print("🎯 評估 2: 答案準確性（需要人工檢查）")
print("="*80)

print("""
⚠️  注意：這個測試框架**無法自動驗證答案正確性**

原因：
1. 大部分任務需要多步驟推理
2. 中間步驟的輸出無法直接對應最終答案
3. 需要人工綜合分析所有步驟結果

建議的驗證方式：
""")

for task in tasks[:3]:  # 只顯示前3個作為範例
    task_id = task['task_id']
    ground_truth = task['Final answer']
    plan = next((p for p in plans if p['task_id'] == task_id), None)
    
    print(f"\n{task_id}:")
    print(f"  標準答案: {ground_truth}")
    print(f"  問題類型: ", end="")
    
    # 分析問題類型
    question = task['Question']
    if 'calculate' in question.lower() or 'percentage' in question.lower():
        print("計算題 → 檢查最後的 calculate 結果")
    elif 'average' in question.lower():
        print("平均數 → 檢查 calculate 或 statistical_analysis 結果")
    elif 'which' in question.lower() or 'what' in question.lower():
        print("查找題 → 需要檢查多步驟結果")
    else:
        print("複雜推理 → 需要人工綜合判斷")
    
    if plan:
        print(f"  可執行步驟: {len(plan['tool_sequence'])}")
        print(f"  成功率: {plan['stats']['executable_rate']*100:.1f}%")

print("\n💡 建議：創建 answer_validator.py 來半自動化驗證")

# ============================================================
# 評估維度 3: Planning 質量
# ============================================================
print("\n" + "="*80)
print("🧠 評估 3: Planning 質量")
print("="*80)

planning_metrics = {
    'total_tasks': len(plans),
    'avg_executable_rate': sum(p['stats']['executable_rate'] for p in plans) / len(plans),
    'avg_steps_per_task': sum(len(p['tool_sequence']) for p in plans) / len(plans),
    'avg_skipped_per_task': sum(p['stats']['skipped_steps'] for p in plans) / len(plans),
}

print(f"\n平均可執行率: {planning_metrics['avg_executable_rate']*100:.1f}%")
print(f"平均步驟數: {planning_metrics['avg_steps_per_task']:.1f}")
print(f"平均跳過數: {planning_metrics['avg_skipped_per_task']:.1f}")

# 分析 Planning 問題
print("\n📊 Planning 問題類別:")
skip_categories = {
    '佔位符參數': 0,
    '檔案不存在': 0,
    '不支援功能': 0,
    '其他': 0
}

for plan in plans:
    for step in plan.get('skipped_steps', []):
        reason = step.get('skip_reason', '')
        if '佔位符' in reason or '<' in reason:
            skip_categories['佔位符參數'] += 1
        elif '檔案不存在' in reason:
            skip_categories['檔案不存在'] += 1
        elif '不支援' in reason:
            skip_categories['不支援功能'] += 1
        else:
            skip_categories['其他'] += 1

for category, count in skip_categories.items():
    print(f"  {category}: {count}次")

# ============================================================
# Research Insights
# ============================================================
print("\n" + "="*80)
print("🔬 Research Insights")
print("="*80)

print("""
基於當前實驗的發現：

1️⃣ **Parser 的主要限制**
   
   a) 無法處理動態參數（30個步驟跳過）
      - 參數需要從前面步驟結果提取
      - 例：<from_context>, <iterate:xxx>
      
   b) 無法處理多步驟依賴
      - 步驟A的輸出 → 步驟B的輸入
      - 缺少「中間變量」機制
      
   c) 無法處理循環和條件邏輯
      - 例：對每個ORCID ID重複操作
      - 例：如果結果不存在則嘗試其他方法

2️⃣ **工具執行的限制**
   
   a) 外部依賴（學術網站反爬蟲）
      - MDPI: 403 Forbidden
      - 解決：使用API或手動獲取
      
   b) 工具覆蓋不完整
      - 缺少某些單位轉換類型
      - 缺少複雜推理工具（如ISBN驗證）
      
   c) 缺少狀態管理
      - 無法保存中間結果
      - 無法在步驟間傳遞數據

3️⃣ **答案準確性的挑戰**
   
   a) 大部分任務需要多步驟推理
      - 單個工具無法得到最終答案
      - 需要人工綜合多個步驟的結果
      
   b) 缺少答案驗證機制
      - 無法自動檢查答案是否正確
      - 需要人工比對ground truth
      
   c) 某些任務超出工具能力
      - 例：l3_007需要複雜數學推理
      - 需要更高級的推理引擎
""")

# ============================================================
# Next Steps 建議
# ============================================================
print("\n" + "="*80)
print("🚀 Next Steps 建議")
print("="*80)

print("""
短期（1-2週）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 1. 實現答案驗證系統
   - 創建 answer_validator.py
   - 對簡單任務自動驗證（計算題）
   - 對複雜任務提供人工驗證界面
   
✅ 2. 改善 Parser
   - 支援中間變量：$result_from_step_1
   - 支援簡單循環：for item in previous_results
   - 支援條件邏輯：if-then-else
   
✅ 3. 擴充工具集
   - 添加缺失的單位轉換
   - 添加數學推理工具
   - 添加狀態管理工具（save/load results）

中期（1-2個月）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 4. 實現 ReAct 風格的執行器
   - 動態規劃：根據前面結果調整後續步驟
   - 錯誤恢復：如果步驟失敗，嘗試替代方案
   - 結果驗證：檢查中間結果是否合理
   
🔄 5. 實現多輪對話系統
   - 讓 LLM 能夠看到前面步驟的結果
   - 根據結果決定下一步操作
   - 支援 "思考→行動→觀察" 循環
   
🔄 6. 建立 Benchmark
   - 標準化評估指標
   - 自動化測試流程
   - 與其他系統比較

長期（3-6個月）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 7. 研究混合系統
   - LLM Planning + Symbolic Reasoning
   - 對於數學題使用SMT Solver
   - 對於邏輯題使用邏輯引擎
   
🎯 8. 研究 Self-Correction
   - 讓系統能夠檢測錯誤
   - 自動修正planning
   - 從失敗中學習
   
🎯 9. 發表研究成果
   - 分析 Parser 的能力邊界
   - 提出改進方法
   - 與 GAIA Benchmark 社群分享
""")

# ============================================================
# 輸出詳細報告
# ============================================================
print("\n" + "="*80)
print("📄 生成詳細報告")
print("="*80)

report = {
    'function_calling': {
        'total_calls': total_calls,
        'valid_calls': valid_calls,
        'invalid_tools': invalid_tools,
        'invalid_args': invalid_args,
        'accuracy': valid_calls / total_calls
    },
    'planning': planning_metrics,
    'skip_categories': skip_categories,
    'insights': {
        'parser_limitations': [
            '無法處理動態參數',
            '無法處理多步驟依賴',
            '無法處理循環和條件邏輯'
        ],
        'tool_limitations': [
            '外部依賴限制',
            '工具覆蓋不完整',
            '缺少狀態管理'
        ],
        'answer_accuracy_challenges': [
            '需要多步驟推理',
            '缺少驗證機制',
            '某些任務超出能力'
        ]
    }
}

with open('evaluation_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("✅ 已生成 evaluation_report.json")

print("\n" + "="*80)
print("✅ 評估完成")
print("="*80)
