import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import gaia_function as gf
from anthropic import Anthropic

# 設定 API
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def load_tasks():
    """載入任務資料"""
    with open('gaia_output/gaia_level3_tasks.json', 'r') as f:
        return json.load(f)

def load_execution_results():
    """載入執行結果"""
    with open('parser_output/plans_v3_executable.json', 'r') as f:
        return json.load(f)

def generate_final_answer(question, tool_results):
    """用 Claude API 生成最終答案"""
    context = f"Question: {question}\n\nTool execution results:\n"
    for i, result in enumerate(tool_results, 1):
        context += f"{i}. {result['tool']}: {result['result']}\n"
    
    prompt = f"""{context}

Based on the above tool results, what is the final answer to the question?
Provide ONLY the answer, nothing else. If it's a number, provide just the number. If it's text, provide just the text."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text.strip()

def check_tools_used(ground_truth_tools, executed_tools):
    """檢查工具使用情況"""
    tool_mapping = {
        "Web browser": ["web_search", "web_fetch"],
        "Search engine": ["web_search"],
        "Calculator": ["calculate"],
        "PDF access": ["read_pdf"],
        "Excel": ["read_excel"],
        "JSONLD": ["read_json"],
        "XML": ["read_xml"]
    }
    
    # 解析標註工具
    gt_tools = [t.strip() for t in ground_truth_tools.split('\n') if t.strip()]
    required_categories = set()
    for tool in gt_tools:
        for category, funcs in tool_mapping.items():
            if category.lower() in tool.lower():
                required_categories.add(category)
    
    # 檢查使用的工具
    used_categories = set()
    for tool in executed_tools:
        for category, funcs in tool_mapping.items():
            if tool in funcs:
                used_categories.add(category)
    
    if not required_categories:
        return 0.5  # 如果沒有明確要求，給滿分
    
    coverage = len(used_categories & required_categories) / len(required_categories)
    return 0.5 if coverage >= 0.5 else 0.0

def compare_answer(system_answer, ground_truth):
    """比對答案"""
    sys_ans = str(system_answer).strip().lower()
    gt_ans = str(ground_truth).strip().lower()
    
    # 完全匹配
    if sys_ans == gt_ans:
        return 0.5
    
    # 數值比對
    try:
        sys_num = float(sys_ans)
        gt_num = float(gt_ans)
        if abs(sys_num - gt_num) <= 0.5:
            return 0.5
        return 0.0
    except:
        pass
    
    # 字串包含
    if sys_ans in gt_ans or gt_ans in sys_ans:
        return 0.5
    
    return 0.0

def evaluate_task(task, plan):
    """評估單一任務"""
    print(f"\n{'='*80}")
    print(f"評估任務: {task['task_id']}")
    print(f"問題: {task['Question'][:80]}...")
    print(f"標準答案: {task['Final answer']}")
    print(f"{'='*80}\n")
    
    # 執行工具並收集結果
    tool_results = []
    executed_tools = []
    
    for step in plan['tool_sequence']:
        if not step.get('executable', True):
            continue
        
        tool_name = step['tool_name']
        executed_tools.append(tool_name)
        
        try:
            func = getattr(gf, tool_name)
            result = func(**step['arguments'])
            
            if result.get('success'):
                tool_results.append({
                    'tool': tool_name,
                    'result': str(result.get('result', result.get('data', '')))[:200]
                })
                print(f"  ✅ {tool_name}: 成功")
            else:
                print(f"  ❌ {tool_name}: 失敗")
        except Exception as e:
            print(f"  ❌ {tool_name}: {str(e)[:100]}")
    
    # 生成最終答案
    print(f"\n🤖 生成最終答案...")
    system_answer = generate_final_answer(task['Question'], tool_results)
    print(f"系統答案: {system_answer}")
    
    # 評分
    tools_score = check_tools_used(
        task['Annotator Metadata']['Tools'],
        executed_tools
    )
    answer_score = compare_answer(system_answer, task['Final answer'])
    
    total_score = tools_score + answer_score
    
    print(f"\n📊 評分:")
    print(f"  步驟分: {tools_score}/0.5")
    print(f"  答案分: {answer_score}/0.5")
    print(f"  總分: {total_score}/1.0")
    
    return {
        'task_id': task['task_id'],
        'system_answer': system_answer,
        'ground_truth': task['Final answer'],
        'tools_score': tools_score,
        'answer_score': answer_score,
        'total_score': total_score
    }

def main():
    print("="*80)
    print("GAIA 評分系統 - 測試前3題")
    print("="*80)
    
    tasks = load_tasks()[:3]  # 只取前3題
    plans = load_execution_results()[:3]
    
    results = []
    for task, plan in zip(tasks, plans):
        result = evaluate_task(task, plan)
        results.append(result)
    
    # 總結
    print(f"\n{'='*80}")
    print("總結")
    print(f"{'='*80}\n")
    
    total = sum(r['total_score'] for r in results)
    print(f"總分: {total}/{len(results)}")
    print(f"平均: {total/len(results):.2f}")
    
    for r in results:
        print(f"\n{r['task_id']}: {r['total_score']:.1f}/1.0")
        print(f"  系統答案: {r['system_answer']}")
        print(f"  標準答案: {r['ground_truth']}")

if __name__ == '__main__':
    main()
