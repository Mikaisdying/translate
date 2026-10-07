#!/usr/bin/env python3
"""
srt_tools.py - Công cụ phụ trợ cho pipeline phụ đề raw -> cleaned -> trans.
Chỉ dùng thư viện chuẩn của Python (3.8+). Chạy từ thư mục gốc dự án.

Dữ liệu nằm trong workspace/ (không đưa lên git), tự tạo khi chạy nếu chưa có:
  workspace/raw/  workspace/cleaned/  workspace/trans/  workspace/work/ (file tạm)
  workspace/glossary.md (chép từ .agent/skills/build-glossary/assets/glossary.template.md nếu chưa có)

Lệnh:
  info     FILE                         Thống kê số block, thời lượng, lỗi định dạng
  text     FILE [--from N] [--to M]     In gọn "ID | text" (đọc nhanh, ít token)
  split    FILE [--size 100] [--out DIR] Chia file dài thành nhiều file SRT (không cần cho clean/dịch)
  merge    SRC TEXT OUT [--cleanup]     Ghép chữ dạng "ID | chữ" (nhiều dòng nối bằng " / ") vào ID, timestamp của SRC;
                                        TEXT là một file hoặc thư mục part_*.txt (--cleanup: xóa thư mục sau khi ghép);
                                        dòng "ID | =" nghĩa là giữ nguyên chữ của block đó trong SRC
  diff     SRC DST [--limit 50] [--loose]         Liệt kê các block có nội dung thay đổi
  validate SRC DST [--target vi|en]     Kiểm tra cấu trúc DST so với SRC
  pair     SRC DST [--from N] [--to M] [--ids 57,63,120-125]
                                        In song song "ID | gốc | dịch" để đối chiếu (dừng nếu lệch số block)
  check-glossary SRC DST --target vi|en [--glossary workspace/glossary.md] [--from N] [--to M]
                                        Báo block có thuật ngữ `x` trong glossary mà bản dịch không dùng
  lint     SRC DST [--from N] [--to M] [--cps 20]
                                        Báo chỗ nghi lỗi máy phát hiện được: số, tổ hợp phím, chuột trái/phải,
                                        chữ Latin trong gốc (tên phần mềm, menu) bị mất, đọc quá nhanh
  review-prep SRC DST --target vi|en [--from N] [--to M] [--cps 20] [--size 100]
                                        validate + check-glossary + lint trong một lần, kèm các lệnh pair cần đọc
  check-asr FILE [FILE ...] [--glossary workspace/glossary.md]
                                        Báo chỗ còn sót lỗi ASR `x` (mục 5 glossary) trong file đã clean
  find     PATTERN FILE [FILE ...] [--regex]
                                        Tìm chuỗi trong phần chữ của nhiều file SRT (không phân biệt hoa thường)
  archive  PATH [PATH ...] [--copy]     Cất file/thư mục vào workspace/work/<tên>/backup/ kèm thời gian
  parts    SRC DIR [--size 100]         part_*.txt nào trong DIR đã xong/dở/chưa làm, và lệnh đọc phần tiếp theo
  status                                Bảng tiến độ: bài nào đã clean, dịch, validate, review

validate trả về mã thoát 1 nếu có LỖI (sai số block, ID, timestamp, block rỗng).
CẢNH BÁO (sót chữ gốc, ký hiệu Markdown...) không làm hỏng lệnh nhưng cần xem lại.
check-glossary, check-asr và lint chỉ cảnh báo, mã thoát 0 trừ khi không đọc được file
hoặc hai file lệch số block.
"""
import argparse
import glob
import os
import re
import shutil
import sys
import time
import unicodedata
from pathlib import Path

WS = Path("workspace")
RAW, CLEANED, TRANS, WORK = WS / "raw", WS / "cleaned", WS / "trans", WS / "work"
GLOSSARY, GLOSSARY_TEMPLATE = WS / "glossary.md", Path(".agent/skills/build-glossary/assets/glossary.template.md")

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

TIMING_RE = re.compile(
    r"^\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")
VI_ONLY_RE = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]")
MARKDOWN_RE = re.compile(r"(```|\*\*|^#{1,6}\s|^>\s|translated by|bản dịch bởi)", re.I | re.M)
_MOD = r"(?:ctrl|control|shift|alt|cmd|command|option|win)"
_KEY = _MOD[:-1] + r"|tab|enter|esc|space|f\d{1,2}|[a-z0-9])(?![\w])"
# "Ctrl cộng R", "Shift và A", "Ctrl加R"; không bắt "giữ Shift và nhấp đúp"
BAD_SHORTCUT_RE = re.compile(
    rf"(?<![a-z]){_MOD}\s*(?:(?:cộng|plus|và)\s+(?={_KEY})|加)",
    re.I,
)
# Chữ Latin (kể cả có dấu tiếng Việt): thuật ngữ bắt đầu/kết thúc bằng các chữ này
# phải khớp trọn từ, để "art" không khớp "start". Chữ Hán không có ranh giới từ.
LATIN = r"A-Za-z0-9À-ɏḀ-ỿ"
LATIN_RE = re.compile(f"[{LATIN}]")


class Block:
    __slots__ = ("idx", "timing", "text", "pos")

    def __init__(self, idx, timing, text, pos):
        self.idx = idx        # chuỗi ID như trong file
        self.timing = timing  # dòng timestamp nguyên văn
        self.text = text      # danh sách dòng chữ
        self.pos = pos        # thứ tự block (bắt đầu từ 1)


def read_srt(path):
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        sys.exit(f"[LỖI] Không đọc được {path}: {e.strerror or e}")
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


def expand_files(patterns):
    """Mở rộng *.srt (PowerShell/cmd không tự làm). Báo nếu mẫu không khớp file nào."""
    files = []
    for f in patterns:
        if any(c in f for c in "*?["):
            found = sorted(glob.glob(f))
            if not found:
                print(f"[CẢNH BÁO] Không có file nào khớp {f!r}", file=sys.stderr)
            files.extend(found)
        else:
            files.append(f)
    return files


def term_regex(options):
    """Regex khớp một trong các cách viết, không phân biệt hoa thường.
    Đầu/cuối là chữ Latin thì đòi ranh giới từ; chữ Hán thì khớp chuỗi con."""
    parts = []
    for o in sorted(options, key=len, reverse=True):
        p = re.escape(o)
        if LATIN_RE.match(o[0]):
            p = f"(?<![{LATIN}])" + p
        if LATIN_RE.match(o[-1]):
            p = p + f"(?![{LATIN}])"
        parts.append(p)
    return re.compile("|".join(parts), re.I)


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
    out = Path(a.out) if a.out else WORK / Path(a.file).stem
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


LOOSE_STRIP_RE = re.compile(r"[\s\W_]+")


def loose_key(lines):
    """Chữ của block sau khi bỏ dấu câu, khoảng trắng, xuống dòng, hoa thường."""
    return LOOSE_STRIP_RE.sub("", "".join(lines)).lower()


KEEP_MARK = "="  # dòng "ID | =" trong file chữ: giữ nguyên block đó
TEXT_LINE_RE = re.compile(r"^\s*(\d+)\s*\|\s?(.*)$")


def parse_text_file(path):
    """Đọc file "ID | chữ". Trả về (dict ID -> chữ, danh sách lỗi)."""
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return {}, [f"{Path(path).name}: không đọc được ({e})"]
    texts, problems = {}, []
    for n, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        m = TEXT_LINE_RE.match(line)
        if not m:
            problems.append(f"{Path(path).name} dòng {n}: không đúng dạng 'ID | chữ': {line[:60]!r}")
            continue
        idx, text = m.group(1), m.group(2).strip()
        if idx in texts:
            problems.append(f"{Path(path).name}: ID {idx} xuất hiện nhiều lần")
        if not text:
            problems.append(f"{Path(path).name}: ID {idx} chữ rỗng")
        texts[idx] = text
    return texts, problems


def cmd_merge(a):
    """Ghép chữ "ID | chữ" (một file, hoặc mọi part_*.txt trong một thư mục)
    vào cấu trúc (ID, timestamp) của SRC, ghi ra OUT."""
    blocks, errors = read_srt(a.src)
    if errors:
        for e in errors:
            print(f"[LỖI] SRC: {e}")
        return 1
    source = Path(a.textfile)
    files = sorted(source.glob("part_*.txt")) if source.is_dir() else [source]
    if not files:
        print(f"[LỖI] Không thấy part_*.txt trong {source.as_posix()}")
        return 1
    texts, problems = {}, []
    for f in files:
        t, p = parse_text_file(f)
        problems += p
        for idx in set(t) & set(texts):
            problems.append(f"{f.name}: ID {idx} đã có ở phần khác")
        texts.update(t)
    ids = [b.idx for b in blocks]
    missing = [i for i in ids if i not in texts]
    extra = sorted(set(texts) - set(ids), key=int)
    if missing:
        problems.append(f"thiếu {len(missing)} ID: {', '.join(missing[:20])}" + (" ..." if len(missing) > 20 else ""))
    if extra:
        problems.append(f"thừa {len(extra)} ID không có trong SRC: {', '.join(extra[:20])}")
    if problems:
        for p in problems:
            print(f"[LỖI] {p}")
        print("Không ghi file. Sửa file chữ rồi chạy lại.")
        return 1
    kept = 0
    for b in blocks:
        if texts[b.idx] == KEEP_MARK:  # "ID | =": giữ nguyên chữ của SRC
            kept += 1
            continue
        b.text = [t.strip() for t in texts[b.idx].split(" / ")]
    write_srt(a.out, blocks)
    print(f"Đã ghép {len(blocks)} block -> {a.out}" + (f" ({kept} block giữ nguyên)" if kept else ""))
    if a.cleanup and source.is_dir():
        shutil.rmtree(source)
        print(f"Đã dọn {source.as_posix()}/")
    return 0


def cmd_diff(a):
    src, _ = read_srt(a.src)
    dst, _ = read_srt(a.dst)
    if len(src) != len(dst):
        print(f"[CẢNH BÁO] Số block khác nhau: SRC={len(src)} DST={len(dst)}. "
              f"So theo vị trí nên từ chỗ lệch trở đi kết quả không còn đúng; "
              f"chạy validate để xem chi tiết.\n")
    shown = changed = 0
    for s, d in zip(src, dst):
        if (loose_key(s.text) != loose_key(d.text)) if a.loose else (s.text != d.text):
            changed += 1
            if shown < a.limit:
                shown += 1
                print(f"[{s.idx}] - {' / '.join(s.text)}")
                print(f"[{d.idx}] + {' / '.join(d.text)}\n")
    print(f"Thay đổi {changed}/{min(len(src), len(dst))} block"
          + (f" (hiển thị {shown})" if changed > shown else ""))
    return 0


def check_pair(src_path, dst_path, target=None):
    """Trả về (src, dst, lỗi, cảnh báo) của DST so với SRC."""
    src, src_err = read_srt(src_path)
    dst, dst_err = read_srt(dst_path)
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
        if target:
            if CJK_RE.search(dt):
                warns.append(f"ID {d.idx}: còn sót chữ Hán/Nhật/Hàn: {dt[:60]!r}")
            if target == "en" and VI_ONLY_RE.search(dt):
                warns.append(f"ID {d.idx}: có chữ tiếng Việt trong bản tiếng Anh: {dt[:60]!r}")
            if st and st == dt and len(st) > 3:
                untranslated += 1

    if target and untranslated:
        warns.append(f"{untranslated} block giống hệt bản gốc (có thể chưa dịch, "
                     f"hoặc chỉ là tên riêng/tiếng kêu) - kiểm tra bằng lệnh diff")
    return src, dst, errors, warns


def cmd_validate(a):
    src, dst, errors, warns = check_pair(a.src, a.dst, a.target)
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


def parse_ids(spec):
    """"57,63,120-125" -> tập ID dạng chuỗi."""
    ids = set()
    for part in re.split(r"[,\s]+", spec.strip()):
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not m:
            sys.exit(f"[LỖI] --ids sai dạng: {part!r} (VD 57,63,120-125)")
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        ids.update(str(i) for i in range(lo, hi + 1))
    return ids


def cmd_pair(a):
    pair = aligned_blocks(a.src, a.dst)
    if pair is None:
        return 1
    ids = parse_ids(a.ids) if a.ids else None
    for s, d in zip(*pair):
        if ids is not None:
            if s.idx not in ids:
                continue
        elif not in_range(s, a.start, a.end):
            continue
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


def load_approved_rows(path, src_col, dst_col, approved_only=True):
    """Trả về danh sách (ô nguồn, [cách viết nguồn], [cách viết đích]) của các dòng `x`
    (hoặc mọi dòng nếu approved_only=False) trong mọi bảng glossary có đủ cột
    src_col, dst_col và Trạng thái."""
    try:
        content = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        sys.exit(f"[LỖI] Không đọc được {path}: {e}")
    content = re.sub(r"<!--.*?-->", "", content, flags=re.S)
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
        if not {src_col, dst_col, "Trạng thái"} <= set(header):
            continue
        row = dict(zip(header, cells))
        if approved_only and row.get("Trạng thái", "").strip().lower() != "x":
            continue
        src_opts = split_options(row[src_col])
        dst_opts = split_options(row[dst_col])
        if src_opts and dst_opts:
            terms.append((row[src_col], src_opts, dst_opts))
    return terms


def joined(block):
    return " / ".join(t.strip() for t in block.text)


def in_range(block, start, end):
    return (not start or block.pos >= start) and (not end or block.pos <= end)


def glossary_report(src, dst, glossary, target, start=0, end=0):
    """In vi phạm glossary `x` của các block trong khoảng [start, end]."""
    col_target = {"vi": "Tiếng Việt", "en": "English"}[target]
    terms = load_approved_rows(glossary, "Gốc", col_target)
    if not terms:
        print(f"Không có dòng `x` nào có cả ô Gốc và ô {col_target} "
              f"trong {glossary}, không có gì để kiểm tra.")
        return
    rules = [(cell, term_regex(src_opts), dst_opts, term_regex(dst_opts))
             for cell, src_opts, dst_opts in terms]
    counts, checked = {}, 0
    for s, d in zip(src, dst):
        if not in_range(s, start, end):
            continue
        checked += 1
        st, dt = joined(s), joined(d)
        for cell, src_re, dst_opts, dst_re in rules:
            hit = src_re.search(st)
            if hit is None or dst_re.search(dt):
                continue
            counts[cell] = counts.get(cell, 0) + 1
            print(f"ID {s.idx}: '{hit.group(0)}' nên dịch là '{' / '.join(dst_opts)}' "
                  f"| gốc: {st} | dịch: {dt}")
    total = sum(counts.values())
    print(f"\nĐã kiểm tra {len(terms)} thuật ngữ `x` trên {checked} block: {total} vi phạm")
    for cell, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cell}: {n}")


def cmd_check_glossary(a):
    pair = aligned_blocks(a.src, a.dst)
    if pair is None:
        return 1
    glossary_report(*pair, a.glossary, a.target, a.start, a.end)
    return 0


# ---- lint: lỗi máy phát hiện được (số, phím, chuột, thuật ngữ Latin, tốc độ đọc) ----

NUM_RE = re.compile(r"\d+")
KEY_NAME = (r"(?:ctrl|control|shift|alt|cmd|command|option|win|tab|enter|return|esc|space|"
            r"delete|del|backspace|home|end|f\d{1,2}|[a-z0-9])")
COMBO_RE = re.compile(rf"(?<![a-z])(?:{_MOD}\s*(?:\+|＋|加|plus|cộng)\s*)+{KEY_NAME}(?![a-z])", re.I)
COMBO_SEP_RE = re.compile(r"\s*(?:\+|＋|加|plus|cộng)\s*", re.I)
# Tên phím viết bằng chữ Hán -> cách viết chấp nhận trong bản dịch
CJK_KEYS = [
    (re.compile(r"空格键"), re.compile(r"space|phím cách|dấu cách", re.I), "Space"),
    (re.compile(r"回车"), re.compile(r"enter|return", re.I), "Enter"),
    (re.compile(r"退格键"), re.compile(r"backspace", re.I), "Backspace"),
    (re.compile(r"删除键"), re.compile(r"delete|del\b", re.I), "Delete"),
]
MOUSE = [
    (re.compile(r"左键|左击|鼠标左|left[- ]?click|left mouse", re.I),
     re.compile(r"trái|left", re.I), "chuột trái"),
    (re.compile(r"右键|右击|鼠标右|right[- ]?click|right mouse", re.I),
     re.compile(r"phải|right", re.I), "chuột phải"),
    (re.compile(r"中键|middle[- ]?(?:click|mouse)", re.I),
     re.compile(r"giữa|cuộn|middle|wheel|scroll", re.I), "chuột giữa"),
]
LATIN_TERM_RE = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]" + rf"[{LATIN}+#]*(?:[.\-][{LATIN}+#]+)*")
LATIN_SKIP = {"ok"}


def norm_text(s):
    return unicodedata.normalize("NFKC", s)


def numbers(s):
    """Các cụm chữ số trong chuỗi, tách riêng từng cụm để 1.5 = 1,5 và 0,0,0 = 0, 0, 0."""
    return set(NUM_RE.findall(norm_text(s)))


def combos(s):
    return {COMBO_SEP_RE.sub("+", c).lower() for c in COMBO_RE.findall(norm_text(s))}


def has_word(word, text):
    return re.search(rf"(?<![{LATIN}]){re.escape(word)}(?![{LATIN}])", text, re.I) is not None


def timing_seconds(timing):
    m = TIMING_RE.match(timing)
    if not m:
        return None

    def sec(t):
        h, mi, s = t.replace(",", ".").split(":")
        return int(h) * 3600 + int(mi) * 60 + float(s)
    return sec(m.group(2)) - sec(m.group(1))


def glossary_source_terms(path):
    """Mọi cách viết ở cột Gốc của glossary (cả `x` lẫn `?`), viết thường."""
    if not Path(path).exists():
        return set()
    rows = load_approved_rows(path, "Gốc", "Gốc", approved_only=False)
    return {o.lower() for _, opts, _ in rows for o in opts}


def lint_issues(src, dst, start=0, end=0, cps=20.0, glossary=None):
    """Trả về danh sách (block gốc, block dịch, loại, mô tả). Chữ cần có trong bản dịch
    được tìm ở cả block liền trước và liền sau, vì câu dịch hay bị dồn sang block bên cạnh."""
    skip_terms = glossary_source_terms(glossary) if glossary else set()
    issues = []
    for i, (s, d) in enumerate(zip(src, dst)):
        if not in_range(s, start, end):
            continue
        st = joined(s)
        near = " / ".join(joined(x) for x in dst[max(i - 1, 0):i + 2])
        near_norm = norm_text(near)

        missing = sorted(numbers(st) - numbers(near), key=lambda n: (len(n), n))
        if missing:
            issues.append((s, d, "Số", f"gốc có {', '.join(missing)}, bản dịch không có"))

        near_combos = combos(near)
        for c in sorted(combos(st)):
            if c not in near_combos:
                issues.append((s, d, "Phím", f"gốc có {c}, bản dịch không có tổ hợp này"))
        for src_re, dst_re, name in CJK_KEYS:
            if src_re.search(st) and not dst_re.search(near):
                issues.append((s, d, "Phím", f"gốc nói phím {name}, bản dịch không có"))

        for src_re, dst_re, name in MOUSE:
            if src_re.search(st) and not dst_re.search(near):
                issues.append((s, d, "Chuột", f"gốc nói {name}, bản dịch không có"))

        # Chữ Latin xen trong gốc chủ yếu là Hán/Nhật/Hàn thường là tên phần mềm, menu, định dạng
        words = LATIN_TERM_RE.findall(COMBO_RE.sub(" ", norm_text(st)))  # tổ hợp phím đã xét ở trên
        if len(CJK_RE.findall(st)) >= len(words):
            lost = []
            for w in words:
                if (len(w) >= 2 and w.isascii() and w.lower() not in LATIN_SKIP and w.lower() not in skip_terms
                        and not has_word(w, near_norm) and w not in lost):
                    lost.append(w)
            if lost:
                issues.append((s, d, "Thuật ngữ Latin", f"gốc có {', '.join(lost)}, bản dịch không giữ"))

        dur = timing_seconds(s.timing)
        if cps and dur and dur > 0:
            rate = len(" ".join(t.strip() for t in d.text)) / dur
            if rate > cps:
                issues.append((s, d, "Đọc nhanh", f"{rate:.0f} ký tự/giây trong {dur:.1f} giây"))
    return issues


def lint_report(src, dst, start=0, end=0, cps=20.0, glossary=None):
    issues = lint_issues(src, dst, start, end, cps, glossary)
    counts = {}
    for s, d, kind, msg in issues:
        counts[kind] = counts.get(kind, 0) + 1
        print(f"ID {s.idx} | {kind} | {msg} | gốc: {joined(s)} | dịch: {joined(d)}")
    print(f"\nLint: {len(issues)} chỗ cần xem"
          + (" (" + ", ".join(f"{k} {n}" for k, n in counts.items()) + ")" if counts else ""))
    if issues:
        print("Máy chỉ so khớp chữ: mỗi dòng là chỗ nghi ngờ, cần đọc ngữ cảnh mới kết luận là lỗi.")


def cmd_lint(a):
    pair = aligned_blocks(a.src, a.dst)
    if pair is None:
        return 1
    lint_report(*pair, a.start, a.end, a.cps, a.glossary)
    return 0


def cmd_review_prep(a):
    """validate + check-glossary + lint trong một lần gọi, rồi in các lệnh pair cần đọc."""
    print("## Validate")
    if cmd_validate(a) and len(read_srt(a.src)[0]) != len(read_srt(a.dst)[0]):
        print("\nLệch số block: không đối chiếu được, dừng.")
        return 1
    src, dst = read_srt(a.src)[0], read_srt(a.dst)[0]
    print("\n## Glossary")
    if Path(a.glossary).exists():
        glossary_report(src, dst, a.glossary, a.target, a.start, a.end)
    else:
        print(f"Không có {a.glossary}, bỏ qua.")
    print("\n## Lint")
    lint_report(src, dst, a.start, a.end, a.cps, a.glossary)
    first, last = a.start or 1, min(a.end or len(src), len(src))
    print("\n## Đọc đối chiếu")
    for n in range(first, last + 1, a.size):
        print(f"python tools/srt_tools.py pair {Path(a.src).as_posix()} {Path(a.dst).as_posix()} "
              f"--from {n} --to {min(n + a.size - 1, last)}")
    return 0


def cmd_find(a):
    flags = re.I
    try:
        pat = re.compile(a.pattern if a.regex else re.escape(a.pattern), flags)
    except re.error as e:
        print(f"[LỖI] Regex sai: {e}")
        return 1
    files = expand_files(a.files)
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


def cmd_check_asr(a):
    terms = load_approved_rows(a.glossary, "ASR nghe sai", "Đúng là")
    if not terms:
        print(f"Không có dòng `x` nào ở mục Lỗi ASR trong {a.glossary}, không có gì để kiểm tra.")
        return 0
    rules = [(term_regex(wrong), term_regex(right), right) for _, wrong, right in terms]
    files = expand_files(a.files)
    total = 0
    for f in files:
        blocks, _ = read_srt(f)
        for b in blocks:
            text = " / ".join(t.strip() for t in b.text)
            for wrong_re, right_re, right in rules:
                # Bỏ cách viết đúng trước, để "图" sai không khớp vào "图层" đúng
                hit = wrong_re.search(right_re.sub("\0", text))
                if hit:
                    total += 1
                    print(f"{Path(f).name} | {b.idx} | '{hit.group(0)}' nên là "
                          f"'{' / '.join(right)}' | {text}")
    print(f"\nĐã kiểm tra {len(terms)} lỗi ASR `x` trong {len(files)} file: {total} chỗ còn sót")
    return 0


def work_dir_for(path):
    """Thư mục work/<tên>/ của bài chứa PATH: work/<tên>/..., trans/<tên>.<mã>.srt, cleaned/<tên>.srt."""
    p = Path(path).resolve()
    work = WORK.resolve()
    try:
        rel = p.relative_to(work)
    except ValueError:
        name = p.stem
        if p.parent.name == "trans" and "." in name:
            name = name.rsplit(".", 1)[0]  # ep01.vi -> ep01
        return work / name
    if len(rel.parts) < 2 or rel.parts[1] == "backup":
        sys.exit(f"[LỖI] Không cất được {path}: chỉ cất file/thư mục bên trong {WORK.as_posix()}/<tên>/")
    return work / rel.parts[0]


def cmd_archive(a):
    stamp = time.strftime("%Y%m%d-%H%M")
    for path in a.paths:
        p = Path(path)
        if not p.exists():
            print(f"(bỏ qua, không có) {path}")
            continue
        dest_dir = work_dir_for(p) / "backup"
        dest_dir.mkdir(parents=True, exist_ok=True)
        base = f"{p.stem}.{stamp}{p.suffix}" if p.is_file() else f"{p.name}.{stamp}"
        dest, n = dest_dir / base, 2
        while dest.exists():
            dest = dest_dir / (f"{p.stem}.{stamp}-{n}{p.suffix}" if p.is_file() else f"{p.name}.{stamp}-{n}")
            n += 1
        if a.copy:
            (shutil.copy2 if p.is_file() else shutil.copytree)(str(p), str(dest))
        else:
            shutil.move(str(p), str(dest))
        print(f"{'Đã chép' if a.copy else 'Đã cất'} {path} -> "
              f"{Path(os.path.relpath(dest)).as_posix()}")
    return 0


def cmd_parts(a):
    blocks, errors = read_srt(a.src)
    if errors:
        for e in errors:
            print(f"[LỖI] SRC: {e}")
        return 1
    d, size = Path(a.dir), a.size
    total = (len(blocks) + size - 1) // size
    todo = []
    for n in range(1, total + 1):
        rng = blocks[(n - 1) * size:n * size]
        f = d / f"part_{n:03d}.txt"
        want = [b.idx for b in rng]
        if not f.exists():
            state = "chưa làm"
        else:
            texts, problems = parse_text_file(f)
            missing = [i for i in want if i not in texts]
            extra = sorted(set(texts) - set(want), key=int)
            if missing:
                problems.append(f"thiếu {len(missing)} ID, từ {missing[0]}")
            if extra:
                problems.append(f"thừa ID {', '.join(extra[:5])}")
            if problems:
                more = f", +{len(problems) - 1}" if len(problems) > 1 else ""
                state = f"LỖI ({problems[0]}{more})"
            else:
                state = "xong"
        if state != "xong":
            todo.append((f, rng))
        print(f"{f.name}  block {rng[0].pos}-{rng[-1].pos}  {state}")
    extra_files = sorted(p for p in d.glob("part_*.txt") if p.name > f"part_{total:03d}.txt")
    for p in extra_files:
        print(f"{p.name}  THỪA (ngoài số phần của SRC, có thể sót từ lần trước)")
    print(f"\n{total - len(todo)}/{total} phần xong.", end=" ")
    if extra_files:
        print("Có phần thừa: cất bằng archive rồi làm lại.")
    elif todo:
        f, rng = todo[0]
        print(f"Làm tiếp {f.name}: python tools/srt_tools.py text {Path(a.src).as_posix()} "
              f"--from {rng[0].pos} --to {rng[-1].pos}")
    else:
        print(f"Ghép: python tools/srt_tools.py merge {Path(a.src).as_posix()} {d.as_posix()} <file đích>")
    return 0 if not todo and not extra_files else 1


LANG_RE = re.compile(r"^(?P<name>.+)\.(?P<code>[a-z]{2,3}(?:-[A-Za-z0-9]+)?)$")


def cmd_status(a):
    raw = {p.stem for p in RAW.glob("*.srt")}
    cleaned = {p.stem for p in CLEANED.glob("*.srt")}
    trans = {}
    for p in TRANS.glob("*.srt"):
        m = LANG_RE.match(p.stem)
        if m:
            trans.setdefault(m["name"], set()).add(m["code"])
    langs = {p.stem[len("target-"):] for p in
             Path(".agent/skills/translate-subtitle/references").glob("target-*.md")}
    langs = sorted(langs.union(*trans.values()) if trans else langs)
    names = sorted(raw | cleaned | set(trans))
    if not names:
        print(f"Chưa có file .srt nào. Bỏ file của FunASR vào {RAW.as_posix()}/")
        return 0

    def verdict(src, dst, target=None):
        try:
            _, _, errors, _ = check_pair(src, dst, target)
        except SystemExit:
            return "lỗi đọc"
        return "FAIL" if errors else "PASS"

    rows = [["Tên", "raw", "cleaned"] + langs]
    for n in names:
        row = [n, "có" if n in raw else "—"]
        c = CLEANED / f"{n}.srt"
        if n not in cleaned:
            row.append("—")
        else:
            row.append(verdict(RAW / f"{n}.srt", c) if n in raw else "có")
        for code in langs:
            t = TRANS / f"{n}.{code}.srt"
            if not t.exists():
                row.append("—")
                continue
            if n not in cleaned:
                row.append("không có gốc")
                continue
            cell = verdict(c, t, code)
            if c.stat().st_mtime > t.stat().st_mtime:
                cell += " · gốc sửa sau"
            r = WORK / n / f"review.{code}.md"
            if r.exists():
                body = r.read_text(encoding="utf-8", errors="replace")
                pending = len(re.findall(r"^(?:###.*\|\s*|- (?:Status|Trạng thái):\s*)(?:pending|unsure|chờ duyệt|cần xác nhận)\s*$",
                                         body, re.M | re.I))
                cell += f" · review: {pending} chờ" if pending else " · review xong"
                if t.stat().st_mtime > r.stat().st_mtime:
                    cell += " (cũ)"
            row.append(cell)
        rows.append(row)

    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for i, r in enumerate(rows):
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())
        if i == 0:
            print("  ".join("-" * w for w in widths))
    print("\nPASS/FAIL: kết quả validate so với bước trước. "
          "\"gốc sửa sau\": cleaned/ đổi sau khi dịch, nên xem lại bản dịch.\n"
          "\"review: N chờ\": số mục chưa xử lý trong workspace/work/<tên>/review.<mã>.md; "
          "\"(cũ)\": bản dịch đổi sau lần cập nhật file review cuối.")
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
    s.add_argument("--out", help="mặc định workspace/work/<tên file>/")
    s.set_defaults(fn=cmd_split)

    s = sub.add_parser("merge"); s.add_argument("src"); s.add_argument("textfile"); s.add_argument("out")
    s.add_argument("--cleanup", action="store_true", help="ghép xong thì xóa thư mục part_*.txt")
    s.set_defaults(fn=cmd_merge)

    s = sub.add_parser("diff"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--loose", action="store_true",
                   help="bỏ qua khác biệt dấu câu, khoảng trắng, xuống dòng, hoa thường")
    s.set_defaults(fn=cmd_diff)

    s = sub.add_parser("validate"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--target", choices=["vi", "en"], help="bật kiểm tra bản dịch")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("pair"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--from", dest="start", type=int, default=0, help="block thứ N (từ 1)")
    s.add_argument("--to", dest="end", type=int, default=0, help="đến block thứ M")
    s.add_argument("--ids", help="chỉ in các ID này, VD 57,63,120-125 (bỏ qua --from/--to)")
    s.set_defaults(fn=cmd_pair)

    s = sub.add_parser("check-glossary"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--target", choices=["vi", "en"], required=True, help="ngôn ngữ của DST")
    s.add_argument("--glossary", default=str(GLOSSARY))
    s.add_argument("--from", dest="start", type=int, default=0, help="block thứ N (từ 1)")
    s.add_argument("--to", dest="end", type=int, default=0, help="đến block thứ M")
    s.set_defaults(fn=cmd_check_glossary)

    for name, fn in (("lint", cmd_lint), ("review-prep", cmd_review_prep)):
        s = sub.add_parser(name); s.add_argument("src"); s.add_argument("dst")
        s.add_argument("--target", choices=["vi", "en"], required=name == "review-prep", help="ngôn ngữ của DST")
        s.add_argument("--glossary", default=str(GLOSSARY))
        s.add_argument("--from", dest="start", type=int, default=0, help="block thứ N (từ 1)")
        s.add_argument("--to", dest="end", type=int, default=0, help="đến block thứ M")
        s.add_argument("--cps", type=float, default=20.0,
                       help="ngưỡng tốc độ đọc, ký tự/giây (mặc định 20, 0 = tắt)")
        if name == "review-prep":
            s.add_argument("--size", type=int, default=100, help="số block mỗi lệnh pair gợi ý")
        s.set_defaults(fn=fn)

    s = sub.add_parser("find"); s.add_argument("pattern"); s.add_argument("files", nargs="+")
    s.add_argument("--regex", action="store_true", help="coi PATTERN là biểu thức chính quy")
    s.set_defaults(fn=cmd_find)

    s = sub.add_parser("check-asr"); s.add_argument("files", nargs="+")
    s.add_argument("--glossary", default=str(GLOSSARY))
    s.set_defaults(fn=cmd_check_asr)

    s = sub.add_parser("archive"); s.add_argument("paths", nargs="+")
    s.add_argument("--copy", action="store_true", help="chép thay vì chuyển (giữ bản gốc tại chỗ)")
    s.set_defaults(fn=cmd_archive)

    s = sub.add_parser("parts"); s.add_argument("src"); s.add_argument("dir")
    s.add_argument("--size", type=int, default=100, help="số block mỗi phần (mặc định 100)")
    s.set_defaults(fn=cmd_parts)

    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)

    a = p.parse_args()
    if Path(__file__).resolve().parent == (Path.cwd() / "tools").resolve():
        for d in (RAW, CLEANED, TRANS):  # chạy từ gốc dự án: tạo sẵn chỗ để bỏ file vào
            d.mkdir(parents=True, exist_ok=True)
        if not GLOSSARY.exists() and GLOSSARY_TEMPLATE.exists():
            shutil.copyfile(GLOSSARY_TEMPLATE, GLOSSARY)
            print(f"(Đã tạo {GLOSSARY.as_posix()} từ {GLOSSARY_TEMPLATE.as_posix()})", file=sys.stderr)
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
