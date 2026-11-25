#!/usr/bin/env python3
"""Máy đo THÓI QUEN tốn token: đọc nhật ký ~/.claude/projects (phiên chính + trợ lý con) trong N ngày,
đếm các kiểu làm việc ngốn token. Chỉ đếm số + tên tệp/công cụ; chỉ chạy trên máy, không gửi đi đâu.

Dùng: python3 do-thoi-quen-token.py [--ngay 7] [--json tep.json] [--goc ~/.claude] [--ttl 5]
Chạy được trên máy BẤT KỲ có Claude Code (macOS/Linux/Windows, Python 3.8+, không cần cài thêm).
In bảng markdown ra màn hình; ghi JSON đầy đủ nếu có tep_json_ra.

Đơn vị "tq" (token quy chuẩn = quy về giá 1 token vào thường, theo bảng giá API Anthropic 20/11/2026):
ghi-cache 5 phút 1,25× · ghi-cache 1 giờ 2× · đọc-cache 0,1× (Opus/Sonnet 5.5: 0,05×; Fable 5.x: 0,025×) · ra 5×.
Dùng để so nặng nhẹ giữa các mục; ai dùng gói thuê bao không trả theo token nhưng tq càng lớn càng mau hết hạn mức.
TTL cache: gói thuê bao → phiên chính 1 giờ, trợ lý con 5 phút; dùng API key → 5 phút. Máy tự nhận theo nhật ký."""
import argparse, collections, datetime as dt, json, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows: in ra tệp/ống dẫn không vỡ chữ Việt

ap = argparse.ArgumentParser()
ap.add_argument("--ngay", type=int, default=7)
ap.add_argument("--json")
ap.add_argument("--goc", default=os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"))
ap.add_argument("--an-noi-dung", action="store_true", help="(mặc định, giữ cho lệnh cũ) ẩn câu người gõ, đường dẫn tệp, tên dự án")
ap.add_argument("--hien-noi-dung", action="store_true", help="hiện câu người gõ, đường dẫn, tên dự án — CHỈ để tự xem, đừng chia sẻ")
ap.add_argument("--hien-du-an", action="store_true", help="hiện tên dự án nhưng VẪN giấu câu người gõ và đường dẫn tệp")
ap.add_argument("--ttl", type=int, default=0, help="ép số phút cache còn hạn; 0 = tự nhận (1h nếu nhật ký ghi cache 1 giờ, không thì 5)")
A = ap.parse_args()
AN = not A.hien_noi_dung  # mặc định GIẤU: báo cáo + JSON hay bị dán/gửi đi
AN_DU_AN = AN and not A.hien_du_an  # --hien-du-an: chỉ mở tên dự án, câu người gõ + đường dẫn vẫn giấu
GOC = Path(A.goc).expanduser() / "projects"
N, RA = A.ngay, A.json
D1 = dt.datetime.now(dt.timezone.utc)
D0 = D1 - dt.timedelta(days=N)
RE_MODEL = re.compile(r"(opus|sonnet|haiku|fable)-[\d-]+")
RE_BAN_5_5 = re.compile(r"-5-5(-\d{6,8})?$")  # bản 5.5, kể cả khi tên model có hậu tố ngày (sonnet-5-5-20261101)
RE_SLEEP = re.compile(r"(^|[;&|\s(])sleep\s+\d")
RE_HOOK = re.compile(r"([\w.-]+\.(?:cjs|js|mjs|py|sh|ts))")
RE_TAG = re.compile(r"<(system-reminder|command-[a-z-]+|local-command-[a-z]+)>.*?</\1>", re.S)
NGU_CANH_DAI = 200_000
NGU_CANH_USAGE = 150_000   # mốc /usage của Claude Code gọi "ngữ cảnh quá 150k"
SONG_SONG_TOI_THIEU = 4    # /usage: "từ 4 phiên chạy song song"
SONG_SONG_PHUT = 10        # ƯỚC: 2 phiên "song song" nếu cùng có lượt AI trong cùng một ô 10 phút (hãng chưa công bố cách tính)
PHIEN_DAI_GIO = 8          # /usage: "phiên sống từ 8 giờ" (từ lượt đầu đến lượt cuối trong cửa sổ đo)
MOC_LUOT = (1, 10, 50, 100, 200, 300, 500)


def he_so_doc(model):
    # ƯỚC: mọi bản "fable" (5.1, 5.2, 5.x…) đều áp hệ số đọc-cache của Fable 5.2 (0,025×); chưa có bảng giá riêng từng bản, không đoán khác.
    return 0.025 if (model or "").startswith("fable") else 0.05 if RE_BAN_5_5.search(model or "") else 0.1


def tq(u, model=None):
    """u có thể có cc1h (phần ghi cache 1 giờ); model=None dùng hệ số đọc 0,1 (theo_model đã tách sẵn)."""
    return 1.25 * (u["cc"] - u.get("cc1h", 0)) + 2 * u.get("cc1h", 0) + he_so_doc(model) * u["cr"] + u["in"] + 5 * u["out"]


def du_an(cwd):
    cwd = (cwd or "").replace("\\", "/").split("/.claude/worktrees/")[0]
    return Path(cwd).name or "?"


def chu(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(str(b.get("text") or "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def do_tep(p):
    """Đọc 1 tệp nhật ký → dict số liệu của tệp đó (None nếu không có tin nào trong cửa sổ)."""
    tin = {}  # bỏ trùng theo mã tin: giữ bản có out lớn nhất
    cong_cu, ket_qua, doc_tep = {}, collections.Counter(), collections.Counter()
    hook, nguoi = collections.Counter(), []
    co_cong_cu = collections.defaultdict(set)  # mã tin → {"skill","mcp"} (cờ giữ riêng: dòng có tool_use có thể đến trước/sau dòng có usage)
    sleep_n, cwd, nen, stop_hook, anh = 0, "", 0, 0, 0
    kenh = collections.Counter()  # entrypoint: claude-desktop / cli / sdk-cli (máy tự chạy) / vscode…
    dau_tep = None  # giờ của tin đầu tiên trong TỆP (trước khi lọc cửa sổ)
    nguon = "người gõ"
    for dong in p.open(encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(dong)
            ts = dt.datetime.fromisoformat(o["timestamp"].replace("Z", "+00:00"))
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        if not isinstance(o, dict):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        dau_tep = dau_tep or ts
        if not (D0 <= ts < D1):
            continue
        cwd = o.get("cwd") or cwd
        if o.get("entrypoint"):
            kenh[o["entrypoint"]] += 1
        m = o.get("message")
        if not isinstance(m, dict):
            m = {}
        if o.get("subtype") == "compact_boundary":
            nen += 1
        if o.get("type") == "assistant":
            u = m.get("usage")
            if isinstance(u, dict):
                if m.get("model") == "<synthetic>":
                    continue
                rec = {"cc": u.get("cache_creation_input_tokens") or 0, "cr": u.get("cache_read_input_tokens") or 0,
                       "in": u.get("input_tokens") or 0, "out": u.get("output_tokens") or 0,
                       "cc1h": (u["cache_creation"] if isinstance(u.get("cache_creation"), dict) else {}).get("ephemeral_1h_input_tokens") or 0,
                       "ts": ts, "model": (RE_MODEL.search(m["model"] if isinstance(m.get("model"), str) else "") or [None])[0] or "khac",
                       "nguon": nguon}
                k = m.get("id") or o.get("uuid")
                if k not in tin or rec["out"] >= tin[k]["out"]:
                    tin[k] = rec
            for b in m.get("content") if isinstance(m.get("content"), list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") not in cong_cu:
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    cong_cu[b["id"]] = b.get("name")
                    kk = m.get("id") or o.get("uuid")
                    if b.get("name") == "Skill" or str(b.get("name")).startswith("mcp__"):
                        co_cong_cu[kk].add("skill" if b.get("name") == "Skill" else "mcp")
                    if b.get("name") == "Read" and inp.get("file_path"):
                        doc_tep[inp["file_path"]] += 1
                    if b.get("name") == "Bash" and RE_SLEEP.search(inp.get("command") or ""):
                        sleep_n += 1
        elif o.get("type") == "user":
            c = m.get("content")
            if not (isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c)):
                nguon = nguon_luot(o, chu(c)) or nguon
            if "Stop hook feedback" in chu(c)[:200]:
                stop_hook += 1
            if isinstance(c, list):
                anh += sum(isinstance(b, dict) and b.get("type") == "image" for b in c)
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        t = chu(b.get("content"))
                        ket_qua[cong_cu.get(b.get("tool_use_id"), "?")] += len(t)
                        if "hook error" in t[:300] or "hook blocking" in t[:300]:
                            hook[(RE_HOOK.search(t[:600]) or [None, "hook-khac"])[1]] += 1
            goc = (o["origin"] if isinstance(o.get("origin"), dict) else {}).get("kind")
            la_nguoi = goc == "human" if goc else not (isinstance(c, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in c))
            if la_nguoi and not o.get("isMeta") and not o.get("isCompactSummary"):
                t = RE_TAG.sub("", chu(c)).strip()
                if t and not t.startswith(("[Request interrupted", "<", "Stop hook feedback", "Caveat:")):
                    nguoi.append(t)
    if not tin:
        return None
    ds = sorted(tin.values(), key=lambda r: r["ts"])
    tong = collections.Counter()
    theo_model = collections.defaultdict(collections.Counter)
    for r in ds:
        for a in ("cc", "cr", "in", "out", "cc1h"):
            tong[a] += r[a]
            theo_model[r["model"]][a] += r[a]
        theo_model[r["model"]]["n"] += 1
    ngu_canh = [r["cc"] + r["cr"] + r["in"] for r in ds]
    # Nghỉ quá hạn cache: lượt sau khoảng lặng > TTL mà phải ghi lại cache lớn (>20k)
    ttl = dt.timedelta(minutes=A.ttl or (60 if tong["cc1h"] > tong["cc"] / 2 else 5))
    qua_han = [r for a, r in zip(ds, ds[1:]) if r["ts"] - a["ts"] > ttl and r["cc"] > 20_000]
    # Đổi model giữa phiên: mỗi model 1 cache riêng → lượt sau đổi phải ghi lại
    doi_model = [r for a, r in zip(ds, ds[1:]) if r["model"] != a["model"] and r["cc"] > 20_000]
    bat_dau_trong = dau_tep is not None and dau_tep >= D0  # phiên mở TRONG cửa sổ mới có lượt khởi động thật
    return {"cac_luot": [(r["ts"].timestamp(), tq(r, r["model"])) for r in ds], "dau_cuoi": (ds[0]["ts"].timestamp(), ds[-1]["ts"].timestamp()),
            "tq_co_skill": sum(tq(r, r["model"]) for k_, r in tin.items() if "skill" in co_cong_cu.get(k_, ())),
            "tq_co_mcp": sum(tq(r, r["model"]) for k_, r in tin.items() if "mcp" in co_cong_cu.get(k_, ())),
            "luot_ngu_canh_150k": sum(x > NGU_CANH_USAGE for x in ngu_canh),
            "tq_ngu_canh_150k": sum(tq(r, r["model"]) for r, x in zip(ds, ngu_canh) if x > NGU_CANH_USAGE),
            "tong": tong, "theo_model": theo_model, "luot": len(ds), "khoi_dong": ngu_canh[0] if bat_dau_trong else None,
            "ngu_canh_max": max(ngu_canh), "luot_ngu_canh_dai": sum(x > NGU_CANH_DAI for x in ngu_canh),
            "tq_ngu_canh_dai": sum(tq(r, r["model"]) for r, x in zip(ds, ngu_canh) if x > NGU_CANH_DAI),
            "phan": {"doc_lai": sum(he_so_doc(r["model"]) * r["cr"] for r in ds),
                     "ghi_moi": sum(1.25 * (r["cc"] - r["cc1h"]) + 2 * r["cc1h"] + r["in"] for r in ds),
                     "viet_ra": sum(5 * r["out"] for r in ds)},
            "tk_doc_lai": sum(r["cr"] for r in ds), "tk_tong": sum(r["cr"] + r["cc"] + r["in"] + r["out"] for r in ds),
            "day_theo_luot": {i: ngu_canh[i - 1] for i in MOC_LUOT if i <= len(ngu_canh)} if bat_dau_trong else {},
            "ket_qua": ket_qua, "so_lan_cong_cu": collections.Counter(cong_cu.values()),
            "doc_lai": {f: n for f, n in doc_tep.items() if n >= 3}, "hook": hook, "sleep": sleep_n,
            "nen": nen, "stop_hook": stop_hook, "qua_han_n": len(qua_han), "qua_han_tq": sum(tq({**r, "cr": 0, "in": 0, "out": 0}) for r in qua_han), "khoi_dong_tq": tq(ds[0], ds[0]["model"]) if bat_dau_trong else 0,
            "doi_model_n": len(doi_model), "doi_model_tq": sum(tq({**r, "cr": 0, "in": 0, "out": 0}) for r in doi_model),
            "anh": anh, "ttl_phut": ttl.seconds // 60,
            "theo_nguon": collections.Counter({n: sum(tq(r, r["model"]) for r in ds if r["nguon"] == n)
                                               for n in {r["nguon"] for r in ds}}),
            "nguoi": nguoi, "du_an": du_an(cwd), "kenh": kenh.most_common(1)[0][0] if kenh else "khong-ro", "model_chinh": max(theo_model, key=lambda k: theo_model[k]["out"])}


# Câu người gõ có dấu hiệu sửa hướng, đổi ý, bổ sung yêu cầu sau khi agent đã làm (ƯỚC theo từ khoá)
RE_SUA = re.compile(r"(?i)\b(sai rồi|làm lại|không phải|ý (tôi|anh|em|mình) là|đổi ý|thôi bỏ|bỏ đi|nhầm rồi|chưa đúng|"
                    r"sửa lại|quên chưa|bổ sung|thêm nữa|à mà|hoá ra|hóa ra|thay vì|wrong|redo|actually|instead)\b")
# Cả câu chỉ là khen / cảm ơn / chê / chửi / chào / cười, không kèm việc (ƯỚC; "ok", "làm đi" là duyệt việc nên KHÔNG tính)
# Tách câu thành từ rồi kiểm từng từ trong tập từ xã giao (KHÔNG dùng regex lồng nhau: tránh treo ReDoS).
CUM_TU = (("cảm ơn", "cảm_ơn"), ("cám ơn", "cảm_ơn"), ("thank you", "thanks"), ("tuyệt vời", "tuyệt"), ("xuất sắc", "xuất_sắc"))
TU_CHINH = {"cảm_ơn", "thanks", "thank", "tks", "tuyệt", "giỏi", "hay", "tốt", "xuất_sắc", "đỉnh", "ngon", "chào", "hello",
            "ngu", "dốt", "đm", "dm", "vl", "vcl", "đéo", "đếch", "chán", "mệt", "bực"}
TU_XA_GIAO = {"hi", "em", "anh", "bạn", "chị", "nhé", "nha", "nhỉ", "à", "ạ", "quá", "lắm", "thế", "vậy", "thật", "rất", "nhiều", "vời"}
RE_CUOI = re.compile(r"(?:ha|hi|he){2,}$")  # haha, hihi, hehe, hahaha… (từ đơn, regex phẳng)
RE_TACH_TU = re.compile(r"[\s,.!?…:;)(*-]+")
RE_BIEU_TUONG = re.compile(r"[^\w\s,.!?…:;)(*-]")


def la_tan_gau(t):
    c = RE_BIEU_TUONG.sub("", RE_TAG.sub("", t)).strip()
    if not c:  # chỉ có biểu tượng cảm xúc
        return bool(t.strip()) and len(t.strip()) <= 10
    if len(c) > 60:
        return False
    c = c.lower()
    for cu, thay in CUM_TU:
        c = c.replace(cu, thay)
    tu = [w for w in RE_TACH_TU.split(c) if w]
    if not tu:
        return False
    chinh = False
    for w in tu:
        if w in TU_CHINH or (RE_CUOI.fullmatch(w) and w[:2] * (len(w) // 2) == w):
            chinh = True
        elif w not in TU_XA_GIAO:
            return False
    return chinh


TIN_TU_DEN = ("<task-notification>", "Another Claude session sent", "<agent-message", "Linked sessions now",
              "Background (from the session", "<side-sessions-event>")


def nguon_luot(o, t):
    """Ai khởi đầu lượt AI này? None = tin giữa lượt (nạp skill, ảnh, bị ngắt), giữ nguồn cũ."""
    k = (o["origin"] if isinstance(o.get("origin"), dict) else {}).get("kind")
    dau = t[:400]
    if "Stop hook feedback" in dau:  # xét trước isMeta: tin chốt có thể gắn isMeta
        return "chốt bắt làm lại"
    if "<task-notification>" in dau:
        return "trợ lý con / phiên khác báo về"
    if o.get("isMeta") or dau.startswith(("[Request interrupted", "This session is being continued")):
        return None  # tin giữa lượt / sau nén: vẫn là việc của nguồn trước đó
    if k == "peer" or k == "task-notification" or any(x in dau for x in TIN_TU_DEN) or "<system-reminder> The session" in dau:
        return "trợ lý con / phiên khác báo về"
    if "ci-monitor-event" in dau or k == "scheduled":
        return "sự kiện tự đến (CI, lịch)"
    if k == "plugin":
        return "plugin / hook"
    if k == "human" or not k:
        if la_tan_gau(t):
            return "người gõ: khen / chê / tán gẫu"
        return "người gõ: sửa / đổi ý / bổ sung" if RE_SUA.search(RE_TAG.sub("", t)[:300]) else "người gõ"
    return "khác"


def tq_song_song(luot_theo_phien, toi_thieu=SONG_SONG_TOI_THIEU, phut=SONG_SONG_PHUT):
    """tq của các lượt AI xảy ra lúc có ≥ toi_thieu phiên khác nhau cùng hoạt động (cùng ô `phut` phút).
    luot_theo_phien: {mã phiên: [(giờ epoch, tq), ...]} (gồm cả lượt trợ lý con, tính vào phiên cha)."""
    o = collections.defaultdict(set)
    for sid, ls in luot_theo_phien.items():
        for e, _ in ls:
            o[int(e // (phut * 60))].add(sid)
    return sum(t for ls in luot_theo_phien.values() for e, t in ls if len(o[int(e // (phut * 60))]) >= toi_thieu)


def tq_phien_dai(khoang, tq_phien, gio=PHIEN_DAI_GIO):
    """tq (cả trợ lý con) của các phiên chính có khoảng từ lượt đầu đến lượt cuối ≥ gio giờ.
    khoang: {mã phiên: (đầu, cuối) tính bằng giây epoch}; tq_phien: {mã phiên: tq cả phiên}."""
    return sum(tq_phien.get(sid, 0.0) for sid, (a, b) in khoang.items() if b - a >= gio * 3600)


def loai_con(p):
    try:
        return json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8")).get("agentType") or "?"
    except (OSError, ValueError):
        return "?"


def main():
    cut = D0.timestamp()
    phien = {}  # sessionId -> số liệu phiên chính (+ cộng dồn con)
    con_theo_loai = collections.defaultdict(lambda: {"so_con": 0, "tq": 0.0, "out": 0, "model": collections.Counter()})
    tong = collections.Counter()
    tq_tong = tq_con = 0.0
    cong_cu_kq, cong_cu_n, hook, cau = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    doc_lai, sleep_n, nen, stop_hook, qh_n, qh_tq = [], 0, 0, 0, 0, 0.0
    dm_n, dm_tq, anh, kd_tq, ttl_dem = 0, 0.0, 0, 0.0, collections.Counter()
    model_chinh = collections.Counter()
    phan, tk_doc, tk_tong, day = collections.Counter(), 0, 0, collections.defaultdict(list)
    tong_chinh, tong_con = collections.Counter(), collections.Counter()
    theo_kenh = collections.Counter()
    theo_nguon = collections.Counter()  # ai khởi đầu lượt (chỉ phiên chính)
    bo_qua = 0  # số tệp nhật ký lạ phải bỏ qua
    out_model = collections.defaultdict(collections.Counter)  # out + số lượt theo model (mọi tệp)
    luot_theo_phien, khoang_phien = collections.defaultdict(list), {}  # cho "song song" và "phiên sống từ 8 giờ"
    luot150, tq150, tq_skill, tq_mcp = 0, 0.0, 0.0, 0.0
    for p in GOC.glob("**/*.jsonl"):
        try:
            if p.stat().st_mtime < cut:
                continue
        except OSError:
            continue
        try:
            r = do_tep(p)
        except (AttributeError, TypeError, ValueError, OSError):
            bo_qua += 1
            continue
        if not r:
            continue
        la_con = p.parent.name == "subagents"
        sid = p.parent.parent.name if la_con else p.stem
        theo_kenh[r["kenh"]] += 0  # giữ khoá; cộng tq bên dưới
        t = sum(tq(u, mo) for mo, u in r["theo_model"].items())
        for mo, u in r["theo_model"].items():
            out_model[mo]["out"] += u["out"]
            out_model[mo]["n"] += u["n"]
        tq_tong += t
        luot_theo_phien[sid] += r["cac_luot"]
        if not la_con:
            khoang_phien[sid] = r["dau_cuoi"]
            luot150 += r["luot_ngu_canh_150k"]
            tq150 += r["tq_ngu_canh_150k"]
            tq_skill += r["tq_co_skill"]
            tq_mcp += r["tq_co_mcp"]
        (tong_con if la_con else tong_chinh).update({a: r["tong"][a] for a in ("cc", "cr", "in")})
        phan.update(r["phan"])
        tk_doc += r["tk_doc_lai"]
        tk_tong += r["tk_tong"]
        theo_kenh[r["kenh"]] += t
        tong.update(r["tong"])
        cong_cu_kq.update(r["ket_qua"])
        cong_cu_n.update(r["so_lan_cong_cu"])
        hook.update(r["hook"])
        sleep_n += r["sleep"]
        nen += r["nen"]
        stop_hook += r["stop_hook"]
        doc_lai += [(n, f, sid[:8]) for f, n in r["doc_lai"].items()]
        ph = phien.setdefault(sid, {"tq_chinh": 0.0, "tq_con": 0.0, "so_con": 0, "du_an": r["du_an"], "cau_dau": ""})
        if la_con:
            tq_con += t
            lc = con_theo_loai[loai_con(p)]
            lc["so_con"] += 1
            lc["tq"] += t
            lc["out"] += r["tong"]["out"]
            lc["model"][r["model_chinh"]] += 1
            ph["tq_con"] += t
            ph["so_con"] += 1
        else:
            for i, x in r["day_theo_luot"].items():
                day[i].append(x)
            qh_n += r["qua_han_n"]
            qh_tq += r["qua_han_tq"]
            dm_n += r["doi_model_n"]
            dm_tq += r["doi_model_tq"]
            anh += r["anh"]
            kd_tq += r["khoi_dong_tq"]
            if r["kenh"] == "sdk-cli":  # cả phiên do máy tự chạy (claude -p) mở
                theo_nguon["máy tự chạy (claude -p)"] += t
            else:
                theo_nguon.update(r["theo_nguon"])
            ttl_dem[r["ttl_phut"]] += 1
            for mo, u in r["theo_model"].items():
                model_chinh[mo] += tq(u, mo)
            ph.update(tq_chinh=t, luot=r["luot"], khoi_dong=r["khoi_dong"], ngu_canh_max=r["ngu_canh_max"],
                      luot_ngu_canh_dai=r["luot_ngu_canh_dai"], tq_ngu_canh_dai=r["tq_ngu_canh_dai"],
                      model=r["model_chinh"], du_an=r["du_an"], cau_dau=(r["nguoi"] or [""])[0][:70].replace("\n", " "))
            for c in r["nguoi"]:
                if len(c) <= 40:
                    cau[re.sub(r"\s+", " ", c.lower())] += 1
    if not phien:
        print(f"Không thấy nhật ký nào ở {A.goc}. Kiểm tra lại --goc.", file=sys.stderr)
        sys.exit(2)
    chinh = [v for v in phien.values() if "luot" in v]
    for v in phien.values():
        v["tq_ca_phien"] = v["tq_chinh"] + v["tq_con"]
    top = sorted(phien.values(), key=lambda v: -v["tq_ca_phien"])[:12]
    trung_vi = lambda xs: sorted(xs)[len(xs) // 2]
    phan_bo_dai = {}
    for nguong in (200, 500):
        dai = [v for v in chinh if v["luot"] > nguong]
        phan_bo_dai[nguong] = {"so_phien": len(dai), "pct_phien": 100 * len(dai) / max(len(chinh), 1),
                               "tq": sum(v["tq_ca_phien"] for v in dai)}
    theo_du_an = collections.Counter()
    for v in phien.values():
        theo_du_an[v["du_an"]] += v["tq_ca_phien"]
    tq_ph = {sid: v["tq_chinh"] + v["tq_con"] for sid, v in phien.items()}
    song_song_tq = tq_song_song(luot_theo_phien)
    phien_dai_tq = tq_phien_dai(khoang_phien, tq_ph)
    kd = sorted(v["khoi_dong"] for v in chinh if v["khoi_dong"] is not None) or [0]
    ket = {
        "cua_so": f"{D0:%Y-%m-%d %H:%M} → {D1:%Y-%m-%d %H:%M} UTC ({N} ngày)",
        "so_ngay": N, "tep_bo_qua": bo_qua, "tong_luot_ai_chinh": sum(v["luot"] for v in chinh),
        "tong_token": dict(tong), "tq_tong": tq_tong, "tq_tro_ly_con": tq_con,
        "so_phien_chinh": len(chinh), "so_tro_ly_con": sum(v["so_con"] for v in phien.values()),
        "khoi_dong_trung_vi": kd[len(kd) // 2], "khoi_dong_tq_tong": kd_tq, "phien_cat_ngang_cua_so": sum(v["khoi_dong"] is None for v in chinh),
        "luot_ngu_canh_150k": luot150, "tq_ngu_canh_150k": tq150,
        "tq_luot_co_skill": tq_skill, "tq_luot_co_mcp": tq_mcp, "tq_song_song_4": song_song_tq, "tq_phien_song_8_gio": phien_dai_tq,
        "luot_ngu_canh_dai": sum(v["luot_ngu_canh_dai"] for v in chinh),
        "tq_ngu_canh_dai": sum(v["tq_ngu_canh_dai"] for v in chinh),
        "ti_le_trung_dem": {"chinh": 100 * tong_chinh["cr"] / max(sum(tong_chinh.values()), 1),
                            "tro_ly_con": 100 * tong_con["cr"] / max(sum(tong_con.values()), 1)},
        "tien_theo_loai_tq": dict(phan), "token_doc_lai_pct": 100 * tk_doc / max(tk_tong, 1),
        "doc_tren_moi_token_viet_ra": round(tk_doc / max(tong["out"], 1)),
        "day_cuon_so_theo_luot": {i: {"trung_vi": trung_vi(v), "so_phien": len(v)} for i, v in sorted(day.items())},
        "phien_dai": phan_bo_dai,
        "top_phien": top, "theo_du_an": dict(theo_du_an.most_common(10)),
        "con_theo_loai": {k: {**v, "model": dict(v["model"])} for k, v in
                          sorted(con_theo_loai.items(), key=lambda kv: -kv[1]["tq"])},
        "cong_cu_ky_tu_tra_ve": dict(cong_cu_kq.most_common(12)), "cong_cu_so_lan": dict(cong_cu_n),
        "doc_lai_cung_tep": sorted(doc_lai, reverse=True)[:15], "hook_chan": dict(hook.most_common(10)),
        "lenh_sleep": sleep_n, "lan_nen_phien": nen, "stop_hook_bat_lam_lai": stop_hook,
        "tq_theo_nguon_luot": dict(theo_nguon.most_common()),
        "nghi_qua_han_cache": qh_n, "tq_nghi_qua_han_cache": qh_tq, "ttl_phien_chinh": dict(ttl_dem),
        "doi_model_giua_phien": dm_n, "tq_doi_model": dm_tq, "anh_dan_vao": anh,
        "phien_chinh_theo_model": dict(model_chinh.most_common()), "theo_kenh": dict(theo_kenh.most_common()),
        "chu_ra_moi_luot_theo_model": {m: round(v["out"] / max(v["n"], 1)) for m, v in out_model.items() if v["n"] >= 20}, "cau_ngan_lap": [(c, n) for c, n in cau.most_common(25) if n >= 3],
    }
    if AN:  # giấu cả trong JSON, không chỉ trên màn hình
        ten = {d: f"dự án {i}" for i, d in enumerate(dict.fromkeys(
            [v["du_an"] for v in ket["top_phien"]] + list(ket["theo_du_an"])), 1)}
        if not AN_DU_AN:
            ten = {d: d for d in ten}
        ket["top_phien"] = [{**v, "du_an": ten[v["du_an"]], "cau_dau": ""} for v in ket["top_phien"]]
        ket["theo_du_an"] = {ten[d]: x for d, x in ket["theo_du_an"].items()}
        ket["doc_lai_cung_tep"] = [(n, an_ten_tep(f), s) for n, f, s in ket["doc_lai_cung_tep"]]
        ket["cau_ngan_lap"] = []
    if RA:
        Path(RA).write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    in_bang(ket)


def an_ten_tep(f):
    """Khi giấu: tên tệp có thể lộ việc riêng → chỉ giữ đuôi (vd 'tệp *.xlsx')."""
    d = Path(str(f)).suffix
    return f"tệp *{d}" if d else "tệp (không đuôi)"


def M(x):
    return f"{x / 1e6:,.1f}M"


def in_bang(k):
    pct = lambda a: f"{100 * a / k['tq_tong']:.0f}%" if k["tq_tong"] else "-"
    print(f"# Đo thói quen token — {k['cua_so']}\n")
    t = k["tong_token"]
    if k.get("tep_bo_qua"):
        print(f"(Bỏ qua {k['tep_bo_qua']} tệp nhật ký có định dạng lạ, không làm hỏng lần đo.)\n")
    print("Các mục dưới đây có thể trùng nhau (1 phiên vừa dài vừa bị bỏ quá hạn), KHÔNG cộng lại.\n")
    print(f"Tổng: ghi nhớ tạm mới (đọc lần đầu) {M(t.get('cc', 0))} · đọc không qua nhớ tạm {M(t.get('in', 0))} · đọc lại thứ AI còn nhớ tạm (cache) {M(t.get('cr', 0))} · AI viết ra {M(t.get('out', 0))} · "
          f"**tq {M(k['tq_tong'])}** · {k['so_phien_chinh']} phiên chính · {k['so_tro_ly_con']} trợ lý con "
          f"(con chiếm {pct(k['tq_tro_ly_con'])} tq)\n")
    print(f"1. **Khởi động phiên**: trung vị {k['khoi_dong_trung_vi'] / 1000:,.0f}k token ngữ cảnh ngay lượt đầu; "
          f"cộng mọi phiên ≈ tq {M(k['khoi_dong_tq_tong'])} ({pct(k['khoi_dong_tq_tong'])}) "
          f"— đã loại {k['phien_cat_ngang_cua_so']} phiên mở từ trước cửa sổ đo.")
    print(f"2. **Phiên kéo dài** (ngữ cảnh >{NGU_CANH_DAI // 1000}k): {k['luot_ngu_canh_dai']:,} lượt, "
          f"tq {M(k['tq_ngu_canh_dai'])} ({pct(k['tq_ngu_canh_dai'])}).")
    hans = ", ".join(f"{p} phút × {n} phiên" for p, n in k["ttl_phien_chinh"].items())
    print(f"3. **Bỏ đi quá hạn AI nhớ tạm rồi quay lại gõ tiếp** (hạn nhớ: {hans}; quá hạn phải đọc lại cả phiên giá đầy đủ): "
          f"{k['nghi_qua_han_cache']:,} lần (mức cao nhất — có thể gồm lúc công cụ chạy lâu), tq {M(k['tq_nghi_qua_han_cache'])} ({pct(k['tq_nghi_qua_han_cache'])}).")
    print(f"4. **Đổi model giữa phiên** (model mới không có trí nhớ tạm của model cũ, phải đọc lại từ đầu): {k['doi_model_giua_phien']:,} lần, "
          f"tq {M(k['tq_doi_model'])} ({pct(k['tq_doi_model'])}) · **ảnh dán vào phiên chính**: {k['anh_dan_vao']:,}.")
    print(f"5. **Nén phiên** (/compact hoặc tự nén): {k['lan_nen_phien']:,} lần · **Stop hook bắt làm lại**: {k['stop_hook_bat_lam_lai']:,} lần · "
          f"**lệnh sleep chờ**: {k['lenh_sleep']:,} lần.")
    print("6. **Theo kênh** (tq; sdk-cli = máy/lịch tự chạy `claude -p`): " + " · ".join(f"{c} {M(x)} ({pct(x)})" for c, x in k["theo_kenh"].items()))
    print("7. **Chữ AI viết ra trung bình mỗi lượt** (gồm cả phần 'suy nghĩ'; cao bất thường = effort/thinking cao hoặc trả lời dài): "
          + " · ".join(f"{m} {n:,}" for m, n in sorted(k["chu_ra_moi_luot_theo_model"].items(), key=lambda x: -x[1])))
    print("8. **Phiên chính theo model** (tq): " + " · ".join(f"{m} {M(x)}" for m, x in k["phien_chinh_theo_model"].items()))
    if any(m.startswith("fable") for m in k["phien_chinh_theo_model"]):
        print("   (ƯỚC: mọi bản fable đang tính giá nhớ tạm của Fable 5.2, 0,025×; chưa có bảng giá riêng từng bản.)")
    print(f"\n**Khớp cách gọi của `/usage` (Claude Code), % trên tổng tq — số ƯỚC theo tq, không trùng từng con số của hãng; các dòng chồng nhau, KHÔNG cộng):**")
    print(f"- Khi ngữ cảnh quá {NGU_CANH_USAGE // 1000}k: {k['luot_ngu_canh_150k']:,} lượt, {pct(k['tq_ngu_canh_150k'])}")
    print(f"- Khi có từ {SONG_SONG_TOI_THIEU} phiên chạy song song (cùng có lượt AI trong cùng {SONG_SONG_PHUT} phút): {pct(k['tq_song_song_4'])}")
    print(f"- Ở phiên sống từ {PHIEN_DAI_GIO} giờ (từ lượt đầu đến lượt cuối trong cửa sổ đo; gồm trợ lý con của phiên): {pct(k['tq_phien_song_8_gio'])}")
    print(f"- Phần nạp sẵn (lượt khởi động phiên): {pct(k['khoi_dong_tq_tong'])} · Trợ lý con: {pct(k['tq_tro_ly_con'])}")
    print(f"- Lượt AI có gọi skill: {pct(k['tq_luot_co_skill'])} · có gọi công cụ MCP: {pct(k['tq_luot_co_mcp'])} (tính cả lượt đó, ước; chỉ phiên chính)\n")
    print()
    tl = k["tien_theo_loai_tq"]
    print("## Tiền đi đâu (theo loại token)")
    print(f"- Đọc lại thứ AI còn nhớ tạm (cache, giá chỉ 5–10%): {k['token_doc_lai_pct']:.1f}% số token nhưng {pct(tl.get('doc_lai', 0))} tiền")
    print(f"- Ghi nhớ tạm mới (đọc lần đầu) / nạp lại sau khi nghỉ lâu: {pct(tl.get('ghi_moi', 0))} tiền")
    print(f"- AI viết ra (trả lời, suy nghĩ, lệnh làm việc): {pct(tl.get('viet_ra', 0))} tiền")
    td = k["ti_le_trung_dem"]
    print(f"- Mỗi 100 chữ AI đọc vào, bao nhiêu chữ AI còn nhớ tạm (được giá rẻ): phiên chính {td['chinh']:.1f} · trợ lý con {td['tro_ly_con']:.1f} "
          f"— càng gần 100 càng tốt; Anthropic canh số này như 'độ sống' hệ thống, tụt bất thường = có thói quen làm AI quên")
    print(f"- Cứ 1 token AI viết ra, nó đọc khoảng {k['doc_tren_moi_token_viet_ra']:,} token")
    print("\n## Cuốn sổ dày lên theo lượt (trung vị, phiên chính mở trong cửa sổ đo)")
    if k["day_cuon_so_theo_luot"]:
        print(" · ".join(f"lượt {i}: {v['trung_vi'] / 1000:,.0f}k ({v['so_phien']} phiên)" for i, v in k["day_cuon_so_theo_luot"].items()))
    else:
        print("(không có phiên mới mở trong cửa sổ đo — chỉ số khởi động và cuốn sổ không đo được)")
    for ng, v in k["phien_dai"].items():
        print(f"- Phiên trên {ng} lượt: {v['so_phien']} phiên ({v['pct_phien']:.1f}% số phiên) chiếm {pct(v['tq'])} tq")
    print()
    print("## Phiên tốn nhất (tính cả trợ lý con)\n| tq | % | dự án | con | lượt | ngữ cảnh max | câu đầu |\n|---|---|---|---|---|---|---|")
    for v in k["top_phien"]:
        print(f"| {M(v['tq_ca_phien'])} | {pct(v['tq_ca_phien'])} | {v['du_an']} | {v['so_con']} | {v.get('luot', '-')} | "
              f"{v.get('ngu_canh_max', 0) // 1000}k | {'(ẩn)' if AN else v['cau_dau'].replace('|', '/')} |")
    print("\n## Theo dự án\n" + " · ".join(f"{d} {M(x)} ({pct(x)})" for d, x in k["theo_du_an"].items()))
    print("\n## Trợ lý con theo loại\n| loại | số con | tq | % | tq/con | model |\n|---|---|---|---|---|---|")
    for ten, v in list(k["con_theo_loai"].items())[:12]:
        print(f"| {ten} | {v['so_con']} | {M(v['tq'])} | {pct(v['tq'])} | {v['tq'] / max(v['so_con'], 1) / 1000:,.0f}k | "
              f"{', '.join(f'{m} {n}' for m, n in v['model'].items())} |")
    print("\n## Công cụ trả về nhiều chữ nhất (chữ này nằm lại trong ngữ cảnh, đọc lại mỗi lượt sau)")
    print(" · ".join(f"{c} {x / 1e6:,.1f}M ký tự/{k['cong_cu_so_lan'].get(c, 0):,} lần" for c, x in k["cong_cu_ky_tu_tra_ve"].items()))
    print("\n## Đọc lại cùng 1 tệp ≥3 lần trong 1 phiên (top)")
    for n, f, sid in k["doc_lai_cung_tep"]:
        f = f if AN else f.replace(str(Path.home()), "~")  # khi giấu: doc_lai_cung_tep đã rút còn đuôi tệp
        print(f"- {n} lần · {f} · phiên {sid}")
    tn = k.get("tq_theo_nguon_luot") or {}
    if tn:
        print("\n## Ai khởi đầu lượt AI (phiên chính)\nMỗi lượt AI đọc lại TOÀN BỘ phiên. Lượt không do người gõ "
              "(trợ lý con báo về, chốt bắt làm lại, tin CI, máy tự chạy) cũng đọc lại cả phiên như vậy.\n")
        tn_t = sum(tn.values()) or 1
        for n, v in tn.items():
            print(f"- {n}: {M(v)} tq ({100 * v / tn_t:.0f}%)")
    print("\n## Hook chặn (mỗi lần chặn = 1 lượt làm lại)\n" + " · ".join(f"{h} {n}" for h, n in k["hook_chan"].items()))
    if AN:
        return
    print("\n## Câu ngắn người gõ lặp ≥3 lần\n" + " · ".join(f"\"{c}\" {n}" for c, n in k["cau_ngan_lap"]))


if __name__ == "__main__":
    main()
