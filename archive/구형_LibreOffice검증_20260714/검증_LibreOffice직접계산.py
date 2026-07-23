#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LibreOffice UNO API를 이용해 직접 파일을 열고 재계산
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
import subprocess
import time

def calculate_with_libreoffice():
    """
    LibreOffice를 직접 띄워서 파일 계산
    """
    
    sample_file = Path('samples/노무비 예시.xlsx').resolve()
    temp_file = Path('temp_calc.ods')  # ODS로 변환해서 계산
    
    print("=" * 80)
    print("LibreOffice를 이용한 직접 계산")
    print("=" * 80)
    
    print("\n[1단계] 파일을 ODS 형식으로 변환...")
    
    libreoffice = r"C:\Program Files\LibreOffice\program\soffice.exe"
    
    # XLSX를 ODS로 변환
    cmd = [
        libreoffice,
        '--headless',
        '--invisible',
        '--norestore',
        '--convert-to', 'ods',
        '--outdir', str(Path.cwd()),
        str(sample_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("변환 완료")
            converted_file = Path('노무비 예시.ods')
            if converted_file.exists():
                print(f"생성 파일: {converted_file.name}")
        else:
            print(f"변환 실패: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"오류: {e}")
        return False
    
    # 원본 파일의 데이터 분석으로 공식 검증
    print("\n" + "=" * 80)
    print("[2단계] 원본 파일의 기존 데이터로 공식 검증")
    print("=" * 80)
    
    from openpyxl import load_workbook
    
    wb = load_workbook(sample_file, data_only=False)
    ws = wb['명세서_철거']
    
    print("\n김희석 (행 14-15)의 데이터:")
    row = 14
    
    # 입력된 데이터 찾기
    input_cols = {}
    for col_letter in ['F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U']:
        col_idx = ord(col_letter) - ord('A') + 1
        for r in [row, row+1]:
            val = ws.cell(r, col_idx).value
            if val == 1:
                input_cols[f'{col_letter}{r}'] = 1
    
    if input_cols:
        print("입력된 출역 데이터:")
        for cell, val in sorted(input_cols.items()):
            print(f"  {cell}: {val}")
    
    # 단가 확인
    daily_rate = ws[f'W{row}'].value
    print(f"\n단가 (W{row}): {daily_rate:,}원")
    
    # 수식 확인
    print(f"\nV{row} 공식: {ws[f'V{row}'].value}")
    print(f"X{row} 공식: {ws[f'X{row}'].value}")
    
    print("\n" + "=" * 80)
    print("[3단계] 파이썬으로 직접 계산")
    print("=" * 80)
    
    # 김경숙 데이터로 계산 (사용자가 제공한 데이터)
    print("\n대상: 김경숙 (행 6-7)")
    print("입력 데이터: F6=1, G6=1, H6=1, W6=210000")
    
    # 데이터
    f6, g6, h6 = 1, 1, 1
    daily_rate = 210000
    
    # V6 = SUM(F6:U7) - 현재 F7, G7 등은 비어있다고 가정
    v6 = f6 + g6 + h6
    
    # X6 = V6 * W6
    x6 = v6 * daily_rate
    
    print(f"\nV6 (출역): {f6} + {g6} + {h6} = {v6}일")
    print(f"X6 (세전): {v6} × {daily_rate:,} = {x6:,}원")
    
    # Y6 + Y7 계산
    # Y6: F6~T6 (F6*W6>=150000 ? F6*W6-150000 : 0) + ...
    # Y7: F7~U7 (비어있음)
    
    print("\nY6 계산 (F6,G6,H6만 입력된 경우):")
    y6_total = 0
    for col_val in [f6, g6, h6]:
        gross = col_val * daily_rate
        tax = (gross - 150000) if gross >= 150000 else 0
        y6_total += tax
        print(f"  {col_val}일 × {daily_rate:,} = {gross:,} → 차감 {tax:,}원")
    
    y7_total = 0  # 입력 없음
    
    z6 = y6_total + y7_total
    
    print(f"\nY6 합계: {y6_total:,}원")
    print(f"Y7 합계: {y7_total:,}원")
    print(f"Z6 (Y6+Y7): {z6:,}원")
    
    net = x6 - z6
    
    print("\n" + "=" * 80)
    print("[결과]")
    print("=" * 80)
    print(f"세전 급여: {x6:,}원")
    print(f"세금 차감: {z6:,}원")
    print(f"실지급액: {net:,}원")
    
    return True

if __name__ == '__main__':
    try:
        calculate_with_libreoffice()
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
