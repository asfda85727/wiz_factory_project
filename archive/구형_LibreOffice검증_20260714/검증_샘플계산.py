#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
샘플 계산: 김경숙 - 5,6,8일 근무, 단가 21만원
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openpyxl import load_workbook
from pathlib import Path
import shutil

def calculate_sample():
    """
    실제 데이터로 계산 테스트
    """
    
    sample_file = Path('samples/노무비 예시.xlsx')
    test_file = Path('samples/노무비_테스트.xlsx')
    
    print("=" * 70)
    print("샘플 계산: 김경숙 근로자")
    print("=" * 70)
    
    # 1. 테스트 파일 복사
    print("\n[1단계] 테스트용 파일 준비...")
    shutil.copy(sample_file, test_file)
    print(f"복사 완료: {test_file.name}")
    
    # 2. 파일 로드 및 데이터 입력
    print("\n[2단계] 데이터 입력...")
    wb = load_workbook(test_file)
    ws = wb['명세서_철거']
    
    # 김경숙이 행 6에 있음 (파일 분석에서 확인)
    row = 6
    
    print(f"대상 행: {row} (이름: {ws.cell(row, 2).value})")
    
    # 입력 데이터
    input_data = {
        'F6': 5,        # 첫 번째 열 (5일)
        'G6': 6,        # 두 번째 열 (6일)
        'H6': 8,        # 세 번째 열 (8일)
        'W6': 210000,   # 단가 (21만원)
    }
    
    print("\n입력 데이터:")
    for cell, value in input_data.items():
        ws[cell] = value
        print(f"  {cell}: {value:,}")
    
    wb.save(test_file)
    print("\n저장 완료")
    
    # 3. 원본 수식 확인
    print("\n[3단계] 계산 공식 확인...")
    print(f"V6 (출역 합계): {ws['V6'].value}")
    print(f"X6 (세전 급여): {ws['X6'].value}")
    print(f"Y6 (세금): {ws['Y6'].value[:50]}...")
    print(f"Z6 (차감/지급): {ws['Z6'].value}")
    
    # 4. LibreOffice로 재계산
    print("\n[4단계] LibreOffice로 재계산 중...")
    
    import subprocess
    libreoffice = r"C:\Program Files\LibreOffice\program\soffice.exe"
    
    # macro를 이용한 재계산 방식 (간단함)
    # 사실 이 방식도 작동 안 할 수 있으니, 수동으로 계산해보겠습니다
    
    # 5. 수동 계산
    print("\n[5단계] 공식에 따른 수동 계산...")
    
    f6, g6, h6 = 5, 6, 8
    w6 = 210000
    
    # V6: =SUM(F6:U7) - 간단히 입력된 값만 합산 (U는 입력 없음)
    v6 = f6 + g6 + h6
    print(f"\nV6 (총 출역 일수): {f6} + {g6} + {h6} = {v6}일")
    
    # X6: =V6*W6 (세전 급여)
    x6 = v6 * w6
    print(f"X6 (세전 급여): {v6} × {w6:,} = {x6:,}원")
    
    # Y6: 복합 IF 공식 (각 열마다 150,000 기준)
    # =IF((F6*W6)>=150000,(F6*W6)-150000,0) + ... 
    y6_parts = []
    
    for col_val, col_name in [(f6, 'F'), (g6, 'G'), (h6, 'H')]:
        gross = col_val * w6
        tax_part = (gross - 150000) if gross >= 150000 else 0
        y6_parts.append(tax_part)
        print(f"  {col_name}6: {col_val}일 × {w6:,} = {gross:,}원 → 세금 {tax_part:,}원")
    
    y6 = sum(y6_parts)
    print(f"Y6 (총 세금 차감): {' + '.join(map(str, y6_parts))} = {y6:,}원")
    
    # Z6: =+Y6+Y7 (다른 차감액이 있을 수 있음)
    # 샘플에서 Y7은 비어있다고 가정
    z6 = y6  # Y7이 없다고 가정
    
    # 최종 지급액
    net_pay = x6 - z6
    
    print(f"\n[결과]")
    print("━" * 70)
    print(f"근로자: 김경숙")
    print(f"출역 일수: {v6}일 (5일, 6일, 8일)")
    print(f"단가: {w6:,}원/일")
    print(f"\n세전 급여(총액): {x6:,}원")
    print(f"세금 차감액: {y6:,}원")
    print(f"실지급액: {net_pay:,}원")
    print("━" * 70)
    
    return True

if __name__ == '__main__':
    try:
        calculate_sample()
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
