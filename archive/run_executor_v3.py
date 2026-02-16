#!/usr/bin/env python3
"""
執行器 v3.0
只執行已驗證為可執行的步驟
"""

import json
import sys
import os

# 匯入 gaia_function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaia_function as gf


def execute_step(step: dict) -> dict:
    """執行單個步驟"""
    tool_name = step['tool_name']
    arguments = step['arguments']
    
    try:
        # 取得工具函數
        tool_func = getattr(gf, tool_name, None)
        
        if tool_func is None:
            return {
                'success': False,
                'error': f'工具不存在: {tool_name}'
            }
        
        # 執行工具
        result = tool_func(**arguments)
        
        return {
            'success': result.get('success', True),
            'result': result,
            'error': result.get('error') if not result.get('success', True) else None
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def execute_plan(plan: dict) -> dict:
    """執行單個 plan"""
    task_id = plan['task_id']
    steps = plan.get('tool_sequence', [])
    
    print(f"{'='*80}")
    print(f"執行任務: {task_id}")
    print(f"問題: {plan['question'][:100]}...")
    print(f"可執行步驟數: {len(steps)}")
    print(f"{'='*80}\n")
    
    results = []
    success_count = 0
    
    for idx, step in enumerate(steps):
        tool_name = step['tool_name']
        arguments = step['arguments']
        description = step.get('description', '')[:100]
        
        print(f"  [{idx+1}/{len(steps)}] {tool_name}")
        print(f"      描述: {description}...")
        
        # 執行步驟
        result = execute_step(step)
        
        if result['success']:
            print(f"      ✅ 成功")
            success_count += 1
            
            # 如果有具體結果，顯示預覽
            if 'result' in result and result['result']:
                data = result['result']
                if isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], (list, dict)):
                        preview = str(data['data'])[:100]
                        print(f"      結果: {preview}...")
                    elif 'result' in data:
                        print(f"      結果: {data['result']}")
        else:
            print(f"      ❌ 失敗: {result['error']}")
        
        print()
        
        results.append({
            'step_id': step['step_id'],
            'tool_name': tool_name,
            'success': result['success'],
            'error': result.get('error')
        })
    
    return {
        'task_id': task_id,
        'total_steps': len(steps),
        'success_count': success_count,
        'success_rate': success_count / len(steps) if steps else 0,
        'results': results
    }


def main():
    """主程式"""
    
    print()
    print("=" * 80)
    print("GAIA Executor v3.0 - 只執行可執行步驟")
    print("=" * 80)
    print()
    
    # 檢查 SERPER_API_KEY
    if not os.getenv('SERPER_API_KEY'):
        print("⚠️  警告: SERPER_API_KEY 未設定")
        print("   部分 web_search 功能可能無法使用")
    else:
        print("✅ SERPER_API_KEY 已設定")
    print()
    
    # 載入 plans
    plans_file = 'parser_output/plans_v3_executable.json'
    
    try:
        with open(plans_file, 'r', encoding='utf-8') as f:
            plans = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到檔案: {plans_file}")
        print("   請先執行 parser_v3_executable.py")
        return
    
    print(f"✅ 載入 {len(plans)} 個計劃")
    
    # 統計
    total_executable = sum(len(p['tool_sequence']) for p in plans)
    total_skipped = sum(p['stats']['skipped_steps'] for p in plans)
    
    print(f"📊 統計:")
    print(f"   可執行步驟: {total_executable} 個")
    print(f"   跳過步驟: {total_skipped} 個")
    print()
    
    # 選擇執行模式
    print("選擇執行模式:")
    print(f"1. 執行所有任務 ({len(plans)} 個)")
    print("2. 執行前 3 個任務")
    print("3. 執行單一任務 (輸入編號 0-{})".format(len(plans)-1))
    print()
    
    choice = input("請選擇 (1/2/3): ").strip()
    
    if choice == '1':
        selected_plans = plans
    elif choice == '2':
        selected_plans = plans[:3]
    elif choice == '3':
        idx = int(input(f"請輸入任務編號 (0-{len(plans)-1}): "))
        selected_plans = [plans[idx]]
    else:
        print("無效的選擇")
        return
    
    print()
    print("=" * 80)
    print(f"開始執行 {len(selected_plans)} 個任務")
    print("=" * 80)
    print()
    
    # 執行所有任務
    all_results = []
    
    for plan in selected_plans:
        result = execute_plan(plan)
        all_results.append(result)
    
    # 統計結果
    print()
    print("=" * 80)
    print("執行統計")
    print("=" * 80)
    print()
    
    total_steps = sum(r['total_steps'] for r in all_results)
    success_steps = sum(r['success_count'] for r in all_results)
    
    print(f"任務統計:")
    print(f"  執行任務數: {len(all_results)}")
    print(f"  總工具呼叫: {total_steps}")
    print(f"  成功呼叫數: {success_steps}")
    if total_steps > 0:
        print(f"  成功率: {success_steps/total_steps*100:.1f}%")
    
    print()
    
    # 每個任務的詳細結果
    print("各任務詳細結果:")
    for result in all_results:
        print(f"  {result['task_id']}: {result['success_count']}/{result['total_steps']} ({result['success_rate']*100:.1f}%)")
    
    print()
    print("=" * 80)
    print()


if __name__ == '__main__':
    main()
