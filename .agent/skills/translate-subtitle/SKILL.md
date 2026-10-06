---
name: translate-subtitle
description: Dịch file phụ đề SRT đã clean trong workspace/cleaned/ sang tiếng Việt (vi) hoặc tiếng Anh (en), ghi vào workspace/trans/, giữ nguyên ID, timestamp và số block, tuân theo workspace/glossary.md. Dùng skill này khi người dùng muốn dịch phụ đề, dịch sub, làm vietsub/engsub, dịch lại bằng model khác, dịch tiếp hay làm tiếp file đang dịch dở (sau khi mất mạng, hết phiên), hoặc gõ /trans-vi, /trans-en, /translate-subtitle vi, /translate-subtitle en.
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

- Đọc từ `workspace/cleaned/`. Ghi vào `workspace/trans/<tên>.<mã ngôn ngữ>.srt`: `workspace/cleaned/ep01.srt` → `workspace/trans/ep01.vi.srt`.
- Không sửa `workspace/cleaned/`, không đụng `workspace/raw/`.
- Nếu file chỉ có trong `workspace/raw/` mà chưa có trong `workspace/cleaned/`: báo người dùng và đề nghị chạy clean trước. Chỉ dịch thẳng từ `workspace/raw/` khi người dùng đồng ý rõ ràng.
- File tạm để trong `workspace/work/<tên file>/`.
- Lệnh chạy từ thư mục gốc dự án: `python tools/srt_tools.py ...` (hoặc `python3`).

## Chọn file

- Người dùng chỉ định file nào thì dịch file đó.
- Không chỉ định: dịch mọi `workspace/cleaned/*.srt` chưa có bản `.<mã>.srt` trong `workspace/trans/`. Đã có thì bỏ qua, trừ khi được yêu cầu dịch lại.
- `python tools/srt_tools.py status` cho bảng tổng quan bài nào đã dịch, validate PASS hay chưa.

## Dịch lại

Khi dịch lại một file đã có bản dịch (VD đổi model), trước khi bắt đầu phải cất bản cũ:

```
python tools/srt_tools.py archive workspace/trans/<file>.<mã>.srt workspace/work/<file>/<mã>
```

Lệnh này chuyển bản dịch cũ và các phần đã dịch cũ vào `workspace/work/<file>/backup/` kèm thời gian. Không dùng lại phần nào của lần dịch trước: nếu phần cũ còn nằm trong `workspace/work/<file>/<mã>/`, `merge` sẽ ghép lẫn hai bản dịch mà `validate` vẫn PASS vì ID và timestamp khớp. Giữ `notes.<mã>.md` vì đó là các quyết định cần nhất quán, nhưng đọc lại với con mắt phê phán. Chỉ đọc bản cũ trong `backup/` khi người dùng yêu cầu.

Đang dịch dở (cùng một lần dịch, làm tiếp ở phiên mới) thì không cất: làm tiếp từ phần chưa có trong `workspace/work/<file>/<mã>/`.

## Quy trình cho mỗi file

1. **Kiểm tra**: `python tools/srt_tools.py info workspace/cleaned/<file>.srt`. Lỗi định dạng thì dừng và báo.
2. **Đọc glossary**: đọc toàn bộ `workspace/glossary.md`. Dòng ✅ là bắt buộc, ưu tiên hơn mọi lựa chọn của bạn. Dòng ❓ dùng làm gợi ý. Ô trống thì tự quyết nhưng phải nhất quán.
3. **Nắm nội dung trước khi dịch**: cần biết ai là ai, quan hệ ra sao, giọng điệu thế nào, vì xưng hô và cách gọi tên ở đầu bài phụ thuộc vào những gì xảy ra về sau. Nhưng không đọc cả file hai lần (một lần lướt, một lần khi dịch).
   - Có `workspace/work/<file>/summary.md` (bước clean đã tạo): đọc file đó, không đọc lại cả bài.
   - Chưa có, file ≤ 150 block: bỏ bước này, đọc thẳng ở bước 5.
   - Chưa có, file dài hơn: giao subagent theo `.agent/skills/clean-funasr/references/summarize.md` với `File: workspace/cleaned/<file>.srt`, ghi câu trả lời vào `summary.md` rồi đọc nó. Không có subagent thì đọc lướt một lần bằng `text` và tự viết `summary.md`.
4. **Ghi sổ quyết định**: tạo `workspace/work/<file>/notes.<mã>.md` (mỗi ngôn ngữ một sổ, vì xưng hô tiếng Việt hay cách viết tên tiếng Anh không áp dụng cho ngôn ngữ kia), ghi lại các quyết định chưa có trong glossary (tên dịch thế nào, ai xưng hô với ai ra sao, thuật ngữ chọn cách nào). Thêm vào ngay khi có quyết định mới. Trong cùng phiên, sổ vẫn còn trong ngữ cảnh nên không cần đọc lại; làm tiếp ở phiên khác thì đọc lại trước tiên.
5. **Dịch**: không tự viết lại ID và timestamp. Đọc bản gốc bằng `text`, viết bản dịch vào file text, mỗi block một dòng dạng `ID | bản dịch` (block hai dòng thì nối bằng ` / `), rồi để `merge` ghép vào đúng ID, timestamp của bản gốc. `merge` từ chối nếu thiếu ID, thừa ID, trùng ID hay có block rỗng.
   - File ≤ 150 block: `python tools/srt_tools.py text workspace/cleaned/<file>.srt`, viết `workspace/work/<file>/<mã>.txt`, rồi `python tools/srt_tools.py merge workspace/cleaned/<file>.srt workspace/work/<file>/<mã>.txt workspace/trans/<file>.<mã>.srt`.
   - File dài hơn: dịch từng phần 100 block. Phần 1 là block 1-100: `python tools/srt_tools.py text workspace/cleaned/<file>.srt --from 1 --to 100`, viết `workspace/work/<file>/<mã>/part_001.txt`; phần 2 là 101-200 vào `part_002.txt`, cứ thế. Ghi mỗi phần ngay khi dịch xong. Không đọc file `.srt` trực tiếp (tốn gấp đôi token vì có ID và timestamp), không cần `split`.
   - Tiến độ: `python tools/srt_tools.py parts workspace/cleaned/<file>.srt workspace/work/<file>/<mã>` cho biết phần nào xong, dở (thiếu, thừa, trùng ID, block rỗng) hay chưa làm, và in sẵn lệnh `text` cho phần tiếp theo. Không cần file checklist: tool kiểm tra thẳng file phần nên không bao giờ lệch với thực tế. Bị ngắt giữa chừng (mất mạng, hết phiên) thì chạy lệnh này, đọc `summary.md` và `notes.<mã>.md`, đọc lại khoảng 10 block cuối của phần trước, cả gốc lẫn dịch (`pair` không dùng được vì bản dịch chưa ghép; đọc `text` bản gốc và cuối file phần trước), rồi làm tiếp. Đang dịch liền một mạch thì phần trước vẫn còn trong ngữ cảnh, không cần đọc lại.
   - Ghép khi `parts` báo xong hết: `python tools/srt_tools.py merge workspace/cleaned/<file>.srt workspace/work/<file>/<mã> workspace/trans/<file>.<mã>.srt --cleanup`. `--cleanup` xóa thư mục phần sau khi ghép thành công, để `workspace/trans/<file>.<mã>.srt` là bản duy nhất; từ đây mọi sửa đổi (kể cả theo review) làm thẳng trên file này.
6. **Kiểm tra**: `python tools/srt_tools.py validate workspace/cleaned/<file>.srt workspace/trans/<file>.<mã>.srt --target <mã>`. Phải PASS. Cảnh báo "còn sót chữ gốc" hay "có Markdown" phải sửa hết; cảnh báo "block giống hệt bản gốc" thì xem lại bằng lệnh `diff` (tên riêng, tiếng kêu, số thì được phép giống).
7. **Glossary**: `python tools/srt_tools.py check-glossary workspace/cleaned/<file>.srt workspace/trans/<file>.<mã>.srt --target <mã>`. Sửa mọi vi phạm dòng ✅, trừ chỗ lệnh báo nhầm (thuật ngữ được diễn đạt khác mà vẫn đúng ý glossary): ghi các chỗ đó vào báo cáo. Sửa xong chạy lại `validate`.
8. **Tự soát**: đọc lại bản dịch bằng lệnh `text`, tìm chỗ xưng hô lệch, tên viết không đồng nhất, câu đọc gượng.

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
- Các quyết định quan trọng đã tự đưa ra (lấy từ `notes.<mã>.md`): tên, xưng hô, thuật ngữ.
- Những chỗ không chắc (kèm ID).
- Đề xuất đưa các quyết định trong `notes.<mã>.md` vào `workspace/glossary.md` với trạng thái ❓ để lần sau dùng lại. Chỉ ghi khi người dùng đồng ý.
