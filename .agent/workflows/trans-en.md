---
description: Translate subtitles from workspace/cleaned/ into English in workspace/trans/
---
1. Use skill `translate-subtitle` (read `.agent/skills/translate-subtitle/SKILL.md` and follow it exactly).
2. Target language: en. Do not ask again.
3. If the user names a file after the command, translate only that file; otherwise pick the next file in `workspace/cleaned/` without a `.en.srt` in `workspace/trans/` (the skill's session budget applies: usually one file per session).
