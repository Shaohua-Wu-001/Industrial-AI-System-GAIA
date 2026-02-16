#!/usr/bin/env python3
"""
自動執行版本 - 執行所有任務
"""
import json
import sys
import os

# 使用當前目錄
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)
import gaia_function as gf

def execute_step(step: dict) -> dict:
    """執行單個步驟"""
    tool_name = step['tool_name']
    arguments = step['arguments']
    
    try:
        tool_func = getattr(gf, tool_name, None)
        if tool_func is None:
            return {
                'success': False,
                'error': f'工具不存在: {tool_name}'
            }
        
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
    
    print(f"\n{'='*80}")
    print(f"執行任務: {task_id}")
    print(f"問題: {plan['question'][:100]}...")
    print(f"可執行步驟數: {len(steps)}")
    print(f"{'='*80}\n")
    
    results = []
    success_count = 0
    
    for idx, step in enumerate(steps):
        tool_name = step['tool_name']
        description = step.get('description', '')[:80]
        
        print(f"  [{idx+1}/{len(steps)}] {tool_name}: {description}...")
        
        result = execute_step(step)
        
        if result['success']:
            print(f"      ✅ 成功")
            success_count += 1
        else:
            print(f"      ❌ 失敗: {result['error']}")
        
        results.append({
            'step_id': step['step_id'],
            'tool_name': tool_name,
            'success': result['success'],
            'error': result.get('error'),
            'result': result.get('result')
        })
    
    return {
        'task_id': task_id,
        'total_steps': len(steps),
        'success_count': success_count,
        'success_rate': success_count / len(steps) if steps else 0,
        'results': results
    }

# 載入 plans
plans_file = os.path.join(PROJECT_DIR, 'parser_output/plans_v3_executable.json')
with open(plans_file, 'r', encoding='utf-8') as f:
    plans = json.load(f)

# 執行所有任務
all_results = []
for plan in plans:
    result = execute_plan(plan)
    all_results.append(result)

# 輸出統計
print("\n" + "="*80)
print("執行統計")
print("="*80)

total_steps = sum(r['total_steps'] for r in all_results)
success_steps = sum(r['success_count'] for r in all_results)

print(f"\n任務統計:")
print(f"  執行任務數: {len(all_results)}")
print(f"  總工具呼叫: {total_steps}")
print(f"  成功呼叫數: {success_steps}")
if total_steps > 0:
    print(f"  成功率: {success_steps/total_steps*100:.1f}%")

print(f"\n各任務詳細結果:")
for result in all_results:
    print(f"  {result['task_id']}: {result['success_count']}/{result['total_steps']} ({result['success_rate']*100:.1f}%)")

# 儲存結果
output_file = os.path.join(PROJECT_DIR, 'parser_output/execution_results.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ 執行結果已儲存至: {output_file}")
