#!/usr/bin/env python3
"""
整合 109 題資料 v2（優化版）
使用統一的工具 schema，精準填入所有參數

改進：
1. 使用 unified_tools_schema.json
2. 精準的參數對應
3. 保留助教的原始工具名稱
4. 完整的參數驗證
"""

import json
import sys
from pathlib import Path

# 讀取統一的工具 schema
TOOLS_DIR = Path(__file__).parent.parent / "tools"
with open(TOOLS_DIR / "unified_tools_schema.json", 'r') as f:
    UNIFIED_TOOLS = json.load(f)

# 建立工具名稱索引
TOOL_INDEX = {tool['function']['name']: tool for tool in UNIFIED_TOOLS}

# 讀取參數對應表
with open(TOOLS_DIR / "parameter_mapping.json", 'r') as f:
    PARAM_MAPPING = json.load(f)


def convert_ta_arguments(tool_id, ta_arguments):
    """
    轉換助教的參數到統一格式

    Args:
        tool_id: 工具 ID
        ta_arguments: 助教的參數列表 [{"name": "query", "value": "..."}]

    Returns:
        轉換後的參數字典
    """
    converted = {}

    # 獲取參數對應規則
    param_map = PARAM_MAPPING.get(tool_id, {})

    for arg in ta_arguments:
        arg_name = arg['name']
        arg_value = arg['value']

        # 檢查是否需要轉換參數名稱
        if arg_name in param_map:
            # 如果對應的值不是 None，使用對應後的名稱
            mapped_name = param_map[arg_name]
            if mapped_name:
                converted[mapped_name] = arg_value
        else:
            # 沒有對應規則，直接使用原名稱
            converted[arg_name] = arg_value

    return converted


def validate_tool_arguments(tool_id, arguments):
    """
    驗證工具參數是否完整

    Returns:
        (is_valid, missing_params, extra_params)
    """
    if tool_id not in TOOL_INDEX:
        return (False, [], [], f"工具 {tool_id} 不在統一 schema 中")

    tool_schema = TOOL_INDEX[tool_id]
    required_params = tool_schema['function']['parameters'].get('required', [])
    all_params = tool_schema['function']['parameters']['properties'].keys()

    # 檢查缺少的必要參數
    missing = [p for p in required_params if p not in arguments]

    # 檢查多餘的參數
    extra = [p for p in arguments.keys() if p not in all_params]

    is_valid = (len(missing) == 0 and len(extra) == 0)

    return (is_valid, missing, extra, None)


def convert_ta_task_to_our_format(ta_task):
    """將助教的單一題目轉換成我們的格式（優化版）"""

    meta = ta_task['meta']
    query = ta_task['query']
    gold = ta_task['gold']

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

            # 特殊工具處理
            if tool_id in ['reasoning', 'submit_final_answer']:
                step['tool_name'] = None  # 推理步驟
                step['arguments'] = {}
            else:
                # 獲取工具調用的參數
                if node['node_id'] in tool_calls:
                    ta_arguments = tool_calls[node['node_id']]['arguments']
                else:
                    ta_arguments = []

                # 轉換參數
                converted_args = convert_ta_arguments(tool_id, ta_arguments)

                # 驗證參數
                is_valid, missing, extra, error = validate_tool_arguments(tool_id, converted_args)

                step['tool_name'] = tool_id
                step['arguments'] = converted_args
                step['validation'] = {
                    'is_valid': is_valid,
                    'missing_params': missing,
                    'extra_params': extra,
                    'error': error
                }
        else:
            # 推理步驟
            step['tool_name'] = None
            step['arguments'] = {}

        our_task['annotated_steps'].append(step)

    return our_task


def main():
    print("=== 整合 109 題資料 v2（優化版）===\n")

    # 1. 讀取助教的 99 題
    ta_path = Path("../../LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl")

    if not ta_path.exists():
        print(f"✗ 找不到助教的資料：{ta_path}")
        print("請確認路徑是否正確")
        sys.exit(1)

    print(f"[1/5] 讀取助教的資料：{ta_path}")
    ta_tasks = []
    with open(ta_path, 'r') as f:
        for line in f:
            ta_tasks.append(json.loads(line))

    print(f"  ✓ 讀取 {len(ta_tasks)} 題\n")

    # 2. 轉換助教的題目
    print("[2/5] 轉換助教的題目格式（使用統一 schema）...")
    converted_ta_tasks = []
    validation_stats = {'valid': 0, 'invalid': 0, 'total_steps': 0}

    for i, ta_task in enumerate(ta_tasks):
        try:
            our_task = convert_ta_task_to_our_format(ta_task)
            converted_ta_tasks.append(our_task)

            # 統計驗證結果
            for step in our_task['annotated_steps']:
                if 'validation' in step:
                    validation_stats['total_steps'] += 1
                    if step['validation']['is_valid']:
                        validation_stats['valid'] += 1
                    else:
                        validation_stats['invalid'] += 1

        except Exception as e:
            print(f"  ✗ 轉換第 {i+1} 題失敗：{e}")

    print(f"  ✓ 成功轉換 {len(converted_ta_tasks)} 題")
    print(f"  參數驗證：{validation_stats['valid']}/{validation_stats['total_steps']} 步驟有效 ({validation_stats['valid']/validation_stats['total_steps']*100:.1f}%)\n")

    # 3. 讀取現有的 10 題 GAIA Level 3
    gaia_l3_path = Path("../v5_original/gaia_level3_tasks.json")
    print(f"[3/5] 讀取現有的 GAIA Level 3：{gaia_l3_path}")

    with open(gaia_l3_path, 'r') as f:
        gaia_l3_tasks_raw = json.load(f)

    print(f"  ✓ 讀取 {len(gaia_l3_tasks_raw)} 題\n")

    # 4. 轉換 GAIA L3 的格式
    print("[4/5] 轉換 GAIA L3 格式...")
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
            'level': 3,
            'file_name': task.get('file_name'),
            'annotated_steps': [],
            'metadata': {
                'source': 'v5_original',
                'original_index': task.get('original_index')
            }
        }

        # 從 Annotator Metadata 提取步驟
        if 'Annotator Metadata' in task:
            metadata = task['Annotator Metadata']
            steps = metadata.get('Steps', [])

            for i, step_desc in enumerate(steps):
                step = {
                    'step_id': f"step_{i+1}",
                    'description': step_desc,
                    'step_type': 'tool',
                    'tool_name': None,  # 需要 Parser 解析
                    'arguments': {}
                }
                unified_task['annotated_steps'].append(step)

        gaia_l3_tasks.append(unified_task)

    print(f"  ✓ 成功轉換 {len(gaia_l3_tasks)} 題\n")

    # 5. 合併
    all_109_tasks = converted_ta_tasks + gaia_l3_tasks

    print("[5/5] 合併和統計...")
    print(f"\n=== 整合結果 ===")
    print(f"助教的題目：{len(converted_ta_tasks)} 題")
    print(f"GAIA L3 題目：{len(gaia_l3_tasks)} 題")
    print(f"總共：{len(all_109_tasks)} 題\n")

    # 統計難度分布
    level_count = {}
    for task in all_109_tasks:
        level = task.get('level', 3)
        if isinstance(level, str):
            level = int(level.replace('level_', '').replace('Level ', ''))
        level_count[level] = level_count.get(level, 0) + 1

    print("難度分布：")
    for level in sorted(level_count.keys()):
        print(f"  Level {level}: {level_count[level]} 題")

    # 儲存
    output_path = Path("gaia_109_tasks_v2.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_109_tasks, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 已儲存至：{output_path}")
    print(f"  檔案大小：{output_path.stat().st_size / 1024:.1f} KB\n")

    # 輸出驗證統計
    print("=== 參數驗證統計 ===")
    print(f"總工具步驟：{validation_stats['total_steps']}")
    print(f"有效步驟：{validation_stats['valid']} ({validation_stats['valid']/validation_stats['total_steps']*100:.1f}%)")
    print(f"無效步驟：{validation_stats['invalid']} ({validation_stats['invalid']/validation_stats['total_steps']*100:.1f}%)")

    # 輸出範例
    print(f"\n=== 第一題範例（助教）===")
    sample = all_109_tasks[0]
    print(f"task_id: {sample['task_id']}")
    print(f"question: {sample['question'][:60]}...")
    print(f"level: {sample['level']}")
    print(f"步驟數: {len(sample['annotated_steps'])}")

    # 顯示前 3 個步驟（包含驗證結果）
    print(f"\n前 3 個步驟：")
    for i, step in enumerate(sample['annotated_steps'][:3], 1):
        print(f"  {i}. {step['description'][:50]}...")
        print(f"     tool: {step['tool_name']}")
        print(f"     args: {step['arguments']}")
        if 'validation' in step:
            val = step['validation']
            if val['is_valid']:
                print(f"     驗證: ✓ 有效")
            else:
                print(f"     驗證: ✗ 缺少 {val['missing_params']}, 多餘 {val['extra_params']}")

    print("\n=== 整合完成！===")
    print("\n下一步：")
    print("1. 執行 run_109_pipeline_v2.py 進行驗證和分析")
    print("2. 檢查無效步驟的原因")
    print("3. 優化參數對應規則")


if __name__ == "__main__":
    main()
