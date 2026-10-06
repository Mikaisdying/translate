---
name: clean-funasr
description: Sửa lỗi nhận dạng giọng nói trong file phụ đề SRT xuất từ FunASR (hoặc ASR khác như Whisper), đọc từ workspace/raw/ và ghi vào workspace/cleaned/, giữ nguyên ID và timestamp, KHÔNG dịch. Dùng skill này khi người dùng muốn clean, dọn, sửa, chuẩn hóa transcript hay phụ đề vừa nhận dạng xong, kể cả khi họ chỉ nói "dọn file trong raw", "fix sub", "sửa lỗi chính tả phụ đề" hoặc gõ /clean.
---

# Clean FunASR

Mục tiêu: biến output thô của ASR thành bản phụ đề gốc sạch, đúng chữ, đúng dấu câu, để làm nguồn chuẩn cho bước dịch. Bản cleaned là thứ sẽ được dịch đi dịch lại nhiều lần bằng nhiều model, nên độ chính xác quan trọng hơn độ "hay".

## Thư mục

- Đọc từ `workspace/raw/`. Không bao giờ sửa hay ghi đè file trong `workspace/raw/`.
- Ghi kết quả vào `workspace/cleaned/` cùng tên file: `workspace/raw/ep01.srt` → `workspace/cleaned/ep01.srt`.
- File tạm để trong `workspace/work/<tên file>/` và có thể xóa sau khi xong.
- Lệnh chạy từ thư mục gốc dự án: `python tools/srt_tools.py ...` (dùng `python3` nếu máy cần).

## Chọn file cần xử lý

- Người dùng chỉ định file nào thì làm file đó.
- Không chỉ định: làm mọi `workspace/raw/*.srt` chưa có bản tương ứng trong `workspace/cleaned/`. File đã có bản cleaned thì bỏ qua, trừ khi người dùng yêu cầu làm lại.
- Làm lại file đã có bản cleaned: trước tiên cất bản cũ bằng `python tools/srt_tools.py archive workspace/cleaned/<file>.srt workspace/work/<file>/cleaned` (chuyển vào `workspace/work/<file>/backup/`), để phần sửa cũ không bị gộp lẫn vào. Báo người dùng rằng các bản dịch trong `workspace/trans/` của file này đã dựa trên bản cleaned cũ.
- Làm lần lượt từng file, xong file này (đến bước giao soát cho subagent) mới sang file khác.

## Quy trình cho mỗi file

1. **Kiểm tra định dạng**: `python tools/srt_tools.py info workspace/raw/<file>.srt`. Nếu báo lỗi định dạng, dừng lại và báo người dùng. Không tự đoán để sửa cấu trúc, vì sửa sai ID/timestamp sẽ làm lệch toàn bộ phụ đề.
2. **Đọc glossary**: đọc `workspace/glossary.md` nếu có, chú ý mục 1 (thông tin chung), 2 (nhân vật), 4 (thuật ngữ), 6 (lỗi ASR hay gặp). Dòng ✅ là bắt buộc theo; dòng ❓ chỉ tham khảo. Glossary trống thì vẫn làm bình thường.
3. **Nắm nội dung trước khi sửa**: nhiều lỗi ASR chỉ nhận ra được khi đã biết bài nói về gì, nhưng không đọc cả file hai lần (một lần lướt, một lần khi sửa).
   - File ≤ 150 block: bỏ bước này, đọc thẳng ở bước 4.
   - File dài hơn: giao subagent tóm tắt, lời giao việc chỉ gồm `Đọc và làm đúng theo .agent/skills/clean-funasr/references/summarize.md` và `File: workspace/raw/<file>.srt`. Ghi nguyên câu trả lời vào `workspace/work/<file>/summary.md`; bước dịch sẽ dùng lại file này thay vì đọc lại cả bài. Môi trường không có subagent thì đọc lướt cả file một lần bằng `text` rồi tự viết `summary.md` theo mẫu đó.
4. **Sửa**: không tự viết lại ID và timestamp. Đọc chữ bằng `text`, viết phần chữ đã sửa vào file text, mỗi block một dòng dạng `ID | chữ` (block nhiều dòng thì nối bằng ` / `), rồi để `merge` ghép vào đúng ID, timestamp của bản gốc. `merge` từ chối nếu thiếu ID, thừa ID, trùng ID hay có block rỗng.
   Block không cần sửa thì ghi `ID | =` (giữ nguyên chữ gốc) thay vì chép lại cả câu: vẫn phải có đủ mọi ID, nhưng chỉ viết lại chữ của những block thật sự sửa. Đây là phần tốn token nhất của bước clean, nên đừng đụng vào block chỉ để làm đẹp (xem "Sửa kèm" bên dưới).
   - File ≤ 150 block: `python tools/srt_tools.py text workspace/raw/<file>.srt`, viết `workspace/work/<file>/cleaned.txt`, rồi `python tools/srt_tools.py merge workspace/raw/<file>.srt workspace/work/<file>/cleaned.txt workspace/cleaned/<file>.srt`.
   - File dài hơn: làm từng phần 100 block. Phần 1 là block 1-100: `python tools/srt_tools.py text workspace/raw/<file>.srt --from 1 --to 100`, viết `workspace/work/<file>/cleaned/part_001.txt`; phần 2 là 101-200 vào `part_002.txt`, cứ thế. Ghi mỗi phần ngay khi xong. Không đọc file `.srt` trực tiếp (tốn gấp đôi token vì có ID và timestamp), không cần `split`.
   - Tiến độ: `python tools/srt_tools.py parts workspace/raw/<file>.srt workspace/work/<file>/cleaned` cho biết phần nào xong, dở hay chưa làm, và in sẵn lệnh `text` cho phần tiếp theo. Bị ngắt giữa chừng thì chạy lệnh này, đọc `summary.md`, đọc lại khoảng 10 block cuối của phần trước bằng `text` để câu nối liền, rồi làm tiếp. Đang làm liền một mạch thì phần trước vẫn còn trong ngữ cảnh, không cần đọc lại.
   - Ghép khi `parts` báo xong hết: `python tools/srt_tools.py merge workspace/raw/<file>.srt workspace/work/<file>/cleaned workspace/cleaned/<file>.srt --cleanup`. `--cleanup` xóa thư mục phần sau khi ghép thành công; từ đây sửa thẳng trên `workspace/cleaned/<file>.srt`.
5. **Kiểm tra**: `python tools/srt_tools.py validate workspace/raw/<file>.srt workspace/cleaned/<file>.srt`. Phải ra PASS. Nếu FAIL, sửa đúng chỗ báo lỗi rồi chạy lại. Không báo hoàn thành khi chưa PASS.
6. **Lỗi ASR đã duyệt**: `python tools/srt_tools.py check-asr workspace/cleaned/<file>.srt` báo những chỗ còn sót lỗi ASR ✅ ở mục 6 glossary. Sửa hết, trừ chỗ mà ngữ cảnh cho thấy chữ đó đúng ở đây (ghi vào báo cáo).
7. **Soát bằng subagent**: giao cho subagent (công cụ Agent/Task trong Claude Code, `runSubagent` trong VS Code Copilot) lời giao việc chỉ gồm:

   ```
   Đọc và làm đúng theo .agent/skills/clean-funasr/references/audit.md
   Bản raw: workspace/raw/<file>.srt
   Bản cleaned: workspace/cleaned/<file>.srt
   ```

   Subagent chỉ đọc và trả danh sách chỗ nghi sửa quá tay, đổi nghĩa, không nhất quán trong câu trả lời, không tạo file. Không kèm nhận xét của bạn để giữ góc nhìn độc lập. Trong lúc chờ có thể làm tiếp file sau. Môi trường không có subagent thì tự làm theo `audit.md` đó.
   Không tự áp dụng kết quả soát: đưa vào báo cáo cuối để người dùng chọn (xem dưới). Người dùng chọn xong thì sửa đúng các mục đó trong `workspace/cleaned/<file>.srt` rồi chạy lại `validate`. Phiên mới không còn danh sách thì giao soát lại.

## Được sửa

Chỉ sửa khi ngữ cảnh cho thấy rõ là lỗi:

- Chữ nhận dạng sai do đồng âm, gần âm (VD tiếng Trung: 他/她/它, 在/再, 的/得/地; tiếng Anh: their/there, "a lot" bị nghe thành "allot").
- Tên riêng, thuật ngữ, địa danh bị nhận sai, đặc biệt khi cùng một tên bị viết nhiều kiểu trong file: thống nhất về một cách viết đúng (theo glossary nếu có).
- Phím tắt và tên phần mềm bị ASR nhận sai: chuẩn hóa về dạng chuẩn. Tên phím viết hoa chữ đầu (Ctrl, Shift, Alt, Cmd, Option, Enter, Tab, Esc, Space), chữ cái viết hoa, nối bằng " + ". VD "ctrl加r", "control R", "Ctrl 加 Shift 加 S" → "Ctrl + R", "Ctrl + Shift + S". Tên phần mềm khi rõ là gì thì viết đúng tên: "photo shop", "PS软件" → "Photoshop". Tên menu, công cụ bằng ngôn ngữ gốc (VD 图层, 画笔工具) KHÔNG đổi sang tiếng Anh ở bước clean vì clean không được dịch; chỉ sửa chính tả.
- Từ bị lặp do ASR làm câu khó hiểu ("我我我们", "the the"), từ bị cắt vỡ.
- Dấu câu thiếu hoặc sai mà làm câu bị hiểu sai (VD không ngắt thì đọc thành nghĩa khác).

**Sửa kèm**: những việc sau chỉ làm trong block đang sửa vì một lý do ở trên, không sửa một block chỉ vì chúng. Bước dịch tự xử lý ngắt câu và bỏ từ đệm, nên viết lại cả file chỉ để làm đẹp là tốn token mà không giúp gì thêm:

- Thêm dấu câu, viết hoa đầu câu và tên riêng (với ngôn ngữ có chữ hoa).
- Bỏ từ đệm thuần túy (嗯, 啊, 呃, um, uh) nếu block vẫn còn nội dung khác. Block chỉ có từ đệm thì giữ nguyên, vì block không được để trống.
- Khoảng trắng thừa, gộp dòng bị ngắt giữa chừng trong block.

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
- Kết quả soát của subagent: số mục theo loại cho từng file, toàn bộ mục "đổi nghĩa" (giữ format từng mục để người dùng chọn theo ID), các mục khác gom theo loại kèm ID. Hỏi người dùng muốn sửa những mục nào (tất cả, theo loại, theo ID, hay không sửa).
- Lỗi ASR lặp lại nhiều lần hoặc tên riêng mới phát hiện: đề xuất thêm vào `workspace/glossary.md` (mục 2, 4 hoặc 6) với trạng thái ❓. Chỉ ghi vào glossary khi người dùng đồng ý.
