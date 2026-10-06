---
name: build-glossary
description: Quét các file phụ đề trong workspace/cleaned/ (và workspace/raw/) để lập nháp workspace/glossary.md gồm nhân vật, xưng hô, thuật ngữ, câu cửa miệng và lỗi ASR hay gặp, đánh dấu ❓ cho người dùng duyệt. Dùng skill này khi người dùng muốn tạo, điền, cập nhật, bổ sung glossary hay bảng thuật ngữ cho dự án phụ đề, hoặc gõ /glossary, kể cả khi họ chỉ nói "lập danh sách tên nhân vật" hay "chuẩn bị trước khi dịch".
---

# Build Glossary

Mục tiêu: lập bản nháp `workspace/glossary.md` để người dùng duyệt nhanh trước khi dịch. Agent chỉ đề xuất; người dùng là người quyết định. Một glossary tốt giúp mọi lần dịch sau (bằng bất kỳ model nào) ra tên và xưng hô giống nhau.

## Khi nào chạy

Tốt nhất là sau bước clean và trước bước dịch. Có thể chạy lại khi thêm tập mới để bổ sung.

## Nguồn

- Chính: `workspace/cleaned/*.srt` (chữ đã đúng). Nếu người dùng chỉ định file thì chỉ quét các file đó.
- Phụ: so sánh `workspace/raw/` với `workspace/cleaned/` bằng `python tools/srt_tools.py diff workspace/raw/<file>.srt workspace/cleaned/<file>.srt --limit 500` để tìm lỗi ASR lặp lại (mục 6).
- Chưa có `workspace/cleaned/`: quét `workspace/raw/`, nhưng nói rõ với người dùng rằng tên riêng có thể còn sai chính tả.
- Đọc nội dung bằng `python tools/srt_tools.py text <file>` (gọn hơn đọc SRT trực tiếp). File dài thì đọc theo đoạn với `--from` / `--to`.

## Chia việc cho subagent

Nhiều file (khóa học, phim bộ) thì đọc hết trong một phiên sẽ tràn context. Giao việc đọc cho subagent (công cụ Agent/Task trong Claude Code, `runSubagent` trong VS Code Copilot), mỗi subagent một file hoặc vài file ngắn, chạy song song:

```
Đọc và làm đúng theo .agent/skills/build-glossary/references/extract.md
File: workspace/cleaned/ep01.srt, workspace/cleaned/ep02.srt
File kết quả: workspace/work/glossary/ep01-ep02.md
```

Subagent chỉ đọc và ghi ứng viên (kèm số lần xuất hiện, ID ví dụ) vào file kết quả; không ai ngoài bạn ghi vào `workspace/glossary.md`. Bạn gộp các file kết quả: cộng số lần, hợp nhất các cách viết của cùng một tên, chọn đề xuất, bỏ ứng viên lặp ít, rồi ghi theo phần "Cách ghi vào workspace/glossary.md". Xưng hô (mục 3) cần nhìn cả mạch truyện: khi gộp, xem lại vài đoạn bằng `text` ở những bài mà subagent ghi là có quan hệ thay đổi.

Chỉ một hai file ngắn, hoặc môi trường không có subagent: tự đọc theo `references/extract.md` rồi gộp như trên.

## Thu thập gì

1. **Thông tin chung** (mục 1): ngôn ngữ gốc, thể loại, bối cảnh, giọng văn. Chỉ điền ô đang trống.
2. **Nhân vật** (mục 2): mọi tên người xuất hiện từ 2 lần trở lên, kèm biệt danh và các cách gọi khác của cùng một người. Ghi vai trò, giới tính, tuổi tương đối nếu suy ra được, vì những thông tin này quyết định xưng hô.
3. **Xưng hô** (mục 3): các cặp nhân vật nói chuyện với nhau nhiều. Dựa vào quan hệ (gia đình, thầy trò, cấp trên cấp dưới, bạn bè, người yêu, kẻ thù) và cách họ gọi nhau trong bản gốc để đề xuất cách xưng hô tiếng Việt. Ghi chú nếu quan hệ thay đổi giữa chừng (kèm ID).
4. **Thuật ngữ** (mục 4): địa danh, tổ chức, chức danh, môn phái, chiêu thức, vật phẩm, thuật ngữ chuyên ngành, từ lặp nhiều lần. Với video phần mềm/hướng dẫn: thêm tên phần mềm, tên công cụ, menu, bảng, phím tắt xuất hiện trong video, kèm đề xuất cách viết theo quy chuẩn (tên giao diện tiếng Anh, đường dẫn menu " > ", phím tắt dạng "Ctrl + Shift + S").
5. **Câu cửa miệng** (mục 5): câu hoặc cụm một nhân vật nói đi nói lại, cần dịch giống nhau mỗi lần.
6. **Lỗi ASR** (mục 6): những chữ mà ASR nghe sai nhiều lần theo cùng một kiểu, rút ra từ diff.

Đề xuất bản dịch cho cả cột Tiếng Việt và English. Nếu không chắc cách dịch thì để trống ô dịch, chỉ ghi bản gốc và ghi chú.

## Cách ghi vào workspace/glossary.md

- Giữ nguyên cấu trúc, tiêu đề và các bảng của file.
- Mọi dòng agent thêm đều có trạng thái ❓.
- Không sửa, không xóa dòng ✅. Nếu thấy dòng ✅ có vẻ sai, nêu trong báo cáo thay vì tự sửa.
- Dòng ❓ đã có từ trước: chỉ cập nhật khi có bằng chứng mới rõ ràng.
- Không thêm trùng: kiểm tra cả các cách viết khác của cùng một tên.
- Ưu tiên chất lượng hơn số lượng: bỏ qua tên chỉ xuất hiện một lần không quan trọng và từ thông dụng ai cũng dịch đúng.
- Nếu `workspace/glossary.md` chưa tồn tại, chép từ `assets/glossary.template.md` của skill này (mọi lệnh `srt_tools.py` chạy từ gốc dự án cũng tự làm việc này).

## Báo cáo khi xong

Ngắn gọn trong chat:

- Đã quét những file nào (và chia cho bao nhiêu subagent, nếu có).
- Số mục đã thêm ở từng phần.
- Những điểm cần người dùng quyết định nhất (thường là quy ước tên riêng và xưng hô giữa các nhân vật chính), kèm lựa chọn đề xuất.
- Nhắc người dùng: duyệt xong thì đổi ❓ thành ✅ cho những dòng đồng ý; agent sẽ bắt buộc tuân theo dòng ✅ khi clean và dịch.
