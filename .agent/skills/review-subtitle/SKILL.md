---
name: review-subtitle
description: Review, soát lỗi, kiểm tra, rà lại bản dịch phụ đề SRT trong workspace/trans/ so với bản gốc trong workspace/cleaned/ và theo workspace/glossary.md, tìm lỗi dịch sai nghĩa, sai thao tác, sai thuật ngữ, lệch xưng hô (giao cho subagent), trình bày cho người dùng chọn, rồi sửa đúng những mục người dùng chọn, hoặc kiểm tra nhất quán chéo nhiều bài. Dùng skill này mỗi khi người dùng nói review, soát lỗi, kiểm tra bản dịch, rà lại sub, check bản dịch, sửa theo review, review chéo, hoặc gõ /review, kể cả khi họ chỉ nói "dịch xong rồi, xem giúp có lỗi không".
---

# Review Subtitle

Review chia làm hai phần tách biệt:

1. **Tìm lỗi**: giao cho subagent. Subagent bắt đầu với context sạch, không mang theo cách hiểu của phiên đã dịch, nên thấy lỗi khách quan hơn. Subagent chỉ đọc và trả danh sách lỗi trong câu trả lời, không tạo file, không sửa bản dịch.
2. **Quyết định sửa**: thuộc về người dùng. Bạn trình bày kết quả, người dùng chọn có sửa không và sửa những mục nào, rồi bạn chỉ sửa đúng những mục đó.

## Chế độ

Xác định từ lời người dùng:

- **Báo lỗi** (mặc định): tìm lỗi, trình bày, hỏi người dùng muốn sửa gì. Không sửa `workspace/trans/`.
- **Sửa** ("sửa", "fix", "sửa theo review"): áp dụng các mục người dùng chọn từ danh sách lỗi đã trình bày trong phiên này.
- **Chéo bài** ("chéo", "cross", "toàn khóa"): kiểm tra nhất quán giữa nhiều bài. Không sửa `workspace/trans/`.

Không rõ thì dùng chế độ báo lỗi.

## Thư mục

- Bản dịch `workspace/trans/<tên>.<mã>.srt`, bản gốc `workspace/cleaned/<tên>.srt`. Ngôn ngữ lấy từ đuôi file (`.vi.srt` → vi); đuôi lạ thì hỏi.
- Không có file review: danh sách lỗi nằm trong câu trả lời của subagent và được trình bày trong chat.
- Không bao giờ sửa `workspace/cleaned/`, `workspace/raw/`, dòng ✅ trong `workspace/glossary.md`. Chỉ chế độ sửa mới được sửa `workspace/trans/`.
- Lệnh chạy từ thư mục gốc dự án: `python tools/srt_tools.py ...` (hoặc `python3`).

## Giao việc cho subagent

Dùng công cụ subagent của môi trường đang chạy (VD công cụ Agent/Task trong Claude Code, `runSubagent` trong VS Code Copilot). Nếu người dùng chỉ định model cho review (VD "review bằng sonnet") và công cụ cho chọn model subagent, dùng model đó; tốt nhất là model khác với model đã dịch.

Lời giao việc chỉ gồm những gì subagent cần, không kèm nhận xét hay phỏng đoán của bạn về bản dịch, để giữ góc nhìn độc lập:

```
Đọc và làm đúng theo .agent/skills/review-subtitle/references/find-errors.md
Bản gốc: workspace/cleaned/ep03.srt
Bản dịch: workspace/trans/ep03.vi.srt
Ngôn ngữ: vi
Phạm vi: toàn bộ
```

Mỗi file một subagent; nhiều file thì chạy song song vài file một lúc. Kiểm tra chéo dùng `references/cross-check.md`, giao một subagent cho mỗi ngôn ngữ kèm danh sách file.

Môi trường không có subagent: tự làm theo đúng file hướng dẫn đó trong phiên hiện tại, và nhắc người dùng một lần rằng review ở phiên mới hoặc bằng model khác sẽ khách quan hơn.

## Chế độ báo lỗi

1. **Chọn file**:
   - Người dùng chỉ định thì làm đúng file đó.
   - Không chỉ định: chạy `status`, liệt kê các bản dịch PASS và hỏi người dùng review bài nào (một bài, vài bài, hay tất cả). Bản dịch FAIL thì báo lỗi cấu trúc, không cần subagent.
   - Không có `workspace/cleaned/<tên>.srt` tương ứng: báo và bỏ qua.
   - Bài có "gốc sửa sau" trong `status`: vẫn review, nhưng nhắc người dùng rằng `workspace/cleaned/` đã đổi sau khi dịch.
2. **Giao việc** cho subagent như trên.
3. **Kiểm tra kết quả**: câu trả lời phải có phần tổng và các mục đúng format (ID, mức độ, gốc, hiện tại, đề xuất, lý do). Thiếu hoặc hỏng thì giao lại một lần; vẫn hỏng thì báo người dùng.
4. **Đối chiếu nhanh**: với mỗi lỗi nghiêm trọng, `pair` đúng ID đó để chắc chữ "Gốc" và "Hiện tại" khớp file thật (subagent có thể chép nhầm block). Mục không khớp thì ghi rõ khi trình bày, không tự bỏ.
   Với mỗi mục "Lỗi ở bản gốc", tự kiểm tra trước khi đề xuất sửa `workspace/cleaned/`: xem ngữ cảnh bằng `text --from N --to M`, và chữ bị nghi sai có thể là tên đúng trên giao diện phần mềm hay thuật ngữ đúng không (VD giao diện Blender tiếng Trung gọi X-Ray là 透视, nên 透视模式 không phải lỗi ASR). Subagent chỉ đoán từ bản dịch nên dễ báo nhầm ở phần này. Khi trình bày, chia rõ mục nào bạn đồng ý sửa, mục nào nên giữ nguyên (kèm lý do).
5. **Trình bày** trong chat, giữ nguyên format từng mục của subagent để người dùng chọn theo ID:
   - Số lỗi theo mức độ; review nhiều file thì một bảng, mỗi file một dòng.
   - Toàn bộ lỗi nghiêm trọng (ID, hiện tại → đề xuất, lý do ngắn).
   - Lỗi trung bình và nhẹ: đầy đủ nếu ít (khoảng 20 mục trở xuống), nhiều hơn thì gom theo loại kèm danh sách ID; người dùng hỏi thì đưa chi tiết.
   - Lỗi ở bản gốc và đề xuất glossary nếu có.
6. **Hỏi người dùng** muốn làm gì, VD: sửa tất cả, chỉ lỗi nghiêm trọng, chỉ các ID cụ thể, xác nhận hoặc bỏ các mục "cần xác nhận", sửa theo đề xuất khác của chính họ, hay không sửa. Dừng ở đây, chờ trả lời.

## Chế độ sửa

Chỉ chạy khi người dùng đã nói rõ sửa những gì, dựa trên danh sách lỗi đã trình bày trong phiên này. Phiên này chưa có danh sách (VD `/review sửa ep03` ở phiên mới) thì chạy chế độ báo lỗi trước và hỏi lại, vì người dùng chưa thấy danh sách thì chưa chọn được.

1. **Lấy các mục người dùng chọn** từ danh sách trong phiên. Bỏ qua mục đã sửa ở lượt trước trong phiên, và mục `cần xác nhận` mà người dùng chưa xác nhận.
2. **Sao lưu**: `python tools/srt_tools.py archive --copy workspace/trans/<tên>.<mã>.srt` (lệnh in ra đường dẫn bản sao lưu).
3. **Sửa đúng các block đã chọn**, theo `Đề xuất` (hoặc cách sửa người dùng đưa ra). Không nhân tiện viết lại block khác. Chỉ thay phần chữ; ID, timestamp, số block, thứ tự giữ nguyên.
4. **Kiểm tra**: `validate ... --target <mã>` phải PASS; chạy `check-glossary` và báo vi phạm còn lại, không tự sửa ngoài phần được chọn.
5. **Báo cáo**: `diff <bản sao lưu> workspace/trans/<tên>.<mã>.srt`, liệt kê block đã đổi (cũ → mới), các mục bỏ qua kèm lý do, và các mục còn `chờ duyệt` để người dùng chọn tiếp nếu muốn.

## Chế độ chéo bài

1. Chọn các bài có bản dịch ngôn ngữ đó (hoặc các bài người dùng chỉ định).
2. Giao subagent theo `references/cross-check.md`.
3. Trình bày: thuật ngữ dịch nhiều kiểu (cách đề xuất cho mỗi cái), chỗ lệch xưng hô, đề xuất glossary. Hỏi người dùng có muốn đưa đề xuất vào `workspace/glossary.md` (trạng thái ❓) không. Muốn sửa bản dịch thì sau khi chốt glossary, chạy chế độ báo lỗi cho từng bài; `check-glossary` sẽ chỉ ra chỗ cần sửa.

## Không được làm

- Không sửa `workspace/cleaned/` hay `workspace/raw/`. Lỗi ở bản gốc thì báo người dùng.
- Không sửa `workspace/trans/` ngoài chế độ sửa, và trong chế độ sửa không sửa ngoài các mục người dùng chọn.
- Không đưa ghi chú, Markdown hay giải thích vào file phụ đề.
- Không sửa hay xóa dòng ✅ trong glossary; thấy có vẻ sai thì nêu trong báo cáo.
