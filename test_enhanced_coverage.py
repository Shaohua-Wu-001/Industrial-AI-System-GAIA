#!/usr/bin/env python3
"""
測試優化後的工具覆蓋率
"""

import json
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib

# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


def test_coverage(tasks_path, unified_tools_path, output_dir):
    """測試工具覆蓋率"""

    # 載入資料
    with open(tasks_path, 'r') as f:
        tasks = json.load(f)

    with open(unified_tools_path, 'r') as f:
        unified_tools = json.load(f)

    tool_names = {tool['function']['name'] for tool in unified_tools}

    # 統計工具使用
    used_tools = set()
    tool_usage_count = Counter()

    for task in tasks:
        for step in task.get('annotated_steps', []):
            tool_name = step.get('tool_name')
            if tool_name:
                used_tools.add(tool_name)
                tool_usage_count[tool_name] += 1

    # 計算覆蓋率
    coverage_rate = len(used_tools) / len(tool_names) * 100

    # 列印統計
    print("=" * 70)
    print("優化後工具覆蓋率測試")
    print("=" * 70)
    print(f"\n總工具數：{len(tool_names)}")
    print(f"已使用工具數：{len(used_tools)}")
    print(f"工具覆蓋率：{coverage_rate:.1f}%")

    print(f"\n最常用的工具（Top 15）：")
    for i, (tool, count) in enumerate(tool_usage_count.most_common(15), 1):
        print(f"  {i:2d}. {tool:30s} : {count:4d} 次")

    print(f"\n未使用的工具（{len(tool_names) - len(used_tools)} 個）：")
    unused = sorted(tool_names - used_tools)
    for i, tool in enumerate(unused[:20], 1):
        print(f"  {i:2d}. {tool}")
    if len(unused) > 20:
        print(f"  ... 還有 {len(unused) - 20} 個")

    # 生成視覺化
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # 圖表 1：覆蓋率對比
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 圓餅圖
    sizes = [len(used_tools), len(tool_names) - len(used_tools)]
    labels = [f'已使用\n{len(used_tools)} 個', f'未使用\n{len(tool_names) - len(used_tools)} 個']
    colors = ['#2ecc71', '#f39c12']
    explode = (0.1, 0)

    ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 12})
    ax1.set_title(f'優化後工具覆蓋率\n{coverage_rate:.1f}%', fontsize=14, fontweight='bold')

    # 長條圖 - Top 10
    top_10_tools = tool_usage_count.most_common(10)
    tools = [t[0] for t in top_10_tools]
    counts = [t[1] for t in top_10_tools]

    ax2.barh(tools, counts, color='#3498db', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('使用次數', fontsize=12)
    ax2.set_title('Top 10 最常用工具', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    ax2.invert_yaxis()

    # 在長條上顯示數值
    for i, (tool, count) in enumerate(top_10_tools):
        ax2.text(count + 5, i, str(count), va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'enhanced_tool_coverage.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✓ 視覺化圖表已儲存：{output_dir / 'enhanced_tool_coverage.png'}")

    # 生成報告
    report = {
        'total_tools': len(tool_names),
        'used_tools': len(used_tools),
        'coverage_rate': coverage_rate,
        'tool_usage_count': dict(tool_usage_count),
        'used_tool_list': list(used_tools),
        'unused_tool_list': unused
    }

    report_path = output_dir / 'enhanced_coverage_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✓ 詳細報告已儲存：{report_path}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    base_dir = Path("/Users/chengpeici/Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/Delta_GAIA")

    test_coverage(
        tasks_path=base_dir / "integrated_109/gaia_109_tasks_v3_enhanced.json",
        unified_tools_path=base_dir / "tools/unified_tools_schema.json",
        output_dir=base_dir / "enhanced_coverage_results"
    )
