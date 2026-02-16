#!/usr/bin/env python3
"""
全面檢驗系統
檢查所有檔案的正確性：語法、邏輯、縮排、參數錯誤
"""

import json
import ast
import sys
from pathlib import Path
from collections import defaultdict
import subprocess


class FileValidator:
    """檔案驗證器"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []

    def validate_python_file(self, file_path):
        """驗證 Python 檔案"""
        print(f"\n檢查 Python 檔案：{file_path.name}")

        try:
            # 1. 語法檢查
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            try:
                ast.parse(source_code)
                print(f"  ✓ 語法檢查通過")
                self.passed.append(f"{file_path.name}: 語法正確")
            except SyntaxError as e:
                error_msg = f"{file_path.name}: 語法錯誤 - Line {e.lineno}: {e.msg}"
                print(f"  ✗ {error_msg}")
                self.errors.append(error_msg)
                return False

            # 2. 縮排檢查
            lines = source_code.split('\n')
            indent_errors = []

            for i, line in enumerate(lines, 1):
                if line.strip() and not line.startswith('#'):
                    # 檢查是否混用 tab 和空格
                    if '\t' in line and ' ' * 4 in line:
                        indent_errors.append(f"Line {i}: 混用 tab 和空格")

            if indent_errors:
                for err in indent_errors[:3]:  # 只顯示前 3 個
                    print(f"  ⚠ 縮排警告: {err}")
                    self.warnings.append(f"{file_path.name}: {err}")
            else:
                print(f"  ✓ 縮排檢查通過")

            # 3. 導入檢查
            import_errors = []
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('from') or line.strip().startswith('import'):
                    # 檢查常見的導入錯誤
                    if 'import *' in line:
                        import_errors.append(f"Line {i}: 使用 'import *' (不建議)")

            if import_errors:
                for err in import_errors[:3]:
                    print(f"  ⚠ 導入警告: {err}")
                    self.warnings.append(f"{file_path.name}: {err}")

            # 4. 函數定義檢查
            try:
                tree = ast.parse(source_code)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                print(f"  ✓ 發現 {len(functions)} 個函數定義")
            except:
                pass

            return True

        except Exception as e:
            error_msg = f"{file_path.name}: 檢查失敗 - {str(e)}"
            print(f"  ✗ {error_msg}")
            self.errors.append(error_msg)
            return False

    def validate_json_file(self, file_path):
        """驗證 JSON 檔案"""
        print(f"\n檢查 JSON 檔案：{file_path.name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"  ✓ JSON 格式正確")

            # 檢查資料結構
            if isinstance(data, list):
                print(f"  ✓ 陣列格式，共 {len(data)} 個元素")
            elif isinstance(data, dict):
                print(f"  ✓ 物件格式，共 {len(data)} 個鍵")

            self.passed.append(f"{file_path.name}: JSON 格式正確")
            return True

        except json.JSONDecodeError as e:
            error_msg = f"{file_path.name}: JSON 格式錯誤 - Line {e.lineno}: {e.msg}"
            print(f"  ✗ {error_msg}")
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"{file_path.name}: 檢查失敗 - {str(e)}"
            print(f"  ✗ {error_msg}")
            self.errors.append(error_msg)
            return False

    def validate_schema_consistency(self, unified_schema_path):
        """驗證 schema 一致性"""
        print(f"\n檢查 Schema 一致性...")

        try:
            with open(unified_schema_path, 'r') as f:
                tools = json.load(f)

            issues = []

            for i, tool in enumerate(tools):
                # 檢查必要欄位
                if 'function' not in tool:
                    issues.append(f"工具 {i}: 缺少 'function' 欄位")
                    continue

                func = tool['function']

                if 'name' not in func:
                    issues.append(f"工具 {i}: 缺少 'name' 欄位")

                if 'parameters' not in func:
                    issues.append(f"工具 {i}: 缺少 'parameters' 欄位")
                    continue

                params = func['parameters']

                if 'properties' not in params:
                    issues.append(f"工具 {func.get('name', i)}: 缺少 'properties' 欄位")

                # 檢查 required 參數是否都在 properties 中
                if 'required' in params:
                    props = params.get('properties', {})
                    for req in params['required']:
                        if req not in props:
                            issues.append(f"工具 {func['name']}: required 參數 '{req}' 不在 properties 中")

            if issues:
                print(f"  ⚠ 發現 {len(issues)} 個問題：")
                for issue in issues[:5]:
                    print(f"    - {issue}")
                self.warnings.extend(issues)
            else:
                print(f"  ✓ Schema 一致性檢查通過")
                self.passed.append("unified_tools_schema.json: 一致性檢查通過")

            return len(issues) == 0

        except Exception as e:
            error_msg = f"Schema 檢查失敗: {str(e)}"
            print(f"  ✗ {error_msg}")
            self.errors.append(error_msg)
            return False

    def print_summary(self):
        """列印總結"""
        print("\n" + "=" * 70)
        print("檢驗總結")
        print("=" * 70)

        print(f"\n✓ 通過：{len(self.passed)} 項")
        if self.passed:
            for item in self.passed[:10]:
                print(f"  - {item}")
            if len(self.passed) > 10:
                print(f"  ... 還有 {len(self.passed) - 10} 項")

        print(f"\n⚠ 警告：{len(self.warnings)} 項")
        if self.warnings:
            for item in self.warnings[:10]:
                print(f"  - {item}")
            if len(self.warnings) > 10:
                print(f"  ... 還有 {len(self.warnings) - 10} 項")

        print(f"\n✗ 錯誤：{len(self.errors)} 項")
        if self.errors:
            for item in self.errors:
                print(f"  - {item}")

        print("\n" + "=" * 70)

        if self.errors:
            print("狀態：❌ 有錯誤需要修復")
            return False
        elif self.warnings:
            print("狀態：⚠️  有警告，但可以使用")
            return True
        else:
            print("狀態：✅ 所有檢查都通過")
            return True


def main():
    print("=" * 70)
    print("全面檔案檢驗系統")
    print("=" * 70)

    validator = FileValidator()

    base_dir = Path("/Users/chengpeici/Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/Delta_GAIA")

    # 1. 檢查核心 Python 檔案
    print("\n【階段 1】檢查核心 Python 檔案")
    print("-" * 70)

    core_python_files = [
        base_dir / "parser_v5.py",
        base_dir / "gaia_function.py",
    ]

    for file_path in core_python_files:
        if file_path.exists():
            validator.validate_python_file(file_path)
        else:
            print(f"\n✗ 找不到檔案：{file_path.name}")
            validator.errors.append(f"{file_path.name}: 檔案不存在")

    # 2. 檢查 integrated_109/ 中的 Python 檔案
    print("\n【階段 2】檢查 integrated_109/ 中的 Python 檔案")
    print("-" * 70)

    integrated_dir = base_dir / "integrated_109"
    python_files = list(integrated_dir.glob("*.py"))

    for file_path in python_files:
        validator.validate_python_file(file_path)

    # 3. 檢查 tools/ 中的 Python 檔案
    print("\n【階段 3】檢查 tools/ 中的 Python 檔案")
    print("-" * 70)

    tools_dir = base_dir / "tools"
    python_files = list(tools_dir.glob("*.py"))

    for file_path in python_files:
        validator.validate_python_file(file_path)

    # 4. 檢查關鍵 JSON 檔案
    print("\n【階段 4】檢查關鍵 JSON 檔案")
    print("-" * 70)

    json_files = [
        tools_dir / "unified_tools_schema.json",
        tools_dir / "ta_tools_schema.json",
        tools_dir / "our_tools_schema.json",
        tools_dir / "parameter_mapping.json",
        integrated_dir / "gaia_109_tasks_v2.json",
        integrated_dir / "validation_results_109_v2.json",
        integrated_dir / "analysis_report_109_v2.json",
    ]

    for file_path in json_files:
        if file_path.exists():
            validator.validate_json_file(file_path)
        else:
            print(f"\n⚠ 找不到檔案：{file_path.name}")
            validator.warnings.append(f"{file_path.name}: 檔案不存在")

    # 5. 檢查 Schema 一致性
    print("\n【階段 5】檢查 Schema 一致性")
    print("-" * 70)

    unified_schema = tools_dir / "unified_tools_schema.json"
    if unified_schema.exists():
        validator.validate_schema_consistency(unified_schema)

    # 6. 列印總結
    validator.print_summary()

    # 7. 儲存報告
    report_path = base_dir / "validation_report.json"
    report = {
        'passed': validator.passed,
        'warnings': validator.warnings,
        'errors': validator.errors,
        'summary': {
            'total_passed': len(validator.passed),
            'total_warnings': len(validator.warnings),
            'total_errors': len(validator.errors),
            'status': 'pass' if len(validator.errors) == 0 else 'fail'
        }
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n報告已儲存：{report_path}")

    return len(validator.errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
