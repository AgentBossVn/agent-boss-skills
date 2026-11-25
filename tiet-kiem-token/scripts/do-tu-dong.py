#!/usr/bin/env python3
"""Tự đo lại + sổ nhớ theo dõi token. Không gọi AI: 0 token.

  python3 do-tu-dong.py chay [--ngay 7]       đo mọi agent có nhật ký, so với mốc, vẽ lại trang
  python3 do-tu-dong.py dat-lich [--gio 9]    đặt máy tự chạy `chay` mỗi 7 ngày (Mac/Linux/Windows)
  python3 do-tu-dong.py go-lich               gỡ lịch
  python3 do-tu-dong.py ghi-thay-doi "việc"   ghi 1 thay đổi vừa làm (để trang đánh dấu)
  python3 do-tu-dong.py dat-moc <YYYY-MM-DD>  chọn lần đo làm mốc so sánh
  python3 do-tu-dong.py thu-muc-hom-nay       tạo + in thư mục kết quả của hôm nay (thay `date +%F`, chạy mọi hệ điều hành)
  python3 do-tu-dong.py da-bao                đánh dấu đã báo người dùng các lần đo mới

Sổ nhớ: <thu-muc>/theo-doi.json — agent nào dùng skill (Claude, Codex, Gemini…) đầu việc
ĐỌC sổ này để biết trang ở đâu, mốc là lần nào, đã đổi gì, lần đo nào chưa báo.
"""
import argparse, datetime as dt, json, os, platform, subprocess, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows: in tiếng Việt ra tệp/ống không sập
    sys.stdout.reconfigure(encoding="utf-8")

DAY = Path(__file__).resolve().parent
sys.path.insert(0, str(DAY))
from lich_noi_dung import dung_dong_cron, dung_plist  # noqa: E402
ap = argparse.ArgumentParser()
ap.add_argument("lenh", choices=["thu-muc-hom-nay", "chay", "dat-lich", "go-lich", "ghi-thay-doi", "dat-moc", "da-bao"])
ap.add_argument("gia_tri", nargs="?")
ap.add_argument("--ngay", type=int, default=7)
ap.add_argument("--gio", type=int, default=9)
ap.add_argument("--thu-muc", help="thư mục lưu kết quả + sổ; chọn 1 lần, máy nhớ cho các lần sau")
A = ap.parse_args()
NHO = Path.home() / ".tiet-kiem-token-thu-muc"  # tệp nhỏ nhớ thư mục đã chọn (sổ nằm trong thư mục đó nên cần chỗ nhớ cố định)
if A.thu_muc:
    GOC = Path(A.thu_muc).expanduser().resolve()  # tuyệt đối: nhớ/đặt lịch không phụ thuộc thư mục đang đứng
    if GOC != (Path.home() / "tiet-kiem-token").resolve():
        NHO.write_text(str(GOC), encoding="utf-8")
    elif NHO.exists():  # chọn lại thư mục mặc định: quên lựa chọn cũ
        NHO.unlink()
else:
    nho = NHO.read_text(encoding="utf-8").strip() if NHO.exists() else ""
    GOC = (Path(nho).expanduser() if nho else Path.home() / "tiet-kiem-token").resolve()
GOC.mkdir(parents=True, exist_ok=True)
SO = GOC / "theo-doi.json"
NHAN = "vn.tiet-kiem-token.do-lai"
HOM_NAY = dt.date.today().isoformat()
THU = ["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "thứ Bảy", "Chủ nhật"]


def doc():
    return json.loads(SO.read_text(encoding="utf-8")) if SO.exists() else {}


def ghi(so):
    so["thu_muc"] = str(GOC)
    so["bang"] = str(GOC / "bang-theo-doi.html")
    tam = SO.with_suffix(".tmp")  # ghi tệp tạm rồi đổi tên: tắt máy giữa chừng không hỏng sổ
    tam.write_text(json.dumps(so, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tam, SO)


def chay_py(ten, *doi, ra=None):
    with open(ra or os.devnull, "w", encoding="utf-8") as f:
        r = subprocess.run([sys.executable, str(DAY / ten), *doi], stdout=f, stderr=subprocess.PIPE, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
    if r.returncode:
        print(f"{ten} lỗi: {r.stderr.strip()[-300:]}", file=sys.stderr)
    return r.returncode == 0


def chua_giai_thich(out):
    """Phần CHƯA CÓ TÊN của lượt đầu mỗi phiên. Ưu tiên máy tách lượt đầu (tach-luot-dau.json: phần "Còn lại");
    không có thì cách cũ: lượt đầu thật trừ phần nạp sẵn đọc từ tệp. Số TĂNG = có thứ mới nạp mỗi phiên mà máy chưa biết."""
    try:
        d = json.loads((out / "so-lieu.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    tn = d.get("tq_theo_nguon_luot") or {}
    khac = 100 * tn.get("khác", 0) / (sum(tn.values()) or 1)
    try:
        t = json.loads((out / "tach-luot-dau.json").read_text(encoding="utf-8"))
        kd, con = t["tong_that_trung_vi"], max(0, t["nhom_trung_vi"]["Còn lại"])
        d["luot_dau_tach"] = t
        cach = f"máy tách lượt đầu (trung vị {t['so_phien']} phiên, chi tiết ở tach-luot-dau.md)"
    except (OSError, ValueError, KeyError):
        try:
            n = json.loads((out / "so-lieu-nap-san.json").read_text(encoding="utf-8"))
            kd = d.get("khoi_dong_trung_vi") or 0
            con = max(0, kd - n["uoc_token_tu_tep"])
        except (OSError, ValueError, KeyError):
            return
        cach = "lượt đầu thật trừ phần nạp sẵn đọc từ tệp"
    if not kd:
        return
    d["chua_giai_thich"] = {"luot_dau_that": kd, "luot_dau_co_ten": kd - con, "luot_dau_chua_ro": con,
                            "luot_dau_chua_ro_pct": round(100 * con / kd, 1), "nguon_luot_khac_pct": round(khac, 1)}
    (out / "so-lieu.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    c = d["chua_giai_thich"]
    with open(out / "thoi-quen.md", "a", encoding="utf-8") as f:
        f.write(f"\n## Phần chưa giải thích được (để biết máy đo còn sót gì)\n"
                f"- Lượt đầu mỗi phiên: thật ~{kd / 1000:,.0f}k token, **chưa có tên ~{con / 1000:,.0f}k ({c['luot_dau_chua_ro_pct']:.0f}%)** "
                f"(cách tính: {cach}). Số này TĂNG giữa 2 lần đo = có thứ mới nạp vào mỗi phiên → xem tach-luot-dau.md hoặc gõ /context.\n"
                f"- Lượt AI không nhận ra ai khởi đầu: {khac:.0f}% token. Trên ~5% → máy đo đang sót 1 loại tin tự đến, nên báo người viết skill.\n")


def chay():
    so = doc()
    out = GOC / HOM_NAY
    out.mkdir(exist_ok=True)
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    codex = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    viec = []
    if claude.is_dir():
        viec.append(("claude", "do-thoi-quen-token.py", "so-lieu.json", "thoi-quen.md"))
    if codex.is_dir():
        viec.append(("codex", "do-token-codex.py", "so-lieu-codex.json", "codex.md"))
    if not viec:
        sys.exit("Không thấy nhật ký Claude Code hay Codex trên máy này.")
    da_do = []
    for agent, may, js, md in viec:
        if not chay_py(may, "--ngay", str(A.ngay), "--json", str(out / js), ra=out / md):
            continue
        da_do.append(agent)
    # nạp sẵn + "chưa giải thích" TRƯỚC khi so sánh: bước này ghi thêm vào so-lieu.json mà so sánh cần đọc
    if "claude" in da_do:
        chay_py("tach-luot-dau-phien.py", "--json", str(out / "tach-luot-dau.json"), ra=out / "tach-luot-dau.md")
        chay_py("do-phan-nap-san.py", "--du-an", str(Path.home()), "--json", str(out / "so-lieu-nap-san.json"), ra=out / "nap-san.md")
        chay_py("do-viec-nen-viet-may.py", "--ngay", str(A.ngay), "--json", str(out / "viec-nen-viet-may.json"), ra=out / "viec-nen-viet-may.md")
        chua_giai_thich(out)
    for agent, may, js, md in viec:
        if agent not in da_do:
            continue
        moc = so.setdefault("moc", {}).setdefault(agent, HOM_NAY)  # lần đo đầu tiên = mốc
        if moc != HOM_NAY and (GOC / moc / js).exists():
            chay_py("so-sanh-hai-lan-do.py", str(GOC / moc / js), str(out / js), ra=out / f"so-sanh-{agent}.md")
    if not da_do:  # đừng ghi lần đo rỗng vào sổ
        sys.exit("Không đo được agent nào (lỗi ở trên). Chưa ghi gì vào sổ theo dõi.")
    so["lan_do"] = [x for x in so.get("lan_do", []) if x["ngay"] != HOM_NAY] + [
        {"ngay": HOM_NAY, "agent": da_do, "da_bao": False}]
    ghi(so)
    chay_py("bang-theo-doi.py", "--thu-muc", str(GOC))
    print(f"Đã đo {', '.join(da_do) or 'không agent nào'} → {out}\nTrang: {GOC / 'bang-theo-doi.html'}")


TXT = dict(encoding="utf-8", errors="replace")


def crontab_cu():
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, **TXT)
    except FileNotFoundError:
        sys.exit("Máy này không có lệnh crontab nên không đặt/gỡ lịch tự động được. Dùng `chay` bằng tay hoặc lịch của hệ điều hành.")
    if r.returncode and "no crontab" not in (r.stderr or "").lower():
        sys.exit(f"Không đọc được crontab hiện có, dừng để khỏi ghi đè: {r.stderr.strip()}")
    return r.stdout if r.returncode == 0 else ""


def ghi_crontab(dong):
    try:
        return subprocess.run(["crontab", "-"], input="\n".join(dong) + "\n", capture_output=True, **TXT)
    except FileNotFoundError:
        sys.exit("Máy này không có lệnh crontab.")


def dat_lich():
    thu = dt.date.today().weekday()  # 0 = thứ Hai; lịch chạy đúng thứ này, tức 7 ngày sau
    py, sc = sys.executable, str(Path(__file__).resolve())
    he = platform.system()
    if he == "Darwin":
        pl = Path.home() / "Library/LaunchAgents" / f"{NHAN}.plist"
        pl.parent.mkdir(parents=True, exist_ok=True)
        pl.write_bytes(dung_plist(NHAN, py, sc, GOC, thu, A.gio))
        dom = f"gui/{os.getuid()}"
        subprocess.run(["launchctl", "bootout", dom, str(pl)], capture_output=True)
        r = subprocess.run(["launchctl", "bootstrap", dom, str(pl)], capture_output=True, **TXT)
        cach = f"launchd {pl}"
    elif he == "Windows":
        thu_en = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][thu]
        r = subprocess.run(["schtasks", "/Create", "/F", "/SC", "WEEKLY", "/D", thu_en, "/ST", f"{A.gio:02d}:00",
                            "/TN", "TietKiemToken", "/TR", f'"{py}" "{sc}" chay --thu-muc "{GOC}"'],
                           capture_output=True, **TXT)
        cach = "Task Scheduler: TietKiemToken"
    else:
        cu = crontab_cu()
        giu = [d for d in cu.splitlines() if NHAN not in d]
        giu.append(dung_dong_cron(NHAN, py, sc, GOC, thu, A.gio))
        r = ghi_crontab(giu)
        cach = "crontab"
    if r.returncode != 0:
        sys.exit(f"Đặt lịch hỏng: {(r.stderr or r.stdout).strip()}")
    so = doc()
    so["lich"] = {"mo_ta": f"{THU[thu]} hằng tuần, {A.gio}h", "cach": cach, "tao_luc": HOM_NAY}
    ghi(so)
    chay_py("bang-theo-doi.py", "--thu-muc", str(GOC))
    print(f"Đã đặt: máy tự đo {THU[thu]} hằng tuần lúc {A.gio}h ({cach}). Máy phải đang bật lúc đó.")


def go_lich():
    he = platform.system()
    if he == "Darwin":
        pl = Path.home() / "Library/LaunchAgents" / f"{NHAN}.plist"
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(pl)], capture_output=True)
        if pl.exists():
            pl.unlink()
    elif he == "Windows":
        subprocess.run(["schtasks", "/Delete", "/F", "/TN", "TietKiemToken"], capture_output=True)
    else:
        cu = crontab_cu()
        r = ghi_crontab([d for d in cu.splitlines() if NHAN not in d])
        if r.returncode:
            sys.exit(f"Gỡ lịch hỏng: {(r.stderr or r.stdout).strip()}")
    so = doc()
    so.pop("lich", None)
    ghi(so)
    chay_py("bang-theo-doi.py", "--thu-muc", str(GOC))
    print("Đã gỡ lịch tự đo.")


if A.lenh == "thu-muc-hom-nay":
    (GOC / HOM_NAY).mkdir(exist_ok=True)
    print(GOC / HOM_NAY)
elif A.lenh == "chay":
    chay()
elif A.lenh == "dat-lich":
    dat_lich()
elif A.lenh == "go-lich":
    go_lich()
else:
    so = doc()
    if A.lenh == "ghi-thay-doi":
        if not A.gia_tri:
            sys.exit('Thiếu nội dung: ghi-thay-doi "việc đã đổi"')
        so.setdefault("thay_doi", []).append({"ngay": HOM_NAY, "viec": A.gia_tri})
    elif A.lenh == "dat-moc":
        co = [a for a, js in (("claude", "so-lieu.json"), ("codex", "so-lieu-codex.json"))
              if A.gia_tri and (GOC / A.gia_tri / js).exists()]
        if not co:
            sys.exit("Không có lần đo ngày đó.")
        so.setdefault("moc", {}).update({a: A.gia_tri for a in co})
    elif A.lenh == "da-bao":
        for x in so.get("lan_do", []):
            x["da_bao"] = True
    ghi(so)
    chay_py("bang-theo-doi.py", "--thu-muc", str(GOC))
    print("Đã ghi sổ.")
