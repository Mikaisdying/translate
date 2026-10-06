---
name: translate-subtitle
description: Dịch file phụ đề SRT đã clean trong cleaned/ sang tiếng Việt (vi) hoặc tiếng Anh (en), ghi vào trans/, giữ nguyên ID, timestamp và số block, tuân theo glossary.md. Dùng skill này khi người dùng muốn dịch phụ đề, dịch sub, làm vietsub/engsub, hoặc gõ /trans-vi, /trans-en, /translate-subtitle vi, /translate-subtitle en.
---

# Translate Subtitle

Mục tiêu: bản dịch phụ đề đọc tự nhiên như người bản ngữ viết, đúng nghĩa, nhất quán tên và xưng hô từ đầu đến cuối, và khớp chính xác từng block với bản gốc.

## Xác định ngôn ngữ đích

Ngôn ngữ đích lấy từ lệnh hoặc lời người dùng:

- `vi`, `/trans-vi`, "tiếng Việt", "vietsub" → **vi**
- `en`, `/trans-en`, "tiếng Anh", "English", "engsub" → **en**

Nếu không rõ, hỏi người dùng một câu trước khi làm. Sau khi xác định, đọc file hướng dẫn riêng cho ngôn ngữ đó:

- vi → `references/target-vi.md`
- en → `references/target-en.md`

(Muốn thêm ngôn ngữ mới: tạo `references/target-<mã>.md` theo mẫu hai file trên.)

## Thư mục

- Đọc từ `cleaned/`. Ghi vào `trans/<tên>.<mã ngôn ngữ>.srt`: `cleaned/ep01.srt` → `trans/ep01.vi.srt`.
- Không sửa `cleaned/`, không đụng `raw/`.
- Nếu file chỉ có trong `raw/` mà chưa có trong `cleaned/`: báo người dùng và đề nghị chạy clean trước. Chỉ dịch thẳng từ `raw/` khi người dùng đồng ý rõ ràng.
- File tạm để trong `.work/<tên file>/`.
- Lệnh chạy từ thư mục gốc dự án: `python tools/srt_tools.py ...` (hoặc `python3`).

## Chọn file

- Người dùng chỉ định file nào thì dịch file đó.
- Không chỉ định: dịch mọi `cleaned/*.srt` chưa có bản `.<mã>.srt` trong `trans/`. Đã có thì bỏ qua, trừ khi được yêu cầu dịch lại.

## Quy trình cho mỗi file

1. **Kiểm tra**: `python tools/srt_tools.py info cleaned/<file>.srt`. Lỗi định dạng thì dừng và báo.
2. **Đọc glossary**: đọc toàn bộ `glossary.md`. Dòng ✅ là bắt buộc, ưu tiên hơn mọi lựa chọn của bạn. Dòng ❓ dùng làm gợi ý. Ô trống thì tự quyết nhưng phải nhất quán.
3. **Đọc trước toàn bộ nội dung** bằng `python tools/srt_tools.py text cleaned/<file>.srt` trước khi dịch block nào. Cần biết ai là ai, quan hệ ra sao, giọng điệu thế nào, vì xưng hô và cách gọi tên ở đầu phim phụ thuộc vào những gì xảy ra về sau.
4. **Ghi sổ quyết định**: tạo `.work/<file>/notes.md`, ghi lại các quyết định chưa có trong glossary (tên dịch thế nào, ai xưng hô với ai ra sao, thuật ngữ chọn cách nào). Đọc lại sổ này trước mỗi phần để giữ nhất quán, kể cả khi phải làm tiếp ở phiên khác.
5. **Dịch**:
   - File ≤ 150 block: dịch cả file một lần.
   - File dài hơn: `python tools/srt_tools.py split cleaned/<file>.srt --size 100`, dịch từng `.work/<file>/part_XXX.srt` và ghi vào `.work/<file>/<mã>/part_XXX.srt` (cùng tên phần). Trước mỗi phần, xem lại khoảng 10 block cuối của phần trước, cả bản gốc lẫn bản dịch, để câu và giọng nối liền.
   - Gộp: `python tools/srt_tools.py merge .work/<file>/<mã> trans/<file>.<mã>.srt`.
6. **Kiểm tra**: `python tools/srt_tools.py validate cleaned/<file>.srt trans/<file>.<mã>.srt --target <mã>`. Phải PASS. Cảnh báo "còn sót chữ gốc" hay "có Markdown" phải sửa hết; cảnh báo "block giống hệt bản gốc" thì xem lại bằng lệnh `diff` (tên riêng, tiếng kêu, số thì được phép giống).
7. **Tự soát**: đọc lại bản dịch bằng lệnh `text`, tìm chỗ xưng hô lệch, tên viết không đồng nhất, câu đọc gượng.

## Quy tắc chung

**Giữ cấu trúc**: chỉ thay phần chữ. ID, timestamp, thứ tự và số block giữ nguyên tuyệt đối.

```
123
00:10:20,000 --> 00:10:23,000
Chữ gốc
```
→
```
123
00:10:20,000 --> 00:10:23,000
Chữ đã dịch
```

**Câu trải qua nhiều block**: hiểu và dịch theo cả câu, rồi chia bản dịch về lại đúng các block đó, sao cho mỗi block khớp với phần lời đang được nói trong khoảng thời gian của nó và đọc được tương đối độc lập. Không dịch từng mảnh rời rạc, vì trật tự từ giữa các ngôn ngữ khác nhau sẽ làm câu vô nghĩa. Ví dụ (Trung → Việt):

```
45  如果你明天还是不来的话          →  Nếu mai cậu vẫn không đến
46  我就自己一个人去了              →  thì tớ sẽ tự đi một mình đấy.
```

**Độ dài**: phụ đề phải đọc kịp. Mỗi block tối đa 2 dòng, ưu tiên cách diễn đạt gọn. Có thể lược từ thừa, nhưng không được bỏ ý.

**Trung thành**: không thêm thông tin, không bỏ ý, không chú thích hay giải thích trong phụ đề, không thêm dòng kiểu "Dịch bởi...". Tiếng kêu, tiếng cười có thể giữ hoặc chuyển sang cách viết tự nhiên của ngôn ngữ đích.

**Thuật ngữ kỹ thuật**: tên phần mềm, menu, công cụ, phím tắt tuân theo mục "Thuật ngữ kỹ thuật, phần mềm, phím tắt" trong file references của ngôn ngữ đích.

**Không chắc nghĩa**: chọn cách hiểu hợp ngữ cảnh nhất, dịch bình thường, ghi ID vào báo cáo. Không để chữ gốc hay dấu [?] trong file.

## Báo cáo khi xong

Ngắn gọn trong chat:

- File, ngôn ngữ, số block, kết quả validate.
- Các quyết định quan trọng đã tự đưa ra (lấy từ `notes.md`): tên, xưng hô, thuật ngữ.
- Những chỗ không chắc (kèm ID).
- Đề xuất đưa các quyết định trong `notes.md` vào `glossary.md` với trạng thái ❓ để lần sau dùng lại. Chỉ ghi khi người dùng đồng ý.
