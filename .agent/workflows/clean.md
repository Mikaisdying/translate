---
description: Clean FunASR subtitles from workspace/raw/ into workspace/cleaned/ (no translation)
---
1. Use skill `clean-funasr` (read `.agent/skills/clean-funasr/SKILL.md` and follow it exactly).
2. If the user names a file after the command, do only that file; otherwise pick the next file in `workspace/raw/` without a counterpart in `workspace/cleaned/` (the skill's session budget applies: usually one file per session).
