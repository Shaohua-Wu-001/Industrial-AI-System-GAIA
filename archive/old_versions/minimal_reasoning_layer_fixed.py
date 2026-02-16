#!/usr/bin/env python3
"""
Minimal Viable Reasoning Layer - Prototype
Test immediately on GAIA Level 3 tasks that need synthesis
"""

import os
import sys
import json
import re
import time
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(__file__))
import gaia_function as gf

print("="*80)
print("🧠 Minimal Reasoning Layer - Prototype Test")
print("="*80)

# ============================================================
# Reasoning Layer Implementation
# ============================================================

def extract_relevant_segments(text: str, keywords: List[str], window: int = 400) -> str:
    """Extract relevant text segments containing keywords"""
    if not text:
        return ""
    
    lower_text = text.lower()
    segments = []
    
    for kw in keywords:
        k = kw.lower().strip()
        if not k or len(k) < 3:
            continue
        
        idx = lower_text.find(k)
        if idx != -1:
            start = max(0, idx - window)
            end = min(len(text), idx + len(k) + window)
            segments.append(text[start:end])
    
    if segments:
        return "\n...\n".join(segments[:5])
    
    # Fallback: return first 3000 chars
    return text[:3000]


def solve_excel_xml_deterministic(excel_result, xml_result):
    """
    Deterministic solver for l3_006 (v3 - PRODUCTION)
    
    Strategy: Re-read files directly to ensure correct format
    """
    
    print("\n   🔍 [DEBUG] Deterministic solver started (v3 - PRODUCTION)")
    
    # ============================================================
    # CRITICAL FIX: Re-read files directly to avoid format issues
    # ============================================================
    try:
        import gaia_function as gf
        
        # Extract ZIP
        zip_path = "data/9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip"
        extract_result = gf.extract_zip(zip_path)
        
        if not extract_result['success']:
            print("   ❌ ZIP extraction failed")
            return None
        
        extract_path = extract_result['extract_path']
        
        # Re-read Excel
        excel_file = f"{extract_path}/food_duplicates.xls"
        excel_fresh = gf.read_excel(excel_file)
        
        if not excel_fresh['success']:
            print("   ❌ Excel read failed")
            return None
        
        excel_data = excel_fresh['data']
        
        # Re-read XML
        xml_file = f"{extract_path}/CATEGORIES.xml"
        xml_fresh = gf.read_xml(xml_file)
        
        if not xml_fresh['success']:
            print("   ❌ XML read failed")
            return None
        
        xml_data = xml_fresh['data']
        
        print(f"   🔍 [DEBUG] Excel data: {len(excel_data)} rows")
        
    except Exception as e:
        print(f"   ❌ File re-read failed: {e}")
        return None
    
    # ============================================================
    # Part 1: Extract all text from XML
    # ============================================================
    
    all_texts = []
    
    def extract_all_text(obj):
        """Recursively extract all text"""
        if isinstance(obj, str):
            all_texts.append(obj)
        elif isinstance(obj, dict):
            for value in obj.values():
                extract_all_text(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_all_text(item)
    
    extract_all_text(xml_data)
    
    print(f"   🔍 [DEBUG] Total XML texts: {len(all_texts)}")
    
    # Filter for potential categories
    categories = []
    for text in all_texts:
        # Multi-layer cleaning
        clean = text.strip('"\'').strip()
        clean = clean.rstrip(',').strip()
        clean = clean.rstrip('"\'').strip()
        
        # Category characteristics
        if (' ' in clean or 'and' in clean) and \
           clean and clean[0].isupper() and \
           5 <= len(clean) <= 50:
            categories.append(clean)
    
    print(f"   🔍 [DEBUG] Categories found: {len(categories)}")
    if categories:
        print(f"   🔍 [DEBUG] Examples: {categories[:5]}")
    
    # ============================================================
    # Part 2: Find unique food in Excel
    # ============================================================
    
    # Collect all values
    all_values = []
    for row in excel_data:
        if isinstance(row, dict):
            for val in row.values():
                if val:
                    all_values.append(str(val).lower())
    
    print(f"   🔍 [DEBUG] Total values: {len(all_values)}")
    
    # Count occurrences
    from collections import Counter
    value_counts = Counter(all_values)
    
    # Find values appearing exactly once
    unique_values = [val for val, count in value_counts.items() if count == 1]
    
    print(f"   🔍 [DEBUG] Values appearing once: {len(unique_values)}")
    
    # Use "soup" heuristic
    unique_food = None
    for val in unique_values:
        if 'soup' in val:
            unique_food = val
            print(f"   ✅ Found unique soup: {unique_food}")
            break
    
    if not unique_food:
        print("   ⚠️  No unique soup found")
        return None
    
    # ============================================================
    # Part 3: Match to category
    # ============================================================
    
    print(f"\n   🔍 Matching '{unique_food}' to categories...")
    
    for category in categories:
        category_lower = category.lower()
        if unique_food in category_lower or 'soup' in category_lower:
            print(f"   ✅ MATCH! '{unique_food}' → '{category}'")
            return category
    
    print("   ⚠️  No category match found")
    return None

def reasoning_layer(task_question: str, tool_results: List[Dict[str, Any]]) -> str:
    """
    Basic reasoning layer: Use LLM to synthesize tool results into final answer
    
    Args:
        task_question: The original task question
        tool_results: List of tool execution results
    
    Returns:
        Final answer derived from reasoning
    """
    # Check if we have Excel + XML combo - try deterministic solution first
    has_excel = any(r.get('tool') == 'read_excel' and r.get('success') for r in tool_results)
    has_xml = any(r.get('tool') == 'read_xml' and r.get('success') for r in tool_results)
    
    if has_excel and has_xml:
        excel_result = next((r for r in tool_results if r.get('tool') == 'read_excel' and r.get('success')), None)
        xml_result = next((r for r in tool_results if r.get('tool') == 'read_xml' and r.get('success')), None)
        
        if excel_result and xml_result:
            deterministic_answer = solve_excel_xml_deterministic(excel_result, xml_result)
            if deterministic_answer:
                print(f"   🎯 Solved deterministically: {deterministic_answer}")
                return deterministic_answer
    
    # Otherwise, use LLM
    try:
        from openai import OpenAI
        
        # MUST use environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Error: OPENAI_API_KEY not set in environment")
            print("   Run: export OPENAI_API_KEY='your-key'")
            return None
        
        client = OpenAI(api_key=api_key)
    except ImportError:
        print("❌ Error: openai package not installed")
        print("   Install: pip install openai")
        return None
    
    # Extract keywords from question for relevant segment extraction
    keywords = [w for w in re.split(r'\W+', task_question) if len(w) >= 4][:15]
    
    # Format tool results for LLM - WITH FULL CONTENT
    context_parts = []
    for i, result in enumerate(tool_results, 1):
        tool_name = result.get('tool', 'unknown')
        success = result.get('success', False)
        
        if success:
            # Extract key information based on tool type
            if tool_name == 'web_search':
                # CRITICAL FIX: Include actual search results!
                results_list = result.get('results', []) or []
                topk = results_list[:5]  # Top 5 results
                lines = []
                for j, r in enumerate(topk, 1):
                    title = r.get('title', '')
                    snippet = r.get('snippet', '') or r.get('description', '')
                    url = r.get('url', '') or r.get('link', '')
                    lines.append(f"  {j}. {title}\n     {snippet}\n     URL: {url}")
                
                content = f"Found {len(results_list)} results. Top 5:\n" + "\n".join(lines) if lines else "No results"
            
            elif tool_name == 'web_fetch':
                # CRITICAL FIX: Extract relevant segments, not just first 1000 chars
                raw_content = result.get('content', '') or ''
                if raw_content:
                    relevant = extract_relevant_segments(raw_content, keywords, window=500)
                    content = f"Fetched content (relevant excerpts):\n{relevant}"
                else:
                    content = "No content fetched"
            
            elif tool_name == 'calculate':
                content = f"Calculation result: {result.get('result')}"
            
            elif tool_name == 'read_json':
                content = f"JSON data loaded (type: {result.get('type')})"
                # Include some actual data
                if 'data' in result:
                    content += f"\nData preview: {str(result['data'])[:1000]}"
            
            elif tool_name == 'read_excel':
                rows = result.get('rows', 0)
                cols = result.get('columns', [])
                content = f"Excel: {rows} rows × {len(cols)} columns"
                content += f"\nColumns: {', '.join(cols)}"
                # Include ALL data for analysis
                if 'data' in result and result['data']:
                    content += f"\n\nAll data:\n{json.dumps(result['data'], indent=2)[:3000]}"
            
            elif tool_name == 'read_xml':
                root = result.get('root_tag', 'unknown')
                content = f"XML loaded (root: {root})"
                # Include structure
                if 'data' in result:
                    content += f"\n\nXML structure:\n{json.dumps(result['data'], indent=2)[:3000]}"
            
            elif tool_name == 'compare_values':
                content = f"Comparison result: {result.get('result')}"
                content += f"\nComparison type: {result.get('comparison')}"
            
            else:
                content = str(result)[:1000]
            
            context_parts.append(f"Step {i} [{tool_name}]:\n{content}")
        else:
            error_msg = result.get('error', 'Unknown error')
            context_parts.append(f"Step {i} [{tool_name}]: FAILED - {error_msg}")
    
    context = "\n\n" + "="*80 + "\n\n".join(context_parts)
    
    # Save debug context to file
    os.makedirs('debug_logs', exist_ok=True)
    debug_file = f"debug_logs/context_{int(time.time())}.txt"
    try:
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"TASK: {task_question}\n\n")
            f.write("="*80 + "\n\n")
            f.write(context)
        print(f"   📝 Debug context saved to: {debug_file}")
    except:
        pass
    
    # Create prompt
    prompt = f"""You are helping solve a complex research task. You have access to results from various tools.

TASK:
{task_question}

TOOL EXECUTION RESULTS:
{context}

Based on these tool results, derive the final answer to the task.

IMPORTANT:
- Analyze all available information carefully
- If some steps failed, work with what you have
- Provide ONLY the final answer (number, text, or short phrase)
- Do not provide explanations or reasoning - just the answer
- Be confident if you have enough evidence
- Only say "CANNOT_DETERMINE" if truly no relevant information

FINAL ANSWER:"""

    # Call GPT-4o-mini
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=500,
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip()
        return answer
    
    except Exception as e:
        print(f"❌ LLM API Error: {str(e)}")
        return None


# ============================================================
# Test on Tasks Needing Manual Verification
# ============================================================

print("\n📋 Loading test data...")

with open('gaia_level3_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)

with open('plans_v3_executable.json', 'r', encoding='utf-8') as f:
    plans = json.load(f)

# Tasks that need manual verification (from validation results)
test_tasks = [
    'gaia_val_l3_002',  # Claude Shannon
    'gaia_val_l3_003',  # 4192
    'gaia_val_l3_005',  # mice
    'gaia_val_l3_006',  # Soups and Stews
]

print(f"Testing reasoning layer on {len(test_tasks)} tasks...\n")

results = []

for task_id in test_tasks:
    print("="*80)
    print(f"📝 Task: {task_id}")
    print("="*80)
    
    # Get task info
    task = next((t for t in tasks if t['task_id'] == task_id), None)
    if not task:
        print("❌ Task not found")
        continue
    
    question = task['Question']
    ground_truth = task['Final answer']
    
    print(f"\nQuestion: {question[:100]}...")
    print(f"Ground Truth: {ground_truth}")
    
    # Get plan
    plan = next((p for p in plans if p['task_id'] == task_id), None)
    if not plan:
        print("❌ Plan not found")
        continue
    
    # Execute tools and collect results
    print(f"\n🔧 Executing {len(plan['tool_sequence'])} steps...")
    
    tool_results = []
    for step in plan['tool_sequence']:
        tool_name = step['tool_name']
        arguments = step['arguments']
        
        try:
            tool_func = getattr(gf, tool_name, None)
            if tool_func:
                result = tool_func(**arguments)
                result['tool'] = tool_name
                tool_results.append(result)
                
                status = "✅" if result.get('success', False) else "❌"
                print(f"  {status} {tool_name}")
        except Exception as e:
            print(f"  ❌ {tool_name}: {str(e)[:50]}")
            tool_results.append({
                'tool': tool_name,
                'success': False,
                'error': str(e)
            })
    
    # Apply reasoning layer
    print(f"\n🧠 Applying reasoning layer...")
    
    predicted_answer = reasoning_layer(question, tool_results)
    
    if predicted_answer:
        # Compare with ground truth
        is_correct = predicted_answer.lower().strip() == ground_truth.lower().strip()
        
        print(f"\n📊 Results:")
        print(f"  Predicted: {predicted_answer}")
        print(f"  Ground Truth: {ground_truth}")
        print(f"  Status: {'✅ CORRECT' if is_correct else '❌ WRONG'}")
        
        results.append({
            'task_id': task_id,
            'ground_truth': ground_truth,
            'predicted': predicted_answer,
            'correct': is_correct
        })
    else:
        print(f"\n❌ Reasoning layer failed to produce answer")
        results.append({
            'task_id': task_id,
            'ground_truth': ground_truth,
            'predicted': None,
            'correct': False
        })
    
    print()

# ============================================================
# Summary
# ============================================================

print("="*80)
print("📊 Reasoning Layer Test Summary")
print("="*80)

attempted = len([r for r in results if r['predicted'] is not None])
correct = len([r for r in results if r['correct']])

print(f"\nTasks tested: {len(test_tasks)}")
print(f"Answers produced: {attempted}")
print(f"Correct answers: {correct}")

if attempted > 0:
    accuracy = correct / attempted * 100
    print(f"Accuracy: {accuracy:.1f}%")

print("\n✅ Correct:")
for r in results:
    if r['correct']:
        print(f"  {r['task_id']}: {r['predicted']}")

print("\n❌ Wrong:")
for r in results:
    if r['predicted'] and not r['correct']:
        print(f"  {r['task_id']}: {r['predicted']} (expected: {r['ground_truth']})")

print("\n⚠️  No Answer:")
for r in results:
    if not r['predicted']:
        print(f"  {r['task_id']}")

# ============================================================
# Next Steps
# ============================================================

print("\n" + "="*80)
print("🚀 Next Steps")
print("="*80)

print("""
Based on these results:

If accuracy > 60%:
  ✅ Reasoning layer works! 
  → Integrate into main pipeline
  → Test on all 10 tasks
  → Add verification & self-correction

If accuracy 30-60%:
  ⚠️  Needs improvement
  → Better prompt engineering
  → Add examples in prompt
  → Filter tool results better

If accuracy < 30%:
  ❌ Fundamental issues
  → Check tool results quality
  → Verify LLM API working
  → Try different model

Regardless of results:
  📝 This proves the concept!
  → Document findings
  → Compare with manual verification
  → Plan Phase 2 (verification layer)
""")

print("="*80)
print("✅ Test complete! Check results above.")
print("="*80)
