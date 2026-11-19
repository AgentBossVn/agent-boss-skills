# Kho skill của Agent Boss

Đây là nơi Agent Boss chia sẻ các skill cho bạn mang về dùng. Hiểu đơn giản thì skill là bộ hướng dẫn kèm công cụ để Agent trên máy bạn (như Claude Code, Codex hay Antigravity) tự làm trọn một việc từ đầu đến cuối.

Hiện tại kho có các skill sau. Bạn thích skill nào thì cài skill đó, không cần cài hết:

| Skill | Làm gì |
|---|---|
| `anh-quang-cao-san-pham` | Ảnh quảng cáo có sản phẩm thật, đúng từng chữ trên nhãn |
| `video-phu-de-to` | Video bạn nói chuyện, chia sẻ → cắt chỗ lặng, phụ đề chữ to, nhạc nền, đăng TikTok được ngay |
| `video-mo-hop-san-pham` | Clip quay sản phẩm → video bán hàng có giọng đọc AI, chữ giá, lời kêu gọi bấm giỏ hàng |
| `video-ghep-nhac-vlog` | Nhiều clip cảnh đời sống → video ghép cắt đúng nhịp nhạc |

Các skill khác mình sẽ thêm dần vào đây.

## Skill "Ảnh quảng cáo sản phẩm" làm gì?

Khi bạn nhờ AI vẽ ảnh quảng cáo, lỗi hay gặp nhất là sản phẩm bị vẽ sai chữ trên nhãn, sai số khối lượng, hoặc thừa thiếu chi tiết. Skill này giúp Agent làm ra ảnh quảng cáo có sản phẩm thật của bạn, giữ đúng dáng, đúng logo, đúng từng chữ trên nhãn như ảnh của hãng.

Khi nhận việc, Agent sẽ tự làm các bước:
- Tải ảnh sản phẩm từ trang của hãng, đếm từng chi tiết trước khi vẽ.
- Vẽ ảnh bằng công cụ do bạn chọn.
- Dùng máy đọc chữ để so chữ trên nhãn ảnh vừa vẽ với ảnh gốc của hãng (bắt được cả những lỗi kiểu "336 g" bị vẽ thành "136 g").
- Chỗ nào vẽ sai thì lấy nhãn thật của hãng dán đè lên.
- Đặt chữ quảng cáo lên ảnh.
- Tự đóng vai khách hàng của bạn để xem lại ảnh rồi sửa tiếp, xong xuôi mới đưa bạn duyệt.

## Skill này ra đời từ đâu?

Skill này được đóng gói từ một ca thật: học viên lớp Marketing bán xe điện nhờ Agent làm ảnh quảng cáo, nhưng ảnh xấu và sai chi tiết xe. Agent Boss đã giao lại việc theo kiểu sếp, yêu cầu Agent làm tới khi có 9 ảnh đúng từng chi tiết như ảnh hãng, rồi gói cách làm thành skill này. Bạn có thể xem bộ slide kể lại từng lần giao việc và ảnh nhận được, ngay trên điện thoại, không cần đăng nhập: https://agentboss.vn/thu-vien/slide/tu-duy-dung-agent/xem

## Vẽ bằng gì và tốn bao nhiêu?

**Xem ảnh ví dụ trước khi chọn: [cùng một sản phẩm, mỗi đường vẽ ra đẹp tới đâu](vi-du/README.md).** Muốn ảnh đẹp như ảnh chụp thì cần gói ChatGPT, gói Gemini hoặc trả tiền theo ảnh; chỉ dùng đường 0đ thì ảnh ra kém hẳn.

Agent sẽ tự kiểm tra máy của bạn rồi in ra một bảng cho bạn chọn công cụ. Công cụ nào chưa có trên máy thì Agent sẽ cho bạn xem danh sách cần cài (lấy từ nguồn chính thức, đúng phiên bản đã kiểm tra), hỏi bạn đồng ý rồi mới cài. Bạn chỉ cần làm những bước bắt buộc người làm như đăng nhập.

- **Ưu tiên gói AI bạn đang trả tiền, không tốn thêm chi phí:** dùng gói ChatGPT Plus/Pro (qua Codex, cho ảnh đẹp nhất mà mình đã đo), gói Google AI Pro (qua Antigravity), hoặc để Agent tự dựng ảnh bằng code từ ảnh thật của sản phẩm (tốn 0đ, sản phẩm đúng 100%, đặt trên cảnh có bục, đèn, bóng đổ; ra kiểu ảnh đồ hoạ như banner sàn thương mại chứ không phải ảnh chụp đời thật).
- **Nếu bạn chưa có gói nào:** dùng Seedream 4.5 của BytePlus được 200 ảnh miễn phí (cần thêm thẻ Visa/Master hoặc PayPal để kích hoạt), hoặc dùng Cloudflare miễn phí khoảng 40 ảnh/ngày (cho chất lượng ảnh kém nhất).
- **Trả tiền theo lượt chỉ khi bạn tự chọn:** dùng Gemini API tốn khoảng 0,05 USD/ảnh. Agent không bao giờ tự ý chuyển sang đường tốn tiền.
- **Phần việc của Agent (đọc, soát lỗi, đặt chữ):** tính vào hạn mức gói Agent bạn đang dùng, hết khoảng 120 nghìn token cho 1 sản phẩm.

## Bạn cần chuẩn bị gì?

Bạn chỉ cần có Claude Code (hoặc Codex, Antigravity) chạy trên máy Mac hoặc Windows 10/11. Phần Python và các thư viện cần thiết thì Agent sẽ tự cài vào một thư mục riêng, không đụng chạm đến các phần mềm khác trên máy của bạn. Khoá API (nếu dùng) sẽ được cất trong kho khoá có sẵn của máy (Keychain trên Mac, Credential Manager trên Windows), không lưu thành tệp chữ.

## Cách cài đặt và cập nhật

Bạn mở Agent lên, nhắn nguyên câu này để Agent tự tải về đúng chỗ:

```text
Cài skill anh-quang-cao-san-pham từ https://github.com/AgentBossVn/agent-boss-skills
```

Khi muốn cập nhật bản mới, bạn nhắn:

```text
Cập nhật skill anh-quang-cao-san-pham từ https://github.com/AgentBossVn/agent-boss-skills
```

## Cách dùng

Bạn nhắn cho Agent theo mẫu:

```text
Làm ảnh quảng cáo cho sản phẩm X, link trang sản phẩm: ...
```

Agent sẽ hỏi bạn vài câu (ảnh dùng để đăng đâu, cỡ nào, chọn công cụ vẽ nào) rồi bắt đầu làm.

Nếu là sản phẩm của chính bạn và trên mạng chưa có ảnh, Agent sẽ nhờ bạn lấy điện thoại chụp sản phẩm (chụp thẳng, nền trơn, đủ sáng) hoặc gửi file thiết kế bao bì. Ảnh gốc của hãng mà mờ thì ảnh làm ra cũng sẽ mờ theo.

## Một vài điều cần nhớ

Ảnh sản phẩm sẽ được gửi sang dịch vụ vẽ mà bạn chọn, vì vậy bạn đừng đưa những sản phẩm chưa công bố vào làm. Nếu có dùng khoá API, bạn nhập vào ô kín do Agent mở ra, tuyệt đối không dán thẳng vào khung chat.

## Các skill video làm gì?

Bạn đưa video thô vào (video tự quay đang nói, clip sản phẩm, clip cảnh đời sống), Agent dựng ra video dọc 9:16 đăng TikTok, Reels, Shorts được ngay, kèm ảnh bìa và chú thích có hashtag. Mỗi skill là một kiểu dựng khác nhau.

Khi nhận việc, Agent sẽ:
- Xem video của bạn: chỗ nào lặng, chỗ nào đổi cảnh, bạn nói gì (chuyển lời nói thành chữ ngay trên máy bạn, không gửi video đi đâu).
- Chọn đoạn hay nhất, đưa câu gây tò mò lên 3 giây đầu.
- Làm phụ đề tiếng Việt, tô màu từ khoá; với video sản phẩm thì viết lời và đọc bằng giọng AI.
- Lót nhạc nền bạn có quyền dùng, gắn thẻ kết có tên và lời kêu gọi của bạn.
- Tự xem lại từng khung hình (chữ tràn mép, sai dấu) rồi mới đưa bạn duyệt.

Lần đầu dùng, Agent hỏi bạn tên shop/kênh, màu, logo, câu kêu gọi và lưu vào `~/.agent-boss/thuong-hieu.json`. Các lần sau và các skill khác của Agent Boss dùng lại, bạn không phải nhập lại.

**Tốn bao nhiêu:** dựng video tốn 0đ, chạy hoàn toàn trên máy bạn bằng ffmpeg. Giọng đọc AI dùng dịch vụ miễn phí của Microsoft (cần mạng). Phần việc của Agent tính vào hạn mức gói Agent bạn đang dùng.

**Cần gì trên máy:** ffmpeg và Python. Agent tự kiểm tra, cho bạn xem danh sách cần cài và hỏi bạn đồng ý rồi mới cài. Lần đầu làm phụ đề, máy sẽ tải mô hình nghe tiếng Việt khoảng 800 MB.

Cài skill video giống như skill ảnh, ví dụ:

```text
Cài skill video-phu-de-to từ https://github.com/AgentBossVn/agent-boss-skills
```

Rồi nhắn: `Dựng video này đăng TikTok: <đường dẫn video>`. Chỉ dùng nhạc, hình, logo mà bạn có quyền dùng.

## Điều khoản sử dụng

Bạn được dùng miễn phí cho công việc của bạn và doanh nghiệp của bạn. Không bán lại skill, không đóng gói lại thành khoá học hay sản phẩm khác.

Tác giả: Agent Boss (Mai Xuân Đạt).

## Học thêm

Nếu muốn tự giao việc cho Agent làm cả marketing, bạn có thể xem lớp Agent Boss Marketing theo hình thức mua chung: 4 buổi Zoom buổi tối và 4 chặng thực hành, không dạy lập trình. Giá mua chung 890.000đ, đặt cọc 100.000đ giữ chỗ và được trừ vào học phí, đủ 200 người thì mở lớp: https://muachung.agentboss.vn/marketing?utm_source=skill-anh-quang-cao&utm_medium=github&utm_campaign=mua-chung-marketing

Trang chính của Agent Boss: https://agentboss.vn
