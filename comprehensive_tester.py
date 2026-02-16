#!/usr/bin/env python3
"""
全面測試系統
測試工具覆蓋率、答案正確率，並生成視覺化圖表
"""

import json
import sys
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式後端


class ComprehensiveTester:
    """全面測試器"""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.tools_dir = self.base_dir / "tools"
        self.integrated_dir = self.base_dir / "integrated_109"
        self.v5_dir = self.base_dir / "v5_original"

        # 載入資料
        self.load_data()

    def load_data(self):
        """載入所有必要的資料"""
        print("載入資料...")

        # 載入統一的工具 schema
        with open(self.tools_dir / "unified_tools_schema.json", 'r') as f:
            self.unified_tools = json.load(f)
        print(f"  ✓ 統一工具 schema：{len(self.unified_tools)} 個工具")

        # 載入 109 題
        with open(self.integrated_dir / "gaia_109_tasks_v2.json", 'r') as f:
            self.tasks_109 = json.load(f)
        print(f"  ✓ 109 題資料：{len(self.tasks_109)} 題")

        # 載入驗證結果
        with open(self.integrated_dir / "validation_results_109_v2.json", 'r') as f:
            self.validation_results = json.load(f)
        print(f"  ✓ 驗證結果：{len(self.validation_results)} 題")

        # 載入分析報告
        with open(self.integrated_dir / "analysis_report_109_v2.json", 'r') as f:
            self.analysis_report = json.load(f)
        print(f"  ✓ 分析報告")

        # 載入原始 10 題的答案驗證結果（如果有）
        validation_path = self.v5_dir / "validation_results.json"
        if validation_path.exists():
            with open(validation_path, 'r') as f:
                self.answer_validation = json.load(f)
            print(f"  ✓ 答案驗證結果")
        else:
            self.answer_validation = None
            print(f"  ⚠ 未找到答案驗證結果")

        print()

    def test_tool_coverage(self):
        """測試工具覆蓋率"""
        print("=" * 70)
        print("工具覆蓋率測試")
        print("=" * 70)

        # 1. 統計所有可用的工具
        all_tools = {tool['function']['name'] for tool in self.unified_tools}
        print(f"\n總可用工具數：{len(all_tools)}")

        # 2. 統計實際使用的工具
        used_tools = set()
        tool_usage_count = Counter()

        for task in self.tasks_109:
            for step in task.get('annotated_steps', []):
                tool_name = step.get('tool_name')
                if tool_name and tool_name != 'None':
                    used_tools.add(tool_name)
                    tool_usage_count[tool_name] += 1

        print(f"實際使用的工具數：{len(used_tools)}")
        print(f"工具覆蓋率：{len(used_tools) / len(all_tools) * 100:.1f}%")

        # 3. 找出未使用的工具
        unused_tools = all_tools - used_tools
        print(f"\n未使用的工具（{len(unused_tools)} 個）：")
        for i, tool in enumerate(sorted(unused_tools), 1):
            print(f"  {i:2d}. {tool}")
            if i >= 10:
                print(f"  ... 還有 {len(unused_tools) - 10} 個")
                break

        # 4. 顯示最常用的工具
        print(f"\n最常用的工具（Top 10）：")
        for i, (tool, count) in enumerate(tool_usage_count.most_common(10), 1):
            percentage = count / sum(tool_usage_count.values()) * 100
            print(f"  {i:2d}. {tool:30s} : {count:3d} 次 ({percentage:5.1f}%)")

        # 5. 按類別統計工具覆蓋率
        categories = {
            'search': ['web_search', 'wikipedia_search'],
            'fetch': ['web_fetch', 'web_browser', 'download_file'],
            'read': [t for t in all_tools if t.startswith('read_')],
            'data': [t for t in all_tools if any(x in t for x in ['data', 'csv', 'excel', 'json', 'xml'])],
            'compute': ['calculate', 'calculator', 'python_executor', 'code_interpreter'],
            'text': [t for t in all_tools if any(x in t for x in ['text', 'string', 'regex', 'extract'])],
            'other': []
        }

        # 將未分類的工具歸到 other
        categorized = set()
        for cat_tools in categories.values():
            categorized.update(cat_tools)
        categories['other'] = list(all_tools - categorized)

        print(f"\n按類別的工具覆蓋率：")
        for category, cat_tools in categories.items():
            if not cat_tools:
                continue
            used_in_cat = [t for t in cat_tools if t in used_tools]
            coverage = len(used_in_cat) / len(cat_tools) * 100 if cat_tools else 0
            print(f"  {category:15s}: {len(used_in_cat):2d}/{len(cat_tools):2d} ({coverage:5.1f}%)")

        return {
            'total_tools': len(all_tools),
            'used_tools': len(used_tools),
            'coverage_rate': len(used_tools) / len(all_tools),
            'unused_tools': list(unused_tools),
            'tool_usage': dict(tool_usage_count.most_common(20)),
            'category_coverage': {
                cat: {
                    'total': len(cat_tools),
                    'used': len([t for t in cat_tools if t in used_tools]),
                    'coverage': len([t for t in cat_tools if t in used_tools]) / len(cat_tools) if cat_tools else 0
                }
                for cat, cat_tools in categories.items() if cat_tools
            }
        }

    def test_answer_correctness(self):
        """測試答案正確率"""
        print("\n" + "=" * 70)
        print("答案正確率測試")
        print("=" * 70)

        if not self.answer_validation:
            print("\n⚠ 未找到答案驗證結果")
            print("原因：validation_results.json 不存在於 v5_original/")
            return None

        # 統計答案正確率
        if isinstance(self.answer_validation, list):
            # 格式：[{"task_id": ..., "correct": True/False/None, ...}]
            total = len(self.answer_validation)
            correct = sum(1 for r in self.answer_validation if r.get('correct') == True)
            incorrect = sum(1 for r in self.answer_validation if r.get('correct') == False)
            not_executed = sum(1 for r in self.answer_validation if r.get('correct') is None)

        elif isinstance(self.answer_validation, dict) and 'results' in self.answer_validation:
            # 格式：{"total": ..., "results": [...]}
            results = self.answer_validation['results']
            total = len(results)
            correct = sum(1 for r in results if r.get('correct') == True)
            incorrect = sum(1 for r in results if r.get('correct') == False)
            not_executed = sum(1 for r in results if r.get('correct') is None)

        else:
            print(f"⚠ 未知的驗證結果格式")
            return None

        print(f"\n總題數：{total}")
        print(f"答對：{correct} 題")
        print(f"答錯：{incorrect} 題")
        print(f"未執行：{not_executed} 題")

        if total > 0:
            print(f"\n整體正確率：{correct / total * 100:.1f}% ({correct}/{total})")

        if correct + incorrect > 0:
            executed_rate = correct / (correct + incorrect) * 100
            print(f"執行正確率：{executed_rate:.1f}% ({correct}/{correct + incorrect})")

        # 按 Level 統計
        print(f"\n按難度統計：")
        level_stats = {}

        for task_result in (self.answer_validation if isinstance(self.answer_validation, list) else self.answer_validation.get('results', [])):
            task_id = task_result.get('task_id', '')

            # 從 task_id 推斷 level（如果有）
            level = 3  # 預設 Level 3
            if 'level_1' in task_id or 'l1' in task_id.lower():
                level = 1
            elif 'level_2' in task_id or 'l2' in task_id.lower():
                level = 2
            elif 'level_3' in task_id or 'l3' in task_id.lower():
                level = 3

            if level not in level_stats:
                level_stats[level] = {'total': 0, 'correct': 0, 'incorrect': 0, 'not_executed': 0}

            level_stats[level]['total'] += 1

            if task_result.get('correct') == True:
                level_stats[level]['correct'] += 1
            elif task_result.get('correct') == False:
                level_stats[level]['incorrect'] += 1
            else:
                level_stats[level]['not_executed'] += 1

        for level in sorted(level_stats.keys()):
            stats = level_stats[level]
            if stats['total'] > 0:
                rate = stats['correct'] / stats['total'] * 100
                print(f"  Level {level}: {stats['correct']}/{stats['total']} ({rate:.1f}%)")

        return {
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'not_executed': not_executed,
            'overall_rate': correct / total if total > 0 else 0,
            'executed_rate': correct / (correct + incorrect) if (correct + incorrect) > 0 else 0,
            'level_stats': level_stats
        }

    def test_parameter_completeness(self):
        """測試參數完整性"""
        print("\n" + "=" * 70)
        print("參數完整性測試")
        print("=" * 70)

        # 統計參數使用情況
        param_stats = {}

        for task in self.tasks_109:
            for step in task.get('annotated_steps', []):
                tool_name = step.get('tool_name')
                if not tool_name or tool_name == 'None':
                    continue

                arguments = step.get('arguments', {})

                if tool_name not in param_stats:
                    param_stats[tool_name] = {
                        'total_calls': 0,
                        'params_used': Counter()
                    }

                param_stats[tool_name]['total_calls'] += 1

                for param_name in arguments.keys():
                    param_stats[tool_name]['params_used'][param_name] += 1

        print(f"\n參數使用統計（Top 10 工具）：")

        for i, (tool_name, stats) in enumerate(sorted(param_stats.items(), key=lambda x: x[1]['total_calls'], reverse=True)[:10], 1):
            print(f"\n{i:2d}. {tool_name} ({stats['total_calls']} 次調用)")

            if stats['params_used']:
                for param, count in stats['params_used'].most_common(5):
                    percentage = count / stats['total_calls'] * 100
                    print(f"    - {param:30s} : {count:3d} 次 ({percentage:5.1f}%)")
            else:
                print(f"    (無參數)")

        return param_stats

    def generate_visualizations(self, tool_coverage, answer_correctness, output_dir):
        """生成視覺化圖表"""
        print("\n" + "=" * 70)
        print("生成視覺化圖表")
        print("=" * 70)

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 1. 工具覆蓋率圓餅圖
        print("\n生成圖表 1/5：工具覆蓋率圓餅圖...")
        fig, ax = plt.subplots(figsize=(10, 8))

        labels = ['Used Tools', 'Unused Tools']
        sizes = [tool_coverage['used_tools'], len(tool_coverage['unused_tools'])]
        colors = ['#4CAF50', '#FFC107']
        explode = (0.1, 0)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90, textprops={'fontsize': 12})
        ax.set_title(f'Tool Coverage Rate\n{tool_coverage["used_tools"]}/{tool_coverage["total_tools"]} tools used', fontsize=14, fontweight='bold')

        plt.savefig(output_dir / '1_tool_coverage_pie.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 已儲存：{output_dir / '1_tool_coverage_pie.png'}")

        # 2. 工具使用頻率長條圖
        print("\n生成圖表 2/5：工具使用頻率長條圖...")
        fig, ax = plt.subplots(figsize=(12, 8))

        tools = list(tool_coverage['tool_usage'].keys())[:15]
        counts = [tool_coverage['tool_usage'][t] for t in tools]

        y_pos = range(len(tools))
        ax.barh(y_pos, counts, color='#2196F3')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(tools, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel('Usage Count', fontsize=12)
        ax.set_title('Top 15 Most Used Tools', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        for i, v in enumerate(counts):
            ax.text(v + max(counts) * 0.01, i, str(v), va='center', fontsize=10)

        plt.tight_layout()
        plt.savefig(output_dir / '2_tool_usage_bar.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 已儲存：{output_dir / '2_tool_usage_bar.png'}")

        # 3. 類別覆蓋率長條圖
        print("\n生成圖表 3/5：類別覆蓋率長條圖...")
        fig, ax = plt.subplots(figsize=(10, 6))

        categories = list(tool_coverage['category_coverage'].keys())
        coverage_rates = [tool_coverage['category_coverage'][c]['coverage'] * 100 for c in categories]

        x_pos = range(len(categories))
        bars = ax.bar(x_pos, coverage_rates, color='#9C27B0')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Coverage Rate (%)', fontsize=12)
        ax.set_title('Tool Coverage by Category', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.grid(axis='y', alpha=0.3)

        for i, (bar, rate) in enumerate(zip(bars, coverage_rates)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                   f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(output_dir / '3_category_coverage_bar.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 已儲存：{output_dir / '3_category_coverage_bar.png'}")

        # 4. 答案正確率圓餅圖（如果有）
        if answer_correctness:
            print("\n生成圖表 4/5：答案正確率圓餅圖...")
            fig, ax = plt.subplots(figsize=(10, 8))

            labels = ['Correct', 'Incorrect', 'Not Executed']
            sizes = [answer_correctness['correct'], answer_correctness['incorrect'], answer_correctness['not_executed']]
            colors = ['#4CAF50', '#F44336', '#9E9E9E']
            explode = (0.1, 0, 0)

            ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                   shadow=True, startangle=90, textprops={'fontsize': 12})
            ax.set_title(f'Answer Correctness\n{answer_correctness["correct"]}/{answer_correctness["total"]} correct ({answer_correctness["overall_rate"]*100:.1f}%)', fontsize=14, fontweight='bold')

            plt.savefig(output_dir / '4_answer_correctness_pie.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ 已儲存：{output_dir / '4_answer_correctness_pie.png'}")
        else:
            print("\n跳過圖表 4/5：無答案驗證資料")

        # 5. Level 分布圓餅圖
        print("\n生成圖表 5/5：難度分布圓餅圖...")
        fig, ax = plt.subplots(figsize=(10, 8))

        level_dist = self.analysis_report['summary']['level_distribution']
        labels = [f'Level {level}' for level in sorted(level_dist.keys())]
        sizes = [level_dist[level] for level in sorted(level_dist.keys())]
        colors = ['#8BC34A', '#FF9800', '#F44336']
        explode = (0, 0.1, 0)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90, textprops={'fontsize': 12})
        ax.set_title(f'Difficulty Distribution\nTotal: {sum(sizes)} tasks', fontsize=14, fontweight='bold')

        plt.savefig(output_dir / '5_level_distribution_pie.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 已儲存：{output_dir / '5_level_distribution_pie.png'}")

        print(f"\n所有圖表已儲存至：{output_dir}/")


def main():
    base_dir = "/Users/chengpeici/Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/Delta_GAIA"

    print("=" * 70)
    print("全面測試系統")
    print("=" * 70)
    print()

    tester = ComprehensiveTester(base_dir)

    # 1. 測試工具覆蓋率
    tool_coverage = tester.test_tool_coverage()

    # 2. 測試答案正確率
    answer_correctness = tester.test_answer_correctness()

    # 3. 測試參數完整性
    param_completeness = tester.test_parameter_completeness()

    # 4. 生成視覺化圖表
    output_dir = Path(base_dir) / "test_results"
    tester.generate_visualizations(tool_coverage, answer_correctness, output_dir)

    # 5. 儲存測試報告
    print("\n" + "=" * 70)
    print("儲存測試報告")
    print("=" * 70)

    report = {
        'tool_coverage': tool_coverage,
        'answer_correctness': answer_correctness,
        'parameter_completeness': {
            tool: {
                'total_calls': stats['total_calls'],
                'params_used': dict(stats['params_used'].most_common())
            }
            for tool, stats in param_completeness.items()
        }
    }

    report_path = Path(base_dir) / "test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 測試報告已儲存：{report_path}")
    print(f"✓ 圖表已儲存：{output_dir}/")

    print("\n" + "=" * 70)
    print("測試完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
