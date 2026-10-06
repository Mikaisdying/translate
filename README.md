# Subtitle Kit: FunASR → clean → dịch

Bộ mẫu để copy vào mỗi dự án phụ đề mới. Cần Python 3.8+ (không cần cài thêm thư viện).

## Cấu trúc

```
subtitle-kit/
├── AGENTS.md                 # luật chung của dự án
├── glossary.md               # để trống, điền theo từng dự án
├── raw/                      # bỏ file .srt của FunASR vào đây
├── cleaned/                  # bản đã sửa lỗi
├── trans/                    # bản dịch: <tên>.vi.srt, <tên>.en.srt
├── tools/srt_tools.py        # kiểm tra, chia, gộp, đối chiếu, tìm file
└── .agent/
    ├── skills/
    │   ├── clean-funasr/
    │   ├── build-glossary/
    │   ├── review-subtitle/
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

1. Copy cả thư mục này thành dự án mới, bỏ các file `.srt` của FunASR vào `raw/`.
2. `/clean` → kiểm tra vài chỗ trong `cleaned/`.
3. `/glossary` → duyệt `glossary.md`, đổi ❓ thành ✅ cho dòng đồng ý.
4. `/trans-vi` hoặc `/trans-en`.
5. `/review` → đọc `.work/<tên>/review.<mã>.md`; muốn áp dụng thì `/review sửa`.

Có thể thêm tên file sau lệnh, VD `/trans-en ep03.srt`. Hoặc nói thường: "dịch ep03 sang tiếng Việt".

Lệnh `/review` có ba chế độ: mặc định chỉ báo lỗi (không sửa file), `/review sửa` để sửa theo danh sách lỗi (có sao lưu trước), `/review chéo` để kiểm tra nhất quán giữa các bài. VD `/review ep03.vi.srt`, `/review sửa ep03.vi.srt chỉ lỗi nghiêm trọng`.

**Lưu ý**: nên review ở phiên mới, tốt nhất bằng model khác với model đã dịch, vì cùng một model thường lặp lại đúng cách hiểu sai của chính nó.

### Quy trình cho khóa học

Với khóa học nhiều bài, thuật ngữ và xưng hô phải thống nhất từ bài đầu đến bài cuối, nên đừng dịch cả khóa một lần:

1. `/clean` toàn bộ.
2. `/glossary` rồi duyệt, đổi ❓ thành ✅.
3. Dịch thử 2–3 bài đầu.
4. `/review` các bài đó.
5. Chỉnh `glossary.md` theo những gì review phát hiện (thuật ngữ dịch lệch, xưng hô).
6. Dịch phần còn lại.
7. `/review chéo` để bắt thuật ngữ không nhất quán giữa các bài, rồi `/review sửa` từng file nếu cần.

Muốn dịch lại bằng model khác: xóa file trong `trans/` rồi chạy lại lệnh dịch. `cleaned/` vẫn nguyên, không cần chạy lại FunASR hay clean.

## Dùng với công cụ khác

Skill theo chuẩn mở Agent Skills nên dùng được ở nhiều nơi, chỉ khác thư mục:

| Công cụ | Thư mục skill | Gọi lệnh |
|---|---|---|
| Antigravity | `.agent/skills/` (sẵn) | `/clean`, `/glossary`, `/trans-vi`, `/trans-en`, `/review` (qua workflows) |
| VS Code + Copilot | copy sang `.agents/skills/` hoặc `.github/skills/` | `/clean-funasr`, `/build-glossary`, `/translate-subtitle vi`, `/review-subtitle` |
| Claude Code | copy sang `.claude/skills/` | `/clean-funasr`, `/build-glossary`, `/translate-subtitle en`, `/review-subtitle` |

Thư mục `workflows/` chỉ dành cho Antigravity; công cụ khác gọi thẳng tên skill. Đường dẫn có thể thay đổi theo phiên bản công cụ, nếu skill không hiện ra hãy kiểm tra tài liệu của công cụ đó.

## Lệnh srt_tools.py

```
python tools/srt_tools.py info  raw/ep01.srt
python tools/srt_tools.py text  cleaned/ep01.srt --from 1 --to 50
python tools/srt_tools.py diff  raw/ep01.srt cleaned/ep01.srt
python tools/srt_tools.py validate cleaned/ep01.srt trans/ep01.vi.srt --target vi
python tools/srt_tools.py split cleaned/ep01.srt --size 100
python tools/srt_tools.py merge .work/ep01/vi trans/ep01.vi.srt
python tools/srt_tools.py pair  cleaned/ep01.srt trans/ep01.vi.srt --from 1 --to 100
python tools/srt_tools.py check-glossary cleaned/ep01.srt trans/ep01.vi.srt --target vi
python tools/srt_tools.py find "图层" cleaned/*.srt
python tools/srt_tools.py find "lớp|layer" trans/*.vi.srt --regex
```

`validate` là chốt chặn quan trọng nhất: sai số block, ID hay timestamp là FAIL. Bạn cũng có thể tự chạy để kiểm tra bản dịch từ bất kỳ nguồn nào.

- `pair` in song song "ID | gốc | dịch" để đối chiếu; dừng với lỗi nếu hai file lệch số block.
- `check-glossary` đọc các dòng ✅ trong `glossary.md` (cột Gốc + cột Tiếng Việt/English, nhận theo tên cột) và báo block có thuật ngữ gốc mà bản dịch không dùng cách dịch đã duyệt. Chỉ là cảnh báo; dòng ❓ không bị kiểm tra.
- `find` tìm trong phần chữ của nhiều file (không phân biệt hoa thường), dùng cho review chéo bài.

## Mở rộng

- Thêm ngôn ngữ đích: tạo `.agent/skills/translate-subtitle/references/target-<mã>.md`, thêm workflow `trans-<mã>.md`, và thêm mã vào `--target` trong `srt_tools.py` nếu cần kiểm tra riêng.
- Quy định thuật ngữ kỹ thuật, tên phần mềm, phím tắt nằm ở mục "Thuật ngữ kỹ thuật, phần mềm, phím tắt" trong `target-vi.md` / `target-en.md`; muốn đổi riêng cho một dự án thì ghi vào mục 4 của `glossary.md`. `validate` sẽ cảnh báo phím tắt viết sai kiểu như "Ctrl cộng R".
- Lỗi ASR bị lặp lại nhiều: ghi vào mục 6 của glossary, bước clean sẽ tự sửa theo.
