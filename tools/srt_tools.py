#!/usr/bin/env python3
"""
srt_tools.py - Công cụ phụ trợ cho pipeline phụ đề raw -> cleaned -> trans.
Chỉ dùng thư viện chuẩn của Python (3.8+).

Lệnh:
  info     FILE                         Thống kê số block, thời lượng, lỗi định dạng
  text     FILE [--from N] [--to M]     In gọn "ID | text" (đọc nhanh, ít token)
  split    FILE [--size 100] [--out DIR] Chia file dài thành nhiều phần
  merge    DIR OUTFILE                  Gộp các phần lại thành một file
  diff     SRC DST [--limit 50]         Liệt kê các block có nội dung thay đổi
  validate SRC DST [--target vi|en]     Kiểm tra cấu trúc DST so với SRC
  pair     SRC DST [--from N] [--to M]  In song song "ID | gốc | dịch" để đối chiếu (dừng nếu lệch số block)
  check-glossary SRC DST --target vi|en [--glossary glossary.md]
                                        Báo block có thuật ngữ ✅ trong glossary mà bản dịch không dùng
  find     PATTERN FILE [FILE ...] [--regex]
                                        Tìm chuỗi trong phần chữ của nhiều file SRT (không phân biệt hoa thường)

validate trả về mã thoát 1 nếu có LỖI (sai số block, ID, timestamp, block rỗng).
CẢNH BÁO (sót chữ gốc, ký hiệu Markdown...) không làm hỏng lệnh nhưng cần xem lại.
check-glossary chỉ cảnh báo, mã thoát 0 trừ khi không đọc được file hoặc hai file lệch số block.
"""
import argparse
import glob
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

TIMING_RE = re.compile(
    r"^\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")
VI_ONLY_RE = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]")
MARKDOWN_RE = re.compile(r"(```|\*\*|^#{1,6}\s|^>\s|translated by|bản dịch bởi)", re.I | re.M)
BAD_SHORTCUT_RE = re.compile(
    r"(?<![a-z])(?:ctrl|control|shift|alt|cmd|command|option|win)\s*(?:(?:cộng|plus|và)(?!\w)|加)",
    re.I,
)


class Block:
    __slots__ = ("idx", "timing", "text", "pos")

    def __init__(self, idx, timing, text, pos):
        self.idx = idx        # chuỗi ID như trong file
        self.timing = timing  # dòng timestamp nguyên văn
        self.text = text      # danh sách dòng chữ
        self.pos = pos        # thứ tự block (bắt đầu từ 1)


def read_srt(path):
    raw = Path(path).read_bytes()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        sys.exit(f"[LỖI] {path} không phải UTF-8. Hãy chuyển sang UTF-8 trước.")
    content = content.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    blocks, errors = [], []
    if not content.strip():
        return blocks, ["File rỗng"]
    for pos, chunk in enumerate(re.split(r"\n[ \t]*\n+", content), start=1):
        lines = chunk.split("\n")
        if len(lines) < 2:
            errors.append(f"Block thứ {pos}: thiếu dòng (chỉ có {len(lines)} dòng)")
            blocks.append(Block(lines[0].strip(), "", [], pos))
            continue
        idx, timing, text = lines[0].strip(), lines[1].strip(), lines[2:]
        if not idx.isdigit():
            errors.append(f"Block thứ {pos}: ID không phải số: {idx!r}")
        if not TIMING_RE.match(timing):
            errors.append(f"Block thứ {pos} (ID {idx}): timestamp sai định dạng: {timing!r}")
        blocks.append(Block(idx, timing, text, pos))
    return blocks, errors


def write_srt(path, blocks):
    out = "\n\n".join(
        "\n".join([b.idx, b.timing] + b.text) for b in blocks
    ) + "\n"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(out, encoding="utf-8", newline="\n")


def timing_end(t):
    m = TIMING_RE.match(t)
    return m.group(2) if m else "?"


# ---------------- lệnh ----------------

def cmd_info(a):
    blocks, errors = read_srt(a.file)
    print(f"File:   {a.file}")
    print(f"Blocks: {len(blocks)}")
    if blocks:
        print(f"ID:     {blocks[0].idx} -> {blocks[-1].idx}")
        print(f"Kết thúc lúc: {timing_end(blocks[-1].timing)}")
        empty = sum(1 for b in blocks if not "".join(b.text).strip())
        if empty:
            print(f"Block rỗng: {empty}")
    for e in errors:
        print(f"[LỖI] {e}")
    return 1 if errors else 0


def cmd_text(a):
    blocks, errors = read_srt(a.file)
    for e in errors:
        print(f"[LỖI] {e}", file=sys.stderr)
    for b in blocks:
        if a.start and b.pos < a.start:
            continue
        if a.end and b.pos > a.end:
            break
        print(f"{b.idx} | {' / '.join(t.strip() for t in b.text)}")
    return 0


def cmd_split(a):
    blocks, errors = read_srt(a.file)
    if errors:
        for e in errors:
            print(f"[LỖI] {e}")
        print("Sửa lỗi định dạng trước khi chia.")
        return 1
    out = Path(a.out) if a.out else Path(".work") / Path(a.file).stem
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("part_*.srt"):
        old.unlink()
    n = 0
    for i in range(0, len(blocks), a.size):
        n += 1
        part = blocks[i:i + a.size]
        write_srt(out / f"part_{n:03d}.srt", part)
        print(f"part_{n:03d}.srt  block {part[0].pos}-{part[-1].pos}  (ID {part[0].idx}-{part[-1].idx})")
    print(f"Đã chia {len(blocks)} block thành {n} phần trong {out}/")
    return 0


def cmd_merge(a):
    parts = sorted(Path(a.dir).glob("part_*.srt"))
    if not parts:
        print(f"[LỖI] Không thấy part_*.srt trong {a.dir}")
        return 1
    allb, bad = [], False
    for p in parts:
        blocks, errors = read_srt(p)
        for e in errors:
            print(f"[LỖI] {p.name}: {e}")
            bad = True
        allb.extend(blocks)
    if bad:
        return 1
    write_srt(a.outfile, allb)
    print(f"Đã gộp {len(parts)} phần, {len(allb)} block -> {a.outfile}")
    return 0


def cmd_diff(a):
    src, _ = read_srt(a.src)
    dst, _ = read_srt(a.dst)
    shown = changed = 0
    for s, d in zip(src, dst):
        if s.text != d.text:
            changed += 1
            if shown < a.limit:
                shown += 1
                print(f"[{s.idx}] - {' / '.join(s.text)}")
                print(f"[{d.idx}] + {' / '.join(d.text)}\n")
    print(f"Thay đổi {changed}/{min(len(src), len(dst))} block"
          + (f" (hiển thị {shown})" if changed > shown else ""))
    return 0


def cmd_validate(a):
    src, src_err = read_srt(a.src)
    dst, dst_err = read_srt(a.dst)
    errors, warns = [], []
    errors += [f"SRC: {e}" for e in src_err]
    errors += [f"DST: {e}" for e in dst_err]

    if len(src) != len(dst):
        errors.append(f"Số block khác nhau: SRC={len(src)} DST={len(dst)}")

    untranslated = 0
    for s, d in zip(src, dst):
        if s.idx != d.idx:
            errors.append(f"Block thứ {s.pos}: ID đổi {s.idx} -> {d.idx}")
        if s.timing != d.timing:
            errors.append(f"ID {s.idx}: timestamp đổi {s.timing!r} -> {d.timing!r}")
        st, dt = "\n".join(s.text).strip(), "\n".join(d.text).strip()
        if st and not dt:
            errors.append(f"ID {d.idx}: block bị bỏ trống")
        if MARKDOWN_RE.search(dt):
            warns.append(f"ID {d.idx}: có ký hiệu Markdown/ghi chú: {dt[:60]!r}")
        m = BAD_SHORTCUT_RE.search(dt)
        if m:
            warns.append(f"ID {d.idx}: phím tắt sai định dạng, nên dùng ' + ': {m.group(0)!r}")
        if a.target:
            if CJK_RE.search(dt):
                warns.append(f"ID {d.idx}: còn sót chữ Hán/Nhật/Hàn: {dt[:60]!r}")
            if a.target == "en" and VI_ONLY_RE.search(dt):
                warns.append(f"ID {d.idx}: có chữ tiếng Việt trong bản tiếng Anh: {dt[:60]!r}")
            if st and st == dt and len(st) > 3:
                untranslated += 1

    if a.target and untranslated:
        warns.append(f"{untranslated} block giống hệt bản gốc (có thể chưa dịch, "
                     f"hoặc chỉ là tên riêng/tiếng kêu) - kiểm tra bằng lệnh diff")

    for e in errors[:50]:
        print(f"[LỖI] {e}")
    if len(errors) > 50:
        print(f"... và {len(errors) - 50} lỗi khác")
    for w in warns[:30]:
        print(f"[CẢNH BÁO] {w}")
    if len(warns) > 30:
        print(f"... và {len(warns) - 30} cảnh báo khác")

    print(f"\nSRC {len(src)} block | DST {len(dst)} block | "
          f"{len(errors)} lỗi | {len(warns)} cảnh báo")
    print("KẾT QUẢ: " + ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


def aligned_blocks(src_path, dst_path):
    """Đọc hai file, trả về (src, dst) hoặc None nếu lệch số block."""
    src, _ = read_srt(src_path)
    dst, _ = read_srt(dst_path)
    if len(src) != len(dst):
        print(f"[LỖI] Số block khác nhau: SRC={len(src)} DST={len(dst)}. "
              f"Chạy validate để xem chi tiết.")
        return None
    return src, dst


def cmd_pair(a):
    pair = aligned_blocks(a.src, a.dst)
    if pair is None:
        return 1
    for s, d in zip(*pair):
        if a.start and s.pos < a.start:
            continue
        if a.end and s.pos > a.end:
            break
        st = " / ".join(t.strip() for t in s.text)
        dt = " / ".join(t.strip() for t in d.text)
        idx = s.idx if s.idx == d.idx else f"{s.idx}≠{d.idx}"
        print(f"{idx} | {st} | {dt}")
    return 0


def split_options(cell):
    """Tách ô có nhiều cách viết, ngăn bằng '/' hoặc ','."""
    return [o.strip() for o in re.split(r"[/,，]", cell) if o.strip()]


def table_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load_glossary_terms(path, target):
    """Trả về danh sách (ô gốc, [cách viết gốc], [phương án đích]) của các dòng ✅."""
    try:
        content = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        sys.exit(f"[LỖI] Không đọc được {path}: {e}")
    content = re.sub(r"<!--.*?-->", "", content, flags=re.S)
    col_target = {"vi": "Tiếng Việt", "en": "English"}[target]
    terms, header = [], None
    for line in content.split("\n"):
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = table_cells(line)
        if all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c):
            continue  # dòng phân cách |---|---|
        if header is None:
            header = cells
            continue
        if not {"Gốc", col_target, "Trạng thái"} <= set(header):
            continue
        row = dict(zip(header, cells))
        if "✅" not in row.get("Trạng thái", ""):
            continue
        src_opts = split_options(row["Gốc"])
        dst_opts = split_options(row[col_target])
        if src_opts and dst_opts:
            terms.append((row["Gốc"], src_opts, dst_opts))
    return terms


def cmd_check_glossary(a):
    terms = load_glossary_terms(a.glossary, a.target)
    if not terms:
        print(f"Không có dòng ✅ nào có cả ô Gốc và ô {'Tiếng Việt' if a.target == 'vi' else 'English'} "
              f"trong {a.glossary}, không có gì để kiểm tra.")
        return 0
    pair = aligned_blocks(a.src, a.dst)
    if pair is None:
        return 1
    counts = {}
    for s, d in zip(*pair):
        st, dt = " / ".join(t.strip() for t in s.text), " / ".join(t.strip() for t in d.text)
        st_low, dt_low = st.lower(), dt.lower()
        for cell, src_opts, dst_opts in terms:
            hit = next((o for o in src_opts if o.lower() in st_low), None)
            if hit is None or any(o.lower() in dt_low for o in dst_opts):
                continue
            counts[cell] = counts.get(cell, 0) + 1
            print(f"ID {s.idx}: '{hit}' nên dịch là '{' / '.join(dst_opts)}' "
                  f"| gốc: {st} | dịch: {dt}")
    total = sum(counts.values())
    print(f"\nĐã kiểm tra {len(terms)} thuật ngữ ✅ trên {len(pair[0])} block: {total} vi phạm")
    for cell, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cell}: {n}")
    return 0


def cmd_find(a):
    flags = re.I
    try:
        pat = re.compile(a.pattern if a.regex else re.escape(a.pattern), flags)
    except re.error as e:
        print(f"[LỖI] Regex sai: {e}")
        return 1
    files = []
    for f in a.files:  # PowerShell/cmd không tự mở rộng *.srt
        files.extend(sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f])
    total = 0
    for f in files:
        blocks, _ = read_srt(f)
        for b in blocks:
            text = " / ".join(t.strip() for t in b.text)
            if pat.search(text):
                total += 1
                print(f"{Path(f).name} | {b.idx} | {text}")
    print(f"\n{total} block khớp trong {len(files)} file")
    return 0


def main():
    p = argparse.ArgumentParser(description="Công cụ SRT cho pipeline raw -> cleaned -> trans")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("info"); s.add_argument("file"); s.set_defaults(fn=cmd_info)

    s = sub.add_parser("text"); s.add_argument("file")
    s.add_argument("--from", dest="start", type=int, default=0, help="block thứ N (từ 1)")
    s.add_argument("--to", dest="end", type=int, default=0, help="đến block thứ M")
    s.set_defaults(fn=cmd_text)

    s = sub.add_parser("split"); s.add_argument("file")
    s.add_argument("--size", type=int, default=100)
    s.add_argument("--out", help="mặc định .work/<tên file>/")
    s.set_defaults(fn=cmd_split)

    s = sub.add_parser("merge"); s.add_argument("dir"); s.add_argument("outfile")
    s.set_defaults(fn=cmd_merge)

    s = sub.add_parser("diff"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_diff)

    s = sub.add_parser("validate"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--target", choices=["vi", "en"], help="bật kiểm tra bản dịch")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("pair"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--from", dest="start", type=int, default=0, help="block thứ N (từ 1)")
    s.add_argument("--to", dest="end", type=int, default=0, help="đến block thứ M")
    s.set_defaults(fn=cmd_pair)

    s = sub.add_parser("check-glossary"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--target", choices=["vi", "en"], required=True, help="ngôn ngữ của DST")
    s.add_argument("--glossary", default="glossary.md")
    s.set_defaults(fn=cmd_check_glossary)

    s = sub.add_parser("find"); s.add_argument("pattern"); s.add_argument("files", nargs="+")
    s.add_argument("--regex", action="store_true", help="coi PATTERN là biểu thức chính quy")
    s.set_defaults(fn=cmd_find)

    a = p.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
