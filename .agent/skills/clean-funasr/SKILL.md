---
name: clean-funasr
description: Sửa lỗi nhận dạng giọng nói trong file phụ đề SRT xuất từ FunASR (hoặc ASR khác như Whisper), đọc từ raw/ và ghi vào cleaned/, giữ nguyên ID và timestamp, KHÔNG dịch. Dùng skill này khi người dùng muốn clean, dọn, sửa, chuẩn hóa transcript hay phụ đề vừa nhận dạng xong, kể cả khi họ chỉ nói "dọn file trong raw", "fix sub", "sửa lỗi chính tả phụ đề" hoặc gõ /clean.
---

# Clean FunASR

Mục tiêu: biến output thô của ASR thành bản phụ đề gốc sạch, đúng chữ, đúng dấu câu, để làm nguồn chuẩn cho bước dịch. Bản cleaned là thứ sẽ được dịch đi dịch lại nhiều lần bằng nhiều model, nên độ chính xác quan trọng hơn độ "hay".

## Thư mục

- Đọc từ `raw/`. Không bao giờ sửa hay ghi đè file trong `raw/`.
- Ghi kết quả vào `cleaned/` cùng tên file: `raw/ep01.srt` → `cleaned/ep01.srt`.
- File tạm để trong `.work/<tên file>/` và có thể xóa sau khi xong.
- Lệnh chạy từ thư mục gốc dự án: `python tools/srt_tools.py ...` (dùng `python3` nếu máy cần).

## Chọn file cần xử lý

- Người dùng chỉ định file nào thì làm file đó.
- Không chỉ định: làm mọi `raw/*.srt` chưa có bản tương ứng trong `cleaned/`. File đã có bản cleaned thì bỏ qua, trừ khi người dùng yêu cầu làm lại.
- Làm lần lượt từng file, xong file này mới sang file khác.

## Quy trình cho mỗi file

1. **Kiểm tra định dạng**: `python tools/srt_tools.py info raw/<file>.srt`. Nếu báo lỗi định dạng, dừng lại và báo người dùng. Không tự đoán để sửa cấu trúc, vì sửa sai ID/timestamp sẽ làm lệch toàn bộ phụ đề.
2. **Đọc glossary**: đọc `glossary.md` nếu có, chú ý mục 1 (thông tin chung), 2 (nhân vật), 4 (thuật ngữ), 6 (lỗi ASR hay gặp). Dòng ✅ là bắt buộc theo; dòng ❓ chỉ tham khảo. Glossary trống thì vẫn làm bình thường.
3. **Đọc lướt toàn bộ** bằng `python tools/srt_tools.py text raw/<file>.srt` để nắm nội dung, nhân vật, chủ đề trước khi sửa. Nhiều lỗi ASR chỉ nhận ra được khi đã biết câu chuyện nói về gì.
4. **Sửa**:
   - File ≤ 150 block: làm cả file một lần.
   - File dài hơn: `python tools/srt_tools.py split raw/<file>.srt --size 100`, rồi làm từng phần `.work/<file>/part_XXX.srt`, ghi bản đã sửa vào `.work/<file>/cleaned/part_XXX.srt` (cùng tên phần). Trước mỗi phần, xem lại khoảng 10 block cuối của phần trước để câu nối liền mạch.
   - Sau cùng gộp: `python tools/srt_tools.py merge .work/<file>/cleaned cleaned/<file>.srt`.
5. **Kiểm tra**: `python tools/srt_tools.py validate raw/<file>.srt cleaned/<file>.srt`. Phải ra PASS. Nếu FAIL, sửa đúng chỗ báo lỗi rồi chạy lại. Không báo hoàn thành khi chưa PASS.
6. **Tự soát**: `python tools/srt_tools.py diff raw/<file>.srt cleaned/<file>.srt` và đọc lại các chỗ đã đổi. Hoàn tác những chỗ sửa quá tay hoặc đổi nghĩa.

## Được sửa

Chỉ sửa khi ngữ cảnh cho thấy rõ là lỗi:

- Chữ nhận dạng sai do đồng âm, gần âm (VD tiếng Trung: 他/她/它, 在/再, 的/得/地; tiếng Anh: their/there, "a lot" bị nghe thành "allot").
- Tên riêng, thuật ngữ, địa danh bị nhận sai, đặc biệt khi cùng một tên bị viết nhiều kiểu trong file: thống nhất về một cách viết đúng (theo glossary nếu có).
- Phím tắt và tên phần mềm bị ASR nhận sai: chuẩn hóa về dạng chuẩn. Tên phím viết hoa chữ đầu (Ctrl, Shift, Alt, Cmd, Option, Enter, Tab, Esc, Space), chữ cái viết hoa, nối bằng " + ". VD "ctrl加r", "control R", "Ctrl 加 Shift 加 S" → "Ctrl + R", "Ctrl + Shift + S". Tên phần mềm khi rõ là gì thì viết đúng tên: "photo shop", "PS软件" → "Photoshop". Tên menu, công cụ bằng ngôn ngữ gốc (VD 图层, 画笔工具) KHÔNG đổi sang tiếng Anh ở bước clean vì clean không được dịch; chỉ sửa chính tả.
- Dấu câu sai hoặc thiếu, viết hoa đầu câu và tên riêng (với ngôn ngữ có chữ hoa).
- Từ bị lặp do ASR ("我我我们", "the the"), từ bị cắt vỡ, khoảng trắng thừa.
- Từ đệm thuần túy (嗯, 啊, 呃, um, uh) có thể bỏ nếu block vẫn còn nội dung khác. Block chỉ có từ đệm thì giữ nguyên, vì block không được để trống.

## Không được làm

- Không dịch. Dịch là việc của skill `translate-subtitle`.
- Không đổi ID, timestamp, thứ tự block, số lượng block. Không gộp hay tách block, kể cả khi một câu bị cắt ngang qua nhiều block: chỉ sửa chữ trong từng block, để câu tự nối qua các block.
- Không viết lại cho hay hơn, không đổi văn phong, không tóm tắt, không thêm ý.
- Không bỏ phần lời có nghĩa, kể cả câu nói lắp, câu chửi, câu ngập ngừng mang cảm xúc.
- Không đưa ghi chú, Markdown, giải thích hay dấu [?] vào file phụ đề. Chỗ nào không chắc thì giữ nguyên chữ gốc và ghi vào báo cáo.

Nguyên tắc khi phân vân: giữ nguyên. Một lỗi ASR còn sót thì người dịch vẫn có thể đoán ra; một chỗ bị "sửa" sai nghĩa thì sẽ bị dịch sai một cách tự tin.

## Báo cáo khi xong

Trả lời ngắn gọn trong chat (không ghi vào file phụ đề):

- File đã xử lý, số block, số block có thay đổi, kết quả validate.
- Vài sửa đổi tiêu biểu.
- Những chỗ không chắc (kèm ID) để người dùng tự kiểm tra.
- Lỗi ASR lặp lại nhiều lần hoặc tên riêng mới phát hiện: đề xuất thêm vào `glossary.md` (mục 2, 4 hoặc 6) với trạng thái ❓. Chỉ ghi vào glossary khi người dùng đồng ý.
