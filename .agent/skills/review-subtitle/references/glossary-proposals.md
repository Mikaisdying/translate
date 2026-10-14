# Writing proposals to the glossary

Write only the rows the user chose ("thêm hết" = every pending proposal).

1. No `workspace/glossary.md` → copy `.agent/skills/build-glossary/assets/glossary.template.md`.
2. One row per proposal in the right table: people → `2. Nhân vật`, address → `3. Xưng hô`, terms, menus, places, repeated phrases → `4. Thuật ngữ`. Status `?`. Fill the reviewed language's column (`Tiếng Việt` or `English`), the other only if known; one chosen form per cell, no pinyin; `Ghi chú` only names the source, e.g. `review ep03.vi`.
3. Term already present: `x` row → don't touch, tell the user it differs; `?` row → fill only empty cells, ask before changing a filled one.
4. Change nothing else in the glossary (no reordering, no rewriting).
5. Review file (not in cross-check): append `— added` or `— skipped` to each handled line under `## Đề xuất glossary`, so later sessions don't ask again.
6. Report rows added; remind the user to change `?` to `x` on accepted rows. After that, `check-glossary` shows which translations deviate.
