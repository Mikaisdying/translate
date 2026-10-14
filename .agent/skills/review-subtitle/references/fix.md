# Fix mode

Run only when the user has said what to fix. Items come from `workspace/work/<name>/review.<code>.md`, so this works in a later session than the review.

- No review file → run report mode first; the user can't choose without the list.
- "sửa" without naming items → present pending items (report step 6) and ask.

1. **Collect** the chosen items. Skip `fixed`, `skipped`, and `unsure` items the user hasn't confirmed.
2. **Stale check**: if `status` marks the review `(cũ)`, run `pair <source> <translation> --ids <chosen IDs>`; don't fix items whose `Hiện tại` no longer matches, and tell the user.
3. **Back up**: `python tools/srt_tools.py archive --copy workspace/trans/<name>.<code>.srt` (prints the backup path).
4. **Fix exactly the chosen blocks** per `Đề xuất` (or the user's wording). Text only; touch no other block.
5. **Check**: `validate <source> <translation> --target <code>` must PASS; `check-glossary ... --target <code>` and report remaining violations without fixing beyond the chosen items.
6. **Update the review file** line by line (never rewrite it): applied → heading status `fixed` (update `Đề xuất` if the user gave other wording); declined → `skipped`; others unchanged.
7. **Report**: `diff <backup> <translation>`, changed blocks (old → new), skipped items with reasons, number still `pending`.
