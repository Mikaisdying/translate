---
name: review-subtitle
description: Use when checking, reviewing, auditing, finding translation errors, fixing reviewed items, or cross-checking consistency across episodes in subtitle translations, e.g. "review", "soát lỗi", "kiểm tra bản dịch", "rà lại sub", "check bản dịch", "sửa theo review", "review chéo", "dịch xong rồi xem giúp", or typing /review.
---

# Review Subtitle

Two separate parts:

1. **Finding errors**: a subagent (fresh context, free of the translator's interpretation) reads and writes the error list to the episode's review file. It never edits the translation.
2. **Deciding fixes**: the user's. You present, the user chooses, you fix exactly those items.

The review file carries results across sessions, independent of chat. Talk to the user in Vietnamese.

## Modes

From the user's words; unclear → report.

- **Report** (default): find errors, write the review file, present, ask what to fix.
- **Fix** ("sửa", "fix", "sửa theo review"): read and follow `references/fix.md`.
- **Cross-check** ("chéo", "cross", "toàn khóa"): consistency across episodes, see below.

## Files

- Translation `workspace/trans/<name>.<code>.srt`, source `workspace/cleaned/<name>.srt`. Language from the suffix; unknown → ask.
- Review file `workspace/work/<name>/review.<code>.md`, format in `references/find-errors.md`. Each entry heading ends with a status: `pending` / `unsure` (from the reviewer), `fixed`, `skipped` (set in fix mode).
- `python tools/srt_tools.py status` shows per episode `review: done`, `review: progressing (N)` (N items pending/unsure) or nothing (not reviewed), plus `(cũ)` if the translation changed after the review file.
- Commands: run from the project root; a short name like `text`, `pair`, `diff` means `python tools/srt_tools.py text ...` (`python3` if needed); put paths in double quotes (file names contain spaces). Commands that the tool prints are already complete: run them as is.

## Delegating

One subagent per file; several files in parallel, a few at a time. If the user names a model ("review bằng sonnet"), use it; ideally not the model that translated. The task message holds only this, none of your opinions about the translation:

```
Read and follow .agent/skills/review-subtitle/references/find-errors.md
Source: workspace/cleaned/ep03.srt
Translation: workspace/trans/ep03.vi.srt
Language: vi
Scope: all
Result file: workspace/work/ep03/review.vi.md
```

The subagent writes the file and replies with only the path and total line.

**Long files** (> ~400 blocks, count from `info`): split into consecutive ranges of ~300-350 blocks, one subagent per range, run **sequentially**, all writing the same result file. First range `Scope: blocks 1-343`; later ranges add `Append: yes`. If interrupted, the file's `Phạm vi` line shows where to continue.

**Self-review** (no subagent) only when all hold: one file ≤ ~400 blocks; you haven't translated, cleaned or read that episode in this session; the user didn't ask for another model; not cross-check. Then follow `references/find-errors.md` yourself, write the review file, and continue at report step 4 (skip the `pair --ids` check in step 5, still verify source errors).

No subagent tool: do `references/find-errors.md` yourself; if you already touched that episode this session, tell the user once that a new session or another model would be more objective.

## Report mode

Don't modify `workspace/trans/`.

1. **Choose files**:
   - Named → exactly those. None → run `status`, list PASS translations with review state, ask which. FAIL → report the structural error, no subagent.
   - No `workspace/cleaned/<name>.srt` → report and skip. Marked "gốc sửa sau" → review, but remind the user the source changed after translation.
   - `review: progressing`, not `(cũ)` → ask: continue that list (go to step 6) or review from scratch.
2. **Re-review**: first `archive workspace/work/<name>/review.<code>.md`, so old statuses aren't overwritten.
3. **Delegate**, or self-review if eligible.
4. **Check the file**: header plus well-formed entries (heading with ID, severity, type, status; lines Gốc, Hiện tại, Đề xuất, Lý do). Missing or broken → delegate once more, then tell the user. If the subagent returned the content instead of writing it, write it yourself.
   Split files: after the last range, `Phạm vi` is `toàn bộ`, no duplicates at boundaries. Ranges can't see each other: for `Đề xuất glossary` terms translated differently across ranges, `find` each variant in the translation and add a medium entry with the proposed form.
5. **Verify**:
   - One `pair <source> <translation> --ids <all serious IDs>` call: confirm Gốc / Hiện tại match the real file. Mismatch → add `- Đối chiếu: không khớp file thật (...)` to the entry and say so; don't drop it.
   - Each `Lỗi ở bản gốc` item: view context with `text --from N --to M`; check whether the word is actually a correct UI name or term (e.g. Blender's Chinese UI calls X-Ray 透视). Write your verdict (fix / keep, reason) into that entry.
6. **Present** from the review file, keeping each entry's format so the user can choose by ID, plus the file path:
   - Counts by severity (several files → one table, row per file).
   - All serious errors (ID, current → proposed, short reason).
   - Medium and minor: in full if ~20 or fewer, else grouped by type with IDs.
   - Source errors and glossary proposals, if any.
   Several episodes may be presented one at a time.
7. **Ask** what to fix (all, serious only, IDs, confirm/drop `unsure`, their own wording, nothing) and, if glossary proposals are pending, which rows to add (then follow `references/glossary-proposals.md`). Stop and wait.

## Cross-check mode

Don't modify `workspace/trans/`.

1. Episodes with translations in that language (or those named).
2. One subagent per language: `Read and follow .agent/skills/review-subtitle/references/cross-check.md`, plus `Language:` and `Files:`.
3. Present inconsistent terms (proposal each), address inconsistencies, glossary proposals. Ask which rows to add, then follow `references/glossary-proposals.md`. To fix translations afterwards, run report mode per episode; `check-glossary` shows what deviates.

## Never

- Modify `workspace/cleaned/` or `workspace/raw/`; report source errors instead.
- Modify `workspace/trans/` outside fix mode, or beyond the chosen items.
- Put notes, Markdown or explanations into subtitle files.
- Edit or delete `x` glossary rows; mention suspicious ones in the report.
