"""Small, auditable CSV cleaner. Python 3.9+, standard library only."""

import argparse
import csv
import json
from pathlib import Path


class ValidationError(ValueError):
    """Input cannot be processed without guessing its structure."""


def clean_csv(input_path, output_dir, trim=(), required=(),
              keep_duplicates=False, encoding="utf-8-sig"):
    """Validate first, then write five reports to a brand-new directory."""
    input_path, output_dir = Path(input_path), Path(output_dir)
    if output_dir.exists():
        raise ValidationError("Output directory already exists; choose a new directory.")
    if encoding not in ("utf-8", "utf-8-sig"):
        raise ValidationError("Supported encodings: utf-8, utf-8-sig.")
    trim, required = list(dict.fromkeys(trim)), list(dict.fromkeys(required))
    records = []
    try:
        with input_path.open("r", encoding=encoding, newline="") as stream:
            reader = csv.reader(stream, delimiter=",", strict=True)
            header = next(reader, None)
            if not header or any(not name.strip() for name in header):
                raise ValidationError("CSV needs a nonempty header with no empty names.")
            if len({name.strip() for name in header}) != len(header):
                raise ValidationError("Duplicate header names (ignoring outer whitespace).")
            unknown = [name for name in trim + required if name not in header]
            if unknown:
                raise ValidationError("Unknown column(s): " + ", ".join(unknown))
            while True:
                source_line = reader.line_num + 1
                row = next(reader, None)
                if row is None:
                    break
                if len(row) != len(header):
                    raise ValidationError(
                        f"Line {source_line}: expected {len(header)} fields, got {len(row)}."
                    )
                records.append((source_line, row))
    except (UnicodeError, csv.Error) as exc:
        raise ValidationError(f"Invalid CSV or encoding: {exc}") from exc

    indexes = {name: index for index, name in enumerate(header)}
    seen, cleaned, removed, changes, review = {}, [], [], [], []
    duplicate_rows, changed_rows = 0, 0
    for source_line, original in records:
        row = original.copy()
        row_changes = []
        for name in trim:
            index = indexes[name]
            row[index] = row[index].strip()
            if original[index] != row[index]:
                row_changes.append([source_line, name, original[index], row[index]])
        changes.extend(row_changes)
        changed_rows += bool(row_changes)
        key = tuple(row)
        if key in seen:
            duplicate_rows += 1
            if not keep_duplicates:
                removed.append([source_line, seen[key], json.dumps(row, ensure_ascii=False)])
                continue
        else:
            seen[key] = source_line
        cleaned.append(row)
        missing = [name for name in required if not row[indexes[name]].strip()]
        if missing:
            review.append([source_line, json.dumps(missing, ensure_ascii=False),
                           json.dumps(row, ensure_ascii=False)])

    report = {
        "input_file": input_path.name,
        "input_encoding": encoding,
        "output_encoding": "utf-8-sig",
        "columns": header,
        "trim_columns": trim,
        "required_columns": required,
        "deduplicate": not keep_duplicates,
        "input_rows": len(records),
        "output_rows": len(cleaned),
        "duplicate_rows": duplicate_rows,
        "removed_rows": len(removed),
        "changed_rows": changed_rows,
        "changed_fields": len(changes),
        "review_rows": len(review),
    }
    # exist_ok=False also protects against another process creating the directory.
    output_dir.mkdir(parents=True, exist_ok=False)

    def write_csv(filename, names, rows):
        with (output_dir / filename).open("x", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(names)
            writer.writerows(rows)

    write_csv("cleaned.csv", header, cleaned)
    write_csv("removed_duplicates.csv", ["source_line", "kept_source_line", "row_json"], removed)
    write_csv("changes.csv", ["source_line", "column", "old_value", "new_value"], changes)
    write_csv("review.csv", ["source_line", "missing_columns", "row_json"], review)
    with (output_dir / "quality_report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Trim specified CSV columns and remove exact full-row duplicates.",
        epilog="Example: python csv_cleaner.py input.csv result --trim name --required email",
    )
    parser.add_argument("input", help="Comma-delimited UTF-8 CSV with a header")
    parser.add_argument("output_dir", help="New directory; must not already exist")
    parser.add_argument("--trim", action="append", default=[], metavar="COLUMN",
                        help="Column to strip outer whitespace; repeat for more columns")
    parser.add_argument("--required", action="append", default=[], metavar="COLUMN",
                        help="Flag empty values for review; repeat for more columns")
    parser.add_argument("--keep-duplicates", action="store_true", help="Keep every input row")
    parser.add_argument("--encoding", choices=["utf-8-sig", "utf-8"], default="utf-8-sig")
    args = parser.parse_args()
    try:
        report = clean_csv(args.input, args.output_dir, args.trim, args.required,
                           args.keep_duplicates, args.encoding)
    except (OSError, ValidationError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Saved {report['output_rows']} rows to {args.output_dir}; "
          f"removed {report['removed_rows']} duplicates, "
          f"changed {report['changed_fields']} fields, "
          f"flagged {report['review_rows']} rows for review.")


if __name__ == "__main__":
    main()
