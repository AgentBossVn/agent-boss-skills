"""Ước số token từ chữ, theo loại chữ: ASCII / JSON ~3,8 ký tự mỗi token; chữ tiếng Việt có dấu ~1,7 ký tự (chỉnh theo /context của Claude Code) mỗi token.
Hệ số nội suy theo tỉ lệ ký tự ngoài ASCII của từng khối. Chỉ để so nặng nhẹ; số thật xem /context hoặc usage của lượt đầu."""
CPT_ASCII, CPT_VIET = 3.8, 1.7
TI_LE_VIET = 0.15  # từ tỉ lệ ký tự ngoài ASCII này trở lên coi như chữ Việt thuần


def uoc_token(text):
    n = len(text or "")
    if not n:
        return 0.0
    r = sum(1 for c in text if ord(c) > 127) / n
    w = min(1.0, r / TI_LE_VIET)
    return n * ((1 - w) / CPT_ASCII + w / CPT_VIET)
