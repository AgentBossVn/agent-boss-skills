#!/usr/bin/env python3
"""Đo token Codex (OpenAI) từ nhật ký trên máy: ~/.codex/sessions + archived_sessions.

Dùng: python3 do-token-codex.py [--ngay 7] [--goc ~/.codex] [--json ra.json]
Ra JSON cùng khuôn chính với do-thoi-quen-token.py để so-sanh-hai-lan-do.py và
bang-theo-doi.py dùng chung. Chỉ ghi số đếm + tên model, KHÔNG ghi câu người gõ.

tq (Codex) = chữ vào mới ×1 + chữ vào AI còn nhớ tạm ×0,1 + chữ viết ra ×8
(tỉ lệ giá GPT công bố phổ biến; số quy đổi để so, không phải tiền).
"""
import argparse, collections, datetime as dt, json, os, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows: in tiếng Việt ra tệp/ống không sập
    sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--ngay", type=int, default=7)
ap.add_argument("--goc", default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
ap.add_argument("--json")
A = ap.parse_args()

D1 = dt.datetime.now(dt.timezone.utc)
D0 = D1 - dt.timedelta(days=A.ngay)
goc = Path(A.goc)
tep = []
for thu in ("sessions", "archived_sessions"):
    if (goc / thu).is_dir():
        for p in (goc / thu).rglob("*.jsonl"):
            try:
                if p.stat().st_mtime >= D0.timestamp():
                    tep.append(p)
            except OSError:  # liên kết hỏng, tệp biến mất giữa chừng
                continue
if not tep:
    print(f"Không thấy nhật ký nào ở {goc}. Kiểm tra lại --goc.", file=sys.stderr)
    sys.exit(2)


def tg(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


da_dem = set()
tong = collections.Counter()
theo_model = collections.Counter()
phien, luot, bo_qua = set(), 0, 0


def dem_tep(p):
    """Đếm 1 tệp; trả danh sách bản ghi (khoa, thời điểm, model, vao, nho, ra). Dòng lạ bị bỏ qua, không bỏ cả tệp."""
    model = "?"
    cac_dong = open(p, encoding="utf-8", errors="replace").read().splitlines()
    co_record = any('"token_usage_record"' in x for x in cac_dong)
    kq = []
    for dong in cac_dong:
        try:
            d = json.loads(dong)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        pl = d.get("payload") if isinstance(d.get("payload"), dict) else {}
        if d.get("type") == "turn_context":
            model = pl["model"] if isinstance(pl.get("model"), str) and pl["model"] else model
            continue
        u, khoa = None, None
        if d.get("type") == "token_usage_record":
            u, khoa = pl.get("usage"), pl.get("response_id")
        elif d.get("type") == "event_msg" and pl.get("type") == "token_count":
            # bản Codex cũ chỉ có dòng này; bản mới có cả 2 → tệp có record thì bỏ, tránh đếm đôi
            if co_record:
                continue
            info = pl.get("info")
            u = info.get("last_token_usage") if isinstance(info, dict) else None
            khoa = ("tc", str(p), d.get("timestamp"))
        if not isinstance(u, dict) or not u:
            continue
        t = tg(d.get("timestamp", ""))
        if not t or t < D0:
            continue
        so = [u.get(k) if isinstance(u.get(k), (int, float)) else 0 for k in ("input_tokens", "cached_input_tokens", "output_tokens")]
        kq.append((str(khoa), model, *so))
    return kq


for p in tep:
    try:
        ban_ghi = dem_tep(p)
    except (AttributeError, TypeError, ValueError, OSError):
        bo_qua += 1
        continue
    for khoa, model, vao, nho, ra in ban_ghi:
        if khoa in da_dem:
            continue
        da_dem.add(khoa)
        tong.update(vao=vao, nho=nho, ra=ra)
        theo_model[model] += (vao - nho) + 0.1 * nho + 8 * ra
        phien.add(p.stem)
        luot += 1

tq = sum(theo_model.values())
ket = {
    "agent": "codex",
    "cua_so": f"{D0:%Y-%m-%d %H:%M} → {D1:%Y-%m-%d %H:%M} UTC ({A.ngay} ngày)",
    "so_ngay": A.ngay, "tq_tong": tq, "so_phien_chinh": len(phien), "tong_luot_ai_chinh": luot,
    "tong_token": dict(tong), "phien_chinh_theo_model": dict(theo_model.most_common()),
    "tep_bo_qua": bo_qua,
    "ti_le_trung_dem": {"chinh": 100 * tong["nho"] / max(tong["vao"], 1)},
}
if A.json:
    Path(A.json).write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"# Token Codex {A.ngay} ngày\n\n{len(phien)} phiên, {luot} lượt trả lời, "
      f"{tq / 1e6:.1f} triệu tq ({tq / A.ngay / 1e6:.1f} triệu/ngày).".replace(".", ",", 2))
if bo_qua:
    print(f"(Bỏ qua {bo_qua} tệp nhật ký có định dạng lạ.)")
print(f"AI còn nhớ tạm: {ket['ti_le_trung_dem']['chinh']:.1f}% chữ vào.")
for m, v in theo_model.most_common():
    print(f"- {m}: {100 * v / max(tq, 1):.0f}% tq")
