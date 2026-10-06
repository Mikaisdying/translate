---
description: Review bản dịch trong trans/ so với cleaned/ và glossary (báo lỗi, sửa, hoặc kiểm tra chéo bài)
---
1. Dùng skill `review-subtitle` (đọc `.agent/skills/review-subtitle/SKILL.md` và làm đúng theo đó).
2. Lấy tên file, ngôn ngữ và chế độ từ phần người dùng ghi sau lệnh: có chữ "sửa" hoặc "fix" thì dùng chế độ sửa, có chữ "chéo" hoặc "cross" thì dùng chế độ chéo bài. Ngôn ngữ lấy từ đuôi file (`.vi.srt`, `.en.srt`) hoặc từ lời người dùng.
3. Không ghi gì thêm thì dùng chế độ báo lỗi cho mọi file trong `trans/`, chỉ liệt kê lỗi, không sửa file.
