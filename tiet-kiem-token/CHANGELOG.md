# Sổ thay đổi — tiet-kiem-token

Số bản: `A.B.C` — C sửa lỗi nhỏ, B thêm phép đo / mục báo cáo, A đổi cách dùng. Bản 1.0 khi: chạy thật trên đủ Mac + Windows + Linux, ≥5 người khác nhau dùng, ≥1 người không rành kỹ thuật đọc hiểu báo cáo, không còn lỗi lớn mở.

## 0.11.1 — 27/11/2026 (bản thử)
- **Không tắt / cấm công cụ mà skill cần:** trước khi tắt công cụ hay MCP "ít dùng" (kể cả cài máy tự cấm như TokenEconomizer `toolprune`), dò tên công cụ trong skill, agent, quy tắc của người dùng; có skill nhắc tới thì không tắt; cài máy tự cấm thì đặt sẵn danh sách không bao giờ cấm. Chuyện thật: máy cấm `ArtifactData` vì ít dùng → skill tạo bảng việc không đọc được câu trả lời.

## 0.11.0 — 26/11/2026 (bản thử)
- **Nối với công cụ của hãng (Bước 0c), không bắt người dùng chạy lệnh dán kết quả:** số tương đương `/usage` máy tự tính từ nhật ký, nhãn giống bảng của hãng; báo cáo `/insights` nếu đã có thì máy tự tìm và đọc (`doc-bao-cao-insights.py`: số phiên, số lần làm sai hướng / hiểu sai, từng gợi ý), chưa có thì bỏ qua và chỉ gợi ý 1 dòng. Không tự chạy `/insights` (tốn lượt).
- **Đối chiếu gợi ý của hãng** với luật, hook, skill người dùng đã có: đã có sẵn / trái luật đã chốt / thật sự mới; báo cáo có thêm mục này.
- **Phép đo khớp `/usage`** (dòng "Khớp cách gọi của `/usage`" trong thoi-quen.md + khoá JSON `tq_ngu_canh_150k`, `tq_song_song_4`, `tq_phien_song_8_gio`): % tq khi ngữ cảnh quá 150k · khi có từ 4 phiên chạy song song · ở phiên sống từ 8 giờ (kèm tq lượt có gọi skill / MCP). Đếm từ nhật ký thật. Thêm tq lượt có gọi skill / công cụ MCP (ước). Phần nạp sẵn và trợ lý con dùng lại số có sẵn, đổi nhãn cho trùng.
- Danh mục: thói quen #39 (luật bằng chữ đã có mà vẫn bị vi phạm → chuyển thành máy chặn, đừng viết thêm chữ) và #40 (làm sai hướng / hiểu sai rồi làm lại, lấy số từ `/insights`, cách phòng).
- "Thế giới nói gì" thêm mục D: công cụ Anthropic đã có sẵn + chỗ skill này khác (nguồn code.claude.com/docs/en/costs).
- Bộ kiểm: thêm `tests/test_do_theo_usage.py` (47 bài); thêm nhật ký mẫu `tests/mau` vào kho riêng của người viết (trước chỉ có ở kho công khai).

## 0.10.0 — 26/11/2026 (bản thử)
- **Tư duy gốc mới ở đầu skill:** agent làm việc CHƯA RÕ cách làm (tự quyết, tự sửa); việc ĐÃ RÕ cách làm thì bảo agent viết công cụ rồi chạy công cụ — 0 token, chính xác, lần nào cũng ra y hệt. Áp cho cả việc lặp lẫn việc làm 1 lần mà nặng.
- Máy mới `do-viec-nen-viet-may.py` (tầng 0), `chay` tự gọi, 4 mục: việc giao lặp ≥3 lần (người giao, máy tự chạy, trợ lý con) · phiên AI đọc nhiều dữ liệu (≥15 tệp hoặc ≥300 nghìn ký tự) · việc nặng có công cụ miễn phí (AI tự đọc video/âm thanh/ảnh/PDF/tệp Office/link video) · cấu hình máy + công cụ đã cài.
- Bước 2c bắt buộc: hỏi "cách làm đã rõ chưa?", xếp A (viết công cụ) / B (công cụ + AI đúng khúc) / C (để agent), kiểm máy chạy nổi, ước hoà vốn, đề xuất công cụ cụ thể.
- Danh mục thêm thói quen #38: bắt agent tự làm việc đã rõ cách làm.

## 0.9.0 — 23/11/2026 (bản thử)
- Đo **ai khởi đầu từng lượt AI**: người gõ / trợ lý con báo về / chốt bắt làm lại / máy tự chạy / plugin — mỗi lượt đọc lại cả phiên.
- Đo lượt **sửa, đổi ý, bổ sung** và lượt **khen, chê, tán gẫu** (ước theo từ khoá, là mức thấp nhất).
- **Tách lượt đầu mỗi phiên từng phần** (`tach-luot-dau-phien.py`: lời dặn hệ thống, công cụ có sẵn/MCP, CLAUDE.md+trí nhớ, skill, agent, hook; ước token theo loại chữ rồi hiệu chỉnh khớp số thật); `do-phan-nap-san` đếm thêm trí nhớ tự động dự án và ước token theo loại chữ (bớt đếm thiếu tiếng Việt).
- **Phần chưa giải thích được**: lượt đầu thật trừ phần nạp sẵn đọc từ tệp; tỉ lệ lượt không nhận ra nguồn. Số này tăng = máy đo đang sót.
- Danh mục thêm thói quen người giao việc (#21–32), tin tự đến (#33–36), nói chuyện không giao việc (#37).
- Agent tự soi 4 câu (Bước 2b); báo cáo 3 lớp cho người không rành kỹ thuật; mục góp ý tự soạn (Bước 7).
- Đo Codex; so 2 lần đo; trang theo dõi; lịch tự đo hằng tuần (macOS/Linux/Windows); sổ nhớ `theo-doi.json`, nhớ thư mục lưu đã chọn.
- Sửa theo góp ý 3 người dùng thử: máy dò code không tự dò chính nó, bỏ tệp test/chú thích, Whisper trên máy = 0đ, bắt model OpenRouter, báo code chưa đặt `max_tokens`; đếm skill/hook của plugin; trỏ sai thư mục thì báo lỗi; chạy trên Windows/PowerShell; nhãn và dòng Tổng dễ hiểu hơn.
- Sửa sau soát code: không treo khi gặp câu lặp dài, bỏ qua dòng nhật ký lạ thay vì sập, chế độ giấu giấu cả tên tệp và tên skill/MCP, lịch tự đo chịu đường dẫn có ký tự đặc biệt, so sánh đúng khi mốc bằng 0.
- Bộ kiểm tự động `tests/` (nhật ký mẫu tự dựng): `python3 -B -m unittest discover -s tests`.

## Trước 0.9 — 21/11/2026
- Bản đầu: đo thói quen từ nhật ký Claude Code, phần nạp sẵn, chỗ gọi AI trong code; bản đồ 9 tầng; mặc định giấu nội dung riêng.
