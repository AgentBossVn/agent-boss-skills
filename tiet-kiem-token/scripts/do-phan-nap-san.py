#!/usr/bin/env python3
"""Đo PHẦN NẠP SẴN đầu mỗi phiên Claude Code (thứ máy đọc trước khi bạn gõ chữ nào): CLAUDE.md, rules,
mô tả skill / agent, máy chủ MCP, hook. Chỉ đếm ký tự + tên; KHÔNG in giá trị khoá trong cấu hình.

Dùng: python3 do-phan-nap-san.py [--du-an <thư mục dự án>] [--goc ~/.claude] [--hien-noi-dung]
Mặc định GIẤU: tên skill/MCP riêng chỉ đếm + độ dài, đường dẫn CLAUDE.md rút gọn theo loại. --hien-noi-dung để tự xem, đừng chia sẻ.
Ước token theo loại chữ (uoc_token.py): ASCII ~3,8 ký tự/token, tiếng Việt có dấu ~1,7 — chỉ để so nặng nhẹ."""
import argparse, json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uoc_token import uoc_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--du-an", default=os.getcwd())
ap.add_argument("--json", help="ghi số ước (token) phần nạp sẵn đọc được từ tệp, để so với lượt đầu thật")
ap.add_argument("--hien-noi-dung", action="store_true", help="hiện tên skill, tên MCP, đường dẫn tệp — CHỈ để tự xem, đừng chia sẻ")
ap.add_argument("--goc", default=os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"))
A = ap.parse_args()
GOC, DU_AN = Path(A.goc).expanduser().resolve(), Path(A.du_an).expanduser().resolve()
if not GOC.is_dir():
    print(f"Không thấy thư mục cấu hình ở {GOC}. Kiểm tra lại --goc.", file=sys.stderr)
    sys.exit(2)
# Thư mục cấu hình cần quét, loại trùng (chạy ở thư mục home thì DU_AN/.claude chính là GOC)
CAU_HINH = list(dict.fromkeys([GOC, (DU_AN / ".claude").resolve()]))
RE_IMPORT = re.compile(r"(?:^|\s)@(~?[\w./-]+\.md)\b")
RE_MOTA = re.compile(r"^description:\s*(.+?)(?=^\w[\w-]*:|^---)", re.M | re.S)


class N(int):
    """Số ký tự, kèm .tok = ước token theo loại chữ (tiếng Việt nặng hơn tiếng Anh)."""
    def __new__(cls, text):
        o = int.__new__(cls, len(text))
        o.tok = uoc_token(text)
        return o


def json_dict(tep):
    try:
        d = json.loads(doc(tep) or "{}")
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def doc(p):
    try:
        return Path(p).expanduser().read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def claude_md(p, da=None):
    """Ký tự của 1 CLAUDE.md + các tệp nó @import (1 tầng sâu là đủ để thấy chỗ nặng)."""
    da = da if da is not None else set()
    p = Path(p).expanduser()
    if p in da or not p.is_file():
        return []
    da.add(p)
    t = doc(p)
    ra = [(str(p), N(t))]
    for im in RE_IMPORT.findall(t):
        q = (p.parent / im).expanduser() if not im.startswith(("~", "/")) else Path(im).expanduser()
        ra += [(f, n) for f, n in claude_md(q, da)] if q.is_file() else []
    return ra


def mo_ta(thu_muc, mau):
    """[(tên, số ký tự description)] của các SKILL.md / agent .md."""
    ra = []
    for p in sorted(Path(thu_muc).glob(mau)):
        m = RE_MOTA.search(doc(p).split("\n---", 2)[0] + "\n---")
        if m:
            ra.append((p.parent.name if p.name == "SKILL.md" else p.stem, N(m.group(1).strip())))
    return ra


def mcp():
    ten = set()
    cau_hinh_chinh = GOC / ".claude.json" if os.environ.get("CLAUDE_CONFIG_DIR") else Path.home() / ".claude.json"
    for tep in (cau_hinh_chinh, DU_AN / ".mcp.json", *(c / "settings.json" for c in CAU_HINH)):
        d = json_dict(tep)
        ten |= set(d.get("mcpServers") or {})
        pj = d.get("projects") or {}
        for khoa in {str(DU_AN), DU_AN.as_posix()}:
            ten |= set(((pj.get(khoa) or {}) if isinstance(pj, dict) else {}).get("mcpServers") or {})
    return sorted(ten)


def hook():
    n = 0
    teps = [c / ten for c in CAU_HINH for ten in ("settings.json", "settings.local.json")]
    for tep in dict.fromkeys(t.resolve() for t in teps):
        h = json_dict(tep).get("hooks")
        if isinstance(h, dict):
            n += sum(len(x.get("hooks") or []) for v in h.values() if isinstance(v, list) for x in v if isinstance(x, dict))
    return n


def plugin_dang_dung():
    """Plugin đã cài (installed_plugins.json) và không bị tắt → (skill [(tên, ký tự)], máy chủ MCP [tên], số hook).
    Chỉ mở đúng 3 loại tệp: SKILL.md, .mcp.json, hooks/hooks.json, và chỉ trong thư mục plugins của GOC."""
    goc_pl = (GOC / "plugins").resolve()
    bat = {}
    for c in CAU_HINH:
        for ten in ("settings.json", "settings.local.json"):
            e = json_dict(c / ten).get("enabledPlugins")
            if isinstance(e, dict):
                bat.update(e)
    cai = json_dict(goc_pl / "installed_plugins.json").get("plugins")
    skill, may_chu, n_hook, da = [], [], 0, set()
    for ten, dsach in (cai.items() if isinstance(cai, dict) else []):
        if bat.get(ten) is False or not isinstance(dsach, list):
            continue
        for b in dsach:
            if not isinstance(b, dict):
                continue
            ip = Path(str(b.get("installPath") or "")).expanduser()
            try:
                ip = ip.resolve()
            except OSError:
                continue
            if ip in da or goc_pl not in ip.parents or not ip.is_dir():
                continue
            da.add(ip)
            skill += [(f"{ten.split('@')[0]}:{t}", n) for t, n in mo_ta(ip, "skills/*/SKILL.md")]
            d = json_dict(ip / ".mcp.json")
            d = d.get("mcpServers") if isinstance(d.get("mcpServers"), dict) else d
            may_chu += [f"{ten.split('@')[0]}:{k}" for k, v in d.items() if isinstance(v, dict)]
            h = json_dict(ip / "hooks" / "hooks.json").get("hooks")
            if isinstance(h, dict):
                n_hook += sum(len(x.get("hooks") or []) for v in h.values() if isinstance(v, list) for x in v if isinstance(x, dict))
    return skill, sorted(set(may_chu)), n_hook


tk = lambda ds: f"~{sum(n.tok for _, n in ds) / 1000:,.1f}k token"
md = claude_md(GOC / "CLAUDE.md") + sum((claude_md(p) for p in sorted((GOC / "rules").rglob("*.md"))), [])
cha = DU_AN
while True:  # CLAUDE.md của dự án và mọi thư mục cha (Claude Code đọc cả)
    for ten in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
        if cha != GOC.parent or ten != ".claude/CLAUDE.md":
            md += claude_md(cha / ten)
    if cha.parent == cha:
        break
    cha = cha.parent
ma_du_an = re.sub(r"[/.]", "-", str(DU_AN))  # mã thư mục của Claude Code cho dự án này
tep_tn = GOC / "projects" / ma_du_an / "memory" / "MEMORY.md"
if not tep_tn.is_file() and "/.claude/worktrees/" in DU_AN.as_posix():  # worktree dùng trí nhớ của kho gốc
    tep_tn = GOC / "projects" / re.sub(r"[/.]", "-", DU_AN.as_posix().split("/.claude/worktrees/")[0]) / "memory" / "MEMORY.md"
if tep_tn.is_file():  # trí nhớ tự động của dự án (mục lục nạp sẵn mỗi phiên)
    md += [(str(tep_tn), N(doc(tep_tn)))]
md = list(dict(md).items())
sk = sum((mo_ta(c / "skills", "*/SKILL.md") for c in CAU_HINH), [])
pl = mo_ta(GOC / "plugins", "**/skills/*/SKILL.md")  # có thể gồm plugin đã tải mà chưa bật
ag = sum((mo_ta(c / "agents", "*.md") for c in CAU_HINH), [])
m = mcp()
sk_pl, m_pl, hook_pl = plugin_dang_dung()
c_md, c_sk, c_ag = sum(n for _, n in md), sum(n for _, n in sk), sum(n for _, n in ag)

HIEN = A.hien_noi_dung


def loai_tep(f):
    """Rút gọn đường dẫn theo loại (khi giấu): không lộ tên thư mục / tệp riêng."""
    p = Path(f)
    if p == GOC / "CLAUDE.md":
        return "CLAUDE.md toàn cục"
    if GOC / "rules" in p.parents:
        return "tệp rules"
    if p.name == "MEMORY.md" and GOC / "projects" in p.parents:
        return "trí nhớ tự động của dự án"
    if p.name in ("CLAUDE.md", "CLAUDE.local.md"):
        return "CLAUDE.md dự án"
    return "tệp @import khác"


print(f"# Phần nạp sẵn đầu phiên — dự án {str(DU_AN).replace(str(Path.home()), '~') if HIEN else '(ẩn)'}\n")
print(f"| Khối | số mục | ký tự | ước |\n|---|---|---|---|")
print(f"| CLAUDE.md + rules + @import + trí nhớ tự động dự án | {len(md)} | {c_md:,} | {tk(md)} |")
print(f"| Mô tả skill | {len(sk)} | {c_sk:,} | {tk(sk)} |")
print(f"| Mô tả skill của plugin (gồm cả plugin chưa bật — ước TRẦN) | {len(pl)} | {sum(n for _, n in pl):,} | {tk(pl)} |")
print(f"| Mô tả agent (trợ lý con tự tạo) | {len(ag)} | {c_ag:,} | {tk(ag)} |")
print(f"| Mô tả skill của plugin ĐÃ BẬT (đọc từ plugins/installed_plugins.json) | {len(sk_pl)} | {sum(n for _, n in sk_pl):,} | {tk(sk_pl)} |")
print(f"| Máy chủ MCP trong cấu hình + plugin (mỗi cái thêm mô tả công cụ) | {len(m) + len(m_pl)} | — | xem /context |")
print(f"| Hook đang cài (trong cấu hình) | {hook()} | — | mỗi lần hook chặn = 1 lượt làm lại |")
print(f"| Hook do plugin mang vào (chỉ đếm tệp hooks/hooks.json; hook khai thẳng trong plugin.json thì chưa gồm) | {hook_pl} | — | — |")
if HIEN:
    print("\n## Tệp chỉ dẫn nặng nhất")
    for f, n in sorted(md, key=lambda x: -x[1])[:8]:
        print(f"- {n:,} ký tự · {f.replace(str(Path.home()), '~')}")
    print("\n## Mô tả skill dài nhất (>500 ký tự là dài)")
    for t, n in sorted(sk, key=lambda x: -x[1])[:8]:
        print(f"- {n:,} · {t}")
    if m or m_pl:
        print("\n## Máy chủ MCP: " + ", ".join(m + m_pl))
else:
    print("\n## Tệp chỉ dẫn theo loại (tên đã ẩn)")
    theo_loai = {}
    for f, n in md:
        so_tep, kt = theo_loai.get(loai_tep(f), (0, 0))
        theo_loai[loai_tep(f)] = (so_tep + 1, kt + n)
    for ten_loai, (so_tep, kt) in sorted(theo_loai.items(), key=lambda x: -x[1][1]):
        print(f"- {ten_loai}: {so_tep} tệp, {kt:,} ký tự")
    dai = [n for _, n in sk if n > 500]
    print("\n## Mô tả skill (tên đã ẩn)")
    print(f"- {len(sk)} skill, {len(dai)} cái dài >500 ký tự; dài nhất {max((n for _, n in sk), default=0):,} ký tự")
    if m or m_pl:
        print(f"\n## Máy chủ MCP: {len(m) + len(m_pl)} (tên đã ẩn)")
if A.json:
    Path(A.json).write_text(json.dumps({"uoc_token_tu_tep": round(sum(n.tok for _, n in md + sk + ag + sk_pl)),
                                        "so_mcp": len(m) + len(m_pl)}), encoding="utf-8")
print("\nConnector cài qua app desktop / claude.ai không có trên đĩa nên máy không đọc được — số MCP có thể thiếu.")
print("\nĐối chiếu số THẬT: gõ /context trong Claude Code (đếm chính xác từng khối).")
print("Vì sao tổng ở đây nhỏ hơn lượt đầu thật của phiên: phần nền của Claude Code (lời dặn hệ thống + mô tả công cụ có sẵn) "
      "không nằm trong tệp nào nên máy không cộng được. Lượt đầu thật của phiên xem ở máy đo thói quen (mục 1 \"Khởi động phiên\"); "
      "chênh nhau chính là phần nền đó.")
