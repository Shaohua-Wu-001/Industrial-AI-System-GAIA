#!/usr/bin/env python3
"""GAIA 評分系統 - 使用 OpenAI API 的最終版"""

import os
import sys
import json
from openai import OpenAI
sys.path.insert(0, os.path.dirname(__file__))
import gaia_function as gf

def load_data():
    """載入任務和計劃"""
    with open('gaia_output/gaia_level3_tasks.json', 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    with open('parser_output/plans_v3_executable.json', 'r', encoding='utf-8') as f:
        plans = json.load(f)
    
    return tasks, plans

def execute_plan_steps(plan):
    """執行計劃中的工具步驟"""
    results = []
    
    for step in plan.get('tool_sequence', []):
        tool = step.get('tool_name')
        args = step.get('arguments', {})
        desc = step.get('description', '')
        
        print(f"\n  🔧 {tool}: {desc[:50]}...")
        
        try:
            if tool == 'web_search':
                result = gf.web_search(args.get('query', ''))
                if result.get('success') and result.get('results'):
                    print(f"      ✅ {len(result['results'])} 個結果")
                    results.append({'tool': tool, 'success': True, 'data': result['results']})
                else:
                    print(f"      ❌ 無結果")
                    results.append({'tool': tool, 'success': False})
                    
            elif tool == 'web_fetch':
                result = gf.web_fetch(args.get('url', ''))
                if result.get('success'):
                    print(f"      ✅ 成功")
                    results.append({'tool': tool, 'success': True, 'data': result.get('content', '')[:1000]})
                else:
                    print(f"      ❌ 失敗")
                    results.append({'tool': tool, 'success': False})
                    
            elif tool == 'calculate':
                result = gf.calculate(args.get('expression', ''))
                if result.get('success'):
                    print(f"      ✅ {result['result']}")
                    results.append({'tool': tool, 'success': True, 'data': result['result']})
                else:
                    print(f"      ❌ 失敗")
                    results.append({'tool': tool, 'success': False})
                    
            elif tool == 'read_json':
                filepath = args.get('file_path') or args.get('filepath', '')
                if not filepath:
                    print(f"      ❌ 無檔案路徑")
                    results.append({'tool': tool, 'success': False})
                    continue
                
                result = gf.read_json(filepath)
                if result.get('success'):
                    print(f"      ✅ 成功")
                    results.append({'tool': tool, 'success': True, 'data': str(result['data'])[:500]})
                else:
                    print(f"      ❌ 失敗")
                    results.append({'tool': tool, 'success': False})
                    
            else:
                print(f"      ⚠️  暫不支援")
                results.append({'tool': tool, 'success': False})
                
        except Exception as e:
            print(f"      ❌ 錯誤: {str(e)[:50]}")
            results.append({'tool': tool, 'success': False})
    
    return results

def extract_answer_with_gpt(question, tool_results, client):
    """使用 GPT-4o-mini 從工具結果提取答案"""
    
    # 整理工具結果為可讀的文字
    context = []
    
    for r in tool_results:
        if not r['success']:
            continue
            
        if r['tool'] == 'calculate':
            context.append(f"計算結果: {r['data']}")
            
        elif r['tool'] == 'web_search':
            context.append("搜尋結果:")
            for i, result in enumerate(r['data'][:3], 1):  # 只取前3個結果
                context.append(f"  {i}. {result.get('title', '')}")
                context.append(f"     {result.get('snippet', '')}")
                
        elif r['tool'] == 'web_fetch':
            context.append(f"網頁內容: {r['data'][:300]}...")
            
        elif r['tool'] == 'read_json':
            context.append(f"JSON 數據: {r['data'][:300]}...")
    
    context_text = "\n".join(context)
    
    prompt = f"""Based on the following question and tool execution results, extract the final answer.

Question: {question}

Tool Results:
{context_text}

Instructions:
- Provide ONLY the final answer (a number, name, or short phrase)
- Do NOT include any explanation or reasoning
- If the answer is a percentage, round to the nearest integer and include the number only (e.g., "86")
- If the answer is a person's name, provide the full name (e.g., "Claude Shannon")
- If you cannot determine the answer, respond with "Unknown"

Answer:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts precise answers from search results."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"      ⚠️  GPT 錯誤: {str(e)[:50]}")
        return "Unknown"

def evaluate_task(task, plan, client):
    """評估單一任務"""
    task_id = task['task_id']
    question = task['Question']
    ground_truth = str(task['Final answer']).strip()
    
    print(f"\n{'='*80}")
    print(f"任務: {task_id}")
    print(f"問題: {question[:60]}...")
    print(f"標準答案: {ground_truth}")
    print('='*80)
    
    # 執行工具
    print("\n🔧 執行工具:")
    tool_results = execute_plan_steps(plan)
    
    # 使用 GPT 提取答案
    print("\n🤖 使用 GPT-4o-mini 提取答案...")
    system_answer = extract_answer_with_gpt(question, tool_results, client)
    print(f"💡 系統答案: {system_answer}")
    
    # 評分
    success_count = sum(1 for r in tool_results if r['success'])
    step_score = success_count / max(len(tool_results), 1) * 0.5
    
    # 答案比對
    system_clean = system_answer.lower().strip()
    truth_clean = ground_truth.lower().strip()
    
    if system_clean == truth_clean:
        answer_score = 0.5
        match_type = "✅ 完全匹配"
    elif system_clean in truth_clean or truth_clean in system_clean:
        answer_score = 0.25
        match_type = "⚠️  部分匹配"
    else:
        answer_score = 0.0
        match_type = "❌ 不匹配"
    
    total_score = step_score + answer_score
    
    print(f"\n📊 評分:")
    print(f"  步驟: {success_count}/{len(tool_results)} ({step_score:.2f}/0.5)")
    print(f"  答案: {match_type} ({answer_score:.2f}/0.5)")
    print(f"  總分: {total_score:.2f}/1.0")
    
    return {
        'task_id': task_id,
        'system_answer': system_answer,
        'ground_truth': ground_truth,
        'step_score': step_score,
        'answer_score': answer_score,
        'total_score': total_score
    }

def main():
    # 檢查 API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ 請設定 OPENAI_API_KEY")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    print("="*80)
    print("GAIA 評分系統 - OpenAI 版（使用 GPT-4o-mini）")
    print("="*80)
    
    # 載入資料
    tasks, plans = load_data()
    
    # 只評估前 3 個任務
    test_tasks = tasks[:3]
    
    print(f"\n⚠️  預估 API 使用:")
    print(f"   - 呼叫次數: {len(test_tasks)} 次")
    print(f"   - 預估成本: ~$0.003 USD (每次 ~$0.001)")
    print(f"   - 模型: gpt-4o-mini")
    
    input("\n按 Enter 繼續...")
    
    # 評估每個任務
    results = []
    for task in test_tasks:
        task_id = task['task_id']
        plan = next((p for p in plans if p['task_id'] == task_id), None)
        
        if plan:
            result = evaluate_task(task, plan, client)
            results.append(result)
    
    # 總結
    print(f"\n{'='*80}")
    print("總結")
    print(f"{'='*80}\n")
    
    total = sum(r['total_score'] for r in results)
    print(f"總分: {total:.1f}/3.0")
    print(f"平均: {total/3:.2f}/1.0")
    print(f"\n💰 實際 API 費用: ~$0.003 USD")
    
    for r in results:
        status = "✅" if r['total_score'] >= 0.5 else "❌"
        print(f"\n{status} {r['task_id']}: {r['total_score']:.1f}/1.0")
        print(f"   系統: {r['system_answer']}")
        print(f"   標準: {r['ground_truth']}")

if __name__ == '__main__':
    main()
