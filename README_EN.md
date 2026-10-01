# CSV Cleanup Demo

A small Python command-line tool with explicit cleaning rules and traceable results. This is an **AI-assisted portfolio demonstration using synthetic data**, not a previous client engagement or evidence of earnings.

## Run

Python 3.9+; standard library only. From this folder:

```powershell
python csv_cleaner.py input.csv my-result --trim name --trim email --required name --required email
python -m unittest -v test_csv_cleaner.py
```

Choose an output directory that does not already exist. The included `example-result/` already contains a completed run; use `my-result` or another new name to reproduce it.

## What happens

- Only named `--trim` columns have leading/trailing whitespace removed.
- Exact full-row duplicates are removed after trimming; the first occurrence is retained. Use `--keep-duplicates` to keep all rows.
- Every field remains text, preserving identifiers such as `0007` and leaving date/amount formats unchanged.
- Missing or whitespace-only values in `--required` columns are flagged for review. They are not filled or dropped because they are missing; normal duplicate removal still applies.
- The input is read-only. Its full structure is validated before the new output directory is created.

## Included demonstration

| Result | Count |
| --- | ---: |
| Input records | 6 |
| Retained records | 5 |
| Removed duplicates | 1 |
| Changed fields | 6 |
| Retained records requiring review | 2 |

The sample covers leading-zero IDs, Chinese text, quoted commas, missing values, varied date/amount text and duplicates. All email addresses use the reserved `.test` domain.

## Deliverables

| File | Purpose |
| --- | --- |
| `cleaned.csv` | Retained data, original column order and row order |
| `removed_duplicates.csv` | Removed source line, retained source line and complete cleaned record |
| `changes.csv` | Source line, column, old value and new value for every change |
| `review.csv` | Retained records with missing required fields |
| `quality_report.json` | Counts and the rules used; input filename only, no local directory |

Evidence records use JSON arrays inside CSV fields to avoid collisions with client column names. Source lines refer to physical starting lines, including records containing quoted newlines. The change log includes changes to rows later removed as duplicates.

## Scope and limitations

- Comma-delimited CSV with a header; UTF-8 or UTF-8 BOM input. Default `utf-8-sig` accepts both. Output CSV uses UTF-8 BOM.
- Headers are case-sensitive and matched exactly. Empty names and duplicate names after outer-whitespace comparison are rejected.
- Incorrect field counts, unknown requested columns, invalid encoding and parser-detected syntax errors are rejected with exit code 2.
- Single-column CSV is valid, so an arbitrary other-delimiter file cannot always be distinguished from single-column CSV. Specifying required columns checks the expected structure.
- No XLSX support, type conversion, fuzzy matching, date inference, email-address validation or external-system integration.
- Records are held in memory. This demonstration targets small files, not multi-gigabyte datasets.
- Spreadsheet software can reinterpret CSV text on opening; import ID columns as text to preserve their display.
- A disk/permission error during output may leave an incomplete new folder. Inspect it and choose a new folder for a retry.

The 12 executed tests cover preservation of IDs and text, selective trimming, deduplication on/off, missing-value retention, invalid input, refusing overwrites, UTF-8/BOM, multiline evidence and empty data. See `TEST_RESULTS.md` for the recorded run.
