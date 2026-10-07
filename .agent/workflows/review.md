---
description: Review translations in workspace/trans/ against workspace/cleaned/ and the glossary (report, fix, or cross-check)
---
1. Use skill `review-subtitle` (read `.agent/skills/review-subtitle/SKILL.md` and follow it exactly).
2. Take file name, language, mode and fix choices from what the user wrote after the command: "sửa" or "fix" → fix mode (with scope if given, e.g. "chỉ lỗi nghiêm trọng", "ID 57 60"); "chéo" or "cross" → cross-check mode. Language comes from the file suffix (`.vi.srt`, `.en.srt`) or the user's words.
3. Nothing else written → report mode: run `status`, ask which file to review; a subagent finds errors and writes `workspace/work/<name>/review.<code>.md`, you present from that file and ask what to fix. Do not modify files before the user chooses.
