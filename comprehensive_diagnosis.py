#!/usr/bin/env python3
"""
全面診斷系統 - 系統性檢查所有問題
作為頂尖計算機科學家，深度分析：
1. Tools Schema 完整性
2. Parser 邏輯正確性
3. Parameters 準確性
4. Executor 可執行性
5. Answer 提取邏輯
"""

import json
from pathlib import Path
from collections import defaultdict, Counter


class ComprehensiveDiagnostics:
    """全面診斷系統"""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.issues = defaultdict(list)
        self.stats = {}

    def diagnose_all(self):
        """執行所有診斷"""
        print("=" * 80)
        print("🔬 全面診斷系統 - 深度分析")
        print("=" * 80)

        # 1. 診斷 Tools Schema
        print("\n【診斷 1/6】Tools Schema 完整性檢查")
        print("-" * 80)
        self.diagnose_tools_schema()

        # 2. 診斷資料整合
        print("\n【診斷 2/6】資料整合一致性檢查")
        print("-" * 80)
        self.diagnose_data_integration()

        # 3. 診斷 Parser 輸出
        print("\n【診斷 3/6】Parser 輸出檢查")
        print("-" * 80)
        self.diagnose_parser_output()

        # 4. 診斷參數完整性
        print("\n【診斷 4/6】參數完整性檢查")
        print("-" * 80)
        self.diagnose_parameters()

        # 5. 診斷答案提取
        print("\n【診斷 5/6】答案提取邏輯檢查")
        print("-" * 80)
        self.diagnose_answer_extraction()

        # 6. 診斷執行能力
        print("\n【診斷 6/6】執行能力檢查")
        print("-" * 80)
        self.diagnose_executability()

        # 生成報告
        self.generate_report()

    def diagnose_tools_schema(self):
        """診斷 Tools Schema"""
        schema_path = self.base_dir / "tools/unified_tools_schema.json"

        try:
            with open(schema_path, 'r') as f:
                tools = json.load(f)

            print(f"✓ 統一 Schema 載入成功")
            print(f"  總工具數：{len(tools)}")

            # 檢查每個工具的結構
            for i, tool in enumerate(tools):
                tool_name = tool['function']['name']

                # 檢查必要欄位
                if 'parameters' not in tool['function']:
                    self.issues['schema'].append(f"{tool_name}: 缺少 parameters 欄位")

                params = tool['function'].get('parameters', {})
                if 'properties' not in params:
                    self.issues['schema'].append(f"{tool_name}: 缺少 properties 欄位")

                # 檢查 required 與 properties 一致性
                required = params.get('required', [])
                properties = params.get('properties', {})

                for req in required:
                    if req not in properties:
                        self.issues['schema'].append(
                            f"{tool_name}: required 參數 '{req}' 不在 properties 中"
                        )

            if not self.issues['schema']:
                print(f"✓ Schema 結構驗證通過")
            else:
                print(f"✗ 發現 {len(self.issues['schema'])} 個 Schema 問題")
                for issue in self.issues['schema'][:5]:
                    print(f"  - {issue}")

        except Exception as e:
            self.issues['schema'].append(f"Schema 載入失敗：{str(e)}")
            print(f"✗ Schema 載入失敗：{str(e)}")

    def diagnose_data_integration(self):
        """診斷資料整合"""
        # 檢查原始 GAIA L3 資料
        gaia_original_path = self.base_dir / "v5_original/gaia_level3_tasks.json"
        integrated_path = self.base_dir / "integrated_109/gaia_109_tasks_v2.json"

        try:
            # 載入原始資料
            with open(gaia_original_path, 'r') as f:
                gaia_original = json.load(f)

            # 載入整合資料
            with open(integrated_path, 'r') as f:
                integrated = json.load(f)

            print(f"✓ 資料載入成功")
            print(f"  原始 GAIA L3：{len(gaia_original)} 題")
            print(f"  整合後總計：{len(integrated)} 題")

            # 檢查 GAIA L3 題目是否都在
            gaia_l3_in_integrated = [t for t in integrated if t['task_id'].startswith('gaia_val_l3')]
            print(f"  整合中的 GAIA L3：{len(gaia_l3_in_integrated)} 題")

            if len(gaia_l3_in_integrated) != len(gaia_original):
                self.issues['integration'].append(
                    f"GAIA L3 題目數量不符：原始 {len(gaia_original)}，整合後 {len(gaia_l3_in_integrated)}"
                )

            # 比對每題的步驟數
            print(f"\n  步驟數對比：")
            for orig_task in gaia_original:
                task_id = orig_task['task_id']

                # 找對應的整合任務
                integrated_task = next((t for t in gaia_l3_in_integrated if t['task_id'] == task_id), None)

                if integrated_task:
                    orig_steps = orig_task['Annotator Metadata']['Steps']
                    orig_step_count = int(orig_task['Annotator Metadata']['Number of steps'])
                    integrated_step_count = len(integrated_task['annotated_steps'])

                    print(f"    {task_id}:")
                    print(f"      原始：{orig_step_count} 步")
                    print(f"      整合後：{integrated_step_count} 步")

                    if integrated_step_count > orig_step_count * 10:
                        self.issues['integration'].append(
                            f"{task_id}: 步驟數異常膨脹（{orig_step_count} → {integrated_step_count}）"
                        )

            if not self.issues['integration']:
                print(f"\n✓ 資料整合一致性通過")
            else:
                print(f"\n✗ 發現 {len(self.issues['integration'])} 個整合問題")

        except Exception as e:
            self.issues['integration'].append(f"資料整合檢查失敗：{str(e)}")
            print(f"✗ 資料整合檢查失敗：{str(e)}")

    def diagnose_parser_output(self):
        """診斷 Parser 輸出"""
        integrated_path = self.base_dir / "integrated_109/gaia_109_tasks_v2.json"

        try:
            with open(integrated_path, 'r') as f:
                tasks = json.load(f)

            # 檢查 GAIA L3 題目
            gaia_l3_tasks = [t for t in tasks if t['task_id'].startswith('gaia_val_l3')]

            print(f"檢查 {len(gaia_l3_tasks)} 個 GAIA L3 題目...")

            for task in gaia_l3_tasks[:3]:  # 檢查前 3 題
                task_id = task['task_id']
                steps = task['annotated_steps']

                print(f"\n  {task_id}:")
                print(f"    總步驟數：{len(steps)}")

                # 檢查步驟類型分布
                step_types = Counter(s['step_type'] for s in steps)
                print(f"    步驟類型：{dict(step_types)}")

                # 檢查最後 5 個步驟
                print(f"    最後 5 個步驟：")
                for i, step in enumerate(steps[-5:], 1):
                    desc = step['description']
                    tool = step.get('tool_name', 'None')
                    print(f"      {i}. [{tool}] {desc[:50]}")

                    # 檢查異常：單字符步驟
                    if len(desc) == 1:
                        self.issues['parser'].append(
                            f"{task_id}: 步驟 {step['step_id']} 只有單個字符：'{desc}'"
                        )

            if self.issues['parser']:
                print(f"\n✗ 發現 {len(self.issues['parser'])} 個 Parser 問題")
            else:
                print(f"\n✓ Parser 輸出檢查通過")

        except Exception as e:
            self.issues['parser'].append(f"Parser 輸出檢查失敗：{str(e)}")
            print(f"✗ Parser 輸出檢查失敗：{str(e)}")

    def diagnose_parameters(self):
        """診斷參數完整性"""
        integrated_path = self.base_dir / "integrated_109/gaia_109_tasks_v2.json"
        schema_path = self.base_dir / "tools/unified_tools_schema.json"

        try:
            with open(integrated_path, 'r') as f:
                tasks = json.load(f)

            with open(schema_path, 'r') as f:
                tools_schema = json.load(f)

            # 建立 schema 索引
            schema_index = {tool['function']['name']: tool for tool in tools_schema}

            # 統計
            total_steps = 0
            valid_steps = 0
            param_issues = []

            for task in tasks:
                for step in task['annotated_steps']:
                    tool_name = step.get('tool_name')
                    if not tool_name:
                        continue

                    total_steps += 1

                    # 檢查工具是否在 schema 中
                    if tool_name not in schema_index:
                        param_issues.append(f"{task['task_id']}: 工具 '{tool_name}' 不在 schema 中")
                        continue

                    # 檢查參數
                    tool_schema = schema_index[tool_name]
                    required = tool_schema['function']['parameters'].get('required', [])
                    provided = step.get('arguments', {})

                    missing = [p for p in required if p not in provided]

                    if missing:
                        param_issues.append(
                            f"{task['task_id']}: {tool_name} 缺少參數 {missing}"
                        )
                    else:
                        valid_steps += 1

            print(f"總工具步驟：{total_steps}")
            print(f"有效步驟：{valid_steps}")
            print(f"參數完整率：{valid_steps/total_steps*100:.1f}%")

            if param_issues:
                print(f"\n✗ 發現 {len(param_issues)} 個參數問題（顯示前 10 個）：")
                for issue in param_issues[:10]:
                    print(f"  - {issue}")
                self.issues['parameters'] = param_issues
            else:
                print(f"\n✓ 參數完整性檢查通過")

        except Exception as e:
            self.issues['parameters'].append(f"參數檢查失敗：{str(e)}")
            print(f"✗ 參數檢查失敗：{str(e)}")

    def diagnose_answer_extraction(self):
        """診斷答案提取邏輯"""
        # 比對原始驗證結果和新驗證結果
        original_validation_path = self.base_dir / "v5_original/validation_results.json"
        new_validation_path = self.base_dir / "answer_validation_report.json"

        try:
            # 載入原始驗證結果
            with open(original_validation_path, 'r') as f:
                original_results = json.load(f)

            print(f"原始驗證結果（v5）：")
            correct_count = sum(1 for r in original_results if r.get('correct'))
            total = len([r for r in original_results if r.get('predicted') is not None])
            print(f"  已執行：{total}/10 題")
            print(f"  正確：{correct_count}/{total} 題")
            print(f"  正確率：{correct_count/total*100 if total > 0 else 0:.1f}%")

            # 檢查新驗證結果
            if new_validation_path.exists():
                with open(new_validation_path, 'r') as f:
                    new_report = json.load(f)

                gaia_stats = new_report['summary']['gaia_l3']
                print(f"\n新驗證結果（answer_validator）：")
                print(f"  總題數：{gaia_stats['total']}")
                print(f"  正確：{gaia_stats['correct']}")
                print(f"  錯誤：{gaia_stats['incorrect']}")
                print(f"  正確率：{gaia_stats['accuracy']*100:.1f}%")

                # 診斷差異
                if correct_count != gaia_stats['correct']:
                    self.issues['answer_extraction'].append(
                        f"答案驗證結果不一致：原始 {correct_count} 題正確，新驗證 {gaia_stats['correct']} 題正確"
                    )
                    print(f"\n⚠️  答案驗證結果不一致！")
                    print(f"  原因可能：")
                    print(f"    1. 答案提取邏輯不同")
                    print(f"    2. 資料源不同（integrated_109 vs v5_original）")
                    print(f"    3. Parser 把答案拆成了單個字符")

        except Exception as e:
            self.issues['answer_extraction'].append(f"答案提取檢查失敗：{str(e)}")
            print(f"✗ 答案提取檢查失敗：{str(e)}")

    def diagnose_executability(self):
        """診斷執行能力"""
        integrated_path = self.base_dir / "integrated_109/gaia_109_tasks_v2.json"

        try:
            with open(integrated_path, 'r') as f:
                tasks = json.load(f)

            # 統計可執行性
            total_tasks = len(tasks)
            tasks_with_tools = 0
            tasks_with_complete_params = 0

            for task in tasks:
                has_tool_steps = False
                all_params_complete = True

                for step in task['annotated_steps']:
                    if step.get('tool_name'):
                        has_tool_steps = True

                        # 檢查參數是否包含 placeholder
                        args = step.get('arguments', {})
                        for v in args.values():
                            if isinstance(v, str) and ('待定' in v or 'placeholder' in v.lower()):
                                all_params_complete = False
                                break

                if has_tool_steps:
                    tasks_with_tools += 1

                if all_params_complete:
                    tasks_with_complete_params += 1

            print(f"總題數：{total_tasks}")
            print(f"有工具步驟：{tasks_with_tools} 題 ({tasks_with_tools/total_tasks*100:.1f}%)")
            print(f"參數完整：{tasks_with_complete_params} 題 ({tasks_with_complete_params/total_tasks*100:.1f}%)")

            potentially_executable = tasks_with_tools
            print(f"\n潛在可執行題目：{potentially_executable} 題")

            if potentially_executable < total_tasks * 0.8:
                self.issues['executability'].append(
                    f"僅 {potentially_executable}/{total_tasks} 題可能可執行 (<80%)"
                )

        except Exception as e:
            self.issues['executability'].append(f"執行能力檢查失敗：{str(e)}")
            print(f"✗ 執行能力檢查失敗：{str(e)}")

    def generate_report(self):
        """生成診斷報告"""
        print("\n" + "=" * 80)
        print("📋 診斷報告總結")
        print("=" * 80)

        # 統計問題
        total_issues = sum(len(issues) for issues in self.issues.values())

        print(f"\n發現的問題總數：{total_issues}")

        for category, issues in self.issues.items():
            if issues:
                print(f"\n【{category.upper()}】{len(issues)} 個問題：")
                for i, issue in enumerate(issues[:5], 1):
                    print(f"  {i}. {issue}")
                if len(issues) > 5:
                    print(f"  ... 還有 {len(issues) - 5} 個問題")

        # 關鍵發現
        print("\n" + "=" * 80)
        print("🔍 關鍵發現")
        print("=" * 80)

        if 'parser' in self.issues and any('單個字符' in issue for issue in self.issues['parser']):
            print("\n⚠️  **嚴重問題**：Parser 把答案步驟拆成了單個字符！")
            print("  影響：GAIA L3 的答案無法正確提取")
            print("  建議：修復 Parser 邏輯，正確處理 Annotator Steps")

        if 'answer_extraction' in self.issues:
            print("\n⚠️  **答案驗證不一致**：")
            print("  原因：integrated_109 的數據可能被 Parser 破壞")
            print("  建議：使用原始 v5_original 資料進行答案驗證")

        if total_issues == 0:
            print("\n✅ 所有檢查都通過！系統健康。")
        else:
            print(f"\n❌ 發現 {total_issues} 個問題需要修復。")

        print("\n" + "=" * 80)

        # 儲存報告
        report_path = self.base_dir / "comprehensive_diagnosis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_issues': total_issues,
                'issues_by_category': {k: len(v) for k, v in self.issues.items()},
                'detailed_issues': dict(self.issues)
            }, f, indent=2, ensure_ascii=False)

        print(f"詳細報告已儲存：{report_path}")


def main():
    base_dir = Path("/Users/chengpeici/Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/Delta_GAIA")

    diagnostics = ComprehensiveDiagnostics(base_dir)
    diagnostics.diagnose_all()


if __name__ == "__main__":
    main()
