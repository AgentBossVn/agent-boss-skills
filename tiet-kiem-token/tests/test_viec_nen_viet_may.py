"""Bộ kiểm máy dò việc giao lặp lại (tầng 0). Nhật ký GIẢ tự dựng, không dữ liệu thật."""
import datetime as dt, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "do-viec-nen-viet-may.py"
GIO = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).isoformat().replace("+00:00", "Z")


def phien(loi_giao, out=100, kenh="cli"):
    dong = [{"type": "user", "timestamp": GIO, "entrypoint": kenh, "message": {"role": "user", "content": loi_giao}},
            {"type": "assistant", "timestamp": GIO, "message": {"id": "m1", "model": "claude-sonnet-5-5",
             "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": out}}}]
    return "\n".join(json.dumps(d, ensure_ascii=False) for d in dong) + "\n"


def chay(goc, *doi):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--goc", str(goc), *doi], capture_output=True, text=True,
                          encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))


class ViecNenVietMay(unittest.TestCase):
    def dung(self, tmp):
        d = Path(tmp) / "projects" / "du-an"
        d.mkdir(parents=True)
        for i in range(3):  # cùng 1 việc, khác ngày → phải gom 1 nhóm
            (d / f"lap{i}.jsonl").write_text(phien(f"Đăng bài ngày {i + 10}/11 lên fanpage bí mật"), encoding="utf-8")
        (d / "le.jsonl").write_text(phien("Việc chỉ làm một lần"), encoding="utf-8")
        for i in range(3):  # máy tự chạy, có câu khung của app ở đầu
            (d / f"may{i}.jsonl").write_text(phien("Background (from the session that started this one): Soi ticket khách số "
                                                   f"{i}", kenh="sdk-cli"), encoding="utf-8")
        sub = d / "lap0" / "subagents"
        sub.mkdir(parents=True)
        for i in range(3):
            (sub / f"agent-{i}.jsonl").write_text(phien("xin chào"), encoding="utf-8")
            (sub / f"agent-{i}.meta.json").write_text(json.dumps({"agentType": "tester", "description": f"Chấm bài vòng {i}"}),
                                                      encoding="utf-8")

    def test_gom_dung_nhom_va_giau_mac_dinh(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.dung(tmp)
            r = chay(tmp, "--json", str(Path(tmp) / "kq.json"))
            self.assertEqual(r.returncode, 0, r.stderr)
            kq = json.loads((Path(tmp) / "kq.json").read_text(encoding="utf-8"))
            loai = sorted((x["loai"], x["lan"]) for x in kq["viec_lap"])
            self.assertEqual(loai, [("máy tự chạy (claude -p)", 3), ("phiên người giao", 3), ("trợ lý con: tester", 3)])
            self.assertNotIn("fanpage", r.stdout + json.dumps(kq, ensure_ascii=False))  # mặc định giấu lời giao

    def test_hien_noi_dung_khi_yeu_cau(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.dung(tmp)
            r = chay(tmp, "--hien-noi-dung", "--json", str(Path(tmp) / "kq.json"))
            self.assertIn("fanpage", r.stdout)
            self.assertNotIn("fanpage", (Path(tmp) / "kq.json").read_text(encoding="utf-8"))
            self.assertNotIn("Background (from", r.stdout)

    def test_sai_thu_muc_bao_loi(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotEqual(chay(Path(tmp) / "khong-co").returncode, 0)


if __name__ == "__main__":
    unittest.main()
