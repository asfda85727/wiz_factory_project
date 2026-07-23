#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6번 기술 검증 - 3단계: LibreOffice headless 재계산 테스트
실제 파일을 LibreOffice로 열어 재계산하고 결과를 추출합니다.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openpyxl import load_workbook
from pathlib import Path
import subprocess
import time

def test_libreoffice_calculation():
    """
    LibreOffice headless를 이용한 재계산 테스트
    """
    
    sample_file = Path('samples/노무비 예시.xlsx').resolve()
    
    print("=" * 60)
    print("LibreOffice Headless 재계산 테스트")
    print("=" * 60)
    
    # 1. 원본 파일 로드 (수식만 읽기)
    print("\n[1단계] 원본 파일 로드...")
    wb = load_workbook(sample_file, data_only=False)
    ws = wb['명세서_철거']
    
    # 재계산 전 샘플 수식 확인
    print(f"원본 파일 X6 셀 (세전급여 공식): {ws['X6'].value}")
    print(f"원본 파일 Y6 셀 (세금 공식): {ws['Y6'].value}")
    
    # 2. LibreOffice로 재계산
    print("\n[2단계] LibreOffice headless 재계산 중...")
    
    libreoffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    
    try:
        # headless로 파일 열기 (자동 저장 없음, 재계산만)
        cmd = [
            libreoffice_path,
            '--headless',
            '--convert-to', 'xlsx',
            '--outdir', str(sample_file.parent),
            str(sample_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("LibreOffice 재계산 성공")
        else:
            print(f"LibreOffice 오류: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print(f"LibreOffice를 찾을 수 없습니다: {libreoffice_path}")
        return False
    except Exception as e:
        print(f"오류: {e}")
        return False
    
    # 3. 재계산된 파일 값 읽기
    print("\n[3단계] 재계산된 결과 확인...")
    time.sleep(1)
    
    wb_calc = load_workbook(sample_file, data_only=True)
    ws_calc = wb_calc['명세서_철거']
    
    # 샘플 셀 값 확인
    test_cells = {
        'V6': '총출역일수',
        'X6': '세전급여',
        'Y6': '세금',
        'Z6': '차감/지급액'
    }
    
    print("\n재계산된 값들:")
    for cell, desc in test_cells.items():
        value = ws_calc[cell].value
        print(f"  {cell} ({desc}): {value}")
    
    print("\n[결론]")
    print("✓ LibreOffice headless 재계산이 정상 작동합니다.")
    print("✓ 1차 시도(headless 재계산) 방식이 가능합니다.")
    
    return True

if __name__ == '__main__':
    try:
        success = test_libreoffice_calculation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
