---
name: build-glossary
description: Use when creating, drafting, updating, or expanding workspace/glossary.md with characters, forms of address, terms, or recurring ASR errors before translation, or when user asks "lập danh sách tên nhân vật", "làm glossary", "chuẩn bị trước khi dịch", or types /glossary.
---

# Build Glossary

Goal: a draft `workspace/glossary.md` the user can approve quickly, so every later translation (by any model) uses the same names and address forms. You only propose; the user decides. Talk to the user in Vietnamese; glossary content stays in Vietnamese like the template.

Best run after clean, before translate; re-run when episodes are added.

## Sources

- Commands: run from the project root; a short name like `text`, `pair`, `diff` means `python tools/srt_tools.py text ...` (`python3` if needed); put paths in double quotes (file names contain spaces). Commands that the tool prints are already complete: run them as is.
- `workspace/cleaned/*.srt`, or only the files the user names. No cleaned files yet: use `workspace/raw/` and warn that names may be misspelled.
- What to collect and how to read is in `references/extract.md`.

## Reading

- Several files, or long ones: one subagent per file (or a few short files), in parallel, each with only:

  ```
  Read and follow .agent/skills/build-glossary/references/extract.md
  Files: workspace/cleaned/001.srt, workspace/cleaned/002.srt
  Result file: workspace/work/glossary/001-002.md
  ```

- One or two short files, or no subagent tool: follow `references/extract.md` yourself.

**Merge**: sum counts, unify spellings of the same name, drop rare candidates. Address (section 3) needs the whole story: where subagents noted changing relationships, reread those passages with `text --from N --to M`.

## Writing workspace/glossary.md

- Missing → copy `assets/glossary.template.md` (any `srt_tools.py` command also creates it).
- Keep its structure, headings and tables. Every added row has status `?`.
- Never edit or delete `x` rows; mention suspicious ones in the report. Update existing `?` rows only with clear new evidence.
- No duplicates (check alternate spellings). Clean and translate are done by LLMs: a row earns its place only if an LLM would likely get it wrong or inconsistent without it (criteria in `references/extract.md`). Every row costs tokens in every later session.
- Fill both Tiếng Việt and English columns; unsure → leave empty with a note.
- Cells hold exactly one chosen form (two only if usage differs, with the condition in `Ghi chú`), no pinyin. `Ghi chú`: a few words that change how to translate, or empty; no definitions.

## Report

Brief, in chat: files scanned (and subagent count), rows added per section, key decisions with a recommendation (usually name conventions and address between main characters). Remind the user to change `?` to `x` on accepted rows; `x` rows are mandatory for clean and translate.
