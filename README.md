# Kho skill của Agent Boss

Đây là nơi Agent Boss chia sẻ các skill cho bạn mang về dùng. Hiểu đơn giản thì skill là bộ hướng dẫn kèm công cụ để Agent trên máy bạn (như Claude Code, Codex hay Antigravity) tự làm trọn một việc từ đầu đến cuối.

Hiện tại kho có các skill sau. Bạn thích skill nào thì cài skill đó, không cần cài hết:

| Skill | Làm gì |
|---|---|
| `anh-quang-cao-san-pham` | Ảnh quảng cáo có sản phẩm thật, đúng từng chữ trên nhãn |
| `video-phu-de-to` | Video bạn nói chuyện, chia sẻ → cắt chỗ lặng, phụ đề chữ to, nhạc nền, đăng TikTok được ngay |
| `video-mo-hop-san-pham` | Clip quay sản phẩm → video bán hàng có giọng đọc AI, chữ giá, lời kêu gọi bấm giỏ hàng |
| `video-ghep-nhac-vlog` | Nhiều clip cảnh đời sống → video ghép cắt đúng nhịp nhạc |
| `bo-nhan-dien-thuong-hieu` | Dựng bộ nhận diện thương hiệu (màu, chữ, logo, luật dùng) cho AI đọc, rồi làm ấn phẩm đúng thương hiệu. |
| `tiet-kiem-token` | Soi chỗ tốn token và đề xuất cách giảm dựa trên số liệu của bạn |

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

## Ca thật đứng sau skill ảnh

Skill ảnh quảng cáo ra đời từ ca một học viên bán xe điện: Agent làm ảnh xấu, thầy giao lại việc theo kiểu làm sếp và có 9 ảnh đúng xe. Xem slide để thấy cách giao việc mới quyết định ảnh đẹp hay xấu, công cụ chỉ là phần sau.

- [Xem trọn ca làm ảnh](https://agentboss.vn/thu-vien/slide/tu-duy-dung-agent)
- [Học Agent Boss Marketing](https://muachung.agentboss.vn/marketing): mua chung 890.000đ, cọc 100.000đ giữ chỗ.

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

**Cần gì trên máy:** ffmpeg và Python. Agent tự kiểm tra, cho bạn xem danh sách cần cài và hỏi bạn đồng ý rồi mới cài. Lần đầu làm phụ đề, máy sẽ tải mô hình nghe tiếng Việt khoảng 1,5 GB.

Cài skill video giống như skill ảnh, ví dụ:

```text
Cài skill video-phu-de-to từ https://github.com/AgentBossVn/agent-boss-skills
```

Rồi nhắn: `Dựng video này đăng TikTok: <đường dẫn video>`. Chỉ dùng nhạc, hình, logo mà bạn có quyền dùng.

## Skill "Bộ nhận diện thương hiệu" làm gì?

Khi bạn nhờ AI làm banner mà không đưa luật thương hiệu, mỗi lần ảnh lại ra một kiểu: màu lệch, font lạ, logo bị vẽ lại. Nhân viên trong công ty cũng dễ làm mỗi người một phong cách.

Mình đã dùng cách làm này cho Agent Boss và SEONGON.

- Lần đầu (cả quá trình mất khoảng 30–60 phút), bạn gửi tên công ty, link web, tệp logo (tốt nhất là SVG hoặc PNG nền trong), brand book nếu có, vài ấn phẩm cũ bạn ưng và vài ấn phẩm bạn ghét.

- Agent sẽ đo màu thật từ logo và web, đo độ dễ đọc của chữ trên nền, rồi đề xuất bộ khung gồm màu nền, màu chữ, màu nhấn theo tỉ lệ 80/15/5, một font có đủ dấu tiếng Việt và tiêu đề 3 dòng. Bạn xem và duyệt bộ khung này.

- Sau khi hoàn thành, bạn có một thư mục gồm:
  - Luật thương hiệu cho AI đọc (`DESIGN.md`).
  - Bản ngắn để dán vào ChatGPT hoặc Gemini (`prompt.md`).
  - Bảng màu cho máy đọc.
  - Logo.
  - 7 ấn phẩm mẫu: bài đăng 4:5, story, banner ngang, slide bìa, slide nội dung, tài liệu A4 và chữ ký email.
  - Một trang guideline mở bằng trình duyệt.

- Những lần sau, bạn chỉ cần nói muốn làm ấn phẩm gì và đưa nội dung. Agent chép mẫu gần nhất, điền chữ, chụp ra ảnh, tự soát màu, cỡ chữ, logo thật, chữ có bị tràn hay không và 3 câu kiểm thương hiệu, rồi mới đưa bạn duyệt.

- Nếu công ty đã có brand book, luật trong brand book được ưu tiên. Agent chỉ chép lại thành dạng AI đọc được, không tự vẽ lại logo, không bịa số liệu hay giải thưởng.

- Bạn cần Claude Code, Codex hoặc Antigravity trên Mac hay Windows; Python có sẵn, không cần cài thêm thư viện; Chrome hoặc Edge để chụp ảnh. Không tốn tiền API.

- Skill video của Agent Boss sẽ tự dùng lại màu và logo trong bộ nhận diện này.

### Cách cài

Nhắn Agent:

```text
Cài skill bo-nhan-dien-thuong-hieu từ https://github.com/AgentBossVn/agent-boss-skills
```

### Cách dùng lần đầu

```text
Dựng bộ nhận diện thương hiệu cho công ty tôi: [tên], web: [link]. Logo ở: [đường dẫn tệp]
```

### Những lần sau

```text
Làm bài đăng Facebook đúng thương hiệu: [nội dung]
```

## Skill "Tiết kiệm token" làm gì?

Dùng Claude Code hay hết lượt nhanh, hoặc tốn tiền mà không biết tốn ở đâu? Token giống như “xăng” của AI. Tốn xăng không chỉ do chat nhiều, còn do:

- Chọn model và mức suy nghĩ chưa phù hợp.
- Cuộc trò chuyện quá dài.
- Kết quả công cụ đổ ra quá nhiều.
- Giao việc cho trợ lý con.
- Để máy tự chạy.
- Bot hoặc web của bạn gọi AI. Phần này là tiền thật, nằm ngoài gói Claude Code.

Skill soi đủ 9 tầng:

- Có cần AI không.
- Model và mức suy nghĩ.
- Ngữ cảnh: độ dài cuộc trò chuyện, phần nạp sẵn đầu phiên.
- Công cụ.
- Trợ lý con.
- Cách giao việc.
- Máy tự chạy.
- Sản phẩm của bạn gọi AI.
- Đo và canh.

Khi nhận việc, Agent chạy 3 máy đo ngay trên máy bạn:

- Đọc nhật ký Claude Code trong N ngày gần nhất.
- Đo phần Claude đọc sẵn trước khi bạn gõ bất kỳ chữ nào.
- Dò trong thư mục code xem chỗ nào đang gọi AI, của hãng nào, dùng model nào.

Sau đó, Agent làm một báo cáo gồm:

- Bảng 9 tầng, đánh dấu từng tầng là nặng, vừa hay nhẹ.
- Tối đa 6 đề xuất sửa, xếp việc có lợi lớn và dễ làm lên trước.
- Mỗi đề xuất có số thật của bạn, lý do gây tốn, việc cần làm và ước bớt được bao nhiêu. Phần ước tính sẽ được ghi rõ là ước.
- Đề xuất dựa trên tài liệu chính thức của Anthropic.
- Danh sách những mẹo phổ biến trên mạng nhưng bị thổi phồng, để bạn tránh làm theo.

Một ví dụ dễ hiểu là “AI nhớ tạm” (cache). Thứ AI vừa đọc, khi đọc lại chỉ tính 5–10% giá. Nhưng AI chỉ nhớ trong 1 giờ với gói tháng, hoặc 5 phút khi dùng trợ lý con và khoá API.

Bạn bỏ đi uống cà phê 2 tiếng, quay lại gõ tiếp, AI có thể phải đọc lại cả cuộc trò chuyện với giá đầy đủ. Skill đếm được bạn đã gặp tình huống này bao nhiêu lần.

Bạn cũng có thể yêu cầu Agent xuất phần “chuyện thật có số” để viết bài hoặc dùng khi dạy nhân viên.

Về an toàn và riêng tư:

- Mọi thứ được đo ngay trên máy bạn.
- 3 máy đo không gửi dữ liệu đi đâu. Agent chỉ đọc bảng số đã đếm, như mọi việc khác bạn làm với Agent.
- Không cần mạng, không tốn tiền API.
- Máy dò code bỏ qua các tệp chứa khoá như `.env`.
- Báo cáo mặc định giấu câu bạn gõ, đường dẫn tệp và tên dự án, nên bạn gửi cho người khác xem được.

Bạn cần:

- Claude Code hoặc Codex trên Mac, Windows hoặc Linux.
- Python 3.8 trở lên.
- Không cần cài thêm gì.

### Bản 0.9 (bản thử) có gì mới

- Đo được nhật ký của cả Codex và Claude Code. Với các Agent khác như Gemini CLI, Antigravity... bạn chỉ dùng được phần dò code, vì skill chưa đo được nhật ký.
- Cho biết mỗi lượt AI do ai khởi đầu: bạn gõ, trợ lý con báo về, hook bắt làm lại hay máy tự chạy. Lượt nào AI cũng đọc lại cả cuộc trò chuyện. Đo thử trên máy tác giả trong 7 ngày, khoảng 43% token đến từ những lượt bạn không gõ gì.
- Đếm số lượt bạn phải sửa, thay đổi ý, bổ sung yêu cầu, cùng những lượt chỉ khen, chê hoặc tán gẫu với AI. Con số được ước theo từ khoá, nên đây là mức thấp nhất.
- Liệt kê các thói quen giao việc gây tốn token: giao không rõ, thiếu ngữ cảnh, thay đổi quyết định giữa chừng, bổ sung sau khi AI đã làm...
- Agent tự trả lời 4 câu hỏi về những chỗ phí token mà máy đo không thấy, ví dụ việc đã làm rồi bỏ.
- Mỗi mục trong báo cáo có 3 lớp: con số, giải thích kỹ thuật và giải thích đời thường.
- Có trang theo dõi trước và sau khi sửa, kèm lịch tự đo lại mỗi tuần. Agent sẽ hỏi bạn trước khi đặt lịch.
- Có dòng “phần chưa giải thích được”. Số này cao hoặc tăng nghĩa là máy đo còn bỏ sót thứ gì đó.

Góp ý giúp skill tốt hơn: Đây là bản thử. Cuối mỗi báo cáo, Agent sẽ soạn sẵn mục góp ý, đã bỏ câu bạn gõ, tên dự án và đường dẫn. Bạn xem lại rồi dán vào https://github.com/AgentBossVn/agent-boss-skills/issues/new. Mỗi máy sẽ lộ ra những thứ tác giả chưa thấy, nên góp ý của bạn sẽ giúp skill tốt lên. Khi có bản mới, bạn cập nhật bằng cách cài lại skill từ kho.

Cách cài:

```text
Cài skill tiet-kiem-token từ https://github.com/AgentBossVn/agent-boss-skills
```

Cách dùng:

```text
Kiểm kê token 7 ngày qua của tôi, code của tôi ở thư mục: ...
```

Sau 1 tuần, bạn nên đo lại để so kết quả trước và sau.

## Điều khoản sử dụng

Bạn được dùng miễn phí cho công việc của bạn và doanh nghiệp của bạn. Không bán lại skill, không đóng gói lại thành khoá học hay sản phẩm khác.

Tác giả: Agent Boss (Mai Xuân Đạt).

## Học thêm

Nếu bạn muốn học cách tự xây Agent cho công việc của mình, mời bạn xem khoá học của Agent Boss tại https://agentboss.vn.