"""주민등록번호·계좌번호 암복호화(AES-256-GCM) 및 마스킹 유틸.

평문은 쓰기 시점에 한 번만 마스킹 문자열로 변환해 별도 컬럼에 저장하고,
이후 조회 경로에서는 다시 복호화하지 않는다(암호문 노출 표면 최소화).
키 누락/길이 오류는 app.config.Settings 검증 단계에서 이미 걸러진다.
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

_NONCE_SIZE = 12
_aesgcm = AESGCM(base64.b64decode(settings.encryption_key_base64))


def encrypt_pii(plaintext: str) -> bytes:
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = _aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_pii(blob: bytes) -> str:
    nonce, ciphertext = blob[:_NONCE_SIZE], blob[_NONCE_SIZE:]
    return _aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def mask_resident_registration_number(raw: str) -> str:
    digits = raw.replace("-", "")
    if len(digits) < 7:
        return "*" * len(digits)
    return f"{digits[:6]}-{digits[6]}{'*' * 6}"


def mask_bank_account(raw: str) -> str:
    digits = raw.replace("-", "")
    if len(digits) <= 6:
        return "*" * len(digits)
    return f"{digits[:3]}{'*' * (len(digits) - 5)}{digits[-2:]}"
