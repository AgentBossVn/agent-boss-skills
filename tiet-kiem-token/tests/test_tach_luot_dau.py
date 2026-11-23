"""Bộ kiểm máy tách lượt đầu phiên. Nhật ký GIẢ tự dựng, không dữ liệu thật."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "tach-luot-dau-phien.py"
VIET = "Tôi muốn bạn đọc kỹ hướng dẫn dùng công cụ và trả lời bằng tiếng Việt có dấu đầy đủ. " * 20


def phien(co_shape=True, mcp="secretsrv", tong=31000):
    dong = [{"type": "attachment", "attachment": {"type": "skill_listing", "content": "- skill-a: mô tả " * 200}},
            {"type": "attachment", "attachment": {"type": "agent_listing_delta", "addedLines": ["- agent-x: việc " * 30] * 10}}]
    if co_shape:
        tools = [{"name": "Bash", "description": "run " * 500, "input_schema": {}},
                 {"name": "Read", "description": "read " * 100, "input_schema": {}},
                 {"name": f"mcp__{mcp}__tim", "description": "tim " * 300, "input_schema": {}}]
        dong.append({"type": "api-request-shape", "shape": {"system": [{"type": "text", "text": "You are Claude Code. " * 5},
                                                                      {"type": "text", "text": "x" * 20000}], "tools": tools}})
        dong.append({"type": "api-request-blob", "message": {"role": "user", "content": [
            {"type": "text", "text": "<system-reminder>\nContents of /x/CLAUDE.md:\n" + VIET + "\n</system-reminder>"},
            {"type": "text", "text": "<system-reminder>\nSessionStart hook: " + "ctx " * 400 + "\n</system-reminder>"},
            {"type": "text", "text": "làm giúp tôi việc này"}]}})
    dong.append({"type": "assistant", "message": {"usage": {"input_tokens": 3, "cache_creation_input_tokens": tong - 1000,
                                                           "cache_read_input_tokens": 1000}}})
    return "\n".join(json.dumps(d, ensure_ascii=False, separators=(",", ":")) for d in dong) + "\n"


def chay(goc, *doi):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--goc", str(goc), *doi], capture_output=True, text=True,
                          encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))


class TachLuotDau(unittest.TestCase):
    def dung(self, tmp, *phiens):
        d = Path(tmp) / "projects" / "du-an"
        d.mkdir(parents=True)
        for i, p in enumerate(phiens):
            (d / f"s{i}.jsonl").write_text(p, encoding="utf-8")

    def test_nhom_tong_khop_va_giau_ten_mcp(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.dung(tmp, phien(), phien(), phien(co_shape=False))
            r = chay(tmp, "--json", str(Path(tmp) / "k.json"))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("secretsrv", r.stdout)
            self.assertIn("máy chủ MCP 1", r.stdout)
            self.assertIn("Dùng được 2 phiên", r.stdout)  # phiên thiếu shape bị bỏ qua
            k = json.loads((Path(tmp) / "k.json").read_text(encoding="utf-8"))
            self.assertNotIn("secretsrv", json.dumps(k))
            tong = sum(k["nhom_trung_vi"].values())
            self.assertAlmostEqual(tong, k["tong_that_trung_vi"], delta=1)  # tổng khớp sau hiệu chỉnh
            n = k["nhom_trung_vi"]
            for ten in ("Công cụ có sẵn", "Công cụ MCP", "CLAUDE.md + rules + trí nhớ", "Danh sách skill", "Danh sách agent",
                        "Chữ hook chèn lúc mở phiên", "Tin người gõ đầu"):
                self.assertGreater(n[ten], 0, ten)
            self.assertEqual(k["cong_cu_to_nhat"][0]["ten"], "Bash")

    def test_con_lai_khong_bi_ep_ve_0(self):
        with tempfile.TemporaryDirectory() as tmp:  # thật 200k >> ước: giữ nguyên các phần, "Còn lại" lớn
            self.dung(tmp, phien(tong=200000))
            chay(tmp, "--json", str(Path(tmp) / "k.json"))
            k = json.loads((Path(tmp) / "k.json").read_text(encoding="utf-8"))
            self.assertEqual(k["he_so_hieu_chinh_trung_vi"], 1.0)
            self.assertGreater(k["con_lai_pct"], 30)
            self.assertAlmostEqual(sum(k["nhom_trung_vi"].values()), 200000, delta=10)
        with tempfile.TemporaryDirectory() as tmp:  # thật 5k << ước: co xuống, "Còn lại" ~0
            self.dung(tmp, phien(tong=5000))
            chay(tmp, "--json", str(Path(tmp) / "k.json"))
            k = json.loads((Path(tmp) / "k.json").read_text(encoding="utf-8"))
            self.assertLess(k["he_so_hieu_chinh_trung_vi"], 1.0)
            self.assertLess(k["con_lai_pct"], 1)

    def test_system_vai_tach_theo_tieu_de(self):
        import importlib.util
        sp = importlib.util.spec_from_file_location("t", SCRIPT)
        m = importlib.util.module_from_spec(sp)
        sys.argv = ["t"]
        sp.loader.exec_module(m)
        x = "SessionStart hook ok\n" + "Available agent types for the Agent tool:\n- a" + "MCP Server Instructions\nx" + "skills are available for use\n- s"
        self.assertEqual([k for k, _ in m.tach_khoi_system(x)],
                         ["Chữ hook chèn lúc mở phiên", "Danh sách agent", "Lời dặn MCP", "Danh sách skill"])

    def test_hien_noi_dung_hien_ten_mcp(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.dung(tmp, phien())
            self.assertIn("secretsrv", chay(tmp, "--hien-noi-dung").stdout)

    def test_khong_phien_nao_co_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.dung(tmp, phien(co_shape=False))
            r = chay(tmp)
            self.assertEqual(r.returncode, 0)
            self.assertIn("không ghi khuôn yêu cầu", r.stdout)

    def test_goc_sai_thoat_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(chay(Path(tmp) / "khong-co").returncode, 2)


if __name__ == "__main__":
    unittest.main()
