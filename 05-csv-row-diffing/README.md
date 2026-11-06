# Module 05: CSV Row Diffing

## The concept

CSV has no tree, but the same question: *which rows are the same row?* Position is useless (someone
re-sorted the export), so rows are paired by **key columns** (`id`, or `country` + `year`). Then:

- key only in b: added row; key only in a: removed row
- key in both: compare cell by cell
- columns only in one file: reported as column changes, and *not* compared per cell

## The input is the hard part

- **BOM.** Excel writes UTF-8 with a byte-order mark; PowerShell's `Out-File` can write UTF-16. Read those as plain
  UTF-8 and the first column is named `﻿id`, so your key column "does not exist". `encoding_for` looks at the
  first four bytes.
- **No silent fallback.** If the bytes are not valid in the detected encoding (a Windows-1252 file with an accented
  letter), we raise. Falling back to Latin-1 "works" and turns bad bytes into plausible wrong text.
- **Delimiters.** European Excel uses `;`; exports use tabs or pipes. `csv.Sniffer` guesses from character
  statistics and fails on small files. `sniff` asks instead: *which candidate splits the first rows into the same
  number of columns (more than one)?* That is a much stronger signal.
- **Duplicate keys.** Two rows with `id=1`. Crashing is unhelpful; silently keeping one loses data. The rows pair
  up in file order and the duplicates are reported.

## Streaming

Index file a in memory (`dict[key] -> [rows]`), then iterate file b row by row, popping matches. Memory is O(rows
of a); b may be arbitrarily large. Whatever is left in the index at the end is "removed".

## Run it

```
python main.py
```
