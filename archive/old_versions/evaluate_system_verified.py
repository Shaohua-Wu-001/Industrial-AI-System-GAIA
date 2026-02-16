#!/usr/bin/env python3
"""GAIA 評分系統 - 最終修正版 (不浪費 API)"""

import os
import sys
import json
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
    
    # 從 tool_sequence 讀取步驟
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
                    results.append({'tool': tool, 'success': True, 'data': result.get('content', '')[:500]})
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
                # 修正：使用正確的 key 名稱
                filepath = args.get('file_path') or args.get('filepath', '')
                
                if not filepath:
                    print(f"      ❌ 無檔案路徑")
                    results.append({'tool': tool, 'success': False})
                    continue
                
                # 嘗試直接讀取（路徑可能已經是相對路徑）
                result = gf.read_json(filepath)
                if result.get('success'):
                    print(f"      ✅ 成功 (路徑: {filepath})")
                    results.append({'tool': tool, 'success': True, 'data': result['data']})
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

def simple_answer_extraction(question, tool_results):
    """改進的答案提取邏輯（不使用 API）"""
    
    # 1. 如果有計算結果，直接返回
    for r in tool_results:
        if r['tool'] == 'calculate' and r['success']:
            value = r['data']
            # 如果是百分比問題，四捨五入
            if 'percentage' in question.lower() or 'percent' in question.lower():
                return str(round(value))
            return str(value)
    
    # 2. 如果有 JSON 數據，嘗試提取答案
    for r in tool_results:
        if r['tool'] == 'read_json' and r['success']:
            data = r['data']
            # 如果問題問 "average"，嘗試找數字並計算平均
            if 'average' in question.lower():
                # 這裡可以加更複雜的邏輯
                pass
    
    # 3. 如果有搜尋結果，嘗試從 snippet 提取
    search_results = []
    for r in tool_results:
        if r['tool'] == 'web_search' and r['success']:
            search_results.extend(r['data'])
    
    if search_results:
        # 尋找人名 (簡單邏輯：大寫開頭的連續兩個詞)
        if 'who' in question.lower() or 'scientist' in question.lower():
            import re
            for result in search_results:
                snippet = result.get('snippet', '') + ' ' + result.get('title', '')
                # 尋找類似 "Claude Shannon" 的模式
                names = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', snippet)
                if names:
                    # 返回第一個找到的名字
                    return names[0]
    
    # 4. 如果有 fetch 結果，嘗試提取
    for r in tool_results:
        if r['tool'] == 'web_fetch' and r['success']:
            content = r['data']
            # 可以加更複雜的文字分析
            pass
    
    return "Unknown"

def evaluate_task(task, plan):
    """評估單一任務（不使用 API）"""
    task_id = task['task_id']
    question = task['Question']
    ground_truth = str(task['Final answer']).strip()
    
    print(f"\n{'='*80}")
    print(f"任務: {task_id}")
    print(f"問題: {question[:60]}...")
    print(f"標準答案: {ground_truth}")
    print('='*80)
    
    # 執行工具
    tool_results = execute_plan_steps(plan)
    
    # 簡單答案提取
    system_answer = simple_answer_extraction(question, tool_results)
    print(f"\n💡 系統答案: {system_answer}")
    
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
    print("="*80)
    print("GAIA 評分系統 - 最終版 (100% 純 Python，0 API 呼叫)")
    print("="*80)
    
    # 載入資料
    tasks, plans = load_data()
    
    # 只評估前 3 個任務
    test_tasks = tasks[:3]
    
    results = []
    for task in test_tasks:
        task_id = task['task_id']
        plan = next((p for p in plans if p['task_id'] == task_id), None)
        
        if plan:
            result = evaluate_task(task, plan)
            results.append(result)
    
    # 總結
    print(f"\n{'='*80}")
    print("總結")
    print(f"{'='*80}\n")
    
    total = sum(r['total_score'] for r in results)
    print(f"總分: {total:.1f}/3.0")
    print(f"平均: {total/3:.2f}/1.0")
    print(f"\n💰 API 費用: $0.00 (100% 純 Python！)")
    
    for r in results:
        status = "✅" if r['total_score'] >= 0.5 else "❌"
        print(f"\n{status} {r['task_id']}: {r['total_score']:.1f}/1.0")
        print(f"   系統: {r['system_answer']}")
        print(f"   標準: {r['ground_truth']}")

if __name__ == '__main__':
    main()
