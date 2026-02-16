#!/usr/bin/env python3
"""
深度分析 109 題數據 - 專業計算機科學家級別
目標：找出所有錯誤模式，設計完美的提取策略
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
import statistics


class DeepAnalyzer:
    """深度分析器"""

    def __init__(self):
        self.base_path = Path(__file__).parent
        self.load_data()

    def load_data(self):
        """載入所有數據"""
        # 載入整合後的 109 題
        with open(self.base_path / "integrated_109/gaia_109_tasks_FIXED.json", 'r') as f:
            self.all_tasks = json.load(f)

        # 載入 TA 答案
        ta_path = Path.home() / "Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl"
        self.ta_answers = {}
        with open(ta_path, 'r') as f:
            for line in f:
                task = json.loads(line)
                task_id = task['meta']['id']
                self.ta_answers[task_id] = task['gold']['final_answer']

        # 載入提取結果
        with open(self.base_path / "extraction_results_109.json", 'r') as f:
            self.extraction_results = json.load(f)

        # 分離 GAIA L3 和 TA
        self.gaia_l3_tasks = [t for t in self.all_tasks if t['task_id'].startswith('gaia_val_l3_')]
        self.ta_tasks = [t for t in self.all_tasks if t['task_id'].startswith('gaia_ta_')]

        print(f"✓ 載入 {len(self.all_tasks)} 題")
        print(f"  - GAIA L3: {len(self.gaia_l3_tasks)} 題")
        print(f"  - TA: {len(self.ta_tasks)} 題")

    def analyze_all(self):
        """執行所有分析"""
        print("\n" + "=" * 80)
        print("🔬 深度分析開始")
        print("=" * 80)

        # 1. 步驟結構分析
        print("\n" + "─" * 80)
        print("📊 Part 1: 步驟結構分析")
        print("─" * 80)
        self.analyze_step_structure()

        # 2. Description 質量分析
        print("\n" + "─" * 80)
        print("📝 Part 2: Description 文本質量分析")
        print("─" * 80)
        self.analyze_description_quality()

        # 3. 工具使用分析
        print("\n" + "─" * 80)
        print("🔧 Part 3: 工具調用分析")
        print("─" * 80)
        self.analyze_tool_usage()

        # 4. 答案位置分析
        print("\n" + "─" * 80)
        print("🎯 Part 4: 答案位置分析")
        print("─" * 80)
        self.analyze_answer_location()

        # 5. 失敗案例深度分析
        print("\n" + "─" * 80)
        print("❌ Part 5: 失敗案例深度剖析")
        print("─" * 80)
        self.analyze_failures()

        # 6. 成功案例分析
        print("\n" + "─" * 80)
        print("✅ Part 6: 成功案例模式識別")
        print("─" * 80)
        self.analyze_successes()

        # 7. 生成改進方案
        print("\n" + "─" * 80)
        print("💡 Part 7: 改進方案設計")
        print("─" * 80)
        self.generate_improvement_plan()

    def analyze_step_structure(self):
        """分析步驟結構"""
        print("\n【GAIA L3 步驟結構】")
        gaia_step_counts = [len(t['annotated_steps']) for t in self.gaia_l3_tasks]
        print(f"  步驟數：min={min(gaia_step_counts)}, max={max(gaia_step_counts)}, "
              f"avg={statistics.mean(gaia_step_counts):.1f}, median={statistics.median(gaia_step_counts):.1f}")

        print("\n【TA 步驟結構】")
        ta_step_counts = [len(t['annotated_steps']) for t in self.ta_tasks]
        print(f"  步驟數：min={min(ta_step_counts)}, max={max(ta_step_counts)}, "
              f"avg={statistics.mean(ta_step_counts):.1f}, median={statistics.median(ta_step_counts):.1f}")

        # 分析步驟類型
        print("\n【步驟類型分布】")
        gaia_step_types = []
        ta_step_types = []

        for task in self.gaia_l3_tasks:
            for step in task['annotated_steps']:
                gaia_step_types.append(step.get('step_type', 'unknown'))

        for task in self.ta_tasks:
            for step in task['annotated_steps']:
                ta_step_types.append(step.get('step_type', 'unknown'))

        print(f"  GAIA L3: {dict(Counter(gaia_step_types))}")
        print(f"  TA: {dict(Counter(ta_step_types))}")

    def analyze_description_quality(self):
        """分析 description 文本質量"""
        print("\n【GAIA L3 Description 質量】")
        gaia_desc_lengths = []
        for task in self.gaia_l3_tasks:
            for step in task['annotated_steps']:
                desc = step['description']
                gaia_desc_lengths.append(len(desc))

        print(f"  長度：min={min(gaia_desc_lengths)}, max={max(gaia_desc_lengths)}, "
              f"avg={statistics.mean(gaia_desc_lengths):.1f}, median={statistics.median(gaia_desc_lengths):.1f}")

        # 檢查空描述
        gaia_empty = sum(1 for l in gaia_desc_lengths if l < 10)
        print(f"  空描述（<10字符）：{gaia_empty}/{len(gaia_desc_lengths)} = {gaia_empty/len(gaia_desc_lengths)*100:.1f}%")

        print("\n【TA Description 質量】")
        ta_desc_lengths = []
        for task in self.ta_tasks:
            for step in task['annotated_steps']:
                desc = step['description']
                ta_desc_lengths.append(len(desc))

        print(f"  長度：min={min(ta_desc_lengths)}, max={max(ta_desc_lengths)}, "
              f"avg={statistics.mean(ta_desc_lengths):.1f}, median={statistics.median(ta_desc_lengths):.1f}")

        ta_empty = sum(1 for l in ta_desc_lengths if l < 10)
        print(f"  空描述（<10字符）：{ta_empty}/{len(ta_desc_lengths)} = {ta_empty/len(ta_desc_lengths)*100:.1f}%")

        # 對比
        print(f"\n【對比】")
        print(f"  GAIA L3 平均長度 / TA 平均長度 = {statistics.mean(gaia_desc_lengths) / statistics.mean(ta_desc_lengths):.2f}x")

    def analyze_tool_usage(self):
        """分析工具使用"""
        print("\n【GAIA L3 工具使用】")
        gaia_tools = []
        gaia_has_tool = 0
        for task in self.gaia_l3_tasks:
            for step in task['annotated_steps']:
                tool = step.get('tool_name')
                if tool:
                    gaia_tools.append(tool)
                    gaia_has_tool += 1

        print(f"  有工具的步驟：{gaia_has_tool}/{sum(len(t['annotated_steps']) for t in self.gaia_l3_tasks)}")
        if gaia_tools:
            print(f"  工具分布：{dict(Counter(gaia_tools).most_common(10))}")
        else:
            print(f"  ⚠️  沒有工具！（全是 None）")

        print("\n【TA 工具使用】")
        ta_tools = []
        ta_has_tool = 0
        for task in self.ta_tasks:
            for step in task['annotated_steps']:
                tool = step.get('tool_name')
                if tool:
                    ta_tools.append(tool)
                    ta_has_tool += 1

        total_ta_steps = sum(len(t['annotated_steps']) for t in self.ta_tasks)
        print(f"  有工具的步驟：{ta_has_tool}/{total_ta_steps} = {ta_has_tool/total_ta_steps*100:.1f}%")
        if ta_tools:
            print(f"  工具分布（Top 10）：")
            for tool, count in Counter(ta_tools).most_common(10):
                print(f"    {tool}: {count}")

        # 檢查 submit_final_answer
        submit_count = sum(1 for tool in ta_tools if 'submit' in tool.lower() or 'final' in tool.lower())
        print(f"\n  ⭐ submit_final_answer 出現次數：{submit_count}")

    def analyze_answer_location(self):
        """分析答案在哪裡"""
        print("\n【分析答案出現位置】")

        # GAIA L3
        print("\n  GAIA L3 (10題)：")
        for task in self.gaia_l3_tasks:
            task_id = task['task_id']
            expected = task.get('final_answer')
            steps = task['annotated_steps']

            # 檢查答案在哪些步驟中出現
            locations = []
            for i, step in enumerate(steps, 1):
                desc = step['description'].lower()
                if expected and str(expected).lower() in desc:
                    locations.append(i)

            if locations:
                print(f"    {task_id}: 答案出現在步驟 {locations} (共{len(steps)}步)")
            else:
                print(f"    {task_id}: ⚠️  答案未出現在任何步驟！(預期: {expected})")

        # TA - 抽樣檢查前 10 個失敗案例
        print("\n  TA 失敗案例抽樣 (前10個)：")
        failed_ta = [r for r in self.extraction_results['results']['ta'] if not r['is_correct']][:10]

        for result in failed_ta:
            task_id = result['task_id']
            task = next((t for t in self.ta_tasks if t['task_id'] == task_id), None)
            if not task:
                continue

            expected = result['expected']
            steps = task['annotated_steps']

            # 檢查答案位置
            locations = []
            for i, step in enumerate(steps, 1):
                desc = step['description'].lower()
                exp_lower = str(expected).lower()
                if exp_lower in desc:
                    locations.append(i)

            extracted = result['extracted']

            if locations:
                print(f"    {task_id[:20]}... 預期:{expected}, 提取:{extracted}")
                print(f"      → 答案在步驟 {locations} (共{len(steps)}步)")
            else:
                print(f"    {task_id[:20]}... 預期:{expected}, 提取:{extracted}")
                print(f"      → ⚠️  答案未在步驟描述中！")
                # 檢查是否在工具參數中
                for i, step in enumerate(steps, 1):
                    args = step.get('arguments', {})
                    if args and str(expected).lower() in str(args).lower():
                        print(f"      → 💡 答案可能在步驟{i}的arguments中：{args}")
                        break

    def analyze_failures(self):
        """深度分析失敗案例"""
        print("\n【失敗案例分類】")

        failed_ta = [r for r in self.extraction_results['results']['ta'] if not r['is_correct']]

        # 分類錯誤
        error_types = {
            'answer_not_in_text': [],      # 答案不在文本中
            'wrong_number': [],            # 提取到錯誤的數字
            'partial_match': [],           # 部分匹配
            'format_mismatch': [],         # 格式不匹配
            'no_extraction': [],           # 完全沒提取到
        }

        for result in failed_ta:
            task_id = result['task_id']
            task = next((t for t in self.ta_tasks if t['task_id'] == task_id), None)
            if not task:
                continue

            expected = str(result['expected'])
            extracted = str(result['extracted']) if result['extracted'] else None

            # 分類
            if not extracted or extracted == 'None':
                error_types['no_extraction'].append(result)
            else:
                # 檢查答案是否在步驟中
                all_text = ' '.join([s['description'] for s in task['annotated_steps']])
                if expected.lower() not in all_text.lower():
                    error_types['answer_not_in_text'].append(result)
                # 檢查是否是數字問題
                elif expected.isdigit() and extracted.isdigit():
                    error_types['wrong_number'].append(result)
                # 檢查是否部分匹配
                elif expected.lower() in extracted.lower() or extracted.lower() in expected.lower():
                    error_types['partial_match'].append(result)
                # 格式問題
                else:
                    error_types['format_mismatch'].append(result)

        print(f"\n  錯誤類型統計（共 {len(failed_ta)} 個失敗案例）：")
        for err_type, cases in error_types.items():
            print(f"    {err_type}: {len(cases)} 個 ({len(cases)/len(failed_ta)*100:.1f}%)")

        # 詳細展示每種錯誤的範例
        print(f"\n【錯誤類型詳細範例】")

        for err_type, cases in error_types.items():
            if not cases:
                continue
            print(f"\n  {err_type} ({len(cases)}個)：")
            for case in cases[:3]:  # 只顯示前3個
                print(f"    • 預期: '{case['expected']}' | 提取: '{case['extracted']}'")
                print(f"      Task: {case['task_id'][:30]}...")

    def analyze_successes(self):
        """分析成功案例的模式"""
        print("\n【成功案例模式分析】")

        # GAIA L3 成功案例
        gaia_success = [r for r in self.extraction_results['results']['gaia_l3'] if r['is_correct']]
        print(f"\n  GAIA L3 成功案例 ({len(gaia_success)}/{len(self.extraction_results['results']['gaia_l3'])})：")

        method_counter = Counter([r['method'] for r in gaia_success])
        print(f"    方法分布：")
        for method, count in method_counter.most_common():
            print(f"      {method}: {count}次")

        # TA 成功案例
        ta_success = [r for r in self.extraction_results['results']['ta'] if r['is_correct']]
        print(f"\n  TA 成功案例 ({len(ta_success)}/{len(self.extraction_results['results']['ta'])})：")

        method_counter = Counter([r['method'] for r in ta_success])
        print(f"    方法分布：")
        for method, count in method_counter.most_common(10):
            print(f"      {method}: {count}次")

        # 分析成功案例的共同特徵
        print(f"\n  成功案例共同特徵：")

        # 檢查答案長度
        success_answer_lengths = [len(str(r['expected'])) for r in ta_success]
        failed_answer_lengths = [len(str(r['expected'])) for r in self.extraction_results['results']['ta'] if not r['is_correct']]

        print(f"    成功案例答案平均長度: {statistics.mean(success_answer_lengths):.1f}")
        print(f"    失敗案例答案平均長度: {statistics.mean(failed_answer_lengths):.1f}")

        # 檢查答案類型
        success_numeric = sum(1 for r in ta_success if str(r['expected']).replace('.', '').replace(',', '').replace('-', '').isdigit())
        print(f"    成功案例中數字答案: {success_numeric}/{len(ta_success)} = {success_numeric/len(ta_success)*100:.1f}%")

    def generate_improvement_plan(self):
        """生成改進方案"""
        print("\n【基於分析的改進方案】")

        print("""
╔══════════════════════════════════════════════════════════════════════╗
║  改進策略 1: 針對 TA 的特殊處理                                    ║
╚══════════════════════════════════════════════════════════════════════╝

問題：TA 的步驟可能不包含答案文本
方案：
  1. 檢查是否有 submit_final_answer 或類似工具
  2. 從該工具的 arguments 中提取答案
  3. 如果沒有，回退到文本提取

代碼框架：
  if task['source'] == 'ta':
      final_step = find_submit_step(task['steps'])
      if final_step and 'answer' in final_step.get('arguments', {}):
          return final_step['arguments']['answer']
      # 回退到文本提取
      return text_extraction(task['steps'])

╔══════════════════════════════════════════════════════════════════════╗
║  改進策略 2: 多層次回退機制                                        ║
╚══════════════════════════════════════════════════════════════════════╝

優先級：
  1. submit_final_answer.arguments.answer (TA專用)
  2. 最後一步的 description 文本提取
  3. 最後 5 步的文本提取（當前方法）
  4. 全部步驟的文本提取
  5. LLM 輔助提取（最後手段）

╔══════════════════════════════════════════════════════════════════════╗
║  改進策略 3: 答案類型識別                                          ║
╚══════════════════════════════════════════════════════════════════════╝

根據答案類型選擇提取方法：
  - 數字答案 → 優先數字提取方法
  - 日期答案 → 使用日期正則
  - 長文本答案 → 使用引號/括號提取
  - 組合答案 → 使用分隔符提取

╔══════════════════════════════════════════════════════════════════════╗
║  改進策略 4: 質量過濾 + LLM 增強                                   ║
╚══════════════════════════════════════════════════════════════════════╝

對於低質量步驟：
  - description < 20 字符 → 標記為低質量
  - 低質量步驟 > 50% → 使用 LLM 輔助提取

LLM 提示：
  "Given the question and steps, extract ONLY the final answer.
   Question: {question}
   Steps: {last_3_steps}
   Answer:"

╔══════════════════════════════════════════════════════════════════════╗
║  預期改進效果                                                       ║
╚══════════════════════════════════════════════════════════════════════╝

  策略 1: TA 27.3% → 40% (+12.7%)
  策略 2: 40% → 50% (+10%)
  策略 3: 50% → 60% (+10%)
  策略 4: 60% → 70% (+10%)

  總體: 33% → 70% (+37%)
        """)


def main():
    analyzer = DeepAnalyzer()
    analyzer.analyze_all()

    # 儲存分析報告
    print("\n" + "=" * 80)
    print("📄 生成詳細分析報告...")
    print("=" * 80)

    # 這裡可以生成 JSON 報告
    print("\n✓ 分析完成！")


if __name__ == "__main__":
    main()
