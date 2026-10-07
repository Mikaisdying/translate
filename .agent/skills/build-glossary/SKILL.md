---
name: build-glossary
description: Scan subtitle files in workspace/cleaned/ (and workspace/raw/) to draft workspace/glossary.md with characters, forms of address, terms and recurring ASR errors, marked `?` for the user to approve. Use when the user wants to create, fill, update or extend the glossary / term list for the subtitle project, or types /glossary, even if they only say "lập danh sách tên nhân vật", "làm glossary" or "chuẩn bị trước khi dịch".
---

# Build Glossary

Goal: a draft `workspace/glossary.md` the user can approve quickly before translating. You only propose; the user decides. A good glossary makes every later translation (by any model) use the same names and address forms.

Talk to the user in Vietnamese. Glossary content (notes, headings) stays in Vietnamese like the template.

## When

Ideally after clean, before translate. Re-run when new episodes are added.

## Sources

- Main: `workspace/cleaned/*.srt` (correct text). If the user names files, scan only those.
- Secondary: `python tools/srt_tools.py diff workspace/raw/<file>.srt workspace/cleaned/<file>.srt --limit 500` to find recurring ASR errors (section 5).
- No `workspace/cleaned/` yet: scan `workspace/raw/`, and tell the user names may still be misspelled.
- Read text with `python tools/srt_tools.py text <file>` (cheaper than raw SRT). Long files: read in chunks with `--from` / `--to`.

## Subagents

Many files (course, series) would overflow one context. Delegate reading to subagents (Agent/Task in Claude Code, `runSubagent` in VS Code Copilot), one file or a few short files each, in parallel:

```
Read and follow .agent/skills/build-glossary/references/extract.md
Files: workspace/cleaned/ep01.srt, workspace/cleaned/ep02.srt
Result file: workspace/work/glossary/ep01-ep02.md
```

Subagents only read and write candidates (with counts and example IDs) to their result file; only you write `workspace/glossary.md`. Merge results: sum counts, unify spellings of the same name, pick proposals, drop rare candidates, then write per "Writing workspace/glossary.md". Address forms (section 3) need the whole story: when merging, re-read a few passages with `text` in episodes where subagents noted changing relationships.

Only one or two short files, or no subagent tool: read per `references/extract.md` yourself and merge the same way.

## What to collect

1. **General info** (section 1): source language, genre, setting, desired tone. Fill only empty fields.
2. **Characters** (section 2): every person name appearing 2+ times, with nicknames and other ways of referring to the same person. Note role, gender, relative age if inferable, since these decide address forms.
3. **Address** (section 3): character pairs who talk a lot. From the relationship (family, teacher-student, boss-subordinate, friends, lovers, enemies) and how they address each other in the source, propose Vietnamese address forms. Note relationship changes (with IDs).
4. **Terms** (section 4): places, organizations, titles, sects, techniques, items, domain terms, frequently repeated words and phrases. For software/tutorial videos: software names, tools, menus, panels, shortcuts, with the standard spelling (English UI names, menu paths with " > ", shortcuts like "Ctrl + Shift + S").
5. **ASR errors** (section 5): words ASR consistently mishears the same way, from the diff.

Propose both Tiếng Việt and English columns. If unsure of a translation, leave it empty and add a note.

## Writing workspace/glossary.md

- Keep the file's structure, headings and tables.
- Every row you add has status `?`.
- Never edit or delete `x` rows. If one looks wrong, mention it in the report.
- Existing `?` rows: update only with clear new evidence.
- No duplicates: check alternate spellings of the same name.
- Quality over quantity: skip unimportant one-off names and common words anyone translates correctly.
- If `workspace/glossary.md` does not exist, copy `assets/glossary.template.md` of this skill (any `srt_tools.py` command run from the project root also does this).

## Report

Brief, in chat:

- Files scanned (and number of subagents, if any).
- Rows added per section.
- Key decisions for the user (usually name conventions and address between main characters), with a recommendation.
- Remind the user: after reviewing, change `?` to `x` on accepted rows; `x` rows are mandatory for clean and translate.
