---
description: Translate subtitles from workspace/cleaned/ into Vietnamese in workspace/trans/
---
1. Use skill `translate-subtitle` (read `.agent/skills/translate-subtitle/SKILL.md` and follow it exactly).
2. Target language: vi. Do not ask again.
3. If the user names a file after the command, translate only that file; otherwise translate every file in `workspace/cleaned/` without a `.vi.srt` in `workspace/trans/`.
