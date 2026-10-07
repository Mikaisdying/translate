---
name: review-subtitle
description: Review SRT translations in workspace/trans/ against the source in workspace/cleaned/ and workspace/glossary.md, finding mistranslations, wrong instructions, wrong terms and address slips (delegated to a subagent), presenting them for the user to choose, then fixing exactly the chosen items, or cross-checking consistency across episodes. Use whenever the user says review, soát lỗi, kiểm tra bản dịch, rà lại sub, check bản dịch, sửa theo review, review chéo, or types /review, even if they only say "dịch xong rồi, xem giúp có lỗi không".
---

# Review Subtitle

Review has two separate parts:

1. **Finding errors**: delegated to a subagent (except self-review, below). A subagent starts with a clean context, free of the translating session's interpretation, so it sees errors more objectively. It only reads and writes the error list to the episode's review file; it never edits the translation.
2. **Deciding fixes**: belongs to the user. You present results, the user chooses whether and what to fix, and you fix exactly those items.

The review file stores results across steps and sessions: review one episode, fix another, come back tomorrow, all from the file, independent of chat.

Talk to the user in Vietnamese.

## Modes

From the user's words:

- **Report** (default): find errors, write the review file, present, ask what to fix. Don't modify `workspace/trans/`.
- **Fix** ("sửa", "fix", "sửa theo review"): apply the items the user chose from the review file.
- **Cross-check** ("chéo", "cross", "toàn khóa"): check consistency across episodes. Don't modify `workspace/trans/`.

Unclear → report mode.

## Files

- Translation `workspace/trans/<name>.<code>.srt`, source `workspace/cleaned/<name>.srt`. Language from the suffix (`.vi.srt` → vi); unknown suffix → ask.
- Review file: `workspace/work/<name>/review.<code>.md`, format per `references/find-errors.md`: one entry per error with heading `### ID 57 | Nghiêm trọng | Sai thao tác | pending` and lines Gốc, Hiện tại, Đề xuất, Lý do, enough to fix in another session. Status (end of heading):
  - `pending`, `unsure`: written by the subagent, not handled yet.
  - `fixed`: applied in fix mode.
  - `skipped`: user chose not to fix.
  `status` shows pending items per episode (`review: N chờ`), and `(cũ)` if the translation changed after the review file was last updated.
- Never modify `workspace/cleaned/`, `workspace/raw/`, or `x` rows in `workspace/glossary.md`. Only fix mode may modify `workspace/trans/`.
- Run from the project root: `python tools/srt_tools.py ...` (or `python3`).

## Delegating to a subagent

Use the environment's subagent tool (Agent/Task in Claude Code, `runSubagent` in VS Code Copilot). If the user names a model for review (e.g. "review bằng sonnet") and the tool allows choosing, use it; ideally a different model from the one that translated.

The task message contains only what the subagent needs, none of your opinions or guesses about the translation, to keep its view independent:

```
Read and follow .agent/skills/review-subtitle/references/find-errors.md
Source: workspace/cleaned/ep03.srt
Translation: workspace/trans/ep03.vi.srt
Language: vi
Scope: all
Result file: workspace/work/ep03/review.vi.md
```

The subagent writes the file and returns only the path and total line, so your context doesn't hold every episode's error list.

One subagent per file; several files run in parallel a few at a time.

Long files (block count from `info`): above ~400 blocks, split into consecutive ranges of ~300-350 blocks (e.g. 1028 blocks → `blocks 1-343`, `blocks 344-686`, `blocks 687-1028`), one subagent per range, run **sequentially** (next range only after the previous finishes), all writing the same `Result file: workspace/work/<name>/review.<code>.md`, no per-range files. First range: `Scope: blocks 1-343`; later ranges add `Append: yes` so the subagent merges into the existing file instead of overwriting. Each subagent has a short context, so it reads more carefully and doesn't carry a thousand blocks through every tool call. If interrupted, the `Phạm vi` line in the review file shows how far it got; continue from there. Different episodes still run in parallel; only ranges within one episode are sequential. Cross-check uses `references/cross-check.md`, one subagent per language with the file list.

**Self-review without a subagent** when all four hold:

- Only one file, at most ~400 blocks.
- In this session you haven't translated, cleaned or read that episode (source or translation). Your context is then as clean as a subagent's, so independence is kept while saving subagent startup cost.
- The user didn't ask for review by another model.
- Not cross-check mode.

Otherwise delegate as above. When self-reviewing, follow `references/find-errors.md` and write the review file like a subagent would, then continue from step 4 of report mode; skip the `pair --ids` check in step 5 (no subagent copy errors), but still verify "Lỗi ở bản gốc" items yourself.

No subagent tool: do the reference file yourself in this session. If the second condition above fails, tell the user once that a review in a new session or with another model would be more objective.

## Report mode

1. **Choose files**:
   - User named files → exactly those.
   - None: run `status`, list PASS translations with their review state, and ask which to review (one, several, all). FAIL translations: report the structural error, no subagent needed.
   - No matching `workspace/cleaned/<name>.srt`: report and skip.
   - Episode marked "gốc sửa sau" in `status`: still review, but remind the user `workspace/cleaned/` changed after translation.
   - Episode with a review file that still has pending items and isn't `(cũ)`: ask whether to continue that list (go to presenting, step 6) or review from scratch.
2. **Archive the old review file** if any (re-review): `archive workspace/work/<name>/review.<code>.md` (moves into `workspace/work/<name>/backup/`). Never let a subagent overwrite old statuses.
3. **Delegate** as above, or self-review if eligible.
4. **Check the result**: the review file must have the header and well-formed entries (heading with ID, severity, type, status; lines Gốc, Hiện tại, Đề xuất, Lý do). Missing or broken → delegate again once; still broken → tell the user. If the subagent returned content in its reply because it couldn't write the file, write it to the review file yourself.
   Split files: after the last range, `Phạm vi` must be `toàn bộ` with no duplicate entries at the boundaries. Since each subagent saw only one range, check file-wide consistency yourself: for terms and names in `Đề xuất glossary` that ranges translated differently, `find` in the translation to count each variant, then add a medium-severity entry with the proposed form.
5. **Quick verification**: put the IDs of all serious errors into one `pair <source> <translation> --ids 57,63,120-121` call to confirm "Gốc" and "Hiện tại" match the real file (subagents can copy the wrong block). For mismatches, add `- Đối chiếu: không khớp file thật (...)` to that entry and say so when presenting; don't drop it yourself.
   For each "Lỗi ở bản gốc" item, verify before proposing a change to `workspace/cleaned/`: view context with `text --from N --to M`, and consider whether the suspect word is a correct software UI name or term (e.g. Blender's Chinese UI calls X-Ray 透视, so 透视模式 is not an ASR error). Subagents only guess from the translation and often misreport here. Record your verdict (fix / keep, with reason) in that entry of the review file.
6. **Present** in chat from the review file, keeping each entry's format (including status) so the user can choose by ID, and give the file path for the full view:
   - Error counts by severity; several files → one table, one row per file.
   - All serious errors (ID, current → proposed, short reason).
   - Medium and minor: in full if few (~20 or fewer), otherwise grouped by type with ID lists; give details on request.
   - Source errors and glossary proposals, if any.
   Several episodes: you may present and ask one episode at a time; the rest stay in their files.
7. **Ask the user** what to do, e.g. fix all, only serious, specific IDs, confirm or drop `unsure` items, apply their own alternative, or fix nothing. If glossary proposals are pending, also ask which rows to add to `workspace/glossary.md` (see [Writing proposals to the glossary](#writing-proposals-to-the-glossary)). Stop here and wait.

## Fix mode

Run only when the user has said what to fix. The list comes from `workspace/work/<name>/review.<code>.md`, so it works in a different session from report mode. No review file → run report mode first and ask again, since the user can't choose without seeing the list. User says "sửa" without naming items → present pending items (step 6 above) and ask.

1. **Collect the chosen items** from the review file. Skip `fixed` or `skipped` items, and `unsure` items the user hasn't confirmed.
2. **Verify**: if the review file is `(cũ)` in `status` (translation changed after review), run `pair <source> <translation> --ids <chosen IDs>` first; items whose `Hiện tại` no longer matches the real file are not fixed; tell the user.
3. **Back up**: `python tools/srt_tools.py archive --copy workspace/trans/<name>.<code>.srt` (prints the backup path).
4. **Fix exactly the chosen blocks**, per `Đề xuất` (or the user's own fix). Don't rewrite other blocks along the way. Replace text only; IDs, timestamps, block count and order stay.
5. **Check**: `validate ... --target <code>` must PASS; run `check-glossary` and report remaining violations, fixing nothing beyond the chosen items.
6. **Update the review file**: applied items → change the status at the end of the heading to `fixed` (if the user gave a different fix, update the `Đề xuất` line to match); items the user declined → `skipped`. Unmentioned items stay. Change only those lines, never rewrite the whole file.
7. **Report**: `diff <backup> workspace/trans/<name>.<code>.srt`, list changed blocks (old → new), skipped items with reasons, and the number still `pending` so the user can continue choosing.

## Cross-check mode

1. Pick the episodes with translations in that language (or those the user names).
2. Delegate per `references/cross-check.md`.
3. Present: terms translated several ways (proposal for each), address inconsistencies, glossary proposals. Ask which proposals to add to `workspace/glossary.md`, then write per [Writing proposals to the glossary](#writing-proposals-to-the-glossary). To fix translations, after the glossary is settled run report mode per episode; `check-glossary` will point out what to fix.

## Writing proposals to the glossary

Shared by report and cross-check modes. Write only the rows the user chose ("thêm hết" = every pending proposal).

1. No `workspace/glossary.md` → copy `.agent/skills/build-glossary/assets/glossary.template.md`.
2. One row per proposal in the right table: people → `2. Nhân vật`, address → `3. Xưng hô`, terms, menus, places, repeated phrases → `4. Thuật ngữ`. Status always `?`. Fill the reviewed language's column (vi → `Tiếng Việt`, en → `English`), leave the other empty if unknown; `Ghi chú` names the source, e.g. `review ep03.vi`.
3. Term already in the glossary:
   - `x` row: don't touch it; tell the user the proposal differs from the approved form.
   - `?` row: fill only empty cells; if a cell has a different value, ask the user which to keep, never overwrite.
4. Add or change only those rows; never reorder or rewrite other parts of the glossary.
5. Mark the review file so later sessions don't ask again: append `— added` or `— skipped` (user declined) to each proposal line under `## Đề xuất glossary`. Cross-check mode has no review file; skip this step.
6. Report the rows added and remind the user to change `?` to `x` on accepted rows so clean and translate must follow them. New `?` rows don't make the current translation wrong; to fix translations per the glossary, after switching to `x`, `check-glossary` points out what to fix.

## Never

- Modify `workspace/cleaned/` or `workspace/raw/`. Report source errors to the user.
- Modify `workspace/trans/` outside fix mode, or beyond the user's chosen items in fix mode.
- Put notes, Markdown or explanations into subtitle files.
- Edit or delete `x` glossary rows; if one looks wrong, mention it in the report. Only add or update `?` rows the user chose.
