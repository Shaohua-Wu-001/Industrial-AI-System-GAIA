#!/usr/bin/env python3
"""
分析助教的工具 vs 我們的工具
找出雷同的部分，決定使用哪個
"""

import json

# 讀取助教的工具（從第一題中提取）
with open('../LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl', 'r') as f:
    first_task = json.loads(f.readline())
    ta_tools = first_task['tool_environment']

# 讀取我們的工具
with open('tools_schema.json', 'r') as f:
    our_tools = json.load(f)

print("=== 工具對比分析 ===\n")

# 建立我們的工具名稱列表
our_tool_names = {tool['function']['name'] for tool in our_tools}

# 建立助教的工具名稱列表
ta_tool_names = {tool['tool_id'] for tool in ta_tools}

print(f"助教的工具數：{len(ta_tool_names)}")
print(f"我們的工具數：{len(our_tool_names)}")
print()

# 顯示助教的所有工具及其 schema
print("助教的工具詳細列表：\n")
for i, tool in enumerate(ta_tools, 1):
    print(f"{i:2d}. {tool['tool_id']}")
    print(f"    描述：{tool['description']}")
    print(f"    參數：")
    for arg in tool['arguments_schema']:
        req = '必要' if arg.get('required', False) else '可選'
        print(f"      - {arg['name']} ({arg['type']}, {req})")
    print()

# 分析雷同和差異
print("=" * 70)
print("工具雷同分析")
print("=" * 70)

# 定義可能的對應關係
potential_matches = {
    'web_search': 'web_search',
    'calculator': 'calculate',
    'pdf_reader': 'read_pdf',
    'excel_reader': 'read_excel',
    'zip_extractor': 'extract_zip',
    'file_reader': 'read_text_file',
    'web_browser': 'web_fetch',  # 功能相近
    'download_file': 'web_fetch',  # 功能相近
    'python_executor': None,  # 我們沒有
    'pptx_reader': 'read_docx',  # 功能相近
    'audio_transcription': None,  # 我們沒有
    'image_recognition': 'image_to_text',  # 功能相近
    'video_analysis': 'analyze_image',  # 功能相近
    'reasoning': None,  # 特殊步驟
    'submit_final_answer': None,  # 特殊步驟
    'code_interpreter': None  # 我們沒有
}

print("\n✓ 雷同的工具（可以用助教的取代）：")
overlap_tools = []
for ta_tool, our_tool in potential_matches.items():
    if our_tool and our_tool in our_tool_names:
        overlap_tools.append((ta_tool, our_tool))
        status = "完全相同" if ta_tool == our_tool else "功能相近"
        print(f"  • {ta_tool:25s} ≈ {our_tool:25s} [{status}]")

print(f"\n✗ 我們沒有的工具（需要從助教那邊補充）：")
missing_tools = []
for ta_tool, our_tool in potential_matches.items():
    if our_tool is None and ta_tool not in ['reasoning', 'submit_final_answer']:
        missing_tools.append(ta_tool)
        print(f"  • {ta_tool}")

print(f"\n+ 我們有但助教沒有的工具（可以保留）：")
# 找出我們有但助教沒有的
matched_our_tools = set(potential_matches.values())
our_extra = our_tool_names - matched_our_tools - {None}

print(f"  總共 {len(our_extra)} 個額外工具")
for i, tool in enumerate(sorted(our_extra), 1):
    print(f"  {i:2d}. {tool}")

# 總結
print("\n" + "=" * 70)
print("建議方案")
print("=" * 70)
print(f"""
1. **使用助教的工具取代雷同的工具**（{len(overlap_tools)} 個）
   - 優點：助教的 schema 更詳細，有完整的 arguments_schema
   - 做法：直接使用助教的 tool_environment

2. **補充我們缺少的工具**（{len(missing_tools)} 個）
   - 需要實作：{', '.join(missing_tools)}
   - 優先級：python_executor > code_interpreter > audio_transcription

3. **保留我們獨有的工具**（{len(our_extra)} 個）
   - 這些工具提供了更細緻的功能
   - 可以與助教的工具合併成一個完整的 tools_schema

**最終方案：合併兩邊的工具，建立統一的 tools_schema**
""")

print(f"\n預估最終工具數：{len(ta_tool_names)} (助教) + {len(our_extra)} (我們獨有) = {len(ta_tool_names) + len(our_extra)} 個")
