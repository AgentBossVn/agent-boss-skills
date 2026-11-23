#!/usr/bin/env python3
"""Bộ thử skill tiet-kiem-token (chạy tay hoặc trên GitHub Actions, Mac + Windows).

Chạy:  python kiem-thu/thu-tiet-kiem-token.py      (Python ≥ 3.8, chỉ thư viện chuẩn, không cần mạng)
Dựng nhật ký Claude Code GIẢ trong thư mục tạm (không đụng ~/.claude thật), chạy 3 máy đo, kiểm số ra đúng.
Sai khẳng định nào → in "THẤT BẠI" + thoát mã 1.
"""
import datetime as dt, json, os, subprocess, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
GOC = Path(__file__).resolve().parent.parent
SC = GOC / 'tiet-kiem-token' / 'scripts'
LOI = []


def khang_dinh(dk, ten, chi_tiet=''):
    print(('  ✓ ' if dk else '  ✗ ') + ten)
    if not dk:
        LOI.append(ten)
        if chi_tiet:
            print('    ' + str(chi_tiet)[-700:].replace('\n', '\n    '))
    return dk


def chay(tep, *thamso, env=None):
    p = subprocess.run([sys.executable, '-X', 'utf8', str(SC / tep)] + [str(x) for x in thamso], env=env,
                       capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')


def gio(phut_truoc):
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=phut_truoc)).isoformat().replace('+00:00', 'Z')


def luot_ai(i, phut_truoc, cc, cr, out, model='claude-opus-5-5', cong_cu=None):
    noi_dung = [{'type': 'tool_use', 'id': f'tu{i}', 'name': cong_cu[0], 'input': cong_cu[1]}] if cong_cu else []
    return {'type': 'assistant', 'timestamp': gio(phut_truoc), 'cwd': '/du-an/thu', 'entrypoint': 'cli',
            'message': {'id': f'm{i}', 'model': model, 'content': noi_dung,
                        'usage': {'input_tokens': 10, 'output_tokens': out, 'cache_creation_input_tokens': cc,
                                  'cache_read_input_tokens': cr}}}


def nguoi(phut_truoc, chu):
    return {'type': 'user', 'timestamp': gio(phut_truoc), 'origin': {'kind': 'human'}, 'message': {'content': chu}}


def ghi(p: Path, dong):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('\n'.join(json.dumps(d, ensure_ascii=False) for d in dong) + '\n', encoding='utf-8')


def dung_nhat_ky(goc: Path):
    """1 phiên chính: 4 lượt AI, có 1 lần nghỉ 30 phút (quá hạn 5 phút) + 1 lệnh sleep; 1 trợ lý con."""
    du_an = goc / 'projects' / '-du-an-thu'
    ghi(du_an / 'phien1.jsonl', [
        nguoi(100, 'kiểm kê token giúp tôi'),
        luot_ai(1, 99, 30_000, 0, 100, cong_cu=('Bash', {'command': 'sleep 30 && ls'})),
        luot_ai(2, 98, 1_000, 30_000, 200),
        luot_ai(3, 60, 40_000, 0, 300),  # sau 38 phút nghỉ → ghi lại cache lớn
        {'type': 'assistant', 'timestamp': gio(59), 'message': {'id': 'gia', 'model': '<synthetic>',
                                                                 'usage': {'output_tokens': 999_999}}},
        luot_ai(4, 58, 500, 41_000, 400),
        {'type': 'assistant', 'timestamp': gio(60 * 24 * 30), 'message': {'id': 'cu', 'model': 'claude-opus-5-5',
                                                                          'usage': {'output_tokens': 777_777}}},
    ])
    con = du_an / 'phien1' / 'subagents' / 'agent-a1.jsonl'
    ghi(con, [luot_ai(10, 97, 20_000, 0, 50, model='claude-sonnet-5-5')])
    con.with_suffix('.meta.json').write_text(json.dumps({'agentType': 'Explore'}), encoding='utf-8')


def thu_thoi_quen(tam: Path):
    print('\n[1] Máy đo thói quen (nhật ký giả)')
    goc = tam / 'cau-hinh'
    dung_nhat_ky(goc)
    ra = tam / 'so-lieu.json'
    ma, out, err = chay('do-thoi-quen-token.py', '--ngay', 7, '--goc', goc, '--json', ra, '--ttl', 5)
    if not khang_dinh(ma == 0 and ra.exists(), 'chạy xong, có tệp số liệu', err or out):
        return
    k = json.loads(ra.read_text(encoding='utf-8'))
    khang_dinh(k['so_phien_chinh'] == 1 and k['so_tro_ly_con'] == 1, '1 phiên chính + 1 trợ lý con', k['so_phien_chinh'])
    khang_dinh(k['tong_token'].get('out') == 1050, 'bỏ tin <synthetic> và tin ngoài 7 ngày (chữ ra = 1050)', k['tong_token'])
    khang_dinh(k['nghi_qua_han_cache'] == 1, 'bắt đúng 1 lần nghỉ quá hạn nhớ tạm', k['nghi_qua_han_cache'])
    khang_dinh(k['lenh_sleep'] == 1, 'đếm 1 lệnh sleep', k['lenh_sleep'])
    khang_dinh('Explore' in k['con_theo_loai'], 'nhận loại trợ lý con từ .meta.json', list(k['con_theo_loai']))
    khang_dinh(k['tq_tong'] > 0 and k['tq_tro_ly_con'] > 0, 'tính được tq tổng + tq trợ lý con')
    khang_dinh('nhớ tạm' in out and 'bộ nhớ đệm' not in out, 'báo cáo dùng chữ dễ hiểu "nhớ tạm"')
    tho = ra.read_text(encoding='utf-8')
    khang_dinh('kiểm kê token giúp tôi' not in out + tho and 'thu' not in json.dumps(k['theo_du_an'], ensure_ascii=False),
               'MẶC ĐỊNH giấu câu người gõ + tên dự án (màn hình lẫn JSON)', k['theo_du_an'])
    ma2, out2, _ = chay('do-thoi-quen-token.py', '--ngay', 7, '--goc', goc, '--hien-noi-dung')
    khang_dinh(ma2 == 0 and 'kiểm kê token giúp tôi' in out2, '--hien-noi-dung mới hiện câu người gõ')
    ma3, out3, err3 = chay('do-thoi-quen-token.py', '--ngay', 7, '--goc', tam / 'khong-co')
    khang_dinh(ma3 == 2 and 'Traceback' not in err3 + out3 and 'Kiểm tra lại --goc' in err3 + out3,
               'thư mục trống: báo lỗi rõ (mã 2), không ra bảng toàn số 0', err3)


def thu_nap_san(tam: Path):
    print('\n[2] Máy đo phần nạp sẵn')
    goc = tam / 'cau-hinh-2'
    (goc / 'skills' / 'mot-skill').mkdir(parents=True)
    (goc / 'CLAUDE.md').write_text('# Luật\n' + 'Viết ngắn gọn. ' * 50, encoding='utf-8')
    (goc / 'skills' / 'mot-skill' / 'SKILL.md').write_text(
        '---\nname: mot-skill\ndescription: Skill thử để đếm mô tả\n---\nNội dung', encoding='utf-8')
    (goc / 'settings.json').write_text(json.dumps({'env': {'API_KEY': 'BI-MAT-KHONG-DUOC-IN'}}), encoding='utf-8')
    ma, out, err = chay('do-phan-nap-san.py', '--goc', goc, '--du-an', tam)
    khang_dinh(ma == 0, 'chạy xong', err)
    khang_dinh('CLAUDE.md' in out and 'mot-skill' not in out, 'mặc định đếm được CLAUDE.md và GIẤU tên skill', out[:600])
    ma2, out2, err2 = chay('do-phan-nap-san.py', '--goc', goc, '--du-an', tam, '--hien-noi-dung')
    khang_dinh(ma2 == 0 and 'CLAUDE.md' in out2 and 'mot-skill' in out2, '--hien-noi-dung hiện tên skill', out2[:600])
    khang_dinh('BI-MAT-KHONG-DUOC-IN' not in out + err, 'không in giá trị khoá trong cấu hình')


def thu_cho_goi_ai(tam: Path):
    print('\n[3] Máy dò chỗ gọi AI trong code')
    code = tam / 'code'
    (code / 'bot').mkdir(parents=True)
    (code / 'bot' / 'tra-loi.py').write_text(
        'import anthropic\nc = anthropic.Anthropic()\nc.messages.create(model="claude-haiku-4-5", max_tokens=200)\n',
        encoding='utf-8')
    (code / 'web.js').write_text('fetch("https://api.openai.com/v1/chat", {model: "gpt-5-mini"})\n', encoding='utf-8')
    (code / '.env').write_text('OPENAI_KEY=sk-BI-MAT\nfrom anthropic\n', encoding='utf-8')
    (code / 'node_modules' / 'x').mkdir(parents=True)
    (code / 'node_modules' / 'x' / 'i.js').write_text('import anthropic', encoding='utf-8')
    ma, out, err = chay('do-cho-goi-ai-trong-code.py', code, code / 'bot')  # chồng thư mục: không đếm đôi
    khang_dinh(ma == 0, 'chạy xong', err)
    khang_dinh('| Anthropic (Claude) | 1 |' in out and 'claude-haiku-4-5' in out, 'thấy 1 tệp gọi Claude + model', out)
    khang_dinh('| OpenAI | 1 |' in out and 'gpt-5-mini' in out, 'thấy tệp gọi OpenAI + model', out)
    khang_dinh('.env' not in out and 'node_modules' not in out and 'BI-MAT' not in out, 'bỏ qua tệp khoá + node_modules')


def main():
    with tempfile.TemporaryDirectory() as t:
        tam = Path(t)
        thu_thoi_quen(tam)
        thu_nap_san(tam)
        thu_cho_goi_ai(tam)
    if LOI:
        print(f'\nTHẤT BẠI {len(LOI)} mục: ' + '; '.join(LOI))
        sys.exit(1)
    print('\nĐẠT hết.')


if __name__ == '__main__':
    main()
