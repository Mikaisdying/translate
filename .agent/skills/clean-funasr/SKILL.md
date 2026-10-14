---
name: clean-funasr
description: Use when cleaning, tidying, fixing ASR/speech-recognition errors, typos, or normalizing raw subtitles in workspace/raw/ before translation, or when user asks "dọn file trong raw", "fix sub", "sửa lỗi chính tả phụ đề", "chuẩn hóa phụ đề", or types /clean.
---

# Clean FunASR

Goal: turn raw ASR output into the canonical source for translation, with correct words and punctuation. Many models will translate it, so accuracy beats elegance. Talk to the user in Vietnamese.

## Files

- `<file>` below = the episode name without `.srt`, exactly as in `workspace/raw/` (e.g. `001.第一节课 人体体块讲解`), spaces included. Never shorten it (`005`, `ep5` are wrong).
- Read `workspace/raw/<file>.srt` (never modify). Write `workspace/cleaned/<file>.srt` (same name). Temp files only in `workspace/work/<file>/`.
- Run every command from the project root exactly as written, with paths in double quotes (names contain spaces). `python3` if `python` is missing.
- Never open an `.srt` directly; read with `text` (half the tokens: no IDs/timestamps).
- Never use `split` (it makes `.srt` parts; the tool refuses it inside `workspace/`). Parts are `part_NNN.txt` from `parts`.
- `parts` and `merge` reject wrong folder/file names (`[LỖI] ... sai chỗ`). Then fix the path to what the message says; never work around it.

## Choosing files

- The files the user names; otherwise run `python tools/srt_tools.py status` and take the first row with raw `có` and cleaned `—`. Use the name exactly as printed in the `Tên` column.
- Redo of a cleaned file: first `python tools/srt_tools.py archive "workspace/cleaned/<file>.srt" "workspace/work/<file>/cleaned" "workspace/work/<file>/audit.md"` (moves them to `workspace/work/<file>/backup/`, so old parts aren't merged in). Tell the user existing translations used the old version.
- **Session budget** (every turn resends the whole context; long sessions cost more and degrade): one file per session (files ≤ 150 blocks may be followed by another), and at most 5 part files saved per session. Count them. After saving the 5th, don't run `parts` again: report progress and ask the user to `/clear` and say "clean tiếp".

## Per-file procedure

Do the steps in order; don't skip or reorder.

1. **Format**: `python tools/srt_tools.py info "workspace/raw/<file>.srt"`. Any `[LỖI]` → stop and tell the user; never guess-fix structure. Note `Blocks:` (the block count used below).
2. **Glossary**: `python tools/srt_tools.py glossary --section 1,2,4,5` (don't open `workspace/glossary.md`). `x` rows are mandatory, `?` rows are hints. Empty is fine.
3. **Context** (> 150 blocks only):
   - `workspace/work/<file>/summary.md` exists → read it; done.
   - Otherwise give a subagent only `Read and follow .agent/skills/clean-funasr/references/summarize.md` and `File: workspace/raw/<file>.srt`. Save its reply verbatim to `workspace/work/<file>/summary.md` (translation reuses it).
   - No subagent tool: never read the file just to summarize. Write `summary.md` with the template's header lines from what you know, and after saving each part in step 4, add that part's `Mạch nội dung` line and any new names, terms, ASR errors, unclear spots.
4. **Fix**. You never write IDs, timestamps or SRT; you write a text file with exactly one line per block, `ID | text` (multi-line blocks joined with ` / `), and `merge` builds the SRT. Every block gets a line. Unchanged block: `ID | =`. Rewrite only blocks you actually fix (see Allowed fixes).
   - **≤ 150 blocks**:
     1. `python tools/srt_tools.py text "workspace/raw/<file>.srt"`
     2. Write `workspace/work/<file>/cleaned.txt`.
     3. `python tools/srt_tools.py merge "workspace/raw/<file>.srt" "workspace/work/<file>/cleaned.txt" "workspace/cleaned/<file>.srt"`
   - **> 150 blocks**: 100-block parts. Each turn:
     1. `python tools/srt_tools.py parts "workspace/raw/<file>.srt" "workspace/work/<file>/cleaned"`
     2. Act on its last lines:

        | `parts` prints | Do |
        |---|---|
        | `Làm tiếp part_NNN.txt: <text command>` + `Ghi kết quả vào: <path>` | Run that exact `text` command, fix, write exactly that path. One part, then end the turn or go to 1. Never read the next part before this file is saved. |
        | a part marked `LỖI (...)` | When `Làm tiếp` names it, rewrite that whole file (not just the missing lines). |
        | `THỪA` | `python tools/srt_tools.py archive "<that part path>"`, then go to 1. |
        | `Ghép: <merge command>` | Run it exactly (it deletes the parts only on success), then step 5. |

     - New session ("clean tiếp"): before the loop, do steps 1-3, then read the last 10 lines of the highest-numbered `part_NNN.txt` that `parts` marks `xong` (for continuity of names and sentences).
   - `merge` prints `[LỖI]` → nothing was written; fix the text file it names and rerun the same command.
   - After the merge, edit only `workspace/cleaned/<file>.srt`, and only its text lines (never ID or timestamp lines); the parts are gone.
5. **Validate**: `python tools/srt_tools.py validate "workspace/raw/<file>.srt" "workspace/cleaned/<file>.srt"` must print `KẾT QUẢ: PASS`; fix and rerun until it does.
6. **Approved ASR errors**: `python tools/srt_tools.py check-asr "workspace/cleaned/<file>.srt"`. Fix every hit in the cleaned `.srt` (text lines only), except where context shows the word is right (list those in the report). If you changed anything, rerun step 5.
7. **Audit**: `workspace/work/<file>/audit.md` exists → read it instead (a redo archives it). Otherwise delegate a subagent with only:

   ```
   Read and follow .agent/skills/clean-funasr/references/audit.md
   Raw: workspace/raw/<file>.srt
   Cleaned: workspace/cleaned/<file>.srt
   ```

   Add no comments of your own. Save its reply verbatim to `workspace/work/<file>/audit.md`. No subagent tool: do `audit.md` yourself, same format. Don't apply any item.
8. **Report** (see Report), then **STOP and end the turn**. Change nothing until the user answers.
9. **After the user chooses**: fix exactly the chosen items in the cleaned `.srt` (text lines only), rerun step 5, and set each chosen item's `Status` to `fixed` (or `skipped` if the user declined it) in `audit.md`. Write glossary rows only if the user agreed.

## Allowed fixes

Only when context clearly shows an error:

- Homophones / near-homophones (他/她/它, 在/再, 的/得/地; their/there).
- Misheard names, terms, places; one name spelled several ways → one spelling (glossary first).
- Shortcuts: "ctrl加r", "control R" → "Ctrl + R"; key names capitalized (Ctrl, Shift, Alt, Cmd, Option, Enter, Tab, Esc, Space), letters uppercase, joined with " + ". Software names: "photo shop", "PS软件" → "Photoshop". Source-language menu names (图层, 画笔工具) stay in the source language; fix spelling only.
- ASR-repeated words ("我我我们", "the the"), broken words.
- Missing or wrong punctuation that changes meaning.

**Incidental** (only inside a block already being fixed; never a reason to touch a block): punctuation, capitalization, dropping pure fillers (嗯, 啊, um) when other content remains, extra whitespace.

## Never

- Translate.
- Change IDs, timestamps, block order or count; merge or split blocks (let sentences flow across blocks).
- Rewrite for style, change tone, summarize, add ideas.
- Drop meaningful speech (stutters, swearing, emotional hesitation).
- Put notes, Markdown or [?] in the subtitle; if unsure, keep the original and mention it.

When in doubt, keep it: a leftover ASR error can still be guessed by the translator, a wrong "fix" gets translated wrong with confidence.

## Report

Brief, in chat:

- File, block count, changed-block count, validate result; a few representative fixes.
- Uncertain spots (IDs).
- Audit (path to `audit.md`): counts per type; every "Đổi nghĩa" item in full in its original format; others grouped by type with IDs. Ask which to fix (all, by type, by ID, none).
- Recurring ASR errors or new names: propose adding to `workspace/glossary.md` (section 2, 4 or 5) as `?`; write only if the user agrees.
