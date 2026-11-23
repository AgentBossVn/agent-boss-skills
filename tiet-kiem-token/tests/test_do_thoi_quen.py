"""Bộ kiểm tự động cho các máy đo. Chạy: python3 -B -m unittest discover -s tests (không cần cài gì).
Dữ liệu mẫu trong tests/mau là nhật ký GIẢ tự dựng, không phải dữ liệu thật của ai."""
import importlib.util, json, os, plistlib, shlex, subprocess, sys, tempfile, time, unittest
from pathlib import Path

GOC_SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = GOC_SKILL / "scripts"
MAU = Path(__file__).resolve().parent / "mau"


def chay(ten, *doi):
    return subprocess.run([sys.executable, "-B", str(SCRIPTS / ten), *doi], capture_output=True, text=True,
                          encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1"))


def nap(ten, *argv):
    """Nạp 1 script (tên có gạch ngang) làm module để thử hàm; argv giả để argparse đầu tệp không đọc lệnh thật."""
    cu = sys.argv
    sys.argv = [ten, *argv]
    try:
        spec = importlib.util.spec_from_file_location(ten.replace("-", "_").replace(".py", ""), SCRIPTS / ten)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    finally:
        sys.argv = cu


class DoThoiQuen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.js = Path(cls.tmp.name) / "ra.json"
        # nhật ký mẫu ghi ngày 20/11/2026: lấy cửa sổ rất rộng để không bao giờ hết hạn
        cls.r = chay("do-thoi-quen-token.py", "--goc", str(MAU), "--ngay", "3650", "--json", str(cls.js))
        cls.k = json.loads(cls.js.read_text(encoding="utf-8")) if cls.js.exists() else {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_chay_khong_loi(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr)

    def test_tq_tong_tinh_dung_tay(self):
        # opus-4-8, hệ số đọc 0,1: 1.25*cc + 0.1*cr + in + 5*out từng lượt
        # 1760 + 605 + 345 + 242,5 + 177,5 = 3130
        self.assertAlmostEqual(self.k["tq_tong"], 3130.0, places=3)

    def test_phan_nguon_luot(self):
        n = self.k["tq_theo_nguon_luot"]
        self.assertAlmostEqual(n["người gõ"], 2365.0, places=3)
        self.assertAlmostEqual(n["chốt bắt làm lại"], 345.0, places=3)
        self.assertAlmostEqual(n["trợ lý con / phiên khác báo về"], 242.5, places=3)
        self.assertAlmostEqual(n["người gõ: khen / chê / tán gẫu"], 177.5, places=3)
        self.assertEqual(self.k["stop_hook_bat_lam_lai"], 1)

    def test_dong_tong_co_input_khong_qua_nho_tam(self):
        self.assertIn("đọc không qua nhớ tạm", self.r.stdout)
        self.assertIn("ghi nhớ tạm mới (đọc lần đầu)", self.r.stdout)
        self.assertNotIn("đọc mới", self.r.stdout)

    def test_mac_dinh_giau_ten_du_an_va_cau_nguoi_go(self):
        self.assertNotIn("du-an-mau", self.r.stdout)
        self.assertNotIn("Làm giúp tôi", self.r.stdout)
        self.assertNotIn("du-an-mau", self.js.read_text(encoding="utf-8"))

    def test_hien_du_an_chi_mo_ten_du_an(self):
        r = chay("do-thoi-quen-token.py", "--goc", str(MAU), "--ngay", "3650", "--hien-du-an")
        self.assertIn("du-an-mau", r.stdout)
        self.assertNotIn("Làm giúp tôi", r.stdout)

    def test_goc_rong_thoat_ma_2(self):
        with tempfile.TemporaryDirectory() as d:
            for goc in (d, str(Path(d) / "khong-co")):
                r = chay("do-thoi-quen-token.py", "--goc", goc)
                self.assertEqual(r.returncode, 2)
                self.assertIn("Kiểm tra lại --goc", r.stderr)
                self.assertNotIn("Tổng:", r.stdout)

    def test_codex_goc_rong_thoat_ma_2(self):
        with tempfile.TemporaryDirectory() as d:
            r = chay("do-token-codex.py", "--goc", d)
            self.assertEqual(r.returncode, 2)
            self.assertIn("Kiểm tra lại --goc", r.stderr)

    def test_phan_nap_san_goc_sai_thoat_ma_2(self):
        r = chay("do-phan-nap-san.py", "--goc", str(Path(MAU) / "khong-co"))
        self.assertEqual(r.returncode, 2)


class DoChoGoiAi(unittest.TestCase):
    def test_khong_tu_do_ra_thu_muc_skill(self):
        r = chay("do-cho-goi-ai-trong-code.py", str(GOC_SKILL.parent))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(str(GOC_SKILL), r.stdout)
        r2 = chay("do-cho-goi-ai-trong-code.py", str(GOC_SKILL))
        self.assertIn("Không thấy code nào gọi AI", r2.stdout)

    def test_bo_test_chu_thich_whisper_va_bat_thieu_tran(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "bot.py").write_text('import anthropic\nx = "claude-sonnet-4-6"\n# "claude-opus-4-8" chỉ là chú thích\n', encoding="utf-8")
            (d / "bot.test.py").write_text('import anthropic\n"claude-haiku-4-5"\n', encoding="utf-8")
            (d / "cpp.sh").write_text('./whisper-cpp -m x\nfaster-whisper\n', encoding="utf-8")
            (d / "router.js").write_text('fetch("https://openrouter.ai/api"); const m = "deepseek/deepseek-chat";\n', encoding="utf-8")
            out = chay("do-cho-goi-ai-trong-code.py", str(d)).stdout
        self.assertIn("claude-sonnet-4-6", out)
        self.assertNotIn("claude-opus-4-8", out)       # dòng chú thích
        self.assertNotIn("claude-haiku-4-5", out)      # tệp test
        self.assertIn("deepseek/deepseek-chat", out)   # tiền tố OpenRouter
        self.assertIn("Chạy trên máy, 0đ", out)
        self.assertIn("Chưa đặt trần chữ viết ra", out)
        self.assertIn("MẪU CHỮ", out)


class TanGau(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = nap("do-thoi-quen-token.py", "--goc", "/khong/co")

    def test_la_tan_gau(self):
        for c in ("cảm ơn em", "tốt lắm, giỏi quá!", "ngu thế", "👍", "haha", "chào em", "em giỏi thật"):
            self.assertTrue(self.m.la_tan_gau(c), c)

    def test_khong_phai_tan_gau(self):
        for c in ("ok", "làm đi", "cảm ơn, giờ sửa file X", "đm sai rồi làm lại", "hay quá, thêm phần Y nữa"):
            self.assertFalse(self.m.la_tan_gau(c), c)

    def test_cau_treo_chay_nhanh(self):
        t = time.time()
        self.assertFalse(self.m.la_tan_gau("hi" * 29 + " làm đi"))
        self.assertFalse(self.m.la_tan_gau("ha" * 25 + "!" + "x"))
        self.assertLess(time.time() - t, 0.1)

    def test_he_so_model_co_hau_to_ngay(self):
        self.assertEqual(self.m.he_so_doc("sonnet-5-5"), 0.05)
        self.assertEqual(self.m.he_so_doc("sonnet-5-5-20261101"), 0.05)
        self.assertEqual(self.m.he_so_doc("opus-4-8"), 0.1)


class DongLaKhongSap(unittest.TestCase):
    def test_claude_dong_lach_chuan(self):
        dong_chuan = (MAU / "projects/du-an-mau/phien-mau.jsonl").read_text(encoding="utf-8").splitlines()
        la = ['{"type":"assistant","timestamp":"2026-11-20T10:02:00Z","message":"chuoi"}',
              '{"type":"assistant","timestamp":"2026-11-20T10:02:01Z","message":{"usage":"chuoi","id":"x"}}',
              '{"type":"user","timestamp":"2026-11-20T10:02:02Z","origin":"chuoi","message":{"content":5}}',
              '{"type":"user","timestamp":"2026-11-20T10:02:03Z","message":{"content":[{"type":"text","text":7}]}}',
              '[1,2]', '"abc"', 'khong phai json']
        with tempfile.TemporaryDirectory() as d:
            pj = Path(d) / "projects" / "x"
            pj.mkdir(parents=True)
            (pj / "a.jsonl").write_text("\n".join(dong_chuan + la) + "\n", encoding="utf-8")
            (Path(d) / "projects" / "hong.jsonl").symlink_to(Path(d) / "khong-ton-tai.jsonl")
            r = chay("do-thoi-quen-token.py", "--goc", d, "--ngay", "3650")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Tổng:", r.stdout)

    def test_tep_hong_bi_bo_qua_va_dem(self):
        m = nap("do-thoi-quen-token.py", "--goc", "/khong/co")
        # do_tep ném lỗi lạ → main bỏ qua tệp đó, vẫn đo tệp khác, in số tệp bỏ qua
        with tempfile.TemporaryDirectory() as d:
            pj = Path(d) / "projects" / "x"
            pj.mkdir(parents=True)
            (pj / "tot.jsonl").write_text((MAU / "projects/du-an-mau/phien-mau.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
            (pj / "xau.jsonl").write_text("{}\n", encoding="utf-8")
            goc_do = m.do_tep
            def gia(p):
                if p.name == "xau.jsonl":
                    raise AttributeError("lạ")
                return goc_do(p)
            m.do_tep, m.GOC, m.D0 = gia, Path(d) / "projects", m.D0.replace(year=2000)
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                m.main()
        self.assertIn("Bỏ qua 1 tệp", buf.getvalue())

    def test_codex_dong_lach_chuan(self):
        with tempfile.TemporaryDirectory() as d:
            ss = Path(d) / "sessions"
            ss.mkdir()
            ts = "2099-01-01T00:00:00Z"
            (ss / "a.jsonl").write_text("\n".join([
                json.dumps({"type": "turn_context", "payload": {"model": "gpt-x"}}),
                json.dumps({"type": "event_msg", "timestamp": ts, "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 100, "cached_input_tokens": 50, "output_tokens": 10}}}}),
                json.dumps({"type": "event_msg", "timestamp": ts, "payload": {"type": "token_count", "info": "chuoi"}}),
                json.dumps({"type": "event_msg", "timestamp": ts, "payload": {"type": "token_count", "info": {"last_token_usage": "chuoi"}}}),
                "[1]", '"s"']) + "\n", encoding="utf-8")
            (ss / "b.jsonl").write_text(json.dumps({"type": "token_usage_record", "timestamp": ts, "payload": {"usage": ["x"], "response_id": ["r"]}}) + "\n", encoding="utf-8")
            (ss / "hong.jsonl").symlink_to(Path(d) / "khong-ton-tai")
            r = chay("do-token-codex.py", "--goc", d, "--ngay", "36500")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 lượt trả lời", r.stdout)


class GiauTenTep(unittest.TestCase):
    def _nhat_ky(self, d):
        pj = Path(d) / "projects" / "x"
        pj.mkdir(parents=True)
        dong = []
        for i in range(3):
            dong.append(json.dumps({"type": "assistant", "uuid": f"a{i}", "timestamp": "2026-11-20T10:00:0%dZ" % i, "message": {
                "id": f"m{i}", "model": "claude-opus-4-8", "usage": {"input_tokens": 1, "output_tokens": 1},
                "content": [{"type": "tool_use", "id": f"t{i}", "name": "Read", "input": {"file_path": "/x/luong-nhan-vien-bi-mat.xlsx"}}]}}))
        (pj / "a.jsonl").write_text("\n".join(dong) + "\n", encoding="utf-8")

    def test_mac_dinh_chi_giu_duoi_tep(self):
        with tempfile.TemporaryDirectory() as d:
            self._nhat_ky(d)
            js = Path(d) / "ra.json"
            r = chay("do-thoi-quen-token.py", "--goc", d, "--ngay", "3650", "--json", str(js))
            kq_json = js.read_text(encoding="utf-8")
            r2 = chay("do-thoi-quen-token.py", "--goc", d, "--ngay", "3650", "--hien-noi-dung")
        self.assertNotIn("bi-mat", r.stdout + kq_json)
        self.assertIn("tệp *.xlsx", r.stdout)
        self.assertIn("luong-nhan-vien-bi-mat.xlsx", r2.stdout)


class NapSanGiau(unittest.TestCase):
    def _goc(self, d):
        g = Path(d) / "cfg"
        (g / "skills" / "mot-skill-rieng").mkdir(parents=True)
        (g / "skills" / "mot-skill-rieng" / "SKILL.md").write_text("---\nname: mot-skill-rieng\ndescription: mo ta ngan\n---\nthan\n", encoding="utf-8")
        (g / "CLAUDE.md").write_text("xin chao", encoding="utf-8")
        (g / "plugins").mkdir()
        (g / "plugins" / "installed_plugins.json").write_text('{"plugins": {"p@m": ["chuoi", 5, {"installPath": "/khong"}]}}', encoding="utf-8")
        return g

    def test_mac_dinh_giau_va_co_the_hien(self):
        with tempfile.TemporaryDirectory() as d:
            g = self._goc(d)
            r = chay("do-phan-nap-san.py", "--goc", str(g), "--du-an", d)
            r2 = chay("do-phan-nap-san.py", "--goc", str(g), "--du-an", d, "--hien-noi-dung")
        self.assertEqual(r.returncode, 0, r.stderr)  # mục installed_plugins là chuỗi cũng không sập
        self.assertNotIn("mot-skill-rieng", r.stdout)
        self.assertIn("CLAUDE.md toàn cục", r.stdout)
        self.assertIn("mot-skill-rieng", r2.stdout)


class LichTuDong(unittest.TestCase):
    DUONG = Path("/tmp/thu muc & 'la' 100%/tiet kiem")

    def test_plist_doc_lai_duoc(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            import lich_noi_dung as ln
        finally:
            sys.path.pop(0)
        b = ln.dung_plist("nhan.thu", "/usr/bin/py thon", self.DUONG / "do-tu-dong.py", self.DUONG, 2, 9)
        d = plistlib.loads(b)
        self.assertEqual(d["ProgramArguments"], ["/usr/bin/py thon", str(self.DUONG / "do-tu-dong.py"), "chay", "--thu-muc", str(self.DUONG)])
        self.assertEqual(d["StartCalendarInterval"], {"Weekday": 3, "Hour": 9, "Minute": 0})
        self.assertEqual(d["StandardOutPath"], str(self.DUONG / "tu-dong.log"))

    def test_dong_cron_dung(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            import lich_noi_dung as ln
        finally:
            sys.path.pop(0)
        dong = ln.dung_dong_cron("nhan.thu", "/usr/bin/py thon", self.DUONG / "do-tu-dong.py", self.DUONG, 6, 9)
        self.assertTrue(dong.startswith("0 9 * * 0 "))
        self.assertTrue(dong.endswith("# nhan.thu"))
        self.assertNotIn("%", dong.replace("\\%", ""))  # mọi % đều đã thoát
        lenh = dong[len("0 9 * * 0 "):-len(" # nhan.thu")].replace("\\%", "%")  # cron trả % về như cũ trước khi đưa cho shell
        self.assertEqual(shlex.split(lenh), ["/usr/bin/py thon", str(self.DUONG / "do-tu-dong.py"), "chay", "--thu-muc",
                                              str(self.DUONG), ">>", str(self.DUONG / "tu-dong.log"), "2>&1"])


class SoSanh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = nap("so-sanh-hai-lan-do.py")

    def test_moc_0_len_x(self):
        T = {"so_ngay": 7, "tq_tong": 700, "lenh_sleep": 0, "so_phien_chinh": 1}
        S = {"so_ngay": 7, "tq_tong": 700, "lenh_sleep": 14, "so_phien_chinh": 1}
        dong = {d[0]: d for d in self.m.so(T, S)}
        d = dong["Lệnh ngủ chờ mỗi ngày"]
        self.assertIn("từ 0 lên", d[3])
        self.assertIn("kém hơn", d[4])
        S0 = dict(S, lenh_sleep=0)
        self.assertIn("như cũ", {x[0]: x for x in self.m.so(T, S0)}["Lệnh ngủ chờ mỗi ngày"][4])

    def test_thieu_khoa_khong_sap(self):
        self.assertIsInstance(self.m.so({}, {}), list)
        self.assertIsInstance(self.m.khoi_luong({}, {}), str)


class DoChoGoiAiBoLoaiNham(unittest.TestCase):
    def test_neo_ten_tep_test(self):
        m = nap("do-cho-goi-ai-trong-code.py")
        for t in ("bot.test.py", "test_bot.py", "bot_test.py", "bot.spec.ts", "tests", "__tests__", "fixtures", "test"):
            self.assertTrue(m.RE_TEP_TEST.search(t), t)
        for t in ("latest.py", "contest.py", "inspector.js", "specification.md", "testimonials.js", "bot.py"):
            self.assertFalse(m.RE_TEP_TEST.search(t), t)

    def test_dong_noi_shell_khong_bi_coi_la_chu_thich(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "chay.sh").write_text('claude -p "x" \\\n  --model claude-sonnet-4-6 \\\n  --foo\n', encoding="utf-8")
            (Path(d) / "latest.py").write_text('import anthropic\nm = "claude-haiku-4-5"\n', encoding="utf-8")
            out = chay("do-cho-goi-ai-trong-code.py", d).stdout
        self.assertIn("claude-sonnet-4-6", out)
        self.assertIn("claude-haiku-4-5", out)  # `latest` không còn bị loại nhầm


if __name__ == "__main__":
    unittest.main()
