#!/usr/bin/env python3
"""Tách LƯỢT ĐẦU mỗi phiên Claude Code ra từng phần (lời dặn hệ thống, công cụ, CLAUDE.md, skill, agent, MCP, hook…).
Đọc nhật ký `<goc>/projects/*/*.jsonl`: dòng api-request-shape (system + tools), api-request-blob (tin đầu + khối
system-reminder), attachment trước lượt AI đầu, usage lượt đầu. Ước token theo loại chữ rồi HIỆU CHỈNH tỉ lệ cho tổng
khớp token thật. Bản Claude Code không ghi api-request-shape → bỏ qua phiên đó.

Dùng: python3 tach-luot-dau-phien.py [--so-phien 10] [--goc ~/.claude] [--json tep] [--hien-noi-dung]
Mặc định GIẤU tên máy chủ MCP (chỉ "máy chủ MCP 1/2…"). Tên công cụ hệ thống (Bash, Read…) không phải riêng tư nên được hiện."""
import argparse, json, os, re, statistics, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uoc_token import uoc_token  # noqa: E402

NHOM = ["Lời dặn hệ thống (lõi)", "Lời dặn hệ thống (khối riêng của app)", "Công cụ có sẵn", "Công cụ MCP", "CLAUDE.md + rules + trí nhớ",
        "Danh sách skill", "Danh sách agent", "Lời dặn MCP", "Chữ hook chèn lúc mở phiên", "Tin người gõ đầu"]
RE_SR = re.compile(r"<system-reminder>(.*?)</system-reminder>", re.S)


def phan_loai_nhac(t):
    d = t[:400].lower()
    if "mcp server instructions" in d:
        return "Lời dặn MCP"
    if "available agent types" in d or "agent types" in d[:150]:
        return "Danh sách agent"
    if "skills are available" in d or "available skills" in d:
        return "Danh sách skill"
    if "instructions are shown below" in d or "contents of" in d:
        return "CLAUDE.md + rules + trí nhớ"
    return "Chữ hook chèn lúc mở phiên"


MOC_SYSTEM = [("Available agent types for the Agent tool", "Danh sách agent"), ("MCP Server Instructions", "Lời dặn MCP"),
              ("skills are available for use", "Danh sách skill"), ("currentTime", "Chữ hook chèn lúc mở phiên")]


def tach_khoi_system(x):
    """Tách khối vai system theo tiêu đề từng phần; phần trước tiêu đề đầu tiên (SessionStart hook…) là chữ hook."""
    cat = sorted((x.find(m), k) for m, k in MOC_SYSTEM if x.find(m) >= 0)
    dau = [(0, "Chữ hook chèn lúc mở phiên")] + cat if not cat or cat[0][0] > 0 else cat
    return [(k, x[a:(dau[i + 1][0] if i + 1 < len(dau) else len(x))]) for i, (a, k) in enumerate(dau)]


def doc_phien(p, bang_chung=None):
    """→ dict {tong_that, ten_cong_cu:{ten:tokens}, nhom:{...}} hoặc None nếu thiếu shape / usage."""
    shape, blob_user, blob_sys, att = None, [], [], []
    tong = None
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            for dong in f:
                if not any(k in dong for k in ('"type":"assistant"', '"type":"attachment"', '"type":"api-request-')):
                    continue
                try:
                    o = json.loads(dong)
                except ValueError:
                    continue
                t = o.get("type")
                if t == "api-request-shape" and shape is None:
                    shape = o.get("shape") or {}
                elif t == "api-request-blob" and isinstance(o.get("message"), dict):
                    m = o["message"]
                    (blob_user if m.get("role") == "user" else blob_sys).append(m.get("content"))
                elif t == "attachment" and isinstance(o.get("attachment"), dict):
                    att.append(o["attachment"])
                elif t == "assistant":
                    u = (o.get("message") or {}).get("usage") or {}
                    s = sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                    if s:
                        tong = s
                        break
    except OSError:
        return None
    if not shape or not tong or not shape.get("tools"):  # thiếu khuôn / không có công cụ = không phải phiên tương tác thường
        return None
    ch = {k: 0.0 for k in NHOM}
    for i, b in enumerate(shape.get("system") or []):
        x = b.get("text", "") if isinstance(b, dict) else str(b)
        ch["Lời dặn hệ thống (khối riêng của app)" if i >= 2 and len(x) > 10000 else "Lời dặn hệ thống (lõi)"] += uoc_token(x)
    cong_cu = {}
    for tl in shape.get("tools") or []:
        if isinstance(tl, dict):
            cong_cu[str(tl.get("name") or "?")] = uoc_token(json.dumps(tl, ensure_ascii=False))
    for ten, n in cong_cu.items():
        ch["Công cụ MCP" if ten.startswith("mcp__") else "Công cụ có sẵn"] += n
    for content in blob_user[:1]:  # tin người dùng đầu tiên
        for b in content if isinstance(content, list) else [{"type": "text", "text": str(content or "")}]:
            if not isinstance(b, dict) or b.get("type") != "text":
                continue
            x = b.get("text", "")
            for m in RE_SR.finditer(x):
                ch[phan_loai_nhac(m.group(1))] += uoc_token(m.group(0))
                if bang_chung is not None:
                    bang_chung.append({"user": (phan_loai_nhac(m.group(1)), len(m.group(0)), m.group(1).strip()[:80])})
            ch["Tin người gõ đầu"] += uoc_token(RE_SR.sub("", x))
    for content in blob_sys:  # khối vai "system" = nhiều tin hệ thống nối nhau: chữ hook + danh sách agent + lời dặn MCP + danh sách skill
        for b in content if isinstance(content, list) else []:
            if isinstance(b, dict):
                for k, x in tach_khoi_system(b.get("text", "")):
                    ch[k] += uoc_token(x)
    if bang_chung is not None:
        bang_chung.append({"system": [(k, len(x), x[:80]) for c in blob_sys for b in (c if isinstance(c, list) else []) if isinstance(b, dict)
                                      for k, x in tach_khoi_system(b.get("text", ""))]})
    ten_tep = {"skill_listing": ("Danh sách skill", lambda a: a.get("content", "")),
               "agent_listing_delta": ("Danh sách agent", lambda a: "\n".join(a.get("addedLines") or [])),
               "mcp_instructions_delta": ("Lời dặn MCP", lambda a: "\n".join(a.get("addedBlocks") or [])),
               "deferred_tools_delta": ("Công cụ có sẵn", lambda a: "\n".join(a.get("addedLines") or []))}
    co = {k for k in NHOM if ch[k] > 0}
    for a in att:  # attachment bù cho phần chưa thấy trong khối tin đầu (tránh đếm trùng)
        k = ten_tep.get(a.get("type"))
        if k and k[0] not in co:
            ch[k[0]] += uoc_token(str(k[1](a)))
        elif a.get("type") == "hook_additional_context" and not blob_sys and "Chữ hook chèn lúc mở phiên" not in co:
            ch["Chữ hook chèn lúc mở phiên"] += uoc_token(str(a.get("content", "")))
    tong_uoc = sum(ch.values())
    he_so = min(1.0, tong / tong_uoc) if tong_uoc else 1.0  # chỉ CO XUỐNG khi ước thô > thật; ước thiếu thì phần thiếu = "Còn lại"
    ch = {k: v * he_so for k, v in ch.items()}
    cong_cu = {k: v * he_so for k, v in cong_cu.items()}
    ch["Còn lại"] = tong - sum(ch.values())
    return {"tong_that": tong, "he_so": he_so, "nhom": ch, "cong_cu": cong_cu}


def tach(goc, so_phien=10, hien=False):
    tep = sorted(Path(goc).glob("projects/*/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:400]
    ds = []
    for p in tep:
        r = doc_phien(p)
        if r:
            ds.append(r)
        if len(ds) >= so_phien:
            break
    return ds, len(tep)


def trung_vi(xs):
    return statistics.median(xs) if xs else 0.0


def tong_hop(ds, hien=False):
    nhom = {k: trung_vi([d["nhom"].get(k, 0) for d in ds]) for k in NHOM + ["Còn lại"]}
    tong = trung_vi([d["tong_that"] for d in ds])
    may_chu = {}  # tên máy chủ → [token mỗi phiên]
    top = {}
    for i, d in enumerate(ds):
        for ten, n in d["cong_cu"].items():
            if ten.startswith("mcp__"):
                sv = ten.split("__")[1] if ten.count("__") >= 2 else ten
                may_chu.setdefault(sv, [0] * len(ds))[i] += n
            else:
                top.setdefault(ten, [0] * len(ds))[i] = n
    mc = sorted(((trung_vi(v), k) for k, v in may_chu.items()), reverse=True)
    t5 = sorted(((trung_vi(v), k) for k, v in top.items()), reverse=True)[:5]
    return {"so_phien": len(ds), "tong_that_trung_vi": tong, "he_so_hieu_chinh_trung_vi": trung_vi([d["he_so"] for d in ds]),
            "nhom_trung_vi": nhom, "cong_cu_to_nhat": [{"ten": k, "token": round(v)} for v, k in t5],
            "mcp_theo_may_chu": [{"ten": k if hien else f"máy chủ MCP {i + 1}", "token": round(v)} for i, (v, k) in enumerate(mc)],
            "con_lai_pct": round(100 * max(0, nhom["Còn lại"]) / tong, 1) if tong else 0.0}


def in_bao_cao(k):
    t = k["tong_that_trung_vi"]
    print(f"# Lượt đầu mỗi phiên tách theo phần — trung vị {k['so_phien']} phiên (lượt đầu thật ~{t / 1000:,.0f}k token)\n")
    print(f"Hệ số hiệu chỉnh (chỉ co xuống khi ước vượt thật; 1,00 = giữ nguyên; trung vị): {k['he_so_hieu_chinh_trung_vi']:.2f}\n")
    print("| Phần | token (~) | % lượt đầu |\n|---|---|---|")
    for ten, v in k["nhom_trung_vi"].items():
        print(f"| {ten} | {v / 1000:,.1f}k | {100 * v / t if t else 0:.0f}% |")
    print(f"\nĐã giải thích được {100 - k['con_lai_pct']:.0f}% lượt đầu; còn lại {k['con_lai_pct']:.0f}% (~{k['nhom_trung_vi']['Còn lại'] / 1000:,.1f}k) "
          f"= thật trừ tổng các phần ước (ảnh dán, khối chưa nhận ra, hoặc ước theo chữ thấp hơn thật).")
    if k["he_so_hieu_chinh_trung_vi"] < 1:
        print(f"Các phần đã co xuống ×{k['he_so_hieu_chinh_trung_vi']:.2f} vì ước thô vượt số thật.")
    print("\n## 5 công cụ có sẵn to nhất")
    for c in k["cong_cu_to_nhat"]:
        print(f"- {c['ten']}: ~{c['token'] / 1000:,.1f}k")
    if k["mcp_theo_may_chu"]:
        print("\n## Công cụ MCP theo máy chủ")
        for c in k["mcp_theo_may_chu"]:
            print(f"- {c['ten']}: ~{c['token'] / 1000:,.1f}k")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-phien", type=int, default=10)
    ap.add_argument("--goc", default=os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"))
    ap.add_argument("--json", help="ghi số tổng hợp ra tệp JSON")
    ap.add_argument("--hien-noi-dung", action="store_true", help="hiện tên máy chủ MCP — chỉ để tự xem, đừng chia sẻ")
    A = ap.parse_args()
    goc = Path(A.goc).expanduser()
    if not (goc / "projects").is_dir():
        print(f"Không thấy nhật ký ở {goc}/projects. Kiểm tra lại --goc.", file=sys.stderr)
        sys.exit(2)
    ds, da_quet = tach(goc, A.so_phien)
    if not ds:
        print("Bản Claude Code này không ghi khuôn yêu cầu (api-request-shape) — dùng /context để xem lượt đầu.")
        sys.exit(0)
    k = tong_hop(ds, A.hien_noi_dung)
    in_bao_cao(k)
    print(f"\nDùng được {len(ds)} phiên (quét {da_quet} nhật ký gần nhất; phiên thiếu khuôn yêu cầu hoặc usage bị bỏ qua).")
    if A.json:
        Path(A.json).write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
