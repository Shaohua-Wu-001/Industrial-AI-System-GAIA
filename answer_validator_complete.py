#!/usr/bin/env python3
"""
完整答案驗證系統
功能：
1. 驗證 GAIA L3 10 題的答案正確性
2. 檢查助教 99 題的完整性（是否有結論步驟）
3. 生成詳細的答案驗證報告
4. 視覺化答案正確率統計
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib


# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


class AnswerValidator:
    """答案驗證系統"""

    def __init__(self, tasks_path, original_gaia_path):
        # 載入 109 題
        with open(tasks_path, 'r') as f:
            self.tasks = json.load(f)

        # 載入原始 GAIA L3 資料（有答案）
        with open(original_gaia_path, 'r') as f:
            self.original_gaia = json.load(f)

        # 建立答案對應表
        self.ground_truth = {}
        for task in self.original_gaia:
            task_id = task['task_id']
            self.ground_truth[task_id] = task.get('Final answer', '')

        # 統計
        self.validation_results = []

    def validate_all(self):
        """驗證所有題目"""
        print(f"開始驗證 {len(self.tasks)} 題...")

        for i, task in enumerate(self.tasks, 1):
            if i % 20 == 0:
                print(f"  進度：{i}/{len(self.tasks)}")

            result = self.validate_task(task)
            self.validation_results.append(result)

        print(f"✓ 驗證完成！")
        return self.validation_results

    def validate_task(self, task):
        """驗證單一題目"""
        task_id = task['task_id']
        source = task.get('metadata', {}).get('source', 'unknown')

        result = {
            'task_id': task_id,
            'source': source,
            'level': task.get('level', 'unknown'),
        }

        # 檢查是否有 ground truth
        if task_id in self.ground_truth:
            # GAIA L3 題目 - 驗證答案
            result.update(self._validate_answer(task, self.ground_truth[task_id]))
        else:
            # 助教題目 - 檢查完整性
            result.update(self._check_completeness(task))

        return result

    def _validate_answer(self, task, ground_truth):
        """驗證答案正確性"""
        steps = task.get('annotated_steps', [])

        # 尋找最後的答案步驟
        predicted_answer = None
        answer_step_index = -1

        # 從後往前找，尋找包含答案的步驟
        for i in range(len(steps) - 1, -1, -1):
            step = steps[i]
            description = step.get('description', '').lower()

            # 檢查是否是答案步驟
            if any(keyword in description for keyword in ['answer', '答案', 'final', 'result']):
                # 嘗試從描述中提取答案
                predicted_answer = self._extract_answer(description)
                answer_step_index = i
                break

        # 比對答案
        if predicted_answer is None:
            return {
                'has_answer': False,
                'is_correct': False,
                'status': 'no_answer',
                'predicted': None,
                'expected': ground_truth
            }

        # 標準化答案進行比對
        predicted_normalized = self._normalize_answer(predicted_answer)
        ground_truth_normalized = self._normalize_answer(ground_truth)

        is_correct = predicted_normalized == ground_truth_normalized

        return {
            'has_answer': True,
            'is_correct': is_correct,
            'status': 'correct' if is_correct else 'incorrect',
            'predicted': predicted_answer,
            'expected': ground_truth,
            'answer_step_index': answer_step_index
        }

    def _check_completeness(self, task):
        """檢查題目完整性（助教題目）"""
        steps = task.get('annotated_steps', [])

        # 檢查是否有工具步驟
        has_tool_steps = any(s.get('tool_name') for s in steps)

        # 檢查是否有推理步驟
        has_reasoning_steps = any(s.get('step_type') == 'thought' for s in steps)

        # 檢查是否有結論性步驟
        has_conclusion = False
        for step in steps[-3:]:  # 檢查最後 3 個步驟
            desc = step.get('description', '').lower()
            if any(word in desc for word in ['conclude', 'final', 'answer', '結論', '答案', 'result']):
                has_conclusion = True
                break

        # 計算完整性分數
        completeness_score = 0
        if has_tool_steps:
            completeness_score += 0.4
        if has_reasoning_steps:
            completeness_score += 0.3
        if has_conclusion:
            completeness_score += 0.3

        return {
            'has_answer': has_conclusion,
            'is_correct': None,  # 無法驗證
            'status': 'complete' if completeness_score >= 0.8 else 'incomplete',
            'completeness_score': completeness_score,
            'has_tool_steps': has_tool_steps,
            'has_reasoning_steps': has_reasoning_steps,
            'has_conclusion': has_conclusion,
            'total_steps': len(steps)
        }

    def _extract_answer(self, text):
        """從文本中提取答案"""
        # 嘗試多種模式提取答案
        patterns = [
            r'answer[:\s]+([^\n]+)',
            r'答案[：:\s]+([^\n]+)',
            r'final answer[:\s]+([^\n]+)',
            r'result[:\s]+([^\n]+)',
            r'結果[：:\s]+([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # 如果找不到，返回整個描述的最後一句
        sentences = text.split('.')
        return sentences[-1].strip() if sentences else text

    def _normalize_answer(self, answer):
        """標準化答案以進行比對"""
        if not answer:
            return ""

        # 轉小寫
        answer = str(answer).lower().strip()

        # 移除標點符號
        answer = re.sub(r'[^\w\s]', '', answer)

        # 移除多餘空白
        answer = ' '.join(answer.split())

        return answer

    def generate_report(self):
        """生成驗證報告"""
        # 按來源分類
        by_source = defaultdict(list)
        for result in self.validation_results:
            by_source[result['source']].append(result)

        report = {
            'summary': self._generate_summary(),
            'by_source': {},
            'detailed_results': self.validation_results
        }

        # 為每個來源生成統計
        for source, results in by_source.items():
            report['by_source'][source] = self._generate_source_stats(results)

        return report

    def _generate_summary(self):
        """生成總結統計"""
        total = len(self.validation_results)

        # GAIA L3 題目（有 ground truth）
        gaia_results = [r for r in self.validation_results if r['task_id'].startswith('gaia_val')]
        gaia_correct = sum(1 for r in gaia_results if r.get('is_correct'))
        gaia_total = len(gaia_results)

        # 助教題目（檢查完整性）
        ta_results = [r for r in self.validation_results if r['task_id'].startswith('gaia_ta')]
        ta_complete = sum(1 for r in ta_results if r.get('status') == 'complete')
        ta_total = len(ta_results)

        return {
            'total_tasks': total,
            'gaia_l3': {
                'total': gaia_total,
                'correct': gaia_correct,
                'incorrect': gaia_total - gaia_correct,
                'accuracy': gaia_correct / gaia_total if gaia_total > 0 else 0
            },
            'ta_tasks': {
                'total': ta_total,
                'complete': ta_complete,
                'incomplete': ta_total - ta_complete,
                'completeness_rate': ta_complete / ta_total if ta_total > 0 else 0
            }
        }

    def _generate_source_stats(self, results):
        """生成來源統計"""
        total = len(results)

        # 統計狀態
        status_count = defaultdict(int)
        for r in results:
            status_count[r['status']] += 1

        # 計算完整性分數（如果有）
        completeness_scores = [r.get('completeness_score', 0) for r in results]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0

        return {
            'total': total,
            'status_distribution': dict(status_count),
            'average_completeness': avg_completeness,
            'has_conclusion': sum(1 for r in results if r.get('has_conclusion', False))
        }

    def visualize_results(self, output_dir):
        """生成視覺化圖表"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        summary = self._generate_summary()

        # 圖表 1：GAIA L3 答案正確率
        self._plot_gaia_accuracy(summary['gaia_l3'], output_dir / "1_gaia_accuracy.png")

        # 圖表 2：助教題目完整性
        self._plot_ta_completeness(summary['ta_tasks'], output_dir / "2_ta_completeness.png")

        # 圖表 3：整體狀態分布
        self._plot_overall_status(output_dir / "3_overall_status.png")

        print(f"\n✓ 視覺化圖表已儲存至：{output_dir}")

    def _plot_gaia_accuracy(self, stats, output_path):
        """繪製 GAIA L3 正確率圖表"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 圓餅圖
        sizes = [stats['correct'], stats['incorrect']]
        labels = [f"正確\n{stats['correct']} 題", f"錯誤\n{stats['incorrect']} 題"]
        colors = ['#2ecc71', '#e74c3c']
        explode = (0.1, 0)

        ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 12})
        ax1.set_title(f"GAIA Level 3 答案正確率\n總計 {stats['total']} 題", fontsize=14, fontweight='bold')

        # 長條圖
        categories = ['正確', '錯誤']
        values = [stats['correct'], stats['incorrect']]
        ax2.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('題目數', fontsize=12)
        ax2.set_title(f"答案驗證統計\n正確率：{stats['accuracy']:.1%}", fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        # 在長條上顯示數值
        for i, v in enumerate(values):
            ax2.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_ta_completeness(self, stats, output_path):
        """繪製助教題目完整性圖表"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 圓餅圖
        sizes = [stats['complete'], stats['incomplete']]
        labels = [f"完整\n{stats['complete']} 題", f"不完整\n{stats['incomplete']} 題"]
        colors = ['#3498db', '#95a5a6']
        explode = (0.1, 0)

        ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 12})
        ax1.set_title(f"助教 99 題完整性分析\n總計 {stats['total']} 題", fontsize=14, fontweight='bold')

        # 長條圖
        categories = ['完整', '不完整']
        values = [stats['complete'], stats['incomplete']]
        ax2.bar(categories, values, color=colors, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('題目數', fontsize=12)
        ax2.set_title(f"完整性統計\n完整率：{stats['completeness_rate']:.1%}", fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        # 在長條上顯示數值
        for i, v in enumerate(values):
            ax2.text(i, v + 1, str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_overall_status(self, output_path):
        """繪製整體狀態分布"""
        status_count = defaultdict(int)
        for result in self.validation_results:
            status_count[result['status']] += 1

        # 創建圖表
        fig, ax = plt.subplots(figsize=(12, 7))

        statuses = list(status_count.keys())
        counts = list(status_count.values())

        # 顏色映射
        color_map = {
            'correct': '#2ecc71',
            'incorrect': '#e74c3c',
            'no_answer': '#f39c12',
            'complete': '#3498db',
            'incomplete': '#95a5a6'
        }
        colors = [color_map.get(s, '#7f8c8d') for s in statuses]

        bars = ax.bar(statuses, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax.set_ylabel('題目數', fontsize=13, fontweight='bold')
        ax.set_title('109 題整體狀態分布', fontsize=15, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # 在長條上顯示數值和百分比
        total = sum(counts)
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            percentage = count / total * 100
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{count}\n({percentage:.1f}%)',
                   ha='center', va='bottom', fontsize=11, fontweight='bold')

        plt.xticks(rotation=15, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()


def main():
    print("=" * 70)
    print("完整答案驗證系統")
    print("=" * 70)

    base_dir = Path("/Users/chengpeici/Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/Delta_GAIA")

    # 路徑
    tasks_path = base_dir / "integrated_109/gaia_109_tasks_v2.json"
    original_gaia_path = base_dir / "v5_original/gaia_level3_tasks.json"
    output_report_path = base_dir / "answer_validation_report.json"
    output_viz_dir = base_dir / "answer_validation_charts"

    # 創建驗證器
    validator = AnswerValidator(tasks_path, original_gaia_path)

    # 執行驗證
    print("\n【階段 1】驗證答案...")
    results = validator.validate_all()

    # 生成報告
    print("\n【階段 2】生成報告...")
    report = validator.generate_report()

    # 儲存報告
    with open(output_report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✓ 驗證報告已儲存：{output_report_path}")

    # 生成視覺化
    print("\n【階段 3】生成視覺化圖表...")
    validator.visualize_results(output_viz_dir)

    # 顯示摘要
    print("\n" + "=" * 70)
    print("驗證摘要")
    print("=" * 70)

    summary = report['summary']

    print(f"\n【GAIA Level 3 - 10 題】")
    gaia = summary['gaia_l3']
    print(f"  總題數：{gaia['total']}")
    print(f"  答對：{gaia['correct']} 題")
    print(f"  答錯：{gaia['incorrect']} 題")
    print(f"  正確率：{gaia['accuracy']:.1%}")

    print(f"\n【助教 99 題】")
    ta = summary['ta_tasks']
    print(f"  總題數：{ta['total']}")
    print(f"  完整：{ta['complete']} 題")
    print(f"  不完整：{ta['incomplete']} 題")
    print(f"  完整率：{ta['completeness_rate']:.1%}")

    print("\n" + "=" * 70)
    print("驗證完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
