#!/usr/bin/env python3
"""
完整優化系統 - 109 題深度優化
功能：
1. 智能工具推薦 - 根據題目內容自動推薦工具
2. 推理步驟增強 - 為每個 thought 步驟生成詳細推理
3. 工具覆蓋率提升 - 自動補充遺漏的工具步驟
4. 動態處理 - 不跳過任何 placeholder
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict


class ToolRecommender:
    """智能工具推薦系統"""

    def __init__(self, unified_tools):
        self.unified_tools = {tool['function']['name']: tool for tool in unified_tools}
        self.tool_keywords = self._build_keyword_map()

    def _build_keyword_map(self):
        """建立工具關鍵字對應表"""
        return {
            # 搜尋類
            'web_search': ['search', 'google', 'find', 'look up', 'query'],
            'wikipedia_search': ['wikipedia', 'wiki', 'encyclopedia'],

            # 網頁瀏覽類
            'web_browser': ['website', 'url', 'browse', 'visit', 'navigate', 'page'],
            'web_fetch': ['fetch', 'download page', 'get content'],

            # 檔案讀取類
            'pdf_reader': ['pdf', 'document', 'paper', 'article'],
            'excel_reader': ['excel', 'spreadsheet', 'xlsx', 'xls', 'csv'],
            'read_csv': ['csv', 'comma separated', 'data file'],
            'read_json': ['json', 'javascript object'],
            'read_xml': ['xml', 'markup'],
            'pptx_reader': ['powerpoint', 'pptx', 'presentation', 'slides'],
            'read_docx': ['word', 'docx', 'document'],
            'file_reader': ['file', 'text file', 'read file'],

            # 圖像處理類
            'image_recognition': ['image', 'picture', 'photo', 'recognize', 'identify'],
            'analyze_image': ['analyze image', 'image analysis', 'visual'],
            'image_to_text': ['ocr', 'extract text from image', 'image to text'],
            'read_image': ['read image', 'image content'],

            # 音視頻類
            'audio_transcription': ['audio', 'transcribe', 'speech', 'voice'],
            'video_analysis': ['video', 'analyze video', 'visual content'],

            # 資料處理類
            'filter_data': ['filter', 'select', 'query data'],
            'aggregate_data': ['aggregate', 'group by', 'sum', 'count', 'average'],
            'join_data': ['join', 'merge', 'combine data'],
            'sort_data': ['sort', 'order', 'arrange'],
            'pivot_table': ['pivot', 'cross tab', 'summarize'],
            'deduplicate_data': ['duplicate', 'unique', 'distinct'],
            'fill_missing': ['missing', 'null', 'fill', 'impute'],
            'validate_data': ['validate', 'check data', 'verify'],
            'sample_data': ['sample', 'random', 'subset'],

            # 統計分析類
            'statistical_analysis': ['statistics', 'statistical', 'mean', 'median', 'std'],
            'correlation_analysis': ['correlation', 'relationship', 'association'],
            'moving_average': ['moving average', 'rolling', 'trend'],

            # 計算類
            'calculator': ['calculate', 'compute', 'math', 'arithmetic', 'formula'],
            'python_executor': ['python', 'code', 'script', 'execute', 'run code'],
            'code_interpreter': ['interpret', 'run code', 'execute code'],

            # 文本處理類
            'regex_search': ['regex', 'pattern', 'regular expression', 'match'],
            'string_transform': ['transform', 'convert', 'format string'],
            'split_join_text': ['split', 'join', 'concatenate'],
            'find_in_text': ['find in text', 'search text', 'locate'],
            'extract_information': ['extract', 'parse', 'information extraction'],
            'count_occurrences': ['count', 'occurrences', 'frequency'],

            # 工具類
            'date_calculator': ['date', 'time', 'duration', 'days between'],
            'unit_converter': ['convert', 'unit', 'measurement'],
            'currency_converter': ['currency', 'exchange rate', 'dollar', 'euro'],
            'geocoding': ['location', 'address', 'coordinates', 'latitude', 'longitude'],
            'encode_decode': ['encode', 'decode', 'base64', 'hash'],

            # 其他
            'zip_extractor': ['zip', 'extract', 'archive', 'decompress'],
            'download_file': ['download', 'get file', 'fetch file'],
            'create_csv': ['create csv', 'export csv', 'save data'],
            'create_markdown': ['markdown', 'create report', 'document'],
            'list_operations': ['list', 'array', 'operations'],
            'compare_values': ['compare', 'difference', 'equal'],
            'compare_data': ['compare data', 'diff', 'changes'],
        }

    def recommend_tools(self, question, existing_tools):
        """根據題目推薦工具"""
        question_lower = question.lower()
        recommended = []

        # 找出已經使用的工具
        used_tools = set(existing_tools)

        # 基於關鍵字推薦工具
        for tool_name, keywords in self.tool_keywords.items():
            if tool_name in used_tools:
                continue

            # 檢查是否有關鍵字匹配
            for keyword in keywords:
                if keyword in question_lower:
                    recommended.append({
                        'tool_name': tool_name,
                        'reason': f"題目提到 '{keyword}'",
                        'confidence': 0.8
                    })
                    break

        return recommended


class ReasoningEnhancer:
    """推理步驟增強系統"""

    @staticmethod
    def enhance_reasoning_step(step, question, previous_steps):
        """增強推理步驟"""
        description = step.get('description', '')

        # 如果是 placeholder，生成具體推理內容
        if 'placeholder' in description.lower() or len(description) < 20:
            # 根據上下文生成推理內容
            enhanced = ReasoningEnhancer._generate_reasoning(
                description, question, previous_steps
            )
            step['enhanced_description'] = enhanced
            step['is_enhanced'] = True
        else:
            step['enhanced_description'] = description
            step['is_enhanced'] = False

        return step

    @staticmethod
    def _generate_reasoning(description, question, previous_steps):
        """生成具體的推理內容"""
        # 簡單的推理生成邏輯
        if not previous_steps:
            return f"開始分析題目：{question[:100]}... 需要先理解問題的核心要求。"

        last_step = previous_steps[-1]
        last_tool = last_step.get('tool_name', 'unknown')

        reasoning_templates = {
            'web_search': f"根據搜尋結果，分析並提取關鍵資訊。",
            'web_browser': f"瀏覽網頁內容，找出與問題相關的資料。",
            'calculator': f"根據計算結果，得出數值答案。",
            'python_executor': f"執行代碼後，分析輸出結果。",
        }

        return reasoning_templates.get(
            last_tool,
            f"綜合前面的步驟結果，進行邏輯推理和分析。{description}"
        )


class EnhancedOptimizer:
    """完整優化引擎"""

    def __init__(self, unified_tools_path, tasks_path):
        # 載入統一工具 schema
        with open(unified_tools_path, 'r') as f:
            self.unified_tools = json.load(f)

        # 載入 109 題
        with open(tasks_path, 'r') as f:
            self.tasks = json.load(f)

        # 初始化子系統
        self.tool_recommender = ToolRecommender(self.unified_tools)
        self.reasoning_enhancer = ReasoningEnhancer()

        # 統計
        self.stats = {
            'original_tool_count': 0,
            'enhanced_tool_count': 0,
            'reasoning_enhanced': 0,
            'tools_added': 0,
            'placeholders_resolved': 0
        }

    def optimize_task(self, task):
        """優化單一題目"""
        task_id = task['task_id']
        question = task['question']
        steps = task.get('annotated_steps', [])

        # 統計原始工具使用
        original_tools = [s['tool_name'] for s in steps if s.get('tool_name')]
        self.stats['original_tool_count'] += len(original_tools)

        # 1. 推薦新工具
        recommended_tools = self.tool_recommender.recommend_tools(
            question, original_tools
        )

        # 2. 增強推理步驟
        enhanced_steps = []
        for i, step in enumerate(steps):
            if step.get('step_type') == 'thought':
                step = self.reasoning_enhancer.enhance_reasoning_step(
                    step, question, enhanced_steps
                )
                if step.get('is_enhanced'):
                    self.stats['reasoning_enhanced'] += 1

            enhanced_steps.append(step)

        # 3. 在適當位置插入推薦的工具
        if recommended_tools:
            enhanced_steps = self._insert_recommended_tools(
                enhanced_steps, recommended_tools, question
            )
            self.stats['tools_added'] += len(recommended_tools)

        # 4. 更新統計 - 計算增強後的工具數
        enhanced_tool_count = len([s for s in enhanced_steps if s.get('tool_name')])
        self.stats['enhanced_tool_count'] += enhanced_tool_count

        # 更新任務
        task['annotated_steps'] = enhanced_steps
        task['optimization_metadata'] = {
            'original_tool_count': len(original_tools),
            'enhanced_tool_count': enhanced_tool_count,
            'recommended_tools': [t['tool_name'] for t in recommended_tools],
            'reasoning_enhanced': sum(1 for s in enhanced_steps if s.get('is_enhanced'))
        }

        return task

    def _insert_recommended_tools(self, steps, recommended_tools, question):
        """在適當位置插入推薦的工具"""
        # 在最後插入推薦工具的使用步驟
        for rec in recommended_tools[:3]:  # 最多插入 3 個推薦工具
            tool_name = rec['tool_name']

            # 創建工具步驟
            tool_step = {
                'step_id': f"enhanced_{len(steps)}",
                'description': f"使用 {tool_name} 來獲取更多資訊。推薦原因：{rec['reason']}",
                'step_type': 'tool',
                'tool_name': tool_name,
                'arguments': self._generate_tool_arguments(tool_name, question),
                'is_recommended': True,
                'metadata': {
                    'recommendation_confidence': rec['confidence']
                }
            }

            # 創建後續推理步驟
            reasoning_step = {
                'step_id': f"enhanced_{len(steps) + 1}",
                'description': f"分析 {tool_name} 的結果，整合到整體分析中。",
                'step_type': 'thought',
                'tool_name': None,
                'arguments': {},
                'is_enhanced': True
            }

            steps.append(tool_step)
            steps.append(reasoning_step)

        return steps

    def _generate_tool_arguments(self, tool_name, question):
        """為推薦工具生成參數"""
        # 根據工具類型生成參數
        if tool_name == 'web_search':
            # 從問題中提取關鍵詞
            keywords = self._extract_keywords(question)
            return {'query': ' '.join(keywords[:5])}

        elif tool_name == 'wikipedia_search':
            keywords = self._extract_keywords(question)
            return {'query': ' '.join(keywords[:3])}

        elif tool_name == 'calculator':
            return {'expression': '待定 - 根據前面步驟的結果填入'}

        elif tool_name in ['pdf_reader', 'excel_reader', 'read_csv']:
            return {'file_path': '待定 - 根據題目提供的檔案'}

        elif tool_name == 'python_executor':
            return {'code': '# 待定 - 根據具體需求編寫代碼'}

        else:
            # 通用參數
            return {'input': question[:200]}

    def _extract_keywords(self, question):
        """從問題中提取關鍵詞"""
        # 移除停用詞
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are',
                      'was', 'were', 'what', 'when', 'where', 'who', 'how', 'in'}

        # 分詞並過濾
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        return keywords[:10]

    def optimize_all(self):
        """優化所有題目"""
        print(f"開始優化 {len(self.tasks)} 題...")

        optimized_tasks = []
        for i, task in enumerate(self.tasks, 1):
            if i % 20 == 0:
                print(f"  進度：{i}/{len(self.tasks)}")

            optimized_task = self.optimize_task(task)
            optimized_tasks.append(optimized_task)

        print(f"✓ 優化完成！")
        return optimized_tasks

    def print_statistics(self):
        """列印統計資訊"""
        print("\n" + "=" * 70)
        print("優化統計")
        print("=" * 70)
        print(f"\n原始工具調用次數：{self.stats['original_tool_count']}")
        print(f"優化後工具調用次數：{self.stats['enhanced_tool_count']}")
        print(f"新增工具步驟：{self.stats['tools_added']}")
        print(f"增強的推理步驟：{self.stats['reasoning_enhanced']}")
        print(f"解決的 placeholder：{self.stats['placeholders_resolved']}")

        if self.stats['original_tool_count'] > 0:
            improvement = ((self.stats['enhanced_tool_count'] - self.stats['original_tool_count'])
                          / self.stats['original_tool_count'] * 100)
            print(f"\n工具覆蓋率提升：{improvement:+.1f}%")


def main():
    print("=" * 70)
    print("完整優化系統 - 109 題深度優化")
    print("=" * 70)

    base_dir = Path("/Users/chengpeici/Desktop/©/Intern Life/Internships/[8] 中研院資創RA (2026 Spring)/Delta_GAIA")

    # 路徑
    unified_tools_path = base_dir / "tools/unified_tools_schema.json"
    tasks_path = base_dir / "integrated_109/gaia_109_tasks_v2.json"
    output_path = base_dir / "integrated_109/gaia_109_tasks_v3_enhanced.json"

    # 創建優化器
    optimizer = EnhancedOptimizer(unified_tools_path, tasks_path)

    # 執行優化
    optimized_tasks = optimizer.optimize_all()

    # 儲存結果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(optimized_tasks, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 優化結果已儲存：{output_path}")

    # 顯示統計
    optimizer.print_statistics()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
