#!/usr/bin/env python3
"""Máy dò VIỆC GIAO LẶP LẠI (tầng 0): việc nào người dùng, máy tự chạy, hay trợ lý con làm đi làm lại nhiều lần
trong N ngày → ứng viên để agent viết thành công cụ / script chạy ít hoặc 0 token thay vì gọi AI mỗi lần.

Gom theo vài chữ đầu của lời giao (câu đầu phiên chính, mô tả trợ lý con). Chỉ đếm số; chỉ chạy trên máy, không gửi đi đâu.
Mặc định GIẤU lời giao (chỉ hiện "việc 1, 2…"). Agent cần biết việc gì để đề xuất → chạy thêm --hien-noi-dung ra MÀN HÌNH,
không ghi tệp, không dán đi đâu.

Dùng: python3 do-viec-nen-viet-may.py [--ngay 7] [--toi-thieu 3] [--json tep.json] [--goc ~/.claude] [--hien-noi-dung]
tq = token quy chuẩn, cách tính như do-thoi-quen-token.py (chỉ để so nặng nhẹ, không phải tiền)."""
import argparse, collections, datetime as dt, json, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--ngay", type=int, default=7)
ap.add_argument("--toi-thieu", type=int, default=3, help="lặp ít nhất bao nhiêu lần mới tính")
ap.add_argument("--json")
ap.add_argument("--goc", default=os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"))
ap.add_argument("--hien-noi-dung", action="store_true", help="hiện lời giao — CHỈ để agent/người dùng tự xem, đừng chia sẻ")
A = ap.parse_args()
GOC = Path(A.goc).expanduser() / "projects"
D1 = dt.datetime.now(dt.timezone.utc)
D0 = D1 - dt.timedelta(days=A.ngay)
RE_TAG = re.compile(r"<(system-reminder|command-[a-z-]+|local-command-[a-z]+)>.*?</\1>", re.S)
RE_TU = re.compile(r"[\w#]+")
RE_KHUNG = re.compile(r"^Background \(from the session[^)]*\):\s*")  # câu khung do app chèn đầu phiên con, không phải lời giao
SO_TU = 6  # số chữ đầu dùng để gom


def tq(u, model):
    doc = 0.025 if model.startswith("fable") else 0.05 if re.search(r"-5-5", model) else 0.1
    cc = u.get("cache_creation_input_tokens") or 0
    c1h = (u["cache_creation"] if isinstance(u.get("cache_creation"), dict) else {}).get("ephemeral_1h_input_tokens") or 0
    return (1.25 * (cc - c1h) + 2 * c1h + doc * (u.get("cache_read_input_tokens") or 0)
            + (u.get("input_tokens") or 0) + 5 * (u.get("output_tokens") or 0))


def chu(c):
    if isinstance(c, str):
        return c
    return "\n".join(str(b.get("text") or "") for b in c if isinstance(b, dict) and b.get("type") == "text") if isinstance(c, list) else ""


def khoa(t):
    """Vài chữ đầu, chữ thường, số → #: 'Đăng bài ngày 12/11' và 'đăng bài ngày 3/12' cùng 1 nhóm."""
    return " ".join(RE_TU.findall(re.sub(r"\d+", "#", t.lower()))[:SO_TU])


def doc_tep(p):
    """→ (tq, câu giao đầu tiên, kênh) của 1 tệp nhật ký; None nếu không có lượt AI nào trong cửa sổ."""
    tin, cau, kenh = {}, "", ""
    for dong in p.open(encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(dong)
            ts = dt.datetime.fromisoformat(o["timestamp"].replace("Z", "+00:00"))
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        if not isinstance(o, dict) or not (D0 <= (ts if ts.tzinfo else ts.replace(tzinfo=dt.timezone.utc)) < D1):
            continue
        kenh = kenh or o.get("entrypoint") or ""
        m = o.get("message") if isinstance(o.get("message"), dict) else {}
        if o.get("type") == "assistant" and isinstance(m.get("usage"), dict) and m.get("model") != "<synthetic>":
            k = m.get("id") or o.get("uuid")
            v = tq(m["usage"], str(m.get("model") or ""))
            tin[k] = max(tin.get(k, 0), v)
        elif o.get("type") == "user" and not cau and not o.get("isMeta"):
            c = m.get("content")
            if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                continue
            t = RE_KHUNG.sub("", RE_TAG.sub("", chu(c)).strip())
            if t and not t.startswith(("<", "[Request interrupted", "Caveat:", "This session is being continued")):
                cau = t
    return (sum(tin.values()), cau, kenh) if tin else None


def main():
    if not GOC.is_dir():
        sys.exit(f"Không thấy nhật ký ở {GOC}. Kiểm tra lại --goc.")
    nhom = collections.defaultdict(lambda: {"lan": 0, "tq": 0.0, "mau": ""})
    tq_tong = 0.0
    for p in GOC.glob("**/*.jsonl"):
        try:
            if p.stat().st_mtime < D0.timestamp():
                continue
            r = doc_tep(p)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if not r:
            continue
        t, cau, kenh = r
        tq_tong += t
        if p.parent.name == "subagents":
            try:
                meta = json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
            cau = meta.get("description") or cau
            loai = f"trợ lý con: {meta.get('agentType') or '?'}"
        else:
            loai = "máy tự chạy (claude -p)" if kenh == "sdk-cli" else "phiên người giao"
        k = khoa(cau)
        if not k:
            continue
        g = nhom[(loai, k)]
        g["lan"] += 1
        g["tq"] += t
        g["mau"] = g["mau"] or cau[:120].replace("\n", " ")
    lap = sorted(((l, k, g) for (l, k), g in nhom.items() if g["lan"] >= A.toi_thieu), key=lambda x: -x[2]["tq"])
    ds = [{"viec": i, "loai": l, "lan": g["lan"], "tq": round(g["tq"]), "tq_moi_lan": round(g["tq"] / g["lan"]),
           "loi_giao": g["mau"] if A.hien_noi_dung else ""} for i, (l, k, g) in enumerate(lap, 1)]
    tq_lap = sum(x["tq"] for x in ds)
    ket = {"cua_so_ngay": A.ngay, "toi_thieu": A.toi_thieu, "tq_tong": round(tq_tong), "tq_viec_lap": tq_lap, "viec_lap": ds}
    if A.json:
        ket_tep = {**ket, "viec_lap": [{**x, "loi_giao": ""} for x in ds]}  # tệp KHÔNG bao giờ mang lời giao, kể cả khi --hien-noi-dung
        Path(A.json).write_text(json.dumps(ket_tep, ensure_ascii=False, indent=1), encoding="utf-8")
    pct = lambda x: f"{100 * x / tq_tong:.1f}%" if tq_tong else "-"
    print(f"# Việc giao lặp lại ≥{A.toi_thieu} lần trong {A.ngay} ngày — ứng viên viết thành công cụ (tầng 0)\n")
    if not ds:
        print("Không thấy việc nào lặp đủ số lần. (Gom theo vài chữ đầu lời giao: việc lặp mà mỗi lần gõ khác hẳn thì máy không bắt được — agent tự nhớ lại ở Bước 2c.)")
        return
    print(f"{len(ds)} nhóm việc lặp, cộng lại tq {tq_lap / 1e6:,.1f}M ({pct(tq_lap)} tổng tq). "
          "Gom theo vài chữ đầu nên có thể gộp nhầm 2 việc khác nhau mở đầu giống nhau: agent xem lời giao trước khi kết luận.\n")
    print("| việc | ai làm | số lần | tq cả nhóm | % | tq mỗi lần | lời giao |\n|---|---|---|---|---|---|---|")
    for x in ds[:25]:
        print(f"| {x['viec']} | {x['loai']} | {x['lan']} | {x['tq'] / 1e6:,.2f}M | {pct(x['tq'])} | {x['tq_moi_lan'] / 1000:,.0f}k | "
              f"{x['loi_giao'].replace('|', '/') if A.hien_noi_dung else '(ẩn — chạy --hien-noi-dung ra màn hình để xem)'} |")
    print("\nVới mỗi nhóm, agent xếp 1 trong 3 loại (SKILL.md Bước 2c): A theo luật cố định → viết script 0 token · "
          "B phần lớn theo luật → script làm phần luật, AI rẻ làm đúng khúc cần hiểu · C cần phán đoán thật → giữ AI, xét model rẻ hơn.")


if __name__ == "__main__":
    main()
