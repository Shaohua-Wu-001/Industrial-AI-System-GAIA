#!/usr/bin/env python3
"""
整合 109 題資料 - 修復版
修復：正確處理 GAIA L3 的 Steps（字符串 → 列表）
"""

import json
import re
from pathlib import Path


def parse_steps_string(steps_string):
    """
    將步驟字符串解析成列表

    輸入：
    "1. Opened the JSONLD file.
     2. Opened each ORCID ID.
     3. Counted the works from pre-2022.
     4. Took the average: (54 + 61 + 1 + 16 + 0) / 5 = 132 / 5 = 26.4."

    輸出：
    ["Opened the JSONLD file.",
     "Opened each ORCID ID.",
     "Counted the works from pre-2022.",
     "Took the average: (54 + 61 + 1 + 16 + 0) / 5 = 132 / 5 = 26.4."]
    """
    # 按行分割
    lines = steps_string.strip().split('\n')

    steps = []
    current_step = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 檢查是否是新步驟（以數字+點開始）
        match = re.match(r'^\d+\.\s+(.*)', line)
        if match:
            # 如果有當前步驟，先儲存
            if current_step:
                steps.append(current_step)
            # 開始新步驟
            current_step = match.group(1)
        else:
            # 繼續當前步驟
            if current_step:
                current_step += " " + line
            else:
                current_step = line

    # 儲存最後一個步驟
    if current_step:
        steps.append(current_step)

    return steps


def convert_gaia_l3_task(task):
    """將 GAIA L3 任務轉換成統一格式（修復版）"""

    unified_task = {
        'task_id': task['task_id'],
        'question': task['Question'],
        'level': task['Level'].replace('Level ', ''),
        'file_name': task.get('file_name'),
        'final_answer': task.get('Final answer'),
        'annotated_steps': [],
        'metadata': {
            'source': 'v5_original',
            'original_number_of_steps': int(task['Annotator Metadata']['Number of steps']),
            'how_long': task['Annotator Metadata'].get('How long did this take?', 'unknown'),
            'tools_used': task['Annotator Metadata'].get('Tools', 'unknown')
        }
    }

    # 從 Annotator Metadata 提取步驟（修復版）
    if 'Annotator Metadata' in task:
        metadata = task['Annotator Metadata']
        steps_string = metadata.get('Steps', '')

        # 正確解析步驟字符串
        if isinstance(steps_string, str):
            steps_list = parse_steps_string(steps_string)
        elif isinstance(steps_string, list):
            steps_list = steps_string
        else:
            steps_list = []

        # 為每個步驟創建結構
        for i, step_desc in enumerate(steps_list, 1):
            step = {
                'step_id': f"step_{i}",
                'description': step_desc,
                'step_type': 'tool',  # GAIA L3 大多是工具步驟
                'tool_name': None,  # 需要進一步解析
                'arguments': {}
            }
            unified_task['annotated_steps'].append(step)

    return unified_task


def convert_ta_task(ta_task, unified_tools):
    """將助教任務轉換成統一格式"""

    meta = ta_task['meta']
    query = ta_task['query']
    gold = ta_task['gold']

    # 建立工具 schema 索引
    tool_index = {tool['function']['name']: tool for tool in unified_tools}

    # 建立基本結構
    our_task = {
        'task_id': f"gaia_ta_{meta['subset']}_" + meta['id'][:8],
        'question': query['user_query'],
        'level': meta['difficulty'],
        'file_name': query['attachments'][0] if query['attachments'] else None,
        'annotated_steps': [],
        'metadata': {
            'source': 'ta_99_tasks',
            'original_id': meta['id'],
            'plan_type': meta['plan_type'],
            'has_arguments': meta['has_arguments']
        }
    }

    # 轉換 DAG 節點和工具調用
    dag = gold['plan_dag']
    tool_calls = {tc['node_id']: tc for tc in gold['tool_calls']}

    for node in dag['nodes']:
        step = {
            'step_id': node['node_id'],
            'description': node['label'],
            'step_type': node['step_type'],
            'metadata': {
                'step_index': node['step_index']
            }
        }

        # 如果是工具步驟
        if node['step_type'] == 'tool':
            tool_id = node['tool_id']

            # 獲取工具調用的參數
            if node['node_id'] in tool_calls:
                ta_arguments = tool_calls[node['node_id']]['arguments']

                # 轉換參數
                converted_args = {}
                for arg in ta_arguments:
                    converted_args[arg['name']] = arg['value']

                step['tool_name'] = tool_id
                step['arguments'] = converted_args

                # 驗證參數（除了特殊工具）
                if tool_id not in ['reasoning', 'submit_final_answer'] and tool_id in tool_index:
                    required = tool_index[tool_id]['function']['parameters'].get('required', [])
                    missing = [p for p in required if p not in converted_args]
                    step['validation'] = {
                        'is_valid': len(missing) == 0,
                        'missing_params': missing
                    }
            else:
                # 沒有工具調用數據（如 reasoning）
                if tool_id == 'reasoning':
                    step['tool_name'] = None
                    step['arguments'] = {}
                else:
                    step['tool_name'] = tool_id
                    step['arguments'] = {}
        else:
            # 推理步驟
            step['tool_name'] = None
            step['arguments'] = {}

        our_task['annotated_steps'].append(step)

    return our_task


def main():
    print("=" * 80)
    print("整合 109 題資料 - 修復版")
    print("=" * 80)

    base_dir = Path(__file__).parent.parent  # Delta_GAIA/
    project_dir = base_dir.parent  # [8] 中研院資創RA (2026 Spring)/

    # 讀取統一 tools schema
    with open(base_dir / "tools/unified_tools_schema.json", 'r') as f:
        unified_tools = json.load(f)

    print(f"\n✓ 載入統一工具 schema：{len(unified_tools)} 個工具")

    # 讀取助教的 99 題
    ta_path = project_dir / "LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl"

    ta_tasks = []
    print(f"\n讀取助教的資料：{ta_path}")
    try:
        with open(ta_path, 'r') as f:
            for line in f:
                ta_tasks.append(json.loads(line))
        print(f"✓ 讀取 {len(ta_tasks)} 題")
    except FileNotFoundError:
        print(f"⚠️  找不到助教資料，跳過")
        ta_tasks = []

    # 轉換助教的題目
    converted_ta_tasks = []
    if ta_tasks:
        print(f"\n轉換助教的題目...")
        for i, ta_task in enumerate(ta_tasks, 1):
            if i % 20 == 0:
                print(f"  進度：{i}/{len(ta_tasks)}")
            try:
                our_task = convert_ta_task(ta_task, unified_tools)
                converted_ta_tasks.append(our_task)
            except Exception as e:
                print(f"  ✗ 轉換第 {i} 題失敗：{e}")

        print(f"✓ 成功轉換 {len(converted_ta_tasks)} 題")

    # 讀取 GAIA L3 的 10 題
    gaia_l3_path = base_dir / "v5_original/gaia_level3_tasks.json"
    print(f"\n讀取 GAIA Level 3：{gaia_l3_path}")

    with open(gaia_l3_path, 'r') as f:
        gaia_l3_tasks_raw = json.load(f)

    print(f"✓ 讀取 {len(gaia_l3_tasks_raw)} 題")

    # 轉換 GAIA L3 的格式（修復版）
    print(f"\n轉換 GAIA L3 格式（修復版）...")
    gaia_l3_tasks = []

    for task in gaia_l3_tasks_raw:
        converted_task = convert_gaia_l3_task(task)
        gaia_l3_tasks.append(converted_task)

        # 顯示轉換結果
        task_id = converted_task['task_id']
        orig_steps = converted_task['metadata']['original_number_of_steps']
        new_steps = len(converted_task['annotated_steps'])
        print(f"  {task_id}: {orig_steps} 步 → {new_steps} 步 ✓")

    print(f"✓ 成功轉換 {len(gaia_l3_tasks)} 題")

    # 合併
    all_109_tasks = converted_ta_tasks + gaia_l3_tasks

    print(f"\n" + "=" * 80)
    print(f"整合結果")
    print(f"=" * 80)
    print(f"助教的題目：{len(converted_ta_tasks)} 題")
    print(f"GAIA L3 題目：{len(gaia_l3_tasks)} 題")
    print(f"總共：{len(all_109_tasks)} 題")

    # 統計難度分布
    level_count = {}
    for task in all_109_tasks:
        level = str(task.get('level', '3'))
        level_count[level] = level_count.get(level, 0) + 1

    print(f"\n難度分布：")
    for level in sorted(level_count.keys()):
        print(f"  Level {level}: {level_count[level]} 題")

    # 統計步驟數
    total_steps = sum(len(t['annotated_steps']) for t in all_109_tasks)
    avg_steps = total_steps / len(all_109_tasks)
    print(f"\n步驟統計：")
    print(f"  總步驟數：{total_steps}")
    print(f"  平均步驟數：{avg_steps:.1f}")

    # 儲存
    output_path = Path(__file__).parent / "gaia_109_tasks_FIXED.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_109_tasks, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 已儲存至：{output_path}")
    print(f"  檔案大小：{output_path.stat().st_size / 1024:.1f} KB")

    # 輸出 GAIA L3 範例
    if gaia_l3_tasks:
        print(f"\n" + "=" * 80)
        print(f"GAIA L3 範例")
        print(f"=" * 80)
        sample = gaia_l3_tasks[1]  # gaia_val_l3_001
        print(f"task_id: {sample['task_id']}")
        print(f"question: {sample['question'][:80]}...")
        print(f"final_answer: {sample['final_answer']}")
        print(f"步驟數: {len(sample['annotated_steps'])}")

        print(f"\n所有步驟：")
        for i, step in enumerate(sample['annotated_steps'], 1):
            print(f"  {i}. {step['description']}")

    print(f"\n" + "=" * 80)
    print(f"整合完成！")
    print(f"=" * 80)


if __name__ == "__main__":
    main()
