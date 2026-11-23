#!/usr/bin/env python3
"""Vẽ trang theo dõi token (1 tệp HTML, mở bằng trình duyệt, không cần mạng).

Dùng: python3 bang-theo-doi.py [--thu-muc ~/tiet-kiem-token]
Đọc mọi lần đo <thu-muc>/<ngày>/so-lieu*.json + sổ <thu-muc>/theo-doi.json
→ ghi <thu-muc>/bang-theo-doi.html. Chạy lại sau mỗi lần đo là trang mới.
Trang chỉ có số đếm, không có câu người gõ hay tên tệp.
"""
import argparse, html, importlib.util, json, re, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows: in tiếng Việt ra tệp/ống không sập
    sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
_nho = Path.home() / ".tiet-kiem-token-thu-muc"  # thư mục đã chọn, do-tu-dong.py ghi nhớ
ap.add_argument("--thu-muc", default=(_nho.read_text(encoding="utf-8").strip() if _nho.exists() else "") or str(Path.home() / "tiet-kiem-token"))
A = ap.parse_args()
GOC = Path(A.thu_muc).expanduser()

_spec = importlib.util.spec_from_file_location("ss", Path(__file__).with_name("so-sanh-hai-lan-do.py"))
ss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ss)

TEP_AGENT = {"claude": "so-lieu.json", "codex": "so-lieu-codex.json"}
TEN_AGENT = {"claude": "Claude Code", "codex": "Codex"}


def doc_so():
    p = GOC / "theo-doi.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def cac_lan_do(agent):
    ra = []
    for d in sorted(GOC.iterdir()):
        f = d / TEP_AGENT[agent]
        if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name) and f.exists():
            try:
                ra.append((d.name, json.loads(f.read_text(encoding="utf-8"))))
            except ValueError:
                print(f"Bỏ qua tệp hỏng: {f}", file=sys.stderr)
    return ra


def duong(ds, thay_doi):
    """SVG đường tq/ngày theo các lần đo, vạch dọc ở ngày có thay đổi."""
    if len(ds) < 2:
        return "<p class='nho'>Cần ít nhất 2 lần đo để vẽ đường.</p>"
    W, H, L, R, T, B = 640, 200, 56, 16, 12, 28
    y = [(v.get("tq_tong") or 0) / ss.so_ngay(v) / 1e6 for _, v in ds]
    top = max(y) * 1.15 or 1
    X = lambda i: L + i * (W - L - R) / (len(ds) - 1)
    Y = lambda v: T + (H - T - B) * (1 - v / top)
    diem = " ".join(f"{X(i):.0f},{Y(v):.0f}" for i, v in enumerate(y))
    s = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='tq mỗi ngày qua các lần đo'>"]
    for k in range(4):
        v = top * k / 3
        s.append(f"<line x1='{L}' x2='{W - R}' y1='{Y(v):.0f}' y2='{Y(v):.0f}' class='luoi'/>"
                 f"<text x='{L - 6}' y='{Y(v) + 4:.0f}' text-anchor='end'>{v:.0f}tr</text>")
    ngay_do = [n for n, _ in ds]
    for t in thay_doi:  # vạch thay đổi đặt ở lần đo đầu tiên SAU ngày thay đổi
        i = next((i for i, n in enumerate(ngay_do) if n >= t.get("ngay", "")), None)
        if i:
            s.append(f"<line x1='{X(i) - 8:.0f}' x2='{X(i) - 8:.0f}' y1='{T}' y2='{H - B}' class='vach'/>")
    s.append(f"<polyline points='{diem}' class='duong'/>")
    for i, (n, _) in enumerate(ds):
        s.append(f"<circle cx='{X(i):.0f}' cy='{Y(y[i]):.0f}' r='4' class='cham'/>"
                 f"<text x='{X(i):.0f}' y='{H - 8}' text-anchor='middle'>{n[5:]}</text>")
    return "".join(s) + "</svg>"


def khoi(agent, so):
    ds = cac_lan_do(agent)
    if not ds:
        return ""
    moc_ngay = (so.get("moc") or {}).get(agent) or ds[0][0]
    moc = next((v for n, v in ds if n == moc_ngay), ds[0][1])
    moi_ngay, moi = ds[-1]
    e = html.escape
    out = [f"<section><h2>{TEN_AGENT[agent]}</h2>",
           f"<p class='nho'>Mốc: lần đo {e(moc_ngay)} · Mới nhất: {e(moi_ngay)} · {len(ds)} lần đo</p>",
           f"<div class='hinh'>{duong(ds, so.get('thay_doi', []))}</div>"]
    if moi_ngay != moc_ngay:
        out.append("<div class='bang'><table><thead><tr><th>Chỉ số</th><th>Mốc</th><th>Mới nhất</th>"
                   "<th>Đổi</th><th>Kết quả</th></tr></thead><tbody>")
        for ten, a, b, doi, kq in ss.so(moc, moi):
            if a == "—" and b == "—":
                continue
            lop = "tot" if "tốt" in kq else "xau" if "kém" in kq else "tb"
            out.append(f"<tr><td>{e(ten)}</td><td class='so'>{e(a)}</td><td class='so'>{e(b)}</td>"
                       f"<td class='so'>{e(doi)}</td><td><span class='the {lop}'>{e(kq)}</span></td></tr>")
        out.append(f"</tbody></table></div><p class='nho'>{e(ss.khoi_luong(moc, moi))}</p>")
    return "".join(out) + "</section>"


CSS = """:root{--nen:#f5f6f8;--the:#fff;--chu:#18202a;--mo:#5d6876;--ke:#dde2e8;--nhan:#2457b3;--tot:#1d7a46;--xau:#b4302a;--tb:#6b6f76}
@media (prefers-color-scheme:dark){:root{--nen:#12171d;--the:#1a222c;--chu:#e6ebf1;--mo:#9ba7b5;--ke:#2b3643;--nhan:#79a6ee;--tot:#5fc98a;--xau:#f08079;--tb:#a7adb5}}
body{margin:0;background:var(--nen);color:var(--chu);font:15px/1.55 system-ui,sans-serif}
main{max-width:880px;margin:0 auto;padding:24px 16px 48px;display:flex;flex-direction:column;gap:24px}
h1{margin:0;font-size:1.6rem}h2{margin:0 0 4px;font-size:1.15rem}.nho{color:var(--mo);font-size:.85rem;margin:4px 0}
section{background:var(--the);border:1px solid var(--ke);border-radius:8px;padding:16px}
.hinh svg{width:100%;height:auto}.hinh text{fill:var(--mo);font-size:11px}.luoi{stroke:var(--ke)}
.duong{fill:none;stroke:var(--nhan);stroke-width:2.5}.cham{fill:var(--nhan)}.vach{stroke:var(--xau);stroke-dasharray:4 4}
.bang{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:560px;font-size:.9rem}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--ke)}th{color:var(--mo);font-size:.78rem}
.so{font-variant-numeric:tabular-nums}.the{font-size:.78rem;font-weight:600}.tot{color:var(--tot)}.xau{color:var(--xau)}.tb{color:var(--tb)}
li{margin:4px 0}"""


def main():
    so = doc_so()
    e = html.escape
    phan = [khoi(a, so) for a in TEP_AGENT]
    if not any(phan):
        raise SystemExit(f"Chưa có lần đo nào trong {GOC}.")
    td = "".join(f"<li><b>{e(t.get('ngay', ''))}</b> · {e(t.get('viec', ''))}</li>" for t in so.get("thay_doi", []))
    lich = so.get("lich") or {}
    trang = (f"<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
             f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>Theo dõi token</title>"
             f"<style>{CSS}</style></head><body><main><header><h1>Theo dõi token</h1>"
             f"<p class='nho'>Lịch tự đo: {e(lich.get('mo_ta', 'chưa đặt'))}. "
             f"tq là số quy đổi để so, không phải tiền thật hay hạn mức gói.</p></header>"
             + "".join(phan)
             + f"<section><h2>Đã thay đổi gì</h2><p class='nho'>Vạch đỏ đứt trên hình = có thay đổi trước lần đo đó.</p>"
             f"<ul>{td or '<li>Chưa ghi thay đổi nào.</li>'}</ul></section></main></body></html>")
    ra = GOC / "bang-theo-doi.html"
    ra.write_text(trang, encoding="utf-8")
    print(ra)


if __name__ == "__main__":
    main()
