#!/usr/bin/env python3
"""
整合 109 題資料
- 99 題：助教的 gaia.infer.jsonl
- 10 題：現有的 GAIA Level 3

輸出統一格式的 JSON 檔案
"""

import json
from pathlib import Path

# 工具對應表（助教的工具 → 我們的工具）
TOOL_MAPPING = {
    'web_search': 'web_search',
    'excel_reader': 'read_excel',
    'file_reader': 'read_text_file',
    'python_executor': 'calculate',  # 簡化
    'pdf_reader': 'read_pdf',
    'zip_extractor': 'extract_zip',
    'download_file': 'web_fetch',
    'web_browser': 'web_fetch',
    'calculator': 'calculate',
    'image_recognition': 'image_to_text',
    'pptx_reader': 'read_docx',  # 暫時用 read_docx 代替
    'audio_transcription': 'read_text_file',  # 暫時用 read_text_file
    'submit_final_answer': None,  # 特殊步驟，不算工具
    'reasoning': None,  # 推理步驟，tool_name = None
    'code_interpreter': 'calculate',  # 暫時用 calculate
    'video_analysis': 'analyze_image'  # 暫時用 analyze_image
}

# 參數對應表（助教的參數 → 我們的參數）
PARAM_MAPPING = {
    'web_search': {
        'query': 'query',
        'engine': None,  # 我們沒有
        'max_results': 'num_results'
    },
    'pdf_reader': {
        'file_path': 'file_path',
        'page': 'page_numbers'
    },
    'excel_reader': {
        'file_path': 'file_path',
        'sheet': 'sheet_name',
        'query': None  # 我們沒有
    },
    'calculator': {
        'expression': 'expression'
    },
    'python_executor': {
        'code': 'expression'  # 簡化為 expression
    },
    'zip_extractor': {
        'file_path': 'zip_path',
        'extract_to': 'extract_to'
    },
    'download_file': {
        'url': 'url',
        'save_path': None  # 我們沒有
    },
    'web_browser': {
        'url': 'url',
        'action': None  # 我們沒有
    },
    'file_reader': {
        'file_path': 'file_path'
    },
    'image_recognition': {
        'image_path': 'file_path',
        'task': None  # 我們沒有
    }
}


def convert_ta_tool_to_our_format(ta_tool_id, ta_arguments):
    """將助教的工具調用轉換成我們的格式"""

    # 獲取對應的工具名稱
    our_tool = TOOL_MAPPING.get(ta_tool_id)

    # 如果是特殊步驟（reasoning, submit_final_answer），返回 None
    if our_tool is None and ta_tool_id in ['reasoning', 'submit_final_answer']:
        return None, {}

    # 轉換參數
    our_arguments = {}
    param_map = PARAM_MAPPING.get(ta_tool_id, {})

    for arg in ta_arguments:
        arg_name = arg['name']
        arg_value = arg['value']

        # 獲取對應的參數名稱
        our_param_name = param_map.get(arg_name, arg_name)  # 預設使用原名稱

        # 如果對應為 None，跳過
        if our_param_name is None:
            continue

        our_arguments[our_param_name] = arg_value

    return our_tool, our_arguments


def convert_ta_task_to_our_format(ta_task):
    """將助教的單一題目轉換成我們的格式"""

    meta = ta_task['meta']
    query = ta_task['query']
    gold = ta_task['gold']

    # 建立基本結構
    our_task = {
        'task_id': f"gaia_ta_{meta['subset']}_" + meta['id'][:8],  # 縮短 ID
        'question': query['user_query'],
        'level': meta['difficulty'],
        'file_name': query['attachments'][0] if query['attachments'] else None,
        'annotated_steps': []
    }

    # 轉換 DAG 節點和工具調用
    dag = gold['plan_dag']
    tool_calls = {tc['node_id']: tc for tc in gold['tool_calls']}

    for node in dag['nodes']:
        step = {
            'step_id': node['node_id'],
            'description': node['label'],
            'step_type': node['step_type']  # tool 或 thought
        }

        # 如果是工具步驟
        if node['step_type'] == 'tool':
            ta_tool_id = node['tool_id']

            # 獲取工具調用的參數
            if node['node_id'] in tool_calls:
                ta_arguments = tool_calls[node['node_id']]['arguments']
            else:
                ta_arguments = []

            # 轉換工具和參數
            our_tool, our_arguments = convert_ta_tool_to_our_format(ta_tool_id, ta_arguments)

            step['tool_name'] = our_tool
            step['arguments'] = our_arguments
        else:
            # 推理步驟
            step['tool_name'] = None
            step['arguments'] = {}

        our_task['annotated_steps'].append(step)

    return our_task


def main():
    print("=== 整合 109 題資料 ===\n")

    # 讀取助教的 99 題
    ta_path = Path("../LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl")
    ta_tasks = []

    print(f"讀取助教的資料：{ta_path}")
    with open(ta_path, 'r') as f:
        for line in f:
            ta_tasks.append(json.loads(line))

    print(f"  ✓ 讀取 {len(ta_tasks)} 題")

    # 轉換助教的題目
    print("\n轉換助教的題目格式...")
    converted_ta_tasks = []
    for i, ta_task in enumerate(ta_tasks):
        try:
            our_task = convert_ta_task_to_our_format(ta_task)
            converted_ta_tasks.append(our_task)
        except Exception as e:
            print(f"  ✗ 轉換第 {i+1} 題失敗：{e}")

    print(f"  ✓ 成功轉換 {len(converted_ta_tasks)} 題")

    # 讀取現有的 10 題 GAIA Level 3
    gaia_l3_path = Path("gaia_level3_tasks.json")
    print(f"\n讀取現有的 GAIA Level 3：{gaia_l3_path}")
    with open(gaia_l3_path, 'r') as f:
        gaia_l3_tasks_raw = json.load(f)

    print(f"  ✓ 讀取 {len(gaia_l3_tasks_raw)} 題")

    # 轉換 GAIA L3 的格式（統一成 annotated_steps）
    print("\n轉換 GAIA L3 格式...")
    gaia_l3_tasks = []
    for task in gaia_l3_tasks_raw:
        # 如果已經有 annotated_steps，直接使用
        if 'annotated_steps' in task:
            gaia_l3_tasks.append(task)
            continue

        # 否則從 Annotator Metadata 轉換
        unified_task = {
            'task_id': task['task_id'],
            'question': task['Question'],
            'level': int(task['Level'].replace('Level ', '')),
            'file_name': task.get('file_name'),
            'annotated_steps': []
        }

        # 從 Annotator Metadata 提取步驟
        if 'Annotator Metadata' in task:
            metadata = task['Annotator Metadata']
            steps = metadata.get('Steps', [])

            for i, step_desc in enumerate(steps):
                step = {
                    'step_id': f"step_{i+1}",
                    'description': step_desc,
                    'step_type': 'tool',  # 簡化，預設為 tool
                    'tool_name': None,  # 需要 Parser 解析
                    'arguments': {}
                }
                unified_task['annotated_steps'].append(step)

        gaia_l3_tasks.append(unified_task)

    print(f"  ✓ 成功轉換 {len(gaia_l3_tasks)} 題")

    # 合併
    all_109_tasks = converted_ta_tasks + gaia_l3_tasks

    print(f"\n=== 整合結果 ===")
    print(f"助教的題目：{len(converted_ta_tasks)} 題")
    print(f"GAIA L3 題目：{len(gaia_l3_tasks)} 題")
    print(f"總共：{len(all_109_tasks)} 題")

    # 統計難度分布
    level_count = {}
    for task in all_109_tasks:
        level = task.get('level', 3)  # 預設 Level 3
        # 統一轉成 int
        if isinstance(level, str):
            level = int(level.replace('level_', '').replace('Level ', ''))
        level_count[level] = level_count.get(level, 0) + 1

    print(f"\n難度分布：")
    for level in sorted(level_count.keys()):
        print(f"  Level {level}: {level_count[level]} 題")

    # 儲存
    output_path = Path("gaia_109_tasks.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_109_tasks, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 已儲存至：{output_path}")
    print(f"  檔案大小：{output_path.stat().st_size / 1024:.1f} KB")

    # 輸出範例
    print(f"\n=== 第一題範例（助教）===")
    sample = all_109_tasks[0]
    print(f"task_id: {sample['task_id']}")
    print(f"question: {sample['question'][:60]}...")
    print(f"level: {sample['level']}")
    print(f"步驟數: {len(sample['annotated_steps'])}")

    # 顯示前 3 個步驟
    print(f"\n前 3 個步驟：")
    for i, step in enumerate(sample['annotated_steps'][:3], 1):
        print(f"  {i}. {step['description'][:50]}...")
        print(f"     tool: {step['tool_name']}")
        print(f"     args: {step['arguments']}")

    print("\n=== 整合完成！===")


if __name__ == "__main__":
    main()
