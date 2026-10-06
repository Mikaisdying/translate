"""Test cho tools/srt_tools.py. Chạy từ thư mục gốc: python -m unittest discover tests"""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "tools" / "srt_tools.py"


def srt(*texts, start=1):
    """Tạo nội dung SRT, mỗi block dài 1 giây."""
    out = []
    for i, t in enumerate(texts):
        s = start + i
        out.append(f"{s}\n00:00:{s:02d},000 --> 00:00:{s + 1:02d},000\n{t}")
    return "\n\n".join(out) + "\n"


GLOSSARY = """# Glossary

## 4. Thuật ngữ

| Gốc | Tiếng Việt | English | Ghi chú | Trạng thái |
|-----|------------|---------|---------|------------|
| art | nghệ thuật | art | | ✅ |
| 图层 | Layer | Layer | | ✅ |
| mask | mặt nạ | mask | | ❓ |

## 6. Lỗi ASR hay gặp

| ASR nghe sai | Đúng là | Ghi chú | Trạng thái |
|--------------|---------|---------|------------|
| photo shop | Photoshop | | ✅ |
| 图 | 图层 | | ✅ |
| PR | Premiere | | ❓ |
"""


class ToolTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        for d in ("raw", "cleaned", "trans"):
            (self.dir / "workspace" / d).mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, content):
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def run_tool(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(TOOL), *args], cwd=self.dir,
                           capture_output=True, text=True, encoding="utf-8", env=env)
        return r.returncode, r.stdout + r.stderr

    # ---- validate ----

    def test_validate_pass(self):
        self.write("workspace/cleaned/a.srt", srt("你好", "再见"))
        self.write("workspace/trans/a.vi.srt", srt("Xin chào", "Tạm biệt"))
        code, out = self.run_tool("validate", "workspace/cleaned/a.srt", "workspace/trans/a.vi.srt", "--target", "vi")
        self.assertEqual(code, 0, out)
        self.assertIn("PASS", out)

    def test_validate_fail_on_block_count_and_timing(self):
        self.write("workspace/cleaned/a.srt", srt("你好", "再见"))
        self.write("workspace/trans/a.vi.srt", srt("Xin chào"))
        code, out = self.run_tool("validate", "workspace/cleaned/a.srt", "workspace/trans/a.vi.srt")
        self.assertEqual(code, 1)
        self.assertIn("Số block khác nhau", out)

        self.write("workspace/trans/a.vi.srt", srt("Xin chào", "Tạm biệt").replace("00:00:02,000 -->", "00:00:02,500 -->"))
        code, out = self.run_tool("validate", "workspace/cleaned/a.srt", "workspace/trans/a.vi.srt")
        self.assertEqual(code, 1)
        self.assertIn("timestamp đổi", out)

    def test_validate_shortcut_warning(self):
        self.write("workspace/cleaned/a.srt", srt("按 Ctrl 加 R", "按 Shift 加 A", "按住 Shift 双击"))
        self.write("workspace/trans/a.vi.srt", srt("Bấm Ctrl cộng R", "Bấm Shift và A", "Giữ Shift và nhấp đúp"))
        code, out = self.run_tool("validate", "workspace/cleaned/a.srt", "workspace/trans/a.vi.srt", "--target", "vi")
        self.assertIn("ID 1: phím tắt", out)
        self.assertIn("ID 2: phím tắt", out)
        self.assertNotIn("ID 3: phím tắt", out)

    def test_missing_file_is_friendly_error(self):
        code, out = self.run_tool("info", "workspace/raw/khong-co.srt")
        self.assertNotEqual(code, 0)
        self.assertIn("[LỖI] Không đọc được", out)
        self.assertNotIn("Traceback", out)

    # ---- diff ----

    def test_diff_warns_on_block_count_mismatch(self):
        self.write("workspace/raw/a.srt", srt("a", "b", "c"))
        self.write("workspace/cleaned/a.srt", srt("a", "B"))
        code, out = self.run_tool("diff", "workspace/raw/a.srt", "workspace/cleaned/a.srt")
        self.assertEqual(code, 0)
        self.assertIn("Số block khác nhau", out)

    def test_diff_loose_ignores_punctuation_and_breaks(self):
        self.write("workspace/raw/a.srt", srt("你好 世界", "按 ctrl / 加 g", "第一针"))
        self.write("workspace/cleaned/a.srt", srt("你好，世界。", "按 Ctrl 加 G", "第一帧"))
        code, out = self.run_tool("diff", "workspace/raw/a.srt", "workspace/cleaned/a.srt", "--loose")
        self.assertIn("Thay đổi 1/3", out)
        self.assertIn("第一帧", out)

    # ---- check-glossary ----

    def test_check_glossary_latin_word_boundary(self):
        self.write("workspace/glossary.md", GLOSSARY)
        self.write("workspace/cleaned/a.srt", srt("start now", "the art of it", "点击图层"))
        self.write("workspace/trans/a.vi.srt", srt("bắt đầu", "cái hay của nó", "Bấm vào Layer"))
        code, out = self.run_tool("check-glossary", "workspace/cleaned/a.srt", "workspace/trans/a.vi.srt", "--target", "vi")
        self.assertEqual(code, 0)
        self.assertNotIn("ID 1:", out)   # "art" trong "start" không tính
        self.assertIn("ID 2:", out)      # "art" đứng riêng mà không dịch "nghệ thuật"
        self.assertNotIn("ID 3:", out)   # chữ Hán vẫn khớp chuỗi con, đã dịch đúng
        self.assertIn("1 vi phạm", out)

    def test_check_glossary_ignores_unapproved(self):
        self.write("workspace/glossary.md", GLOSSARY)
        self.write("workspace/cleaned/a.srt", srt("add a mask"))
        self.write("workspace/trans/a.vi.srt", srt("thêm mask"))
        code, out = self.run_tool("check-glossary", "workspace/cleaned/a.srt", "workspace/trans/a.vi.srt", "--target", "vi")
        self.assertIn("0 vi phạm", out)

    # ---- check-asr ----

    def test_check_asr(self):
        self.write("workspace/glossary.md", GLOSSARY)
        self.write("workspace/cleaned/a.srt", srt("mở photo shop lên", "点击图层", "这个图很好", "dùng PR"))
        code, out = self.run_tool("check-asr", "workspace/cleaned/*.srt")
        self.assertEqual(code, 0)
        self.assertIn("a.srt | 1 | 'photo shop'", out)
        self.assertNotIn("| 2 |", out)   # 图 nằm trong 图层 đúng thì bỏ qua
        self.assertIn("a.srt | 3 | '图'", out)
        self.assertNotIn("| 4 |", out)   # dòng ❓ không kiểm tra
        self.assertIn("2 chỗ còn sót", out)

    # ---- find ----

    def test_find_warns_when_glob_matches_nothing(self):
        code, out = self.run_tool("find", "x", "workspace/trans/*.srt")
        self.assertIn("Không có file nào khớp", out)

    # ---- split / merge ----

    def test_split(self):
        self.write("workspace/cleaned/a.srt", srt(*[f"câu {i}" for i in range(1, 8)]))
        code, _ = self.run_tool("split", "workspace/cleaned/a.srt", "--size", "3")
        self.assertEqual(code, 0)
        self.assertEqual(len(list((self.dir / "workspace/work/a").glob("part_*.srt"))), 3)

    # ---- merge ----

    def test_merge(self):
        self.write("workspace/cleaned/a.srt", srt("一", "二", "三"))
        self.write("t.txt", "1 | một\n2 | hai / dòng hai\n\n3 | ba\n")
        code, out = self.run_tool("merge", "workspace/cleaned/a.srt", "t.txt", "out.srt")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.dir / "out.srt").read_text(encoding="utf-8"),
                         srt("một", "hai\ndòng hai", "ba"))

    def test_merge_keep_mark(self):
        self.write("workspace/raw/a.srt", srt("你好 世界", "第一针", "嗯"))
        self.write("t.txt", "1 | =\n2 | 第一帧\n3 | =\n")
        code, out = self.run_tool("merge", "workspace/raw/a.srt", "t.txt", "out.srt")
        self.assertEqual(code, 0, out)
        self.assertIn("2 block giữ nguyên", out)
        self.assertEqual((self.dir / "out.srt").read_text(encoding="utf-8"), srt("你好 世界", "第一帧", "嗯"))

    def test_merge_rejects_missing_extra_empty(self):
        self.write("workspace/cleaned/a.srt", srt("一", "二", "三"))
        self.write("t.txt", "1 | một\n3 |\n9 | thừa\nlinh tinh\n")
        code, out = self.run_tool("merge", "workspace/cleaned/a.srt", "t.txt", "out.srt")
        self.assertEqual(code, 1)
        for s in ("thiếu 1 ID: 2", "thừa 1 ID", "ID 3 chữ rỗng", "không đúng dạng"):
            self.assertIn(s, out)
        self.assertFalse((self.dir / "out.srt").exists())

    def test_merge_from_parts_dir_with_cleanup(self):
        self.write("workspace/cleaned/a.srt", srt(*[f"句{i}" for i in range(1, 6)]))
        self.write("workspace/work/a/vi/part_001.txt", "1 | một\n2 | hai\n3 | ba\n")
        self.write("workspace/work/a/vi/part_002.txt", "4 | bốn\n3 | ba lần nữa\n")
        code, out = self.run_tool("merge", "workspace/cleaned/a.srt", "workspace/work/a/vi", "out.srt", "--cleanup")
        self.assertEqual(code, 1)
        self.assertIn("part_002.txt: ID 3 đã có ở phần khác", out)
        self.assertIn("thiếu 1 ID: 5", out)
        self.assertTrue((self.dir / "workspace/work/a/vi").exists())

        self.write("workspace/work/a/vi/part_002.txt", "4 | bốn\n5 | năm\n")
        code, out = self.run_tool("merge", "workspace/cleaned/a.srt", "workspace/work/a/vi", "out.srt", "--cleanup")
        self.assertEqual(code, 0, out)
        self.assertFalse((self.dir / "workspace/work/a/vi").exists())
        self.assertEqual((self.dir / "out.srt").read_text(encoding="utf-8"),
                         srt("một", "hai", "ba", "bốn", "năm"))

    # ---- parts ----

    def test_parts_detects_done_partial_missing_extra(self):
        self.write("workspace/cleaned/a.srt", srt(*[f"句{i}" for i in range(1, 8)]))
        src, d = "workspace/cleaned/a.srt", "workspace/work/a/vi"
        self.write(f"{d}/part_001.txt", "1 | một\n2 | hai\n3 | ba\n")
        self.write(f"{d}/part_002.txt", "4 | bốn\n")  # ghi dở: thiếu block
        self.write(f"{d}/part_009.txt", "1 | cũ\n")
        code, out = self.run_tool("parts", src, d, "--size", "3")
        self.assertEqual(code, 1)
        self.assertIn("part_001.txt  block 1-3  xong", out)
        self.assertIn("part_002.txt  block 4-6  LỖI (thiếu 2 ID, từ 5)", out)
        self.assertIn("part_003.txt  block 7-7  chưa làm", out)
        self.assertIn("part_009.txt  THỪA", out)

        (self.dir / d / "part_009.txt").unlink()
        code, out = self.run_tool("parts", src, d, "--size", "3")
        self.assertIn("Làm tiếp part_002.txt: python tools/srt_tools.py text workspace/cleaned/a.srt --from 4 --to 6", out)

        self.write(f"{d}/part_002.txt", "4 | bốn\n5 | năm\n6 | sáu\n")
        self.write(f"{d}/part_003.txt", "7 | bảy\n")
        code, out = self.run_tool("parts", src, d, "--size", "3")
        self.assertEqual(code, 0, out)
        self.assertIn("Ghép: python tools/srt_tools.py merge", out)

    # ---- archive ----

    def test_archive_moves_translation_and_parts(self):
        self.write("workspace/trans/ep01.vi.srt", srt("cũ"))
        self.write("workspace/work/ep01/vi/part_001.srt", srt("cũ"))
        code, out = self.run_tool("archive", "workspace/trans/ep01.vi.srt", "workspace/work/ep01/vi", "workspace/raw/khong-co.srt")
        self.assertEqual(code, 0, out)
        self.assertFalse((self.dir / "workspace/trans/ep01.vi.srt").exists())
        self.assertFalse((self.dir / "workspace/work/ep01/vi").exists())
        backup = self.dir / "workspace/work/ep01/backup"
        self.assertEqual(len(list(backup.glob("ep01.vi.*.srt"))), 1)
        dirs = [p for p in backup.glob("vi.*") if p.is_dir()]
        self.assertEqual(len(dirs), 1)
        self.assertTrue((dirs[0] / "part_001.srt").exists())
        self.assertIn("bỏ qua", out)

    def test_archive_copy_twice_same_minute(self):
        self.write("workspace/trans/ep01.vi.srt", srt("x"))
        self.run_tool("archive", "--copy", "workspace/trans/ep01.vi.srt")
        self.run_tool("archive", "--copy", "workspace/trans/ep01.vi.srt")
        self.assertTrue((self.dir / "workspace/trans/ep01.vi.srt").exists())
        self.assertEqual(len(list((self.dir / "workspace/work/ep01/backup").glob("ep01.vi.*.srt"))), 2)

    def test_archive_refuses_backup_dir(self):
        (self.dir / "workspace/work/ep01/backup").mkdir(parents=True)
        code, out = self.run_tool("archive", "workspace/work/ep01/backup")
        self.assertNotEqual(code, 0)

    # ---- status ----

    def test_status(self):
        self.write("workspace/raw/ep01.srt", srt("a"))
        self.write("workspace/raw/ep02.srt", srt("a"))
        self.write("workspace/cleaned/ep01.srt", srt("A"))
        self.write("workspace/trans/ep01.vi.srt", srt("Á"))
        self.write("workspace/trans/ep01.en.srt", srt("A", "thừa"))
        later = time.time() + 10
        os.utime(self.dir / "workspace/cleaned/ep01.srt", (later, later))
        code, out = self.run_tool("status")
        self.assertEqual(code, 0, out)
        lines = {l.split()[0]: l for l in out.splitlines() if l.startswith("ep")}
        self.assertIn("PASS · gốc sửa sau", lines["ep01"])
        self.assertIn("FAIL", lines["ep01"])
        self.assertRegex(lines["ep02"], r"ep02\s+có\s+—")


if __name__ == "__main__":
    unittest.main()
