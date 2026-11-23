#!/usr/bin/env python3
"""So 2 lần đo (so-lieu.json của do-thoi-quen-token.py): TRƯỚC và SAU khi sửa.

Dùng: python3 so-sanh-hai-lan-do.py <truoc/so-lieu.json> <sau/so-lieu.json> > so-sanh.md

Mọi số quy về MỖI NGÀY để 2 lần đo dài khác nhau vẫn so được. Kèm số theo
MỖI LƯỢT AI TRẢ LỜI: tuần làm nhiều việc hơn thì tq/ngày tăng mà chưa chắc là tệ hơn.
Không đọc nhật ký, không gửi gì đi đâu.
"""
import json, re, sys

if hasattr(sys.stdout, "reconfigure"):  # Windows: in tiếng Việt ra tệp/ống không sập
    sys.stdout.reconfigure(encoding="utf-8")

def so_ngay(d):
    if d.get("so_ngay"):
        return d["so_ngay"]
    m = re.search(r"\((\d+) ngày\)", d.get("cua_so", ""))
    return int(m.group(1)) if m else 7



def ngay(d, n, k):
    v = d.get(k)
    return None if v is None else v / n


def ti_le_opus(d):
    m = d.get("phien_chinh_theo_model") or {}
    tong = sum(m.values())
    return None if not tong else 100 * sum(v for k, v in m.items() if "opus" in k) / tong


def ti_le_con(d):
    return None if not d.get("tq_tong") else 100 * d.get("tq_tro_ly_con", 0) / d["tq_tong"]


def tu_den(d):
    tn = d.get("tq_theo_nguon_luot") or {}
    t = sum(tn.values())
    return None if not t else 100 * (t - sum(v for n, v in tn.items() if n.startswith("người gõ"))) / t


def sua(d):
    tn = d.get("tq_theo_nguon_luot") or {}
    t = sum(tn.values())
    return None if not t else 100 * tn.get("người gõ: sửa / đổi ý / bổ sung", 0) / t


def tan_gau(d):
    tn = d.get("tq_theo_nguon_luot") or {}
    t = sum(tn.values())
    return None if not t else 100 * tn.get("người gõ: khen / chê / tán gẫu", 0) / t


def moi_luot(d):
    l = d.get("tong_luot_ai_chinh")
    return None if not l or not d.get("tq_tong") else d["tq_tong"] / l


# (tên, hàm lấy số, đơn vị, True nếu số NHỎ hơn là tốt)
CHI_SO = [
    ("tq mỗi ngày", lambda d, n: ngay(d, n, "tq_tong"), "tq", True),
    ("tq mỗi lượt AI trả lời", lambda d, n: moi_luot(d), "tq", True),
    ("Lượt đầu chưa giải thích được", lambda d, n: (d.get("chua_giai_thich") or {}).get("luot_dau_chua_ro"), "token", True),
    ("Trợ lý con chiếm", lambda d, n: ti_le_con(d), "%", True),
    ("Lượt AI không do người gõ (tin tự đến)", lambda d, n: tu_den(d), "%", True),
    ("Lượt AI do sửa / đổi ý / bổ sung (ước)", lambda d, n: sua(d), "%", True),
    ("Lượt khen / chê / tán gẫu (ước)", lambda d, n: tan_gau(d), "%", True),
    ("Phiên chính chạy Opus", lambda d, n: ti_le_opus(d), "%", True),
    ("AI còn nhớ tạm (phiên chính)", lambda d, n: (d.get("ti_le_trung_dem") or {}).get("chinh"), "%", False),
    ("Gói khởi động mỗi phiên (trung vị)", lambda d, n: d.get("khoi_dong_trung_vi"), "token", True),
    ("Lệnh ngủ chờ mỗi ngày", lambda d, n: ngay(d, n, "lenh_sleep"), "lần", True),
    ("Chốt bắt làm lại mỗi ngày", lambda d, n: ngay(d, n, "stop_hook_bat_lam_lai"), "lần", True),
    ("Nghỉ quá lâu, AI quên tạm mỗi ngày", lambda d, n: ngay(d, n, "nghi_qua_han_cache"), "lần", True),
    ("Nén phiên mỗi ngày", lambda d, n: ngay(d, n, "lan_nen_phien"), "lần", True),
]


def fm(v, dv):
    if v is None:
        return "—"
    if dv in ("tq", "token") and v >= 1e6:
        return f"{v / 1e6:.1f} triệu".replace(".", ",")
    if dv in ("tq", "token") and v >= 1e3:
        return f"{v / 1e3:.0f} nghìn"
    return f"{v:.1f}".replace(".", ",") + ("%" if dv == "%" else "")


def so(T, S):
    """Trả list dòng (tên, trước, sau, đổi, kết quả) — dùng chung cho trang theo dõi."""
    nT, nS = so_ngay(T), so_ngay(S)
    dong = []
    for ten, lay, dv, nho_tot in CHI_SO:
        a, b = lay(T, nT), lay(S, nS)
        if a is None or b is None:
            dong.append((ten, fm(a, dv), fm(b, dv), "—", "chưa so được"))
            continue
        if dv == "%":
            doi = b - a
        elif a:
            doi = 100 * (b - a) / a
        else:  # mốc = 0: có thêm là đổi thật (không chia được cho 0), cùng 0 là như cũ
            doi = float("inf") if b > 0 else 0
        nguong = 3 if dv == "%" else 10  # lệch nhỏ hơn ngưỡng = coi như không đổi
        if abs(doi) < nguong:
            kq = "≈ như cũ"
        else:
            kq = "✅ tốt hơn" if (doi < 0) == nho_tot else "🔴 kém hơn"
        chu_doi = f"từ 0 lên {fm(b, dv)}" if doi == float("inf") else \
            f"{doi:+.1f} {'điểm' if dv == '%' else '%'}".replace(".", ",")
        dong.append((ten, fm(a, dv), fm(b, dv), chu_doi, kq))
    return dong


def khoi_luong(T, S):
    nT, nS = so_ngay(T), so_ngay(S)
    pT, pS = (T.get("so_phien_chinh") or 0) / nT, (S.get("so_phien_chinh") or 0) / nS
    lT, lS = (d.get("tong_luot_ai_chinh") for d in (T, S))
    cau = f"Khối lượng việc: {pT:.0f} → {pS:.0f} phiên/ngày"
    if lT and lS:
        cau += f", {lT / nT:,.0f} → {lS / nS:,.0f} lượt AI/ngày".replace(",", ".")
    cau += "."
    if pT and abs(pS - pT) / pT > 0.3:
        cau += " ⚠️ Lệch hơn 30%: khối lượng việc khác hẳn, tin dòng 'mỗi lượt' hơn dòng 'mỗi ngày'."
    return cau


GIOI_HAN = ("tq là số quy đổi theo bảng giá API để so, KHÔNG phải tiền trừ thật hay hạn mức gói. "
            "Số này không cho biết chất lượng việc có giữ được không: hỏi người dùng có phải làm lại nhiều hơn không.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    T, S = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
    print(f"# So trước / sau\n\nTRƯỚC: {T.get('cua_so', '?')}  \nSAU: {S.get('cua_so', '?')}\n")
    print("| Chỉ số | Trước | Sau | Đổi | Kết quả |\n|---|---|---|---|---|")
    for d in so(T, S):
        print("| " + " | ".join(d) + " |")
    print("\n" + khoi_luong(T, S) + "\n\nGiới hạn: " + GIOI_HAN)
