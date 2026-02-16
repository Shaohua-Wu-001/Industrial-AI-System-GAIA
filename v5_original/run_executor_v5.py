import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from gaia_function import *


class GAIAExecutorV5:    
    def __init__(self, plans_file: str = 'parser_output/plans_v5_ultimate.json'):
        self.plans_file = plans_file
        self.plans = self._load_plans()
        
        # 統計
        self.stats = {
            'total_tasks': 0,
            'total_steps': 0,
            'executed_steps': 0,
            'success_steps': 0,
            'failed_steps': 0,
            'skipped_steps': 0,
        }
    
    def _load_plans(self) -> List[Dict]:
        if not Path(self.plans_file).exists():
            print(f"找不到計劃檔案: {self.plans_file}")
            print(f"請先運行: python3 parser_v5_ultimate.py gaia_level3_tasks.json")
            sys.exit(1)
        
        with open(self.plans_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def execute_step(self, step: Dict) -> Dict:
        tool_name = step['tool_name']
        arguments = step['arguments']
        
        try:
            # 動態調用工具函數
            tool_func = globals().get(tool_name)
            
            if not tool_func:
                return {
                    'success': False,
                    'error': f'工具函數 {tool_name} 不存在',
                    'result': None
                }
            
            # 執行工具
            result = tool_func(**arguments)
            
            return {
                'success': True,
                'error': None,
                'result': result
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'result': None
            }
    
    def execute_task(self, task: Dict, task_mode: str = 'all') -> Dict:
        task_id = task['task_id']
        question = task['question']
        tool_sequence = task['tool_sequence']
        executable_steps = [s for s in tool_sequence if s.get('executable', False)]
        
        print(f"\n{'='*80}")
        print(f"執行任務: {task_id}")
        print(f"問題: {question[:100]}..." if len(question) > 100 else f"問題: {question}")
        print(f"可執行步驟數: {len(executable_steps)}")
        print(f"{'='*80}")
        
        if not executable_steps:
            print("無可執行步驟")
            return {
                'task_id': task_id,
                'executed': 0,
                'success': 0,
                'failed': 0,
                'results': []
            }
        
        results = []
        
        for i, step in enumerate(executable_steps, 1):
            step_id = step.get('step_id', f'step_{i}')
            tool_name = step.get('tool_name')
            description = step.get('description', '')[:100]
            
            print(f"\n  [{i}/{len(executable_steps)}] {tool_name}")
            print(f"      描述: {description}...")
            
            # 執行步驟
            self.stats['executed_steps'] += 1
            execution_result = self.execute_step(step)
            
            if execution_result['success']:
                print(f"      ✅ 成功")
                self.stats['success_steps'] += 1
                
                # 顯示結果（如果有且不是太長）
                result = execution_result['result']
                if result is not None:
                    result_str = str(result)
                    if len(result_str) < 200:
                        print(f"結果: {result_str}")
            else:
                print(f"失敗: {execution_result['error']}")
                self.stats['failed_steps'] += 1
            
            results.append({
                'step_id': step_id,
                'tool_name': tool_name,
                'success': execution_result['success'],
                'error': execution_result['error'],
                'result': execution_result['result']
            })
        
        return {
            'task_id': task_id,
            'executed': len(results),
            'success': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }
    
    def run(self, mode: str = 'all'):        
        # 統計可執行步驟
        total_executable = sum(
            len([s for s in p['tool_sequence'] if s.get('executable', False)])
            for p in self.plans
        )
        print(f"可執行步驟: {total_executable} 個")
        
        # 選擇執行模式
        if mode == 'all':
            tasks_to_run = self.plans
            print(f"\n開始執行 {len(tasks_to_run)} 個任務")
        elif mode == 'first3':
            tasks_to_run = self.plans[:3]
            print(f"\n開始執行前 {len(tasks_to_run)} 個任務")
        elif mode == 'single':
            print(f"\n請選擇任務 (0-{len(self.plans)-1}):")
            for i, p in enumerate(self.plans):
                q = p['question'][:50]
                print(f"  {i}. {p['task_id']}: {q}...")
            
            try:
                task_idx = int(input("\n輸入編號: "))
                tasks_to_run = [self.plans[task_idx]]
            except (ValueError, IndexError):
                print("無效的編號")
                return
        else:
            print(f"無效的模式: {mode}")
            return
        
        # 執行任務
        self.stats['total_tasks'] = len(tasks_to_run)
        task_results = []
        
        for task in tasks_to_run:
            result = self.execute_task(task)
            task_results.append(result)
            self.stats['total_steps'] += result['executed']
        
        # 顯示統計
        self._print_stats(task_results)
    
    def _print_stats(self, task_results: List[Dict]):        
        print(f"\n任務統計:")
        print(f"  執行任務數: {self.stats['total_tasks']}")
        print(f"  總工具呼叫: {self.stats['executed_steps']}")
        print(f"  成功呼叫數: {self.stats['success_steps']}")
        
        if self.stats['executed_steps'] > 0:
            success_rate = self.stats['success_steps'] / self.stats['executed_steps'] * 100
            print(f"  成功率: {success_rate:.1f}%")
        
        print(f"\n各任務詳細結果:")
        for result in task_results:
            task_id = result['task_id']
            executed = result['executed']
            success = result['success']
            
            if executed > 0:
                rate = success / executed * 100
                print(f"  {task_id}: {success}/{executed} ({rate:.1f}%)")
            else:
                print(f"  {task_id}: 0/0 (0.0%)")
        
        print(f"\n{'='*80}")


def main():
    print("\n選擇執行模式:")
    print("1. 執行所有任務")
    print("2. 執行前 3 個任務")
    print("3. 執行單一任務 (輸入編號)")
    
    try:
        choice = input("\n請選擇 (1/2/3): ").strip()
        
        mode_map = {
            '1': 'all',
            '2': 'first3',
            '3': 'single'
        }
        
        mode = mode_map.get(choice, 'all')
        
        executor = GAIAExecutorV5()
        executor.run(mode)
    
    except KeyboardInterrupt:
        print("\n執行已中斷")
        sys.exit(0)


if __name__ == '__main__':
    main()
