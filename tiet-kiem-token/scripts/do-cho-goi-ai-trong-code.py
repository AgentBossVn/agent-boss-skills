#!/usr/bin/env python3
"""Dò CHỖ GỌI AI trong code của bạn (bot, web, máy tự chạy): tệp nào gọi hãng AI nào, model nào.
Tầng này KHÔNG nằm trong nhật ký Claude Code nhưng thường là chỗ tốn TIỀN THẬT (trả theo token qua API key).
Chỉ đọc mã nguồn; bỏ qua tệp khoá (.env, .dev.vars…), node_modules, .git. Không in nội dung dòng.

Dùng: python3 do-cho-goi-ai-trong-code.py <thư mục 1> [thư mục 2 …]"""
import collections, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SKILL_DIR = Path(__file__).resolve().parent.parent  # thư mục chứa chính skill này: không tự dò ra chính nó
BO_THU_MUC = {"node_modules", ".git", "dist", "build", ".next", ".venv", "venv", "__pycache__", ".wrangler",
              ".claude", "vendor", "coverage", ".cache", "worktrees", "secrets", ".ssh", ".aws", ".gnupg"}
DUOI = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rb", ".php", ".sh", ".toml", ".yaml", ".yml", ".json"}
# Tệp có thể chứa khoá: KHÔNG mở (kể cả chỉ để dò chữ)
TEP_KHOA = re.compile(r"(^\.env|\.dev\.vars$|secret|credential|token|passw|private|service.?account"
                      r"|(^|[-_.])(auth|keys?)([-_.]|$)|\.pem$)", re.I)
MODEL = re.compile(r"\b(claude-(?:opus|sonnet|haiku|fable|3)[\w.-]*|gpt-[\w.-]+|(?<=[\"'])o[134](?:-mini|-pro)?(?=[\"'])|gemini-[\w.-]+"
                   r"|deepseek-[\w-]+|grok-[\w.-]+|llama-?[\d.]+[\w.-]*|mistral-[\w-]+|whisper-[\w-]+|@cf/[\w/.-]+)", re.I)
# Tệp test / mẫu thử: không phải chỗ chạy thật
RE_TEP_TEST = re.compile(r"(^|[-_.])(test|tests|spec|specs|__tests__|fixtures?)([-_.]|$)", re.I)
# Dòng chỉ là chú thích (khi dò tên model)
CHU_THICH = ("#", "//", "/*", "* ")  # không có "--" / "*" trần: dòng nối shell "  --model x \\" là code thật
# Chạy ngay trên máy = 0đ, không phải gọi API trả tiền
RE_WHISPER_MAY = re.compile(r"whisper[-_.]?cpp|faster[-_]whisper", re.I)
RE_OPENROUTER_MODEL = re.compile(r"\b(?:openai|anthropic|google|meta-llama|deepseek|mistralai)/[\w.:-]+", re.I)
RE_TRAN_CHU = re.compile(r"max_tokens|max_output_tokens|maxTokens|max_completion_tokens|maxOutputTokens")
RE_DUOI_TEP = re.compile(r"\.(txt|md|py|js|mjs|ts|json|sh|html|png|jpg|yml|yaml)$|-(review|report|test)s?$", re.I)
# Model thuộc hãng nào — theo TÊN model, không theo tệp (1 tệp có thể gọi nhiều hãng)
CHU_MODEL = [("claude-", ("Anthropic (Claude)", "Claude Code chạy tự động (claude -p)")), ("gpt-", ("OpenAI", "Groq")),
             ("o1", ("OpenAI",)), ("o3", ("OpenAI",)), ("o4", ("OpenAI",)), ("gemini-", ("Google Gemini",)),
             ("deepseek-", ("DeepSeek", "Cloudflare Workers AI")), ("@cf/", ("Cloudflare Workers AI",)),
             ("llama", ("Cloudflare Workers AI", "Groq")), ("mistral-", ("Cloudflare Workers AI",)),
             ("whisper-", ("OpenAI", "Groq", "Cloudflare Workers AI")), ("grok-", ("xAI",)),
             ("openai/", ("OpenRouter",)), ("anthropic/", ("OpenRouter",)), ("google/", ("OpenRouter",)),
             ("meta-llama/", ("OpenRouter",)), ("deepseek/", ("OpenRouter",)), ("mistralai/", ("OpenRouter",))]


def cua_hang(model, hang):
    return any(model.startswith(tien_to) and hang in chu for tien_to, chu in CHU_MODEL)


HANG = [("Anthropic (Claude)", re.compile(r"api\.anthropic\.com|@anthropic-ai/sdk|from anthropic|import anthropic", re.I)),
        ("OpenAI", re.compile(r"api\.openai\.com|from openai|['\"]openai['\"]", re.I)),
        ("Google Gemini", re.compile(r"generativelanguage\.googleapis|@google/gen(erative-)?ai|google\.genai|google\.generativeai", re.I)),
        ("OpenRouter", re.compile(r"openrouter\.ai", re.I)), ("DeepSeek", re.compile(r"api\.deepseek\.com", re.I)),
        ("Groq", re.compile(r"api\.groq\.com", re.I)), ("fal.ai", re.compile(r"fal\.(ai|run)", re.I)),
        ("Cloudflare Workers AI", re.compile(r"env\.AI\.run|@cf/", re.I)),
        ("Claude Code chạy tự động (claude -p)", re.compile(r"\bclaude\s+(-p|--print)\b|claude-agent-sdk|claude_agent_sdk", re.I))]


def quet(goc):
    for thu_muc, con, tep in os.walk(goc):
        con[:] = [c for c in con if c not in BO_THU_MUC and not RE_TEP_TEST.search(c)
                  and (Path(thu_muc) / c).resolve() != SKILL_DIR]
        for t in tep:
            p = Path(thu_muc) / t
            if RE_TEP_TEST.search(t):
                continue
            if not p.is_symlink() and p.suffix.lower() in DUOI and not TEP_KHOA.search(t) and not t.endswith((".lock", "-lock.json")):
                try:
                    if p.stat().st_size < 2_000_000:
                        yield p, p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    theo_hang = collections.defaultdict(lambda: {"tep": set(), "model": collections.Counter()})
    whisper_may, thieu_tran = set(), set()
    da_quet = set()
    for goc in sys.argv[1:]:
        goc = Path(goc).expanduser().resolve()
        if not goc.is_dir():
            print(f"(bỏ qua: không có thư mục {goc})", file=sys.stderr)
            continue
        if goc == SKILL_DIR or SKILL_DIR in goc.parents:
            print(f"(bỏ qua: {goc} nằm trong thư mục của chính skill này)", file=sys.stderr)
            continue
        for p, chu in quet(goc):
            p = p.absolute()  # truyền thư mục cha + con chồng nhau vẫn không đếm đôi (không theo symlink)
            if p in da_quet:
                continue
            da_quet.add(p)
            ten_tep = str(p).replace(str(Path.home()), "~")
            if RE_WHISPER_MAY.search(chu):
                whisper_may.add(ten_tep)
            hang = [ten for ten, re_ in HANG if re_.search(chu)]
            if not hang:
                continue
            if any(h in ("Anthropic (Claude)", "OpenAI") for h in hang) and not RE_TRAN_CHU.search(chu):
                thieu_tran.add(ten_tep)
            # chỉ dò tên model ở dòng không phải chú thích; whisper chạy trên máy không tính là model API
            code = RE_WHISPER_MAY.sub("", "\n".join(d for d in chu.splitlines() if not d.lstrip().startswith(CHU_THICH)))
            tim = MODEL.findall(code)
            if "OpenRouter" in hang:
                tim += RE_OPENROUTER_MODEL.findall(code)
            models = collections.Counter(m.lower().rstrip(".-") for m in tim if not RE_DUOI_TEP.search(m))
            for h in hang:
                theo_hang[h]["tep"].add(ten_tep)
                theo_hang[h]["model"].update({m: n for m, n in models.items() if cua_hang(m, h)})
    print("# Chỗ gọi AI trong code\n")
    print("Máy dò theo MẪU CHỮ: liệt kê tệp CÓ NHẮC hãng/model AI, không chắc tệp đó đang chạy thật.\n")
    if not theo_hang:
        print("Không thấy code nào gọi AI trong các thư mục đã dò.")
        return
    print("| Hãng | số tệp | model nhắc tới (số lần) |\n|---|---|---|")
    for h, v in sorted(theo_hang.items(), key=lambda kv: -len(kv[1]["tep"])):
        print(f"| {h} | {len(v['tep'])} | {', '.join(f'{m} {n}' for m, n in v['model'].most_common(6)) or '-'} |")
    print("\n## Tệp (tối đa 8 mỗi hãng)")
    for h, v in theo_hang.items():
        print(f"- **{h}**: " + " · ".join(sorted(v["tep"])[:8]) + (" …" if len(v["tep"]) > 8 else ""))
    if whisper_may:
        print(f"\n## Chạy trên máy, 0đ (whisper.cpp / faster-whisper — không tính là API trả tiền): {len(whisper_may)} tệp")
        print("- " + " · ".join(sorted(whisper_may)[:8]) + (" …" if len(whisper_may) > 8 else ""))
    if thieu_tran:
        print(f"\n## Chưa đặt trần chữ viết ra (max_tokens): {len(thieu_tran)} tệp gọi Anthropic/OpenAI")
        print("Không thấy max_tokens / max_output_tokens / maxTokens — AI có thể viết dài vô hạn, tốn tiền.")
        print("- " + " · ".join(sorted(thieu_tran)[:8]) + (" …" if len(thieu_tran) > 8 else ""))
    print("\nModel ghi trong tệp chưa chắc là model đang chạy (có thể là chú thích, tệp cũ). "
          "Số tiền thật: trang Usage/Billing của từng hãng (Anthropic: platform.claude.com → Usage).")


if __name__ == "__main__":
    main()
