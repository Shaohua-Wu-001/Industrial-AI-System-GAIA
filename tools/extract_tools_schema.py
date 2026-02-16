#!/usr/bin/env python3
"""
從 gaia_function.py 自動提取 43 個 tools 並生成 OpenAI function calling schema

執行：python extract_tools_schema.py
輸出：tools_schema.json
"""

import ast
import json
import inspect
from pathlib import Path
from typing import Dict, List, Any
import gaia_function


def extract_function_info(func) -> Dict[str, Any]:
    """從 function 提取資訊並生成 OpenAI schema"""

    # 取得 function 名稱
    name = func.__name__

    # 取得 docstring
    doc = func.__doc__ or ""

    # 提取完整描述（取前3行或到第一個空行）
    doc_lines = [line.strip() for line in doc.strip().split('\n')]
    description_parts = []
    for line in doc_lines:
        if not line or line.startswith('Args:') or line.startswith('Parameters:') or line.startswith('Returns:'):
            break
        description_parts.append(line)
    description = ' '.join(description_parts) if description_parts else f"Execute {name}"

    # 解析參數說明（簡單版）
    param_descriptions = {}
    if 'Args:' in doc or 'Parameters:' in doc:
        # 嘗試解析參數說明
        in_params = False
        for line in doc_lines:
            if 'Args:' in line or 'Parameters:' in line:
                in_params = True
                continue
            if in_params:
                if line.startswith('Returns:') or line.startswith('Raises:'):
                    break
                # 嘗試匹配 "param_name: description" 或 "param_name (type): description"
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        param_part = parts[0].strip()
                        desc_part = parts[1].strip()
                        # 移除類型註解 (如果有)
                        if '(' in param_part:
                            param_part = param_part.split('(')[0].strip()
                        param_descriptions[param_part] = desc_part

    # 取得參數
    sig = inspect.signature(func)
    params = sig.parameters

    # 建立 parameters schema
    properties = {}
    required = []

    for param_name, param in params.items():
        # 取得類型提示
        annotation = param.annotation

        # 預設值
        has_default = param.default != inspect.Parameter.empty

        # 根據類型建立 schema
        if annotation == str or annotation == inspect.Parameter.empty:
            param_type = "string"
        elif annotation == int:
            param_type = "integer"
        elif annotation == float:
            param_type = "number"
        elif annotation == bool:
            param_type = "boolean"
        elif annotation == list or annotation == List:
            param_type = "array"
        elif annotation == dict or annotation == Dict:
            param_type = "object"
        else:
            # 處理 Optional, Union 等
            param_type = "string"  # 預設

        # 使用解析的描述，如果沒有則用預設
        param_desc = param_descriptions.get(param_name, f"The {param_name} parameter")

        properties[param_name] = {
            "type": param_type,
            "description": param_desc
        }

        if not has_default:
            required.append(param_name)

    # 建立 OpenAI function schema
    schema = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

    return schema


def main():
    # 排除內部輔助函數（以 _ 開頭）
    exclude = {
        '_keyify', '_check_int_size', '_is_within_directory',
        '_is_zipinfo_symlink', '_is_domain_allowed', '_is_safe_url',
        '_safe_extract_zip', '_create_safe_session', '_build_line_index',
        '_find_line_number', '_rankdata', 'eval_node', 'uniq', 'element_to_dict'
    }

    # 取得所有 public functions
    all_funcs = [
        (name, obj) for name, obj in inspect.getmembers(gaia_function)
        if inspect.isfunction(obj) and not name.startswith('_')
    ]

    # 過濾掉巢狀函數
    tools = []
    tool_names = []

    for name, func in all_funcs:
        if name in exclude:
            continue
        if name in tool_names:
            continue

        try:
            schema = extract_function_info(func)
            tools.append(schema)
            tool_names.append(name)
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name}: {e}")

    print(f"\n總共提取 {len(tools)} 個 tools")

    # 儲存
    output_file = "tools_schema.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tools, f, indent=2, ensure_ascii=False)

    print(f"已儲存至：{output_file}")

    # 同時生成 tool_name → function 的映射
    tool_map = {name: name for name in tool_names}

    with open("tools_mapping.json", 'w', encoding='utf-8') as f:
        json.dump(tool_map, f, indent=2, ensure_ascii=False)

    print(f"映射檔已儲存至：tools_mapping.json")

    # 顯示統計
    print(f"\n工具列表：")
    for i, name in enumerate(tool_names, 1):
        print(f"  {i:2d}. {name}")


if __name__ == "__main__":
    main()
