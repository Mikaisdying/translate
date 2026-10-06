#!/usr/bin/env python3
"""
link_skills.py - Cho công cụ khác dùng chung skill trong .agent/skills/ mà không phải copy.

  python tools/link_skills.py                  # .claude/skills (Claude Code)
  python tools/link_skills.py .github/skills   # VS Code + Copilot
  python tools/link_skills.py .claude/skills .github/skills

Tạo liên kết thư mục trỏ về .agent/skills/: junction trên Windows (không cần quyền admin),
symlink trên macOS/Linux. Sửa skill ở một chỗ là mọi công cụ thấy ngay.
Nếu không tạo được liên kết thì chép sang và báo; khi đó sửa skill xong phải chạy lại.
Các thư mục đích đã nằm trong .gitignore.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

SRC = Path(".agent/skills")


def is_link(p):
    if p.is_symlink():
        return True
    if hasattr(os.path, "isjunction"):  # Python 3.12+
        return os.path.isjunction(p)
    # Python cũ không nhận ra junction; resolve() đi theo junction nên đường dẫn sẽ khác
    return (os.name == "nt" and p.exists()
            and os.path.normcase(p.resolve()) != os.path.normcase(p.absolute()))


def link(dst):
    if is_link(dst):
        if dst.resolve() == SRC.resolve():
            print(f"{dst}: đã liên kết sẵn")
            return 0
        print(f"[LỖI] {dst} đang trỏ tới chỗ khác ({dst.resolve()}). Xóa liên kết đó rồi chạy lại.")
        return 1
    if dst.exists():
        print(f"[LỖI] {dst} đã có và là thư mục thật. Kiểm tra rồi xóa (hoặc đổi tên) trước, "
              f"tránh mất skill riêng đang để ở đó.")
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(SRC.resolve())],
                           check=True, capture_output=True)
        else:
            os.symlink(os.path.relpath(SRC, dst.parent), dst, target_is_directory=True)
        print(f"{dst} -> {SRC}")
        return 0
    except (OSError, subprocess.CalledProcessError) as e:
        shutil.copytree(SRC, dst)
        print(f"[CẢNH BÁO] Không tạo được liên kết ({e}); đã chép {SRC} sang {dst}. "
              f"Sửa skill trong {SRC} xong thì xóa {dst} và chạy lại lệnh này.")
        return 0


def main():
    if not SRC.is_dir():
        sys.exit(f"[LỖI] Không thấy {SRC}. Chạy lệnh từ thư mục gốc dự án.")
    targets = sys.argv[1:] or [".claude/skills"]
    sys.exit(max(link(Path(t)) for t in targets))


if __name__ == "__main__":
    main()
