# Sổ thay đổi — tiet-kiem-token

Số bản: `A.B.C` — C sửa lỗi nhỏ, B thêm phép đo / mục báo cáo, A đổi cách dùng. Bản 1.0 khi: chạy thật trên đủ Mac + Windows + Linux, ≥5 người khác nhau dùng, ≥1 người không rành kỹ thuật đọc hiểu báo cáo, không còn lỗi lớn mở.

## 0.9.0 — 23/11/2026 (bản thử)
- Đo **ai khởi đầu từng lượt AI**: người gõ / trợ lý con báo về / chốt bắt làm lại / máy tự chạy / plugin — mỗi lượt đọc lại cả phiên.
- Đo lượt **sửa, đổi ý, bổ sung** và lượt **khen, chê, tán gẫu** (ước theo từ khoá, là mức thấp nhất).
- **Phần chưa giải thích được**: lượt đầu thật trừ phần nạp sẵn đọc từ tệp; tỉ lệ lượt không nhận ra nguồn. Số này tăng = máy đo đang sót.
- Danh mục thêm thói quen người giao việc (#21–32), tin tự đến (#33–36), nói chuyện không giao việc (#37).
- Agent tự soi 4 câu (Bước 2b); báo cáo 3 lớp cho người không rành kỹ thuật; mục góp ý tự soạn (Bước 7).
- Đo Codex; so 2 lần đo; trang theo dõi; lịch tự đo hằng tuần (macOS/Linux/Windows); sổ nhớ `theo-doi.json`, nhớ thư mục lưu đã chọn.
- Sửa theo góp ý 3 người dùng thử: máy dò code không tự dò chính nó, bỏ tệp test/chú thích, Whisper trên máy = 0đ, bắt model OpenRouter, báo code chưa đặt `max_tokens`; đếm skill/hook của plugin; trỏ sai thư mục thì báo lỗi; chạy trên Windows/PowerShell; nhãn và dòng Tổng dễ hiểu hơn.
- Sửa sau soát code: không treo khi gặp câu lặp dài, bỏ qua dòng nhật ký lạ thay vì sập, chế độ giấu giấu cả tên tệp và tên skill/MCP, lịch tự đo chịu đường dẫn có ký tự đặc biệt, so sánh đúng khi mốc bằng 0.
- Bộ kiểm tự động `tests/` (nhật ký mẫu tự dựng): `python3 -B -m unittest discover -s tests`.

## Trước 0.9 — 21/11/2026
- Bản đầu: đo thói quen từ nhật ký Claude Code, phần nạp sẵn, chỗ gọi AI trong code; bản đồ 9 tầng; mặc định giấu nội dung riêng.
