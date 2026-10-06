---
description: Review bản dịch trong workspace/trans/ so với workspace/cleaned/ và glossary (báo lỗi, sửa, hoặc kiểm tra chéo bài)
---
1. Dùng skill `review-subtitle` (đọc `.agent/skills/review-subtitle/SKILL.md` và làm đúng theo đó).
2. Lấy tên file, ngôn ngữ, chế độ và lựa chọn sửa từ phần người dùng ghi sau lệnh: có chữ "sửa" hoặc "fix" thì dùng chế độ sửa (kèm phạm vi nếu có, VD "chỉ lỗi nghiêm trọng", "ID 57 60"), có chữ "chéo" hoặc "cross" thì dùng chế độ chéo bài. Ngôn ngữ lấy từ đuôi file (`.vi.srt`, `.en.srt`) hoặc từ lời người dùng.
3. Không ghi gì thêm thì dùng chế độ báo lỗi: chạy `status`, hỏi người dùng review bài nào; subagent tìm lỗi và trả kết quả trong câu trả lời, bạn trình bày rồi hỏi người dùng muốn sửa gì. Không sửa file khi người dùng chưa chọn.
