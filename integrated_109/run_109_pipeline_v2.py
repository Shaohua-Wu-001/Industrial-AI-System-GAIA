#!/usr/bin/env python3
"""
針對 109 題執行 Pipeline v2（優化版）

使用統一的工具 schema，提供完整的分析報告
"""

import json
from pathlib import Path
from collections import Counter


def validate_task_v2(task, unified_tools):
    """驗證單一題目的工具和參數（v2 優化版）"""

    task_id = task['task_id']
    annotated_steps = task.get('annotated_steps', [])

    # 建立工具 schema 的快速查找表
    schema_map = {tool['function']['name']: tool for tool in unified_tools}

    # 驗證每個步驟
    validation_results = []

    for step in annotated_steps:
        tool_name = step.get('tool_name')
        arguments = step.get('arguments', {})

        # 跳過推理步驟
        if tool_name is None:
            continue

        # 如果步驟已經包含驗證結果，使用它
        if 'validation' in step:
            step_validation = step['validation']
            validation_results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'status': 'valid' if step_validation['is_valid'] else 'parameter_error',
                'missing_required': step_validation.get('missing_params', []),
                'extra_params': step_validation.get('extra_params', [])
            })
            continue

        # 檢查工具是否在 schema 中
        if tool_name not in schema_map:
            validation_results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'status': 'tool_not_found',
                'message': f"工具 {tool_name} 不在統一 schema 中"
            })
            continue

        tool_schema = schema_map[tool_name]
        required_params = tool_schema['function']['parameters'].get('required', [])
        all_params = tool_schema['function']['parameters']['properties'].keys()

        # 檢查必要參數
        missing_required = [p for p in required_params if p not in arguments]

        # 檢查未知參數
        extra_params = [p for p in arguments.keys() if p not in all_params]

        # 記錄結果
        if missing_required or extra_params:
            validation_results.append({
                'step_id': step.get('step_id'),
                'tool': tool_name,
                'status': 'parameter_error',
                'missing_required': missing_required,
                'extra_params': extra_params
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
        'source': task.get('metadata', {}).get('source', 'unknown'),
        'total_steps': total_count,
        'valid_steps': valid_count,
        'validation_rate': valid_count / total_count if total_count > 0 else 0,
        'validation_results': validation_results
    }


def analyze_109_tasks_v2(tasks, validation_results, unified_tools):
    """分析 109 題的統計資訊（v2 優化版）"""

    # 統計難度分布
    level_count = Counter()
    source_count = Counter()

    for task in tasks:
        level = task.get('level', 3)
        if isinstance(level, str):
            level = int(level.replace('level_', '').replace('Level ', ''))
        level_count[level] += 1

        source = task.get('metadata', {}).get('source', 'unknown')
        source_count[source] += 1

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

    # 按來源統計
    source_stats = {}
    for source in source_count.keys():
        source_results = [r for r in validation_results if r['source'] == source]
        if source_results:
            source_validated = sum(r['total_steps'] for r in source_results)
            source_valid = sum(r['valid_steps'] for r in source_results)
            source_stats[source] = {
                'tasks': source_count[source],
                'total_steps': source_validated,
                'valid_steps': source_valid,
                'validation_rate': source_valid / source_validated if source_validated > 0 else 0
            }

    return {
        'summary': {
            'total_tasks': len(tasks),
            'level_distribution': dict(level_count),
            'source_distribution': dict(source_count),
            'total_steps': total_steps,
            'avg_steps_per_task': avg_steps,
            'total_validated_steps': total_validated,
            'total_valid_steps': total_valid,
            'overall_validation_rate': overall_validation_rate
        },
        'source_stats': source_stats,
        'tool_usage': dict(tool_usage.most_common()),
        'param_usage': dict(param_usage.most_common(30)),  # Top 30
        'validation_summary': {
            'tasks_with_100%_valid': sum(1 for r in validation_results if r['validation_rate'] == 1.0),
            'tasks_with_errors': sum(1 for r in validation_results if r['validation_rate'] < 1.0)
        },
        'unified_tools_count': len(unified_tools)
    }


def main():
    print("=== 針對 109 題執行 Pipeline v2（優化版）===\n")

    # 1. 讀取 109 題 v2
    tasks_path = Path("gaia_109_tasks_v2.json")
    print(f"[1/4] 讀取 109 題 v2：{tasks_path}")

    with open(tasks_path, 'r') as f:
        tasks_109 = json.load(f)

    print(f"  ✓ 讀取 {len(tasks_109)} 題\n")

    # 2. 讀取統一的 tools_schema
    schema_path = Path("../tools/unified_tools_schema.json")
    print(f"[2/4] 讀取統一的工具 Schema：{schema_path}")

    with open(schema_path, 'r') as f:
        unified_tools = json.load(f)

    print(f"  ✓ 讀取 {len(unified_tools)} 個工具的 schema\n")

    # 3. 驗證每題
    print(f"[3/4] 驗證 109 題的工具和參數（使用統一 schema）...")
    validation_results = []

    for i, task in enumerate(tasks_109, 1):
        if i % 20 == 0:
            print(f"  進度：{i}/{len(tasks_109)}")

        result = validate_task_v2(task, unified_tools)
        validation_results.append(result)

    print(f"  ✓ 驗證完成\n")

    # 4. 生成分析報告
    print("[4/4] 生成分析報告...")
    analysis = analyze_109_tasks_v2(tasks_109, validation_results, unified_tools)

    # 5. 儲存結果
    output_validation = Path("validation_results_109_v2.json")
    with open(output_validation, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 驗證結果已儲存：{output_validation}")

    output_analysis = Path("analysis_report_109_v2.json")
    with open(output_analysis, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 分析報告已儲存：{output_analysis}\n")

    # 6. 顯示摘要
    print("=" * 70)
    print("分析摘要")
    print("=" * 70)

    summary = analysis['summary']
    print(f"\n【基本統計】")
    print(f"總題數：{summary['total_tasks']}")
    print(f"總步驟數：{summary['total_steps']}")
    print(f"平均步驟數：{summary['avg_steps_per_task']:.1f}")

    print(f"\n【難度分布】")
    for level in sorted(summary['level_distribution'].keys()):
        count = summary['level_distribution'][level]
        print(f"  Level {level}: {count} 題")

    print(f"\n【資料來源】")
    for source, count in summary['source_distribution'].items():
        print(f"  {source}: {count} 題")

    print(f"\n【驗證結果】")
    print(f"  驗證步驟數：{summary['total_validated_steps']}")
    print(f"  有效步驟數：{summary['total_valid_steps']}")
    print(f"  整體驗證率：{summary['overall_validation_rate']:.1%}")

    # 按來源顯示驗證率
    print(f"\n【各來源驗證率】")
    for source, stats in analysis['source_stats'].items():
        print(f"  {source}:")
        print(f"    題目數：{stats['tasks']}")
        print(f"    步驟數：{stats['total_steps']}")
        print(f"    驗證率：{stats['validation_rate']:.1%}")

    print(f"\n【工具使用統計】（Top 10）")
    for i, (tool, count) in enumerate(list(analysis['tool_usage'].items())[:10], 1):
        percentage = count / summary['total_steps'] * 100
        bar = '█' * min(int(percentage), 50)
        print(f"  {i:2d}. {tool:30s} : {count:5d} 次 ({percentage:5.1f}%) {bar}")

    print(f"\n【參數使用統計】（Top 15）")
    for i, (param, count) in enumerate(list(analysis['param_usage'].items())[:15], 1):
        print(f"  {i:2d}. {param:45s} : {count:3d} 次")

    val_summary = analysis['validation_summary']
    print(f"\n【題目驗證狀況】")
    print(f"  100% 有效：{val_summary['tasks_with_100%_valid']} 題")
    print(f"  有錯誤：{val_summary['tasks_with_errors']} 題")

    print(f"\n【統一工具 Schema】")
    print(f"  工具總數：{analysis['unified_tools_count']} 個")

    print("\n" + "=" * 70)
    print("Pipeline v2 執行完成！")
    print("=" * 70)

    # 如果有錯誤，顯示詳情
    if val_summary['tasks_with_errors'] > 0:
        print("\n⚠️ 發現有錯誤的題目，詳細資訊請查看 validation_results_109_v2.json")


if __name__ == "__main__":
    main()
