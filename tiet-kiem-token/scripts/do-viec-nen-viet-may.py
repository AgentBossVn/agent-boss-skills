#!/usr/bin/env python3
"""Máy dò việc NÊN VIẾT THÀNH CÔNG CỤ (tầng 0), 3 loại:
1. Việc giao LẶP LẠI: người dùng, máy tự chạy, hay trợ lý con làm đi làm lại nhiều lần trong N ngày.
2. Phiên AI ĐỌC NHIỀU DỮ LIỆU (nhiều tệp / nhiều chữ từ công cụ): vd kế toán bắt agent đọc từng hoá đơn, sao kê rồi
   cộng, đối chiếu — việc máy móc, nhờ agent viết 1 công cụ đọc + tính thì AI chỉ cần xem kết quả.
3. Việc NẶNG dù chỉ làm 1 lần: AI tự đọc video / âm thanh / ảnh / PDF / tệp Office / link video, trong khi công cụ
   miễn phí trên máy làm được (Whisper chép lời, ffmpeg, đọc chữ trong ảnh, pdftotext…) → 0 token. Kèm cấu hình máy
   + công cụ đã có, để agent biết máy người dùng chạy nổi không.

Gom theo vài chữ đầu của lời giao (câu đầu phiên chính, mô tả trợ lý con). Chỉ đếm số; chỉ chạy trên máy, không gửi đi đâu.
Mặc định GIẤU lời giao (chỉ hiện "việc 1, 2…"). Agent cần biết việc gì để đề xuất → chạy thêm --hien-noi-dung ra MÀN HÌNH,
không ghi tệp, không dán đi đâu.

Dùng: python3 do-viec-nen-viet-may.py [--ngay 7] [--toi-thieu 3] [--json tep.json] [--goc ~/.claude] [--hien-noi-dung]
tq = token quy chuẩn, cách tính như do-thoi-quen-token.py (chỉ để so nặng nhẹ, không phải tiền)."""
import argparse, collections, datetime as dt, json, os, platform, re, shutil, sys
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
LOAI_TEP = {  # đuôi tệp AI tự đọc → loại việc nặng + công cụ miễn phí trên máy làm thay
    "video / âm thanh": ({".mp4", ".mov", ".mkv", ".webm", ".avi", ".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"},
                         "Whisper (whisper.cpp / faster-whisper) chép lời, ffmpeg cắt / lấy khung hình"),
    "ảnh": ({".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".bmp", ".tiff"},
            "xem giao diện / kiểm hình thì AI hợp, giữ; ảnh chỉ để LẤY CHỮ, SỐ (hoá đơn, bảng) → đọc chữ trên máy (tesseract, macOS Live Text)"),
    "PDF": ({".pdf"}, "pdftotext / pypdf lấy chữ, chỉ đưa AI đoạn cần"),
    "Word / Excel / PowerPoint / CSV": ({".docx", ".xlsx", ".xls", ".pptx", ".csv"},
                                        "script Python đọc + lọc + cộng số, chỉ đưa AI kết quả"),
}
RE_LINK_VIDEO = re.compile(r"(?i)(youtube\.com|youtu\.be|tiktok\.com|vimeo\.com|facebook\.com/.*/videos|fb\.watch)")
CC_LINK_VIDEO = "yt-dlp tải về + Whisper chép lời trên máy"
NGUONG_TEP, NGUONG_KY_TU = 15, 300_000  # 1 phiên đọc ≥15 tệp khác nhau HOẶC công cụ trả về ≥300 nghìn ký tự = "đọc nhiều"


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
    """→ (tq, câu giao đầu tiên, kênh, việc nặng) của 1 tệp nhật ký; None nếu không có lượt AI nào trong cửa sổ."""
    tin, cau, kenh, nang = {}, "", "", collections.Counter()
    tep_doc, ky_tu, cong_cu = set(), 0, {}
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
        if o.get("type") == "assistant":
            for b in m.get("content") if isinstance(m.get("content"), list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use" and isinstance(b.get("input"), dict)):
                    continue
                cong_cu[b.get("id")] = b.get("name")
                if b.get("name") == "Read":
                    tep_doc.add(str(b["input"].get("file_path") or ""))
                    duoi = Path(str(b["input"].get("file_path") or "")).suffix.lower()
                    nang.update(l for l, (duois, _) in LOAI_TEP.items() if duoi in duois)
                elif b.get("name") == "WebFetch" and RE_LINK_VIDEO.search(str(b["input"].get("url") or "")):
                    nang["link video"] += 1
        elif o.get("type") == "user" and isinstance(m.get("content"), list):
            for b in m["content"]:  # người dùng dán thẳng ảnh / PDF vào khung chat; kết quả công cụ đổ vào phiên
                if isinstance(b, dict) and b.get("type") == "tool_result" and cong_cu.get(b.get("tool_use_id")) not in ("Edit", "Write", "Agent", "Task"):
                    ky_tu += len(chu(b.get("content")))
                if isinstance(b, dict) and b.get("type") in ("image", "document"):
                    nang["ảnh" if b["type"] == "image" else "PDF"] += 1
        if o.get("type") == "user" and not cau and not o.get("isMeta"):
            c = m.get("content")
            if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                continue
            t = RE_KHUNG.sub("", RE_TAG.sub("", chu(c)).strip())
            if t and not t.startswith(("<", "[Request interrupted", "Caveat:", "This session is being continued")):
                cau = t
    return (sum(tin.values()), cau, kenh, nang, len(tep_doc), ky_tu) if tin else None


def may_nguoi_dung():
    """Cấu hình máy + công cụ miễn phí đã cài: agent dựa vào đây nói 'máy bạn chạy được / không'."""
    ram = None
    try:
        if hasattr(os, "sysconf") and "SC_PHYS_PAGES" in os.sysconf_names:
            ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
        elif sys.platform == "win32":
            import ctypes

            class Mem(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("u", ctypes.c_ulong), ("t", ctypes.c_ulonglong)] + \
                           [(f"x{i}", ctypes.c_ulonglong) for i in range(6)]
            m = Mem()
            m.l = ctypes.sizeof(Mem)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            ram = m.t / 2**30
    except (OSError, ValueError, AttributeError):
        pass
    co = [c for c in ("ffmpeg", "whisper", "whisper-cli", "yt-dlp", "tesseract", "pdftotext", "magick") if shutil.which(c)]
    return {"he_dieu_hanh": f"{platform.system()} {platform.machine()}", "ram_gb": round(ram) if ram else None, "cong_cu_da_co": co}


def main():
    if not GOC.is_dir():
        sys.exit(f"Không thấy nhật ký ở {GOC}. Kiểm tra lại --goc.")
    nhom = collections.defaultdict(lambda: {"lan": 0, "tq": 0.0, "mau": ""})
    tq_tong = 0.0
    nang, nang_phien = collections.Counter(), collections.Counter()
    doc_nhieu = []
    for p in GOC.glob("**/*.jsonl"):
        try:
            if p.stat().st_mtime < D0.timestamp():
                continue
            r = doc_tep(p)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if not r:
            continue
        t, cau, kenh, n, so_tep, ky_tu = r
        tq_tong += t
        nang.update(n)
        nang_phien.update(n.keys())
        if p.parent.name == "subagents":
            try:
                meta = json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                meta = {}
            cau = meta.get("description") or cau
            loai = f"trợ lý con: {meta.get('agentType') or '?'}"
        else:
            loai = "máy tự chạy (claude -p)" if kenh == "sdk-cli" else "phiên người giao"
        if so_tep >= NGUONG_TEP or ky_tu >= NGUONG_KY_TU:
            doc_nhieu.append({"loai": loai, "so_tep": so_tep, "ky_tu": ky_tu, "tq": round(t),
                              "loi_giao": cau[:120].replace("\n", " ") if A.hien_noi_dung else ""})
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
    may = may_nguoi_dung()
    ds_nang = [{"loai": l, "so_lan": n, "so_phien": nang_phien[l],
                "cong_cu_thay": LOAI_TEP[l][1] if l in LOAI_TEP else CC_LINK_VIDEO} for l, n in nang.most_common()]
    ket = {"cua_so_ngay": A.ngay, "toi_thieu": A.toi_thieu, "tq_tong": round(tq_tong), "tq_viec_lap": tq_lap, "viec_lap": ds,
           "viec_nang_mot_lan": ds_nang, "may": may}
    doc_nhieu.sort(key=lambda x: -x["tq"])
    ket["phien_doc_nhieu"] = {"so_phien": len(doc_nhieu), "tq": sum(x["tq"] for x in doc_nhieu),
                              "top": [{**x, "loi_giao": ""} for x in doc_nhieu[:15]]}
    if A.json:
        # tệp KHÔNG bao giờ mang lời giao, kể cả khi --hien-noi-dung (top phiên đọc nhiều đã giấu sẵn ở trên)
        ket_tep = {**ket, "viec_lap": [{**x, "loi_giao": ""} for x in ds]}
        Path(A.json).write_text(json.dumps(ket_tep, ensure_ascii=False, indent=1), encoding="utf-8")
    pct = lambda x: f"{100 * x / tq_tong:.1f}%" if tq_tong else "-"
    print(f"# Việc giao lặp lại ≥{A.toi_thieu} lần trong {A.ngay} ngày — ứng viên viết thành công cụ (tầng 0)\n")
    if not ds:
        print("Không thấy việc nào lặp đủ số lần. (Gom theo vài chữ đầu lời giao: việc lặp mà mỗi lần gõ khác hẳn thì máy không bắt được — agent tự nhớ lại ở Bước 2c.)")
    else:
        in_viec_lap(ds, tq_lap, pct)
    in_doc_nhieu(doc_nhieu, pct)
    in_viec_nang(ds_nang, may)


def in_viec_lap(ds, tq_lap, pct):
    print(f"{len(ds)} nhóm việc lặp, cộng lại tq {tq_lap / 1e6:,.1f}M ({pct(tq_lap)} tổng tq). "
          "Gom theo vài chữ đầu nên có thể gộp nhầm 2 việc khác nhau mở đầu giống nhau: agent xem lời giao trước khi kết luận.\n")
    print("| việc | ai làm | số lần | tq cả nhóm | % | tq mỗi lần | lời giao |\n|---|---|---|---|---|---|---|")
    for x in ds[:25]:
        print(f"| {x['viec']} | {x['loai']} | {x['lan']} | {x['tq'] / 1e6:,.2f}M | {pct(x['tq'])} | {x['tq_moi_lan'] / 1000:,.0f}k | "
              f"{x['loi_giao'].replace('|', '/') if A.hien_noi_dung else '(ẩn — chạy --hien-noi-dung ra màn hình để xem)'} |")
    print("\nVới mỗi nhóm, agent xếp 1 trong 3 loại (SKILL.md Bước 2c): A theo luật cố định → viết script 0 token · "
          "B phần lớn theo luật → script làm phần luật, AI rẻ làm đúng khúc cần hiểu · C cần phán đoán thật → giữ AI, xét model rẻ hơn.")



def in_doc_nhieu(ds, pct):
    print(f"\n## Phiên AI đọc nhiều dữ liệu (≥{NGUONG_TEP} tệp hoặc ≥{NGUONG_KY_TU // 1000} nghìn ký tự từ công cụ)\n")
    if not ds:
        print("Không có phiên nào.")
        return
    print(f"{len(ds)} phiên, cộng lại tq {sum(x['tq'] for x in ds) / 1e6:,.1f}M ({pct(sum(x['tq'] for x in ds))}). "
          "Đọc nhiều chưa chắc là phí (sửa code, soát bài cần đọc). Agent xét: AI đọc để HIỂU / PHÁN ĐOÁN, "
          "hay chỉ để lọc, đối chiếu, cộng số, chép sang bảng? Loại sau → viết công cụ.\n")
    print("| ai làm | số tệp đọc | nghìn ký tự | tq | lời giao |\n|---|---|---|---|---|")
    for x in ds[:15]:
        print(f"| {x['loai']} | {x['so_tep']} | {x['ky_tu'] // 1000:,} | {x['tq'] / 1e6:,.2f}M | "
              f"{x['loi_giao'].replace('|', '/') if A.hien_noi_dung else '(ẩn)'} |")


def in_viec_nang(ds_nang, may):
    print("\n## Việc nặng AI tự làm mà công cụ miễn phí trên máy làm được (dù chỉ 1 lần)\n")
    if ds_nang:
        print("| loại | số lần AI tự đọc | số phiên | công cụ miễn phí làm thay |\n|---|---|---|---|")
        for x in ds_nang:
            print(f"| {x['loai']} | {x['so_lan']} | {x['so_phien']} | {x['cong_cu_thay']} |")
    else:
        print("Không thấy AI tự đọc video, âm thanh, ảnh, PDF, tệp Office hay link video.")
    print(f"\nMáy này: {may['he_dieu_hanh']}, RAM {may['ram_gb'] or '?'} GB · công cụ đã có: "
          f"{', '.join(may['cong_cu_da_co']) or 'chưa có cái nào'}. Agent dựa vào đây nói máy chạy nổi công cụ nào (SKILL.md Bước 2c).")


if __name__ == "__main__":
    main()
