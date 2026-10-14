---
name: translate-subtitle
description: Use when translating cleaned subtitles into Vietnamese (vi) or English (en), creating vietsub/engsub, retranslating with another model, or resuming a partial translation, e.g. "dịch sub", "dịch tiếp", "làm vietsub", "engsub", or typing /trans-vi, /trans-en, /translate-subtitle.
---

# Translate Subtitle

Goal: a translation that reads as if written by a native speaker, accurate, with consistent names and address forms, matching the source block for block. Talk to the user in Vietnamese.

## Target language

`vi` / `/trans-vi` / "tiếng Việt" / "vietsub" → **vi**; `en` / `/trans-en` / "tiếng Anh" / "engsub" → **en**. Unclear → ask once. Then read `references/target-<code>.md` (new language: add one modeled on these).

## Files

- `<file>` below = the episode name without `.srt` (e.g. `001.第一节课 人体体块讲解`); `<code>` = `vi` or `en`.
- Read `workspace/cleaned/<file>.srt` (never modify; never touch `workspace/raw/`). Write `workspace/trans/<file>.<code>.srt`. Temp files in `workspace/work/<file>/`.
- File only in `workspace/raw/`: suggest cleaning first; translate from raw only with explicit consent.
- Run every command from the project root exactly as written, with paths in double quotes (names contain spaces). `python3` if `python` is missing.
- Never open an `.srt` directly; read with `text` (half the tokens: no IDs/timestamps).

## Choosing files

- The files the user names; otherwise run `python tools/srt_tools.py status` and take the first episode whose cleaned is PASS and `<code>` column is `—`.
- **Session budget** (every turn resends the whole context; quality drops late in long sessions): one file per session (files ≤ 150 blocks may be followed by another), and at most 5 parts (~500 blocks) per session. Then stop after saving a part, report progress, and ask the user to `/clear` and say "dịch tiếp".
- **Retranslating** (e.g. another model): first `python tools/srt_tools.py archive "workspace/trans/<file>.<code>.srt" "workspace/work/<file>/<code>"` (moves both to `backup/`); leftover parts would otherwise be merged into the new run and still PASS. Keep `notes.<code>.md` but read it critically. Resuming the same run ("dịch tiếp"): don't archive.

## Per-file procedure

1. **Format**: `python tools/srt_tools.py info "workspace/cleaned/<file>.srt"`. Error → stop and report. Note `Blocks:` (the block count used below).
2. **Glossary**: `python tools/srt_tools.py glossary --section 1-4` (don't open `workspace/glossary.md`). `x` rows are mandatory and override your choices; `?` rows are suggestions; empty cells: decide yourself, consistently.
3. **Context** (who's who, relationships, tone; early address depends on later events). Never read the file twice:
   - `workspace/work/<file>/summary.md` exists (usually from clean): read it.
   - Missing, ≤ 150 blocks: skip; you read it in step 5.
   - Missing, longer: give a subagent only `Read and follow .agent/skills/clean-funasr/references/summarize.md` and `File: workspace/cleaned/<file>.srt`; save its reply verbatim to `workspace/work/<file>/summary.md`. No subagent tool: skim once with `text` and write it yourself.
4. **Decision log** `workspace/work/<file>/notes.<code>.md`: decisions not in the glossary (name rendering, who addresses whom how, non-obvious terms). One line each, `<gốc> → <bản dịch đã chọn>` (+ `từ ID N` if it changes), exactly one chosen form, never `A / B`. No ordinary words, no restating glossary rows, no pinyin. Append each decision when made. In a new session read it first.
5. **Translate**. You never write IDs, timestamps or SRT; you write a text file with exactly one line per source block, `ID | translation` (a two-line block joined with ` / `), and `merge` builds the SRT.
   - ≤ 150 blocks: `python tools/srt_tools.py text "workspace/cleaned/<file>.srt"` → write `workspace/work/<file>/<code>.txt` → `python tools/srt_tools.py merge "workspace/cleaned/<file>.srt" "workspace/work/<file>/<code>.txt" "workspace/trans/<file>.<code>.srt"`.
   - Longer: work in 100-block parts, repeating this loop:
     1. `python tools/srt_tools.py parts "workspace/cleaned/<file>.srt" "workspace/work/<file>/<code>"`. It prints the next `text` command and the part file to write.
     2. Run that `text` command, translate, and save the part file immediately (one part per turn; never hold unsaved output).
     3. Back to 1. A part marked `LỖI` must be rewritten; `THỪA` → archive it.
     When `parts` prints `Ghép: ...`, run that `merge` command (it deletes the parts only on success). Later edits, including review fixes, go directly into the `.srt`.
   - New session ("dịch tiếp"): before the loop, read glossary (step 2), `summary.md`, `notes.<code>.md`, and the last ~10 blocks of the last finished part (source via `text --from --to`, translation from its part file).
6. **Machine checks, one command**: `python tools/srt_tools.py review-prep "workspace/cleaned/<file>.srt" "workspace/trans/<file>.<code>.srt" --target <code>` (ignore its `## Đọc đối chiếu`).
   - `## Validate` must PASS. Fix "còn sót chữ gốc" and "có Markdown"; "block giống hệt bản gốc" may be legitimate (names, sounds, numbers).
   - `## Glossary`: fix every `x` violation; list false positives in the report.
   - `## Lint`: one `pair "<source>" "<translation>" --ids 12,57,80` call for all flagged blocks; fix real errors, list false positives.
   - To fix a block, edit only its text line(s) in the `.srt`. Then rerun `python tools/srt_tools.py validate "workspace/cleaned/<file>.srt" "workspace/trans/<file>.<code>.srt" --target <code>` until PASS.
   Don't reread the whole translation; content review is `review-subtitle`'s job (suggest it).

## Translation rules

- **Sentences spanning blocks**: translate the whole sentence, then split it back so each block matches what is spoken in its time range. Never translate fragments in isolation. E.g. zh → vi:

  ```
  45  如果你明天还是不来的话  →  Nếu mai cậu vẫn không đến
  46  我就自己一个人去了      →  thì tớ sẽ tự đi một mình đấy.
  ```

- **Length**: max 2 lines per block, concise; trim fillers, never meaning.
- **Faithful**: nothing added or dropped; no notes, glosses or "Dịch bởi..." lines. Sounds and laughter may be kept or rendered naturally.
- **Technical terms, software, shortcuts**: per the target-language reference.
- **Unsure of meaning**: translate the most plausible reading, list the ID in the report. Never leave source text or [?].

## Report

Brief, in chat:

- File, language, block count, validate result.
- Key decisions (names, address, terms) and uncertain spots (IDs).
- Propose moving decisions from `notes.<code>.md` into `workspace/glossary.md` as `?`, only those another model would likely get wrong or inconsistent (loanwords kept, jargon, names, address); write only if the user agrees.
