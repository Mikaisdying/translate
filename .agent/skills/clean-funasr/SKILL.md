---
name: clean-funasr
description: Fix speech-recognition errors in SRT subtitles from FunASR (or other ASR like Whisper), reading workspace/raw/ and writing workspace/cleaned/, keeping IDs and timestamps, WITHOUT translating. Use when the user wants to clean, tidy, fix or normalize a fresh transcript/subtitle, even if they only say "dọn file trong raw", "fix sub", "sửa lỗi chính tả phụ đề" or type /clean.
---

# Clean FunASR

Goal: turn raw ASR output into a clean source subtitle with correct words and punctuation, the canonical source for translation. It will be translated many times by many models, so accuracy matters more than elegance.

Talk to the user in Vietnamese.

## Folders

- Read from `workspace/raw/`. Never modify or overwrite files there.
- Write to `workspace/cleaned/` with the same name: `workspace/raw/ep01.srt` → `workspace/cleaned/ep01.srt`.
- Temp files go in `workspace/work/<file>/`, deletable afterwards.
- Run commands from the project root: `python tools/srt_tools.py ...` (`python3` if needed).

## Choosing files

- Do the files the user names.
- None named: every `workspace/raw/*.srt` without a counterpart in `workspace/cleaned/`. Skip already-cleaned files unless asked to redo.
- Redoing a cleaned file: first archive the old one with `python tools/srt_tools.py archive workspace/cleaned/<file>.srt workspace/work/<file>/cleaned` (moves into `workspace/work/<file>/backup/`) so old parts don't get merged in. Tell the user that existing translations in `workspace/trans/` were based on the old cleaned version.
- One file at a time: finish a file (up to handing the audit to a subagent) before the next.

## Per-file procedure

1. **Check format**: `python tools/srt_tools.py info workspace/raw/<file>.srt`. On a format error, stop and tell the user. Never guess-fix structure; a wrong ID/timestamp shifts the whole subtitle.
2. **Read glossary**: `workspace/glossary.md` if present, especially sections 1 (general), 2 (characters), 4 (terms), 5 (ASR errors). `x` rows are mandatory; `?` rows are hints. An empty glossary is fine.
3. **Understand the content first**: many ASR errors are only recognizable once you know the topic, but never read the whole file twice (one skim, one pass while fixing).
   - ≤ 150 blocks: skip this step, read directly in step 4.
   - Longer: delegate a summary to a subagent with a task message of only `Read and follow .agent/skills/clean-funasr/references/summarize.md` and `File: workspace/raw/<file>.srt`. Save its reply verbatim to `workspace/work/<file>/summary.md`; the translate step reuses it instead of rereading the file. No subagent tool: skim once with `text` and write `summary.md` yourself using that template.
4. **Fix**: never rewrite IDs or timestamps yourself. Read text with `text`, write the fixed text to a text file, one block per line as `ID | text` (multi-line blocks joined with ` / `), then let `merge` put it back onto the original IDs and timestamps. `merge` rejects missing, extra or duplicate IDs and empty blocks.
   For unchanged blocks write `ID | =` (keep original text) instead of copying the sentence: every ID must be present, but only rewrite blocks you actually fix. This is the most token-expensive part of cleaning, so don't touch a block just to polish it (see "Incidental fixes").
   - ≤ 150 blocks: `python tools/srt_tools.py text workspace/raw/<file>.srt`, write `workspace/work/<file>/cleaned.txt`, then `python tools/srt_tools.py merge workspace/raw/<file>.srt workspace/work/<file>/cleaned.txt workspace/cleaned/<file>.srt`.
   - Longer: work in 100-block parts. Part 1 = blocks 1-100: `python tools/srt_tools.py text workspace/raw/<file>.srt --from 1 --to 100`, write `workspace/work/<file>/cleaned/part_001.txt`; part 2 = 101-200 → `part_002.txt`, and so on. Write each part as soon as it's done. Never read the `.srt` directly (twice the tokens due to IDs/timestamps); no need for `split`.
   - Progress: `python tools/srt_tools.py parts workspace/raw/<file>.srt workspace/work/<file>/cleaned` shows done, partial and pending parts and prints the `text` command for the next part. If interrupted: run it, read `summary.md`, reread the last ~10 blocks of the previous part with `text` for continuity, then continue. Working in one go, the previous part is still in context; don't reread.
   - When `parts` reports all done: `python tools/srt_tools.py merge workspace/raw/<file>.srt workspace/work/<file>/cleaned workspace/cleaned/<file>.srt --cleanup`. `--cleanup` deletes the parts folder after a successful merge; from then on edit `workspace/cleaned/<file>.srt` directly.
5. **Validate**: `python tools/srt_tools.py validate workspace/raw/<file>.srt workspace/cleaned/<file>.srt`. Must PASS. On FAIL, fix the reported spots and rerun. Never report done before PASS.
6. **Approved ASR errors**: `python tools/srt_tools.py check-asr workspace/cleaned/<file>.srt` lists leftover `x` ASR errors from glossary section 5. Fix all, except where context shows the word is correct here (note those in the report).
7. **Subagent audit**: delegate (Agent/Task in Claude Code, `runSubagent` in VS Code Copilot) with a task message of only:

   ```
   Read and follow .agent/skills/clean-funasr/references/audit.md
   Raw: workspace/raw/<file>.srt
   Cleaned: workspace/cleaned/<file>.srt
   ```

   The subagent only reads and returns, in its reply, spots that look over-edited, meaning-changed or inconsistent; it creates no files. Add none of your own comments, to keep its view independent. You may start the next file while waiting. No subagent tool: do `audit.md` yourself.
   Don't apply audit results yourself: put them in the final report for the user to choose (below). After the user chooses, fix exactly those items in `workspace/cleaned/<file>.srt` and rerun `validate`. In a new session without the list, rerun the audit.

## Allowed fixes

Only when context clearly shows an error:

- Homophone / near-homophone misrecognitions (Chinese: 他/她/它, 在/再, 的/得/地; English: their/there, "a lot" heard as "allot").
- Misrecognized names, terms, places, especially one name spelled several ways in the file: unify to one correct spelling (per glossary if present).
- Misrecognized shortcuts and software names: normalize. Key names capitalized (Ctrl, Shift, Alt, Cmd, Option, Enter, Tab, Esc, Space), letter keys uppercase, joined with " + ". E.g. "ctrl加r", "control R", "Ctrl 加 Shift 加 S" → "Ctrl + R", "Ctrl + Shift + S". Software names when clear: "photo shop", "PS软件" → "Photoshop". Menu/tool names in the source language (e.g. 图层, 画笔工具) are NOT converted to English at clean, since clean doesn't translate; only fix spelling.
- ASR-repeated words that hurt readability ("我我我们", "the the"), broken words.
- Missing or wrong punctuation that changes meaning.

**Incidental fixes**: only inside a block already being fixed for a reason above; never edit a block just for these. Translation handles sentence breaks and fillers, so rewriting the whole file for looks wastes tokens:

- Punctuation, capitalizing sentence starts and names (for cased languages).
- Removing pure fillers (嗯, 啊, 呃, um, uh) if the block still has other content. A filler-only block stays as is, since blocks may not be empty.
- Extra whitespace, joining lines broken mid-block.

## Never

- Translate. That is the job of `translate-subtitle`.
- Change IDs, timestamps, block order or count. Never merge or split blocks, even when a sentence spans several: fix text within each block and let the sentence flow across them.
- Rewrite for style, change tone, summarize or add ideas.
- Drop meaningful speech, including stutters, swearing, emotional hesitation.
- Put notes, Markdown, explanations or [?] into the subtitle file. If unsure, keep the original text and mention it in the report.

When in doubt, keep it. A leftover ASR error can still be guessed by the translator; a wrong "fix" gets translated wrong with confidence.

## Report

Brief, in chat (never in the subtitle file):

- Files processed, block count, changed-block count, validate result.
- A few representative fixes.
- Uncertain spots (with IDs) for the user to check.
- Subagent audit: counts per type per file, all "Đổi nghĩa" items in full (keep each item's format so the user can choose by ID), other items grouped by type with IDs. Ask which to fix (all, by type, by ID, or none).
- Recurring ASR errors or newly found names: propose adding them to `workspace/glossary.md` (section 2, 4 or 5) with status `?`. Write to the glossary only if the user agrees.
