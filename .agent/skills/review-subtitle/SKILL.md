---
name: review-subtitle
description: Review, soát lỗi, kiểm tra, rà lại bản dịch phụ đề SRT trong trans/ so với bản gốc trong cleaned/ và theo glossary.md, tìm lỗi dịch sai nghĩa, sai thao tác, sai thuật ngữ, lệch xưng hô, rồi (nếu được yêu cầu) sửa theo kết quả review hoặc kiểm tra nhất quán chéo nhiều bài. Dùng skill này mỗi khi người dùng nói review, soát lỗi, kiểm tra bản dịch, rà lại sub, check bản dịch, sửa theo review, review chéo, hoặc gõ /review, kể cả khi họ chỉ nói "dịch xong rồi, xem giúp có lỗi không".
---

# Review Subtitle

Mục tiêu: tìm ra những lỗi thật trong bản dịch phụ đề, để người dùng sửa được ngay mà không phải đọc lại cả file. Review chỉ có giá trị khi người dùng tin được nó: mỗi lỗi báo nhầm làm họ mất thời gian kiểm tra và dần mất tin vào cả danh sách, nên báo ít mà chắc còn hơn báo nhiều mà nhiễu.

Review phải chấm theo đúng quy tắc mà bước dịch đã dùng (`glossary.md` và `references/target-<mã>.md` của skill `translate-subtitle`), không theo khẩu vị riêng.

## Ba chế độ

Xác định từ lời người dùng:

- **Báo lỗi** (mặc định): chỉ liệt kê lỗi, không sửa file nào trong `trans/`.
- **Sửa** ("sửa", "fix", "sửa theo review"): áp dụng các sửa đổi đã có trong danh sách lỗi.
- **Chéo bài** ("chéo", "cross", "toàn khóa"): kiểm tra tính nhất quán giữa nhiều file.

Không rõ người dùng muốn gì thì dùng chế độ báo lỗi, vì nó không làm hỏng gì.

## Thư mục

- Bản dịch: `trans/<tên>.<mã>.srt`. Bản gốc tương ứng: `cleaned/<tên>.srt`.
- Không bao giờ sửa `cleaned/` và `raw/`. Chế độ báo lỗi và chế độ chéo bài không sửa `trans/`.
- Kết quả review và file tạm để trong `.work/<tên>/`.
- Lệnh chạy từ thư mục gốc dự án: `python tools/srt_tools.py ...` (hoặc `python3`).

## Chọn file

- Người dùng chỉ định file nào thì làm file đó.
- Không chỉ định: review mọi file trong `trans/`, lần lượt từng file.
- Ngôn ngữ lấy từ đuôi tên file (`.vi.srt` → vi, `.en.srt` → en). Đuôi khác thì hỏi người dùng.
- Không có `cleaned/<tên>.srt` tương ứng: báo rõ và bỏ qua file đó, vì không có bản gốc chuẩn thì không đối chiếu được.

## Chế độ báo lỗi: quy trình cho mỗi file

1. **Kiểm tra cấu trúc**: `python tools/srt_tools.py validate cleaned/<tên>.srt trans/<tên>.<mã>.srt --target <mã>`. Lỗi cấu trúc (sai ID, timestamp, số block) ghi vào danh sách lỗi nghiêm trọng. Nếu số block khớp thì vẫn review phần nội dung; lệch số block thì `pair` sẽ không chạy, dừng ở đây và báo.
2. **Kiểm tra glossary bằng máy**: `python tools/srt_tools.py check-glossary cleaned/<tên>.srt trans/<tên>.<mã>.srt --target <mã>`. Mọi vi phạm đưa vào danh sách lỗi mức trung bình. Lệnh này chỉ so khớp chuỗi nên có thể báo nhầm (VD thuật ngữ được dịch bằng cách diễn đạt khác nhưng vẫn đúng ý glossary); xem lại ngữ cảnh trước khi đưa vào danh sách.
3. **Đọc quy tắc**: đọc `glossary.md` và `.agent/skills/translate-subtitle/references/target-<mã>.md`. Dòng ✅ là bắt buộc; dòng ❓ chỉ là gợi ý nên lệch ❓ không phải lỗi.
4. **Đọc đối chiếu**: `python tools/srt_tools.py pair cleaned/<tên>.srt trans/<tên>.<mã>.srt --from 1 --to 100`, rồi 101-200 và tiếp tục như vậy. Mỗi lần khoảng 100 block để đủ ngữ cảnh mà vẫn đọc kỹ. Nhớ rằng một câu có thể trải qua nhiều block: đánh giá theo cả câu, không theo từng mảnh.
5. **Phân loại lỗi**:
   - **Nghiêm trọng**: dịch sai nghĩa; bỏ sót ý; sai hướng dẫn thao tác (sai phím, sai chuột trái/phải, sai tên menu, sai con số, sai thứ tự bước). Với video hướng dẫn, lỗi thao tác là nặng nhất vì người học làm theo sẽ làm sai.
   - **Trung bình**: vi phạm glossary; thuật ngữ hoặc tên không nhất quán trong file; xưng hô lệch; phím tắt sai định dạng; còn sót chữ gốc.
   - **Nhẹ**: câu đọc gượng, dịch word-by-word, quá dài khó đọc kịp.
6. **Chỉ báo lỗi thật**. Không báo những chỗ chỉ khác sở thích văn phong mà bản dịch vẫn đúng và tự nhiên: người dịch có quyền chọn cách diễn đạt riêng. Tự hỏi "nếu là người dùng, tôi có muốn sửa chỗ này không?" Không chắc là lỗi hay không thì vẫn ghi, nhưng ghi rõ "cần người dùng xác nhận" thay vì khẳng định.
7. **Ghi danh sách lỗi** vào `.work/<tên>/review.<mã>.md`. Mỗi lỗi gồm: ID, mức độ, loại lỗi, gốc, bản dịch hiện tại, đề xuất sửa, lý do ngắn. Ví dụ:

   ```
   ### ID 57 | Nghiêm trọng | Sai thao tác
   - Gốc: 按住Alt键点击图层缩览图
   - Hiện tại: Nhấn Ctrl và bấm vào ảnh thu nhỏ của Layer
   - Đề xuất: Giữ Alt và bấm vào ảnh thu nhỏ của Layer
   - Lý do: Gốc nói Alt, bản dịch ghi Ctrl; hai phím làm hai việc khác nhau.
   ```

   File này là đầu vào cho chế độ sửa, kể cả khi sửa ở phiên khác, nên đề xuất sửa phải là câu hoàn chỉnh, dùng được ngay mà không cần đoán lại ý. Lỗi chia theo mức độ, nghiêm trọng đứng trước. Lỗi mà đề xuất cần người dùng xác nhận thì ghi chú "cần xác nhận" ở đầu mục để chế độ sửa không tự áp dụng.
8. **Trả lời trong chat**: số lỗi theo mức độ; toàn bộ lỗi nghiêm trọng; tóm tắt các lỗi còn lại; đề xuất bổ sung glossary nếu thấy (thuật ngữ bị dịch nhiều kiểu, tên chưa có trong glossary); đường dẫn file review. Review nhiều file thì thêm một bảng tổng hợp ngắn, mỗi file một dòng.

## Chế độ sửa

1. **Đọc** `.work/<tên>/review.<mã>.md`. Chưa có thì chạy chế độ báo lỗi trước.
2. **Sao lưu** bản dịch hiện tại vào `.work/<tên>/backup/<tên>.<mã>.<YYYYMMDD-HHMM>.srt` trước khi sửa, để hoàn tác được nếu sửa hỏng.
3. **Chỉ sửa đúng các block có trong danh sách lỗi**. Nếu người dùng chỉ định mức độ hoặc ID cụ thể (VD "chỉ sửa lỗi nghiêm trọng", "sửa ID 57 và 60") thì chỉ sửa phần đó. Bỏ qua mục đang ghi "cần xác nhận" trừ khi người dùng đã xác nhận. Không nhân tiện viết lại block khác, vì mỗi thay đổi ngoài danh sách là một thay đổi người dùng chưa duyệt. Chỉ thay phần chữ; ID, timestamp, số block, thứ tự giữ nguyên.
4. **Kiểm tra**: chạy `validate ... --target <mã>` và `check-glossary ...`. Validate phải PASS. Vi phạm glossary còn lại thì xem có thuộc phần được phép sửa không; nếu có thì sửa nốt, nếu không thì báo.
5. **So sánh**: `python tools/srt_tools.py diff .work/<tên>/backup/<tên>.<mã>.<thời gian>.srt trans/<tên>.<mã>.srt`. Báo trong chat các block đã đổi (cũ → mới) và những mục trong danh sách chưa sửa kèm lý do.

## Chế độ chéo bài

Mục đích: bắt những lỗi mà từng file đọc riêng thì không thấy, vì mỗi bài dùng một cách dịch khác nhau cho cùng một thuật ngữ. Chế độ này không sửa file dịch.

1. **Glossary từng cặp**: chạy `check-glossary` cho từng cặp `cleaned/<tên>.srt` ↔ `trans/<tên>.<mã>.srt`, tổng hợp số vi phạm theo thuật ngữ và theo bài.
2. **Thuật ngữ không nhất quán giữa các bài**: với các thuật ngữ trong glossary (cả ✅ lẫn ❓) và các thuật ngữ kỹ thuật lặp lại nhiều trong bản gốc, dùng `python tools/srt_tools.py find "<thuật ngữ>" cleaned/*.srt` để lấy các ID chứa thuật ngữ, rồi `pair` đúng các block đó (`--from N --to N`) để xem mỗi bài dịch thế nào. Báo những thuật ngữ có từ hai cách dịch trở lên, kèm tên file và ID ví dụ cho từng cách. Cũng có thể `find` trong `trans/*.srt` để đếm mỗi cách dịch xuất hiện bao nhiêu lần, rồi đề xuất cách chiếm đa số hoặc cách khớp giao diện phần mềm.
3. **Xưng hô**: lấy mẫu vài đoạn mỗi bài (đầu, giữa, cuối) bằng `pair`, kiểm tra giảng viên hoặc nhân vật chính có giữ nguyên cách xưng hô với người xem/người nghe giữa các bài không (VD bài này "mình - các bạn", bài kia "tôi - các bạn"). Chỉ báo khi lệch thật, không phải khi bối cảnh đổi.
4. **Đề xuất glossary**: liệt kê các thuật ngữ và xưng hô nên đưa vào hoặc sửa trong `glossary.md` với trạng thái ❓, mỗi mục kèm cách chọn đề xuất và lý do. Chỉ ghi vào `glossary.md` khi người dùng đồng ý. Không tự sửa file dịch ở chế độ này; muốn sửa thì người dùng chạy chế độ sửa cho từng file (sau khi glossary đã chốt, `check-glossary` sẽ chỉ ra chỗ cần sửa).

Ghi kết quả vào `.work/cross-review.md` và nêu đường dẫn trong chat.

## Không được làm

- Không sửa `cleaned/` hay `raw/`. Nếu phát hiện lỗi ở bản gốc (VD ASR nghe sai mà bước clean bỏ sót), báo người dùng chứ không sửa, vì bản dịch dựa trên nó.
- Không sửa `trans/` ngoài chế độ sửa.
- Không đưa ghi chú, Markdown hay giải thích vào file phụ đề. Mọi nhận xét nằm trong file review hoặc trả lời chat.
- Không sửa hay xóa dòng ✅ trong glossary. Thấy dòng ✅ có vẻ sai thì nêu trong báo cáo.

## Gợi ý cho người dùng

Review hiệu quả nhất khi làm ở phiên mới, và tốt nhất bằng model khác với model đã dịch: cùng một model thường lặp lại đúng cách hiểu sai của chính nó nên khó thấy lỗi của mình. Nếu đang ở cùng phiên dịch, nhắc người dùng điều này một lần ngắn gọn trong báo cáo.
