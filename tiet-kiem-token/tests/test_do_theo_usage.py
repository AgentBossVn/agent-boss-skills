"""Bộ kiểm 3 phép đo khớp `/usage`: ngữ cảnh quá 150k, từ 4 phiên chạy song song, phiên sống từ 8 giờ.
Nhật ký GIẢ tự dựng; model opus-4-8 (hệ số đọc lại 0,1) nên tq tính tay được."""
import json, tempfile, unittest
from pathlib import Path
from test_do_thoi_quen import chay, nap


def luot(sid, i, gio, vao, doc=0):
    return json.dumps({"type": "assistant", "uuid": f"{sid}{i}", "timestamp": f"2026-11-20T{gio}Z", "cwd": "/x/du-an", "entrypoint": "cli",
                       "message": {"id": f"{sid}{i}", "model": "claude-opus-4-8", "content": [],
                                   "usage": {"input_tokens": vao, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": doc}}})


class TinhHam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = nap("do-thoi-quen-token.py", "--goc", "/khong/co")

    def test_song_song_dung_nguong_4(self):
        t = 1_700_000_000 - 1_700_000_000 % 600  # đầu một ô 10 phút
        bon = {s: [(t + 60, 10.0)] for s in "abcd"}
        self.assertEqual(self.m.tq_song_song(bon), 40.0)
        ba = {s: [(t + 60, 10.0)] for s in "abc"}
        self.assertEqual(self.m.tq_song_song(ba), 0.0)
        # cùng 1 phiên nhiều lượt trong ô vẫn chỉ là 1 phiên
        self.assertEqual(self.m.tq_song_song({"a": [(t + 1, 5.0), (t + 2, 5.0)] * 4}), 0.0)

    def test_song_song_khac_o_khong_tinh(self):
        t = 1_700_000_000 - 1_700_000_000 % 600
        ls = {s: [(t + 60 + 600 * i, 1.0)] for i, s in enumerate("abcd")}  # mỗi phiên một ô riêng
        self.assertEqual(self.m.tq_song_song(ls), 0.0)

    def test_phien_dai_dung_moc_8_gio(self):
        khoang = {"a": (0, 8 * 3600), "b": (0, 8 * 3600 - 1), "c": (100, 100)}
        tq = {"a": 5.0, "b": 7.0, "c": 9.0}
        self.assertEqual(self.m.tq_phien_dai(khoang, tq), 5.0)  # đúng 8 giờ tính, thiếu 1 giây không


class DoTrenNhatKy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        pj = Path(cls.tmp.name) / "projects" / "x"
        pj.mkdir(parents=True)
        for s in "ABCD":  # 4 phiên cùng hoạt động trong ô 10:00–10:10, mỗi phiên 2 lượt × 1000 tq
            (pj / f"{s}.jsonl").write_text(luot(s, 1, "10:01:00", 1000) + "\n" + luot(s, 2, "10:04:00", 1000) + "\n", encoding="utf-8")
        # E sống 9 giờ, chạy một mình; lượt cuối ngữ cảnh 161k (>150k): tq = 1000 + 0,1 × 160000 = 17000
        (pj / "E.jsonl").write_text(luot("E", 1, "03:00:00", 1000) + "\n" + luot("E", 2, "12:00:00", 1000, doc=160_000) + "\n", encoding="utf-8")
        js = Path(cls.tmp.name) / "ra.json"
        cls.r = chay("do-thoi-quen-token.py", "--goc", cls.tmp.name, "--ngay", "3650", "--json", str(js))
        cls.k = json.loads(js.read_text(encoding="utf-8")) if js.exists() else {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_chay_khong_loi(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr)
        self.assertAlmostEqual(self.k["tq_tong"], 26000.0, places=3)

    def test_ngu_canh_150k(self):
        self.assertEqual(self.k["luot_ngu_canh_150k"], 1)
        self.assertAlmostEqual(self.k["tq_ngu_canh_150k"], 17000.0, places=3)

    def test_bon_phien_song_song(self):
        self.assertAlmostEqual(self.k["tq_song_song_4"], 8000.0, places=3)

    def test_phien_song_8_gio(self):
        self.assertAlmostEqual(self.k["tq_phien_song_8_gio"], 18000.0, places=3)

    def test_nhan_khop_usage_tren_man_hinh(self):
        for chu in ("Khớp cách gọi của `/usage`", "Khi ngữ cảnh quá 150k", "từ 4 phiên chạy song song", "phiên sống từ 8 giờ"):
            self.assertIn(chu, self.r.stdout)


if __name__ == "__main__":
    unittest.main()


class LuotCoSkillMcp(unittest.TestCase):
    def test_dem_luot_goi_skill_va_mcp(self):
        def dong(i, ten):
            return json.dumps({"type": "assistant", "uuid": f"u{i}", "timestamp": f"2026-11-20T10:0{i}:00Z", "cwd": "/x", "message": {
                "id": f"m{i}", "model": "claude-opus-4-8", "usage": {"input_tokens": 1000, "output_tokens": 0},
                "content": [{"type": "tool_use", "id": f"t{i}", "name": ten, "input": {}}]}})
        with tempfile.TemporaryDirectory() as d:
            pj = Path(d) / "projects" / "x"
            pj.mkdir(parents=True)
            (pj / "a.jsonl").write_text("\n".join([dong(1, "Skill"), dong(2, "mcp__abc__tim"), dong(3, "Read")]) + "\n", encoding="utf-8")
            js = Path(d) / "ra.json"
            r = chay("do-thoi-quen-token.py", "--goc", d, "--ngay", "3650", "--json", str(js))
            k = json.loads(js.read_text(encoding="utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertAlmostEqual(k["tq_luot_co_skill"], 1000.0, places=3)
        self.assertAlmostEqual(k["tq_luot_co_mcp"], 1000.0, places=3)


class DocBaoCaoInsights(unittest.TestCase):
    HTML = ('<style>.x{}</style><h1>Claude Code Insights</h1><p>100 messages across 5 sessions (30 total) | 2026-11-01 to 2026-11-25</p>'
            '<div>Primary Friction Types Wrong Approach 7 Buggy Code 3 Misunderstood Request 2 Inferred Satisfaction (model-estimated)</div>'
            '<code class="cmd-code">## Scope discipline\n- Do only what was asked.</code>'
            '<div class="feature-title">Hooks</div><div class="pattern-title">Restate the requirements</div><script>alert(1)</script>')

    def test_doc_so_vuong_va_goi_y(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "usage-data").mkdir()
            (Path(d) / "usage-data" / "report-x.html").write_text(self.HTML, encoding="utf-8")
            r = chay("doc-bao-cao-insights.py", "--goc", d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Wrong Approach 7", r.stdout)
        self.assertIn("**9** lần", r.stdout)            # 7 sai hướng + 2 hiểu sai
        self.assertIn("100 tin trong 5 phiên", r.stdout)
        self.assertIn("Scope discipline", r.stdout)
        self.assertIn("Hooks", r.stdout)
        self.assertNotIn("alert(1)", r.stdout)

    def test_khong_co_bao_cao_thoat_ma_2(self):
        with tempfile.TemporaryDirectory() as d:
            r = chay("doc-bao-cao-insights.py", "--goc", d)
        self.assertEqual(r.returncode, 2)
        self.assertIn("/insights", r.stderr)


class InsightsHtmlLa(unittest.TestCase):
    def test_html_lap_khong_treo(self):
        import time
        for h in ("<" * 200_000, "<script>" * 20_000, "Primary Friction Types " + "Abc " * 60_000, ""):
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / "usage-data").mkdir()
                (Path(d) / "usage-data" / "report.html").write_text(h, encoding="utf-8")
                t = time.time()
                r = chay("doc-bao-cao-insights.py", "--goc", d)
                self.assertLess(time.time() - t, 5, h[:20])
                self.assertEqual(r.returncode, 0, r.stderr)
