#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6번 기술 검증 - 1단계: VBA 매크로 확인
엑셀 파일에 VBA 매크로가 포함되어 있는지 확인합니다.
"""

import zipfile
from pathlib import Path
import sys
import io

# stdout을 UTF-8로 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_vba_macro(xlsx_path):
    """
    XLSX 파일(실제로는 ZIP)을 열어 vbaProject.bin이 있는지 확인
    """
    try:
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            file_list = z.namelist()
            has_vba = 'xl/vbaProject.bin' in file_list

            print(f"파일: {xlsx_path.name}")
            has_vba_str = "포함됨" if has_vba else "없음"
            print(f"VBA 매크로 포함 여부: {has_vba_str}")
            print(f"\n파일 내 주요 구조:")

            important = [f for f in file_list if f.startswith('xl/') and f.endswith('.xml')]
            for f in sorted(important)[:10]:
                print(f"  - {f}")

            print(f"\n총 {len(file_list)}개 파일 포함")
            return not has_vba
    except Exception as e:
        print(f"오류: {e}")
        return False

if __name__ == '__main__':
    sample_file = Path('samples/노무비 예시.xlsx')

    if not sample_file.exists():
        print(f"파일 없음: {sample_file}")
    else:
        is_safe = check_vba_macro(sample_file)

        if is_safe:
            print("\n[OK] VBA 매크로가 없어 LibreOffice headless 재계산이 가능합니다.")
        else:
            print("\n[경고] VBA 매크로가 포함되어 있습니다.")
            print("1차 시도(headless 재계산)가 실패할 가능성이 있습니다.")
