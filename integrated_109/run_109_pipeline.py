#!/usr/bin/env python3
"""
針對 109 題執行 Pipeline（不做 Data Synthesis）

Pipeline 流程：
1. 讀取 gaia_109_tasks.json
2. 驗證每題的工具和參數（validation）
3. 生成分析報告（analysis_report_109.json）

不執行：
- Parser（已經有 annotated_steps）
- Data Synthesis（按用戶要求暫不處理）
"""

import json
from pathlib import Path
from collections import Counter


def validate_task(task, tools_schema):
    """驗證單一題目的工具和參數"""

    task_id = task['task_id']
    annotated_steps = task.get('annotated_steps', [])

    # 建立工具 schema 的快速查找表
    schema_map = {}
    for tool_def in tools_schema:
        tool_name = tool_def['function']['name']
        params = tool_def['function']['parameters']['properties']
        required = tool_def['function']['parameters'].get('required', [])

        schema_map[tool_name] = {
            'params': list(params.keys()),
            'required': required,
            'param_details': params
        }

    # 驗證每個步驟
    validation_results = []
    for step in annotated_steps:
        tool_name = step.get('tool_name')
        arguments = step.get('arguments', {})

        # 跳過推理步驟
        if tool_name is None:
            continue

        # 檢查工具是否在 schema 中
        if tool_name not in schema_map:
            validation_results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'status': 'tool_not_found',
                'message': f"工具 {tool_name} 不在 schema 中"
            })
            continue

        tool_schema = schema_map[tool_name]

        # 檢查參數
        missing_required = []
        unknown_params = []
        param_type_errors = []

        # 檢查必要參數
        for required_param in tool_schema['required']:
            if required_param not in arguments:
                missing_required.append(required_param)

        # 檢查未知參數
        for param_name in arguments.keys():
            if param_name not in tool_schema['params']:
                unknown_params.append(param_name)

        # 記錄結果
        if missing_required or unknown_params or param_type_errors:
            validation_results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'status': 'parameter_error',
                'missing_required': missing_required,
                'unknown_params': unknown_params,
                'param_type_errors': param_type_errors
            })
        else:
            validation_results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'status': 'valid'
            })

    # 統計結果
    valid_count = sum(1 for r in validation_results if r['status'] == 'valid')
    total_count = len(validation_results)

    return {
        'task_id': task_id,
        'total_steps': total_count,
        'valid_steps': valid_count,
        'validation_rate': valid_count / total_count if total_count > 0 else 0,
        'validation_results': validation_results
    }


def analyze_109_tasks(tasks, validation_results):
    """分析 109 題的統計資訊"""

    # 統計難度分布
    level_count = Counter()
    for task in tasks:
        level = task.get('level', 3)
        level_count[level] += 1

    # 統計工具使用
    tool_usage = Counter()
    param_usage = Counter()

    for task in tasks:
        for step in task.get('annotated_steps', []):
            tool_name = step.get('tool_name')
            if tool_name is None:
                tool_usage['None'] += 1
                continue

            tool_usage[tool_name] += 1

            # 統計參數
            for param_name in step.get('arguments', {}).keys():
                param_usage[f"{tool_name}.{param_name}"] += 1

    # 統計步驟數
    total_steps = sum(len(task.get('annotated_steps', [])) for task in tasks)
    avg_steps = total_steps / len(tasks)

    # 統計驗證結果
    total_validated = sum(r['total_steps'] for r in validation_results)
    total_valid = sum(r['valid_steps'] for r in validation_results)
    overall_validation_rate = total_valid / total_validated if total_validated > 0 else 0

    return {
        'summary': {
            'total_tasks': len(tasks),
            'level_distribution': dict(level_count),
            'total_steps': total_steps,
            'avg_steps_per_task': avg_steps,
            'total_validated_steps': total_validated,
            'total_valid_steps': total_valid,
            'overall_validation_rate': overall_validation_rate
        },
        'tool_usage': dict(tool_usage.most_common()),
        'param_usage': dict(param_usage.most_common(20)),  # Top 20
        'validation_summary': {
            'tasks_with_100%_valid': sum(1 for r in validation_results if r['validation_rate'] == 1.0),
            'tasks_with_errors': sum(1 for r in validation_results if r['validation_rate'] < 1.0)
        }
    }


def main():
    print("=== 針對 109 題執行 Pipeline ===\n")

    # 1. 讀取 109 題
    tasks_path = Path("gaia_109_tasks.json")
    print(f"[1/3] 讀取 109 題：{tasks_path}")
    with open(tasks_path, 'r') as f:
        tasks_109 = json.load(f)

    print(f"  ✓ 讀取 {len(tasks_109)} 題\n")

    # 2. 讀取 tools_schema
    schema_path = Path("tools_schema.json")
    print(f"[2/3] 讀取工具 Schema：{schema_path}")
    with open(schema_path, 'r') as f:
        tools_schema = json.load(f)

    print(f"  ✓ 讀取 {len(tools_schema)} 個工具的 schema\n")

    # 3. 驗證每題
    print(f"[3/3] 驗證 109 題的工具和參數...")
    validation_results = []

    for i, task in enumerate(tasks_109, 1):
        if i % 10 == 0:
            print(f"  進度：{i}/{len(tasks_109)}")

        result = validate_task(task, tools_schema)
        validation_results.append(result)

    print(f"  ✓ 驗證完成\n")

    # 4. 生成分析報告
    print("生成分析報告...")
    analysis = analyze_109_tasks(tasks_109, validation_results)

    # 5. 儲存結果
    output_validation = Path("validation_results_109.json")
    with open(output_validation, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 驗證結果已儲存：{output_validation}")

    output_analysis = Path("analysis_report_109.json")
    with open(output_analysis, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 分析報告已儲存：{output_analysis}\n")

    # 6. 顯示摘要
    print("=" * 70)
    print("分析摘要")
    print("=" * 70)

    summary = analysis['summary']
    print(f"\n總題數：{summary['total_tasks']}")
    print(f"總步驟數：{summary['total_steps']}")
    print(f"平均步驟數：{summary['avg_steps_per_task']:.1f}")

    print(f"\n難度分布：")
    # 確保 level 是 int
    level_dist = {(int(k) if isinstance(k, str) else k): v for k, v in summary['level_distribution'].items()}
    for level in sorted(level_dist.keys()):
        count = level_dist[level]
        print(f"  Level {level}: {count} 題")

    print(f"\n驗證結果：")
    print(f"  驗證步驟數：{summary['total_validated_steps']}")
    print(f"  有效步驟數：{summary['total_valid_steps']}")
    print(f"  整體驗證率：{summary['overall_validation_rate']:.1%}")

    print(f"\n工具使用（Top 10）：")
    for i, (tool, count) in enumerate(list(analysis['tool_usage'].items())[:10], 1):
        print(f"  {i:2d}. {tool:30s} : {count:3d} 次")

    print(f"\n參數使用（Top 10）：")
    for i, (param, count) in enumerate(list(analysis['param_usage'].items())[:10], 1):
        print(f"  {i:2d}. {param:45s} : {count:3d} 次")

    val_summary = analysis['validation_summary']
    print(f"\n題目驗證狀況：")
    print(f"  100% 有效：{val_summary['tasks_with_100%_valid']} 題")
    print(f"  有錯誤：{val_summary['tasks_with_errors']} 題")

    print("\n" + "=" * 70)
    print("Pipeline 執行完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
