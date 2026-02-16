#!/usr/bin/env python3
import sys
import os

# 使用當前目錄
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from parser_v3_executable import ExecutablePlanParser

parser = ExecutablePlanParser(
    gaia_tasks_file=os.path.join(PROJECT_DIR, 'gaia_level3_tasks.json'),
    data_dir=os.path.join(PROJECT_DIR, 'data')
)

parser.parse_all_tasks(
    original_plans_file=os.path.join(PROJECT_DIR, 'parser_output/plans_v2.1.json'),
    output_file=os.path.join(PROJECT_DIR, 'parser_output/plans_v3_executable.json')
)
