# Subtitle Kit: FunASR → clean → dịch

Bộ mẫu để copy vào mỗi dự án phụ đề mới. Cần Python 3.8+ (không cần cài thêm thư viện).

## Cấu trúc

```
subtitle-kit/
├── AGENTS.md                 # luật chung của dự án
├── workspace/                # dữ liệu, chỉ nằm trên máy (đã ignore), tool tự tạo
│   ├── glossary.md           # glossary của dự án (tên, xưng hô, thuật ngữ)
│   ├── raw/                  # bỏ file .srt của FunASR vào đây
│   ├── cleaned/              # bản đã sửa lỗi
│   ├── trans/                # bản dịch: <tên>.vi.srt, <tên>.en.srt
│   └── work/                 # file tạm, sao lưu (backup/), xóa được
├── tools/srt_tools.py        # kiểm tra, chia, gộp, đối chiếu, tìm file, tiến độ
├── tools/link_skills.py      # liên kết skill cho Claude Code / Copilot
├── tests/                    # python -m unittest discover tests
└── .agent/
    ├── skills/
    │   ├── clean-funasr/
    │   │   └── references/   # audit.md (subagent soát bản clean)
    │   ├── build-glossary/
    │   │   ├── assets/       # glossary.template.md: mẫu trống, tool tự chép thành workspace/glossary.md
    │   │   └── references/   # extract.md (subagent trích ứng viên)
    │   ├── review-subtitle/
    │   │   └── references/   # find-errors.md, cross-check.md (cho subagent)
    │   └── translate-subtitle/
    │       └── references/   # target-vi.md, target-en.md
    └── workflows/            # lệnh slash cho Antigravity
        ├── clean.md          # /clean
        ├── glossary.md       # /glossary
        ├── trans-vi.md       # /trans-vi
        ├── trans-en.md       # /trans-en
        └── review.md         # /review
```

## Cách dùng

1. Copy cả thư mục này thành dự án mới, bỏ các file `.srt` của FunASR vào `workspace/raw/`.
2. `/clean` → kiểm tra vài chỗ trong `workspace/cleaned/`.
3. `/glossary` → duyệt `workspace/glossary.md`, đổi ❓ thành ✅ cho dòng đồng ý.
4. `/trans-vi` hoặc `/trans-en`.
5. `/review` → subagent tìm lỗi, agent trình bày và hỏi bạn muốn sửa gì; trả lời VD "sửa lỗi nghiêm trọng", "sửa ID 57, 60", "ID 61 sửa thành ...". Danh sách lỗi chỉ nằm trong chat, không tạo file.

Có thể thêm tên file sau lệnh, VD `/trans-en ep03.srt`. Hoặc nói thường: "dịch ep03 sang tiếng Việt".

Lệnh `/review` có ba chế độ: mặc định tìm lỗi rồi hỏi bạn (không tự sửa), `/review sửa` để sửa các mục bạn chọn từ danh sách vừa trình bày (có sao lưu trước; ở phiên mới thì review lại trước), `/review chéo` để kiểm tra nhất quán giữa các bài. VD `/review ep03.vi.srt`, `/review sửa ep03.vi.srt chỉ lỗi nghiêm trọng`.

**Subagent**: việc chỉ đọc và báo cáo được giao cho subagent với context sạch: tìm lỗi bản dịch (`/review`), soát bản clean (bước cuối của `/clean`), đọc từng bài để lập glossary (`/glossary`). Subagent không sửa file nào; sửa gì là do bạn chọn. Có thể chỉ định model cho subagent, VD `/review ep03 bằng sonnet`; tốt nhất là model khác với model đã dịch, vì cùng một model thường lặp lại đúng cách hiểu sai của chính nó. Công cụ không có subagent thì agent tự làm trong phiên hiện tại.

### Quy trình cho khóa học

Với khóa học nhiều bài, thuật ngữ và xưng hô phải thống nhất từ bài đầu đến bài cuối, nên đừng dịch cả khóa một lần:

1. `/clean` toàn bộ.
2. `/glossary` rồi duyệt, đổi ❓ thành ✅.
3. Dịch thử 2–3 bài đầu.
4. `/review` các bài đó.
5. Chỉnh `workspace/glossary.md` theo những gì review phát hiện (thuật ngữ dịch lệch, xưng hô).
6. Dịch phần còn lại.
7. `/review chéo` để bắt thuật ngữ không nhất quán giữa các bài, rồi `/review sửa` từng file nếu cần.

Muốn dịch lại bằng model khác: nói "dịch lại ep03". Agent sẽ cất bản dịch cũ và các phần đã dịch vào `workspace/work/ep03/backup/` (lệnh `archive`) rồi dịch từ đầu, không trộn với lần trước. `workspace/cleaned/` vẫn nguyên, không cần chạy lại FunASR hay clean.

Bị ngắt giữa chừng (mất mạng, hết phiên): gọi lại lệnh dịch là được. Agent chạy `parts` để biết phần nào đã xong, phần nào dở, rồi làm tiếp; không cần file checklist.

Xem tiến độ cả khóa: `python tools/srt_tools.py status`.

## Dùng với công cụ khác

Skill theo chuẩn mở Agent Skills nên dùng được ở nhiều nơi, chỉ khác thư mục:

| Công cụ | Thư mục skill | Gọi lệnh |
|---|---|---|
| Antigravity | `.agent/skills/` (sẵn) | `/clean`, `/glossary`, `/trans-vi`, `/trans-en`, `/review` (qua workflows) |
| VS Code + Copilot | `python tools/link_skills.py .github/skills` | `/clean-funasr`, `/build-glossary`, `/translate-subtitle vi`, `/review-subtitle` |
| Claude Code | `python tools/link_skills.py` (tạo `.claude/skills/`) | `/clean-funasr`, `/build-glossary`, `/translate-subtitle en`, `/review-subtitle` |

`link_skills.py` tạo liên kết (junction trên Windows, symlink trên macOS/Linux) trỏ về `.agent/skills/`, nên sửa skill một chỗ là mọi công cụ thấy ngay; liên kết đã nằm trong `.gitignore`. Thư mục `workflows/` chỉ dành cho Antigravity; công cụ khác gọi thẳng tên skill. Đường dẫn có thể thay đổi theo phiên bản công cụ, nếu skill không hiện ra hãy kiểm tra tài liệu của công cụ đó.

## Lệnh srt_tools.py

```
python tools/srt_tools.py info  workspace/raw/ep01.srt
python tools/srt_tools.py text  workspace/cleaned/ep01.srt --from 1 --to 50
python tools/srt_tools.py diff  workspace/raw/ep01.srt workspace/cleaned/ep01.srt
python tools/srt_tools.py validate workspace/cleaned/ep01.srt workspace/trans/ep01.vi.srt --target vi
python tools/srt_tools.py merge workspace/cleaned/ep01.srt workspace/work/ep01/vi workspace/trans/ep01.vi.srt
python tools/srt_tools.py pair  workspace/cleaned/ep01.srt workspace/trans/ep01.vi.srt --from 1 --to 100
python tools/srt_tools.py pair  workspace/cleaned/ep01.srt workspace/trans/ep01.vi.srt --ids 57,63,120-125
python tools/srt_tools.py check-glossary workspace/cleaned/ep01.srt workspace/trans/ep01.vi.srt --target vi
python tools/srt_tools.py lint  workspace/cleaned/ep01.srt workspace/trans/ep01.vi.srt
python tools/srt_tools.py review-prep workspace/cleaned/ep01.srt workspace/trans/ep01.vi.srt --target vi
python tools/srt_tools.py find "图层" workspace/cleaned/*.srt
python tools/srt_tools.py find "lớp|layer" workspace/trans/*.vi.srt --regex
python tools/srt_tools.py check-asr workspace/cleaned/*.srt
python tools/srt_tools.py parts workspace/cleaned/ep01.srt workspace/work/ep01/vi
python tools/srt_tools.py archive workspace/trans/ep01.vi.srt workspace/work/ep01/vi
python tools/srt_tools.py status
```

`validate` là chốt chặn quan trọng nhất: sai số block, ID hay timestamp là FAIL. Bạn cũng có thể tự chạy để kiểm tra bản dịch từ bất kỳ nguồn nào.

- `pair` in song song "ID | gốc | dịch" để đối chiếu; dừng với lỗi nếu hai file lệch số block. `--ids 57,63,120-125` chỉ in đúng các ID đó.
- `check-glossary` đọc các dòng ✅ trong `workspace/glossary.md` (cột Gốc + cột Tiếng Việt/English, nhận theo tên cột) và báo block có thuật ngữ gốc mà bản dịch không dùng cách dịch đã duyệt. Chỉ là cảnh báo; dòng ❓ không bị kiểm tra.
  Thuật ngữ chữ Latin khớp trọn từ ("art" không khớp "start"); chữ Hán khớp chuỗi con.
- `lint` báo chỗ nghi lỗi mà máy so được: số trong gốc không có trong bản dịch, tổ hợp phím hoặc tên phím (空格键, 回车...) khác gốc, chuột trái/phải/giữa bị mất, chữ Latin trong gốc tiếng Trung (tên phần mềm, menu, định dạng) bị mất, block đọc quá nhanh (`--cps`, mặc định 20 ký tự/giây, 0 để tắt). Chữ cần tìm được xét cả ở block liền trước và sau, vì câu dịch hay dồn sang block bên cạnh. Chỉ là chỗ nghi ngờ, cần đọc ngữ cảnh.
- `review-prep` chạy validate, check-glossary, lint trong một lần và in các lệnh `pair` cần đọc; subagent review dùng lệnh này để bớt số lượt gọi. `--from/--to` giới hạn trong một khoảng block (khi file dài được chia cho nhiều subagent).
- `find` tìm trong phần chữ của nhiều file (không phân biệt hoa thường), dùng cho review chéo bài.
- `check-asr` báo chỗ trong `workspace/cleaned/` còn sót lỗi ASR ✅ ở mục 6 glossary.
- `merge` ghép chữ dạng `ID | chữ` vào đúng ID, timestamp của file gốc, nên agent không phải chép lại timestamp. Nhận một file hoặc cả thư mục `part_*.txt`; thiếu, thừa, trùng ID hay block rỗng thì từ chối. `--cleanup` xóa thư mục phần sau khi ghép.
- `parts` liệt kê `part_*.txt` nào (mỗi phần 100 block) đã xong, dở hay chưa làm, phần thừa sót từ lần trước, và in lệnh `text` để đọc phần tiếp theo. Dùng để làm tiếp sau khi bị ngắt.
- File dài được làm theo từng đoạn `text --from --to`; bước clean ghi `workspace/work/<tên>/summary.md` (do subagent tóm tắt) để bước dịch không phải đọc lại cả bài.
- `archive` chuyển file/thư mục vào `workspace/work/<tên>/backup/` kèm thời gian (`--copy` để chép, giữ bản gốc).
- `status` in bảng mỗi bài một dòng: đã clean/dịch chưa, validate PASS/FAIL, `workspace/cleaned/` có bị sửa sau khi dịch không. Tính trực tiếp từ file nên không có file tiến độ nào cần lưu hay ignore.

## Mở rộng

- Thêm ngôn ngữ đích: tạo `.agent/skills/translate-subtitle/references/target-<mã>.md`, thêm workflow `trans-<mã>.md`, và thêm mã vào `--target` trong `srt_tools.py` nếu cần kiểm tra riêng.
- Quy định thuật ngữ kỹ thuật, tên phần mềm, phím tắt nằm ở mục "Thuật ngữ kỹ thuật, phần mềm, phím tắt" trong `target-vi.md` / `target-en.md`; muốn đổi riêng cho một dự án thì ghi vào mục 4 của `workspace/glossary.md`. `validate` sẽ cảnh báo phím tắt viết sai kiểu như "Ctrl cộng R".
- Lỗi ASR bị lặp lại nhiều: ghi vào mục 6 của glossary, bước clean sẽ tự sửa theo (và `check-asr` bắt chỗ sót).
- Sửa `srt_tools.py` xong thì chạy `python -m unittest discover tests`.
