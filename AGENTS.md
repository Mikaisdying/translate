# Dự án phụ đề

Pipeline: FunASR → `raw/` → clean → `cleaned/` → dịch → `trans/`

- `raw/`: output gốc của FunASR. Không bao giờ sửa hay ghi đè.
- `cleaned/`: bản gốc đã sửa lỗi, là nguồn chuẩn để dịch. Bước dịch không được sửa thư mục này.
- `trans/`: bản dịch, đặt tên `<tên>.<mã ngôn ngữ>.srt` (VD `ep01.vi.srt`).
- `.work/`: file tạm, xóa được.
- `glossary.md`: tên, xưng hô, thuật ngữ. Dòng ✅ bắt buộc tuân theo.

Clean và dịch là hai bước riêng: skill `clean-funasr` và `translate-subtitle`. Glossary: skill `build-glossary`. Review bản dịch: skill `review-subtitle` (mặc định chỉ báo lỗi, ghi vào `.work/`, không sửa `trans/` nếu chưa được yêu cầu).

Mọi file phụ đề: UTF-8, giữ nguyên ID, timestamp, số block, thứ tự. Không ghi chú, Markdown hay lời giải thích vào file phụ đề.

Công cụ kiểm tra: `python tools/srt_tools.py` (info, text, split, merge, diff, validate, pair, check-glossary, find).
