#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 계산: 김경숙 - 2026년 6월, 5일, 6일, 8일 근무, 단가 21만원
주민번호로부터 나이 추출, 파일의 실제 수식 바탕으로 계산
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openpyxl import load_workbook
from pathlib import Path
from datetime import datetime

def extract_age_from_rrn(rrn_str):
    """
    주민등록번호에서 나이 계산
    rrn_str: "601021-2630411" 형태
    """
    if not rrn_str or '-' not in rrn_str:
        return None
    
    try:
        front, back = rrn_str.split('-')
        year_str = front[:2]
        month_str = front[2:4]
        day_str = front[4:6]
        gender = back[0]  # 1,2,3,4
        
        # 생년 계산 (1-4는 1900~2099)
        if gender in ['1', '2']:  # 1900~1999
            birth_year = 1900 + int(year_str)
        else:  # 3,4는 2000~2099
            birth_year = 2000 + int(year_str)
        
        current_year = datetime.now().year
        age = current_year - birth_year
        
        return age, birth_year, month_str, day_str
    except:
        return None

def calculate_detailed():
    """
    파일의 실제 수식을 기반으로 계산
    """
    
    sample_file = Path('samples/노무비 예시.xlsx')
    
    print("=" * 80)
    print("실제 계산: 김경숙 - 2026년 6월 근무")
    print("=" * 80)
    
    # 1. 파일에서 김경숙 정보 추출
    print("\n[1단계] 근로자 정보 추출...")
    wb = load_workbook(sample_file, data_only=False)
    ws = wb['명세서_철거']
    
    row = 6
    name = ws.cell(row, 2).value  # B6
    rrn = ws.cell(row, 3).value   # C3에서 주민번호 앞자리
    
    print(f"이름: {name}")
    print(f"주민번호: {rrn}")
    
    # 주민번호에서 뒷자리 추출 (C6에 있음)
    rrn_back = ws.cell(row, 3).value  # 실제로는 두 개 셀에 나뉨
    
    # 파일 보기
    print(f"\nC6 값: {ws['C6'].value}")
    print(f"C7 값: {ws['C7'].value}")
    
    # 주민번호 합치기: 601021-2630411
    full_rrn = "601021-2630411"  # 파일에서 본 정보
    
    age_info = extract_age_from_rrn(full_rrn)
    if age_info:
        age, birth_year, month, day = age_info
        print(f"\n생년월일: {birth_year}년 {month}월 {day}일")
        print(f"현재 나이: {age}세")
    
    # 2. 근무 데이터 설정
    print("\n[2단계] 근무 데이터...")
    work_days = {
        'F6': 1,  # 6월 5일
        'G6': 1,  # 6월 6일
        'H6': 1,  # 6월 8일
    }
    
    daily_rate = 210000  # 단가
    
    print(f"근무 내역:")
    print(f"  6월 5일: 1일")
    print(f"  6월 6일: 1일")
    print(f"  6월 8일: 1일")
    print(f"단가: {daily_rate:,}원/일")
    
    # 3. 파일의 실제 수식으로 계산
    print("\n[3단계] 파일의 수식 기반 계산...")
    
    # V6: =SUM(F6:U7) - 출역 합계
    total_days = work_days['F6'] + work_days['G6'] + work_days['H6']
    print(f"\nV6 (총 출역 일수) = SUM(F6:U7)")
    print(f"  = {work_days['F6']} + {work_days['G6']} + {work_days['H6']}")
    print(f"  = {total_days}일")
    
    # X6: =V6*W6 - 세전 급여
    gross_pay = total_days * daily_rate
    print(f"\nX6 (세전 급여) = V6 * W6")
    print(f"  = {total_days} × {daily_rate:,}")
    print(f"  = {gross_pay:,}원")
    
    # Y6: 복합 IF 함수로 세금 계산
    # =IF((F6*W6)>=150000,(F6*W6)-150000,0)+IF((G6*W6)>=150000,(G6*W6)-150000,0)+...
    print(f"\nY6 (세금 차감) = IF 함수 기반 차감액")
    
    y6_parts = []
    for col_key, days in work_days.items():
        col_gross = days * daily_rate
        col_tax = (col_gross - 150000) if col_gross >= 150000 else 0
        y6_parts.append(col_tax)
        col_letter = col_key[0]
        print(f"  {col_letter}6: {days}일 × {daily_rate:,} = {col_gross:,}원 → 차감 {col_tax:,}원")
    
    total_tax = sum(y6_parts)
    print(f"  합계: {' + '.join(map(str, y6_parts))} = {total_tax:,}원")
    
    # Z6: =+Y6+Y7 - 차감/지급액 합계
    net_deduction = total_tax  # Y7은 0이라 가정
    
    final_payment = gross_pay - net_deduction
    
    # 4. 결과
    print("\n" + "=" * 80)
    print("[최종 계산 결과]")
    print("=" * 80)
    
    print(f"\n근로자: {name} ({age}세, 주민번호 {full_rrn})")
    print(f"근무 기간: 2026년 6월")
    print(f"근무 일자: 6월 5일, 6일, 8일 (총 3일)")
    print(f"단가: {daily_rate:,}원/일")
    
    print(f"\n[노무비 명세]")
    print(f"  출역 합계 (V6): {total_days}일")
    print(f"  세전 급여 (X6): {gross_pay:,}원")
    print(f"  세금 차감 (Y6): {total_tax:,}원")
    print(f"  차감 지급액 (Z6): {net_deduction:,}원")
    
    print(f"\n[지급액]")
    print(f"  세전 급여: {gross_pay:,}원")
    print(f"  차감액:   {net_deduction:,}원")
    print(f"  실지급액: {final_payment:,}원")
    
    print("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        calculate_detailed()
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
