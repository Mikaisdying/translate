---
name: translate-subtitle
description: Translate cleaned SRT subtitles in workspace/cleaned/ into Vietnamese (vi) or English (en), writing workspace/trans/, keeping IDs, timestamps and block count, following workspace/glossary.md. Use when the user wants to translate subtitles, make vietsub/engsub, retranslate with another model, or resume a half-finished translation (after a dropped connection or ended session), e.g. "dịch sub", "dịch tiếp", or types /trans-vi, /trans-en, /translate-subtitle vi, /translate-subtitle en.
---

# Translate Subtitle

Goal: a translation that reads naturally as if written by a native speaker, accurate, with consistent names and address forms throughout, matching the source block for block.

Talk to the user in Vietnamese.

## Target language

From the command or the user's words:

- `vi`, `/trans-vi`, "tiếng Việt", "vietsub" → **vi**
- `en`, `/trans-en`, "tiếng Anh", "English", "engsub" → **en**

If unclear, ask one question first. Then read the language guide:

- vi → `references/target-vi.md`
- en → `references/target-en.md`

(New language: add `references/target-<code>.md` modeled on those two.)

## Folders

- Read `workspace/cleaned/`. Write `workspace/trans/<name>.<code>.srt`: `workspace/cleaned/ep01.srt` → `workspace/trans/ep01.vi.srt`.
- Never modify `workspace/cleaned/` or touch `workspace/raw/`.
- File only in `workspace/raw/`, not in `workspace/cleaned/`: tell the user and suggest cleaning first. Translate from `workspace/raw/` only with explicit consent.
- Temp files in `workspace/work/<file>/`.
- Run from the project root: `python tools/srt_tools.py ...` (or `python3`).

## Choosing files

- Translate the files the user names.
- None named: every `workspace/cleaned/*.srt` without a `.<code>.srt` in `workspace/trans/`. Skip existing ones unless asked to retranslate.
- `python tools/srt_tools.py status` gives an overview: what's translated, validate PASS or not.

## Retranslating

When retranslating a file that already has a translation (e.g. switching model), archive the old one first:

```
python tools/srt_tools.py archive workspace/trans/<file>.<code>.srt workspace/work/<file>/<code>
```

This moves the old translation and old parts into `workspace/work/<file>/backup/` with a timestamp. Reuse no part of the previous run: if old parts remain in `workspace/work/<file>/<code>/`, `merge` will mix two translations and `validate` still PASSes because IDs and timestamps match. Keep `notes.<code>.md` (decisions that must stay consistent) but read it critically. Read the old version in `backup/` only if the user asks.

Resuming the same run in a new session: don't archive; continue from parts missing in `workspace/work/<file>/<code>/`.

## Per-file procedure

1. **Check**: `python tools/srt_tools.py info workspace/cleaned/<file>.srt`. Format error → stop and report.
2. **Read glossary**: all of `workspace/glossary.md`. `x` rows are mandatory and override your choices. `?` rows are suggestions. Empty cells: decide yourself, consistently.
3. **Understand the content first**: you need to know who's who, relationships and tone, since address and naming early on depend on what happens later. But never read the whole file twice (one skim, one pass while translating).
   - `workspace/work/<file>/summary.md` exists (made at clean): read it, not the whole file.
   - Missing, ≤ 150 blocks: skip this step, read directly in step 5.
   - Missing, longer: delegate to a subagent per `.agent/skills/clean-funasr/references/summarize.md` with `File: workspace/cleaned/<file>.srt`, save the reply to `summary.md` and read it. No subagent tool: skim once with `text` and write `summary.md` yourself.
4. **Decision log**: create `workspace/work/<file>/notes.<code>.md` (one per language, since Vietnamese address or English name spelling don't carry over), recording decisions not in the glossary (how names are rendered, who addresses whom how, term choices). Add to it as soon as a new decision is made. Within a session it's still in context, no need to reread; in a new session read it first.
5. **Translate**: never rewrite IDs or timestamps yourself. Read the source with `text`, write the translation to a text file, one block per line as `ID | translation` (two-line blocks joined with ` / `), then let `merge` put it onto the source IDs and timestamps. `merge` rejects missing, extra or duplicate IDs and empty blocks.
   - ≤ 150 blocks: `python tools/srt_tools.py text workspace/cleaned/<file>.srt`, write `workspace/work/<file>/<code>.txt`, then `python tools/srt_tools.py merge workspace/cleaned/<file>.srt workspace/work/<file>/<code>.txt workspace/trans/<file>.<code>.srt`.
   - Longer: translate in 100-block parts. Part 1 = blocks 1-100: `python tools/srt_tools.py text workspace/cleaned/<file>.srt --from 1 --to 100`, write `workspace/work/<file>/<code>/part_001.txt`; part 2 = 101-200 → `part_002.txt`, and so on. Write each part as soon as it's translated. Never read the `.srt` directly (twice the tokens due to IDs/timestamps); no need for `split`.
   - Progress: `python tools/srt_tools.py parts workspace/cleaned/<file>.srt workspace/work/<file>/<code>` shows done, partial (missing, extra, duplicate IDs, empty blocks) and pending parts, and prints the `text` command for the next part. No checklist file needed: the tool checks the part files directly, so it never drifts. If interrupted (connection lost, session ended): run it, read `summary.md` and `notes.<code>.md`, reread the last ~10 blocks of the previous part, both source and translation (`pair` doesn't work before merging; read the source with `text` and the end of the previous part file), then continue. Translating in one go, the previous part is still in context; don't reread.
   - When `parts` reports all done: `python tools/srt_tools.py merge workspace/cleaned/<file>.srt workspace/work/<file>/<code> workspace/trans/<file>.<code>.srt --cleanup`. `--cleanup` deletes the parts folder after a successful merge so `workspace/trans/<file>.<code>.srt` is the only copy; from then on every edit (including review fixes) goes directly into that file.
6. **Validate**: `python tools/srt_tools.py validate workspace/cleaned/<file>.srt workspace/trans/<file>.<code>.srt --target <code>`. Must PASS. Fix every "còn sót chữ gốc" or "có Markdown" warning; for "block giống hệt bản gốc" check with `diff` (names, sounds, numbers may legitimately be identical).
7. **Glossary**: `python tools/srt_tools.py check-glossary workspace/cleaned/<file>.srt workspace/trans/<file>.<code>.srt --target <code>`. Fix every `x` violation, except false positives (term phrased differently but matching the glossary's intent): list those in the report. Rerun `validate` afterwards.
8. **Self-check**: reread the translation with `text`, looking for address slips, inconsistent names, awkward sentences.

## General rules

**Keep structure**: replace only text. IDs, timestamps, order and block count stay exactly the same.

```
123
00:10:20,000 --> 00:10:23,000
Chữ gốc
```
→
```
123
00:10:20,000 --> 00:10:23,000
Chữ đã dịch
```

**Sentences spanning blocks**: understand and translate the whole sentence, then split it back across those blocks so each matches what is spoken in its time range and reads fairly independently. Don't translate fragments in isolation; word order differs between languages and the result becomes nonsense. Example (zh → vi):

```
45  如果你明天还是不来的话          →  Nếu mai cậu vẫn không đến
46  我就自己一个人去了              →  thì tớ sẽ tự đi một mình đấy.
```

**Length**: subtitles must be readable in time. Max 2 lines per block, prefer concise phrasing. Trim filler words, never meaning.

**Faithfulness**: no added information, no dropped meaning, no notes or explanations in the subtitle, no "Dịch bởi..." lines. Sounds and laughter may be kept or rendered naturally in the target language.

**Technical terms**: software, menus, tools, shortcuts follow the "Technical terms, software, shortcuts" section of the target language reference.

**Unsure of meaning**: choose the most plausible reading in context, translate normally, list the ID in the report. Never leave source text or [?] in the file.

## Report

Brief, in chat:

- File, language, block count, validate result.
- Key decisions you made (from `notes.<code>.md`): names, address, terms.
- Uncertain spots (with IDs).
- Propose moving decisions from `notes.<code>.md` into `workspace/glossary.md` with status `?` for reuse. Write only if the user agrees.
