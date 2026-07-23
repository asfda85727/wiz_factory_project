#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Y6 공식의 정확한 내용 추출 및 검증
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openpyxl import load_workbook
from pathlib import Path

sample_file = Path('samples/노무비 예시.xlsx')

print("=" * 80)
print("Y6 공식 정확한 내용 추출")
print("=" * 80)

wb = load_workbook(sample_file, data_only=False)
ws = wb['명세서_철거']

print(f"\nY6 전체 공식:")
print(f"{ws['Y6'].value}")

print("\n" + "=" * 80)
print("Y6 공식 길이 및 구조 분석")
print("=" * 80)

y6_formula = ws['Y6'].value
print(f"\n공식 길이: {len(y6_formula)} 자")
print(f"\n첫 200자: {y6_formula[:200]}")
print(f"\n마지막 200자: {y6_formula[-200:]}")

# 공식에서 특징 찾기
print("\n" + "=" * 80)
print("공식 특징 분석")
print("=" * 80)

if 'IF' in y6_formula:
    print("✓ IF 함수 포함")

if '150000' in y6_formula:
    print("✓ 150000 값 포함")

if 'SUM' in y6_formula:
    print("✓ SUM 함수 포함")

# IF의 개수 세기
if_count = y6_formula.count('IF(')
print(f"✓ IF 함수 개수: {if_count}개")

print("\n" + "=" * 80)
print("Z6 공식도 확인")
print("=" * 80)

print(f"\nZ6 공식: {ws['Z6'].value}")

print("\n" + "=" * 80)
print("전체 수식 목록 (Y, Z 행 관련)")
print("=" * 80)

for row_idx in [6, 7]:
    for col_idx in range(1, 30):  # A~AD
        cell = ws.cell(row_idx, col_idx)
        if cell.data_type == 'f':  # 수식 셀
            col_letter = cell.column_letter
            print(f"\n{col_letter}{row_idx}: {cell.value[:100]}")
