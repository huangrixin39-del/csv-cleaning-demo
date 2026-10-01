import csv
import json
from pathlib import Path
import tempfile
import unittest

from csv_cleaner import ValidationError, clean_csv


class CleanerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "input.csv"
        self.output = self.root / "result"

    def write(self, text, encoding="utf-8"):
        self.source.write_text(text, encoding=encoding)

    def read(self, name):
        with (self.output / name).open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.reader(stream))

    def test_preserves_ids_formats_and_unselected_whitespace(self):
        self.write('id,name,date,amount,note\n0007, Alice ,01/02/2026,"1,000", keep \n')
        clean_csv(self.source, self.output, trim=["name"])
        self.assertEqual(self.read("cleaned.csv")[1],
                         ["0007", "Alice", "01/02/2026", "1,000", " keep "])
        self.assertEqual(self.read("changes.csv")[1], ["2", "name", " Alice ", "Alice"])

    def test_deduplication_after_trim_is_full_row_exact(self):
        self.write("id,name\n001, A \n001,A\n002,A\n001,a\n")
        report = clean_csv(self.source, self.output, trim=["name"])
        self.assertEqual(report["removed_rows"], 1)
        self.assertEqual(report["output_rows"], 3)
        evidence = self.read("removed_duplicates.csv")[1]
        self.assertEqual(evidence[:2], ["3", "2"])
        self.assertEqual(json.loads(evidence[2]), ["001", "A"])

    def test_duplicates_can_be_kept(self):
        self.write("id,name\n001,A\n001,A\n")
        report = clean_csv(self.source, self.output, keep_duplicates=True)
        self.assertEqual((report["output_rows"], report["duplicate_rows"], report["removed_rows"]),
                         (2, 1, 0))
        self.assertEqual(len(self.read("removed_duplicates.csv")), 1)

    def test_missing_values_are_retained_and_reviewed(self):
        self.write("id,name,email\n001, ,\n002,B,b@example.test\n")
        report = clean_csv(self.source, self.output, required=["name", "email"])
        self.assertEqual(report["output_rows"], 2)
        self.assertEqual(report["review_rows"], 1)
        self.assertEqual(self.read("cleaned.csv")[1], ["001", " ", ""])
        record = self.read("review.csv")[1]
        self.assertEqual(json.loads(record[1]), ["name", "email"])
        self.assertEqual(json.loads(record[2]), ["001", " ", ""])

    def test_rejects_invalid_headers_and_widths_before_writing(self):
        for text in ("", "id,\n1,A\n", "id,id\n1,2\n", "id, id \n1,2\n",
                     "id,name\n1\n", "id,name\n1,A,extra\n", "id,name\n\n",
                     'id,name\n1,"unterminated\n'):
            with self.subTest(text=text):
                self.write(text)
                with self.assertRaises(ValidationError):
                    clean_csv(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_rejects_other_delimiters_when_requested_columns_are_absent(self):
        for separator in (";", "\t"):
            with self.subTest(separator=separator):
                self.write(f"id{separator}name\n001{separator}Alice\n")
                with self.assertRaises(ValidationError):
                    clean_csv(self.source, self.output, trim=["name"])
                self.assertFalse(self.output.exists())

    def test_existing_output_and_input_are_protected(self):
        self.write("id\n001\n")
        original = self.source.read_bytes()
        self.output.mkdir()
        sentinel = self.output / "cleaned.csv"
        sentinel.write_text("existing output")
        with self.assertRaises(ValidationError):
            clean_csv(self.source, self.output)
        self.assertEqual(sentinel.read_text(), "existing output")
        self.assertEqual(self.source.read_bytes(), original)
        with self.assertRaises(ValidationError):
            clean_csv(self.source, self.source)
        self.assertEqual(self.source.read_bytes(), original)

    def test_utf8_bom_and_plain_utf8(self):
        for encoding in ("utf-8-sig", "utf-8"):
            with self.subTest(encoding=encoding):
                self.write("id,name\n001,王小明\n", encoding=encoding)
                destination = self.root / encoding
                clean_csv(self.source, destination, encoding=encoding)
                self.assertTrue((destination / "cleaned.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
                with (destination / "cleaned.csv").open(encoding="utf-8-sig") as stream:
                    self.assertEqual(list(csv.reader(stream))[1], ["001", "王小明"])

    def test_default_encoding_accepts_bom_and_plain_utf8(self):
        for encoding in ("utf-8-sig", "utf-8"):
            self.write("id\n0001\n", encoding=encoding)
            clean_csv(self.source, self.root / encoding)

    def test_multiline_csv_evidence_uses_physical_start_lines(self):
        self.write('id,note\n001,"a\nb"\n001,"a\nb"\n')
        clean_csv(self.source, self.output)
        self.assertEqual(self.read("removed_duplicates.csv")[1][:2], ["4", "2"])

    def test_invalid_encoding_and_unknown_columns_do_not_write(self):
        self.source.write_bytes(b"id,name\n1,\xff\n")
        with self.assertRaises(ValidationError):
            clean_csv(self.source, self.output)
        self.write("id\n001\n")
        with self.assertRaises(ValidationError):
            clean_csv(self.source, self.output, required=["email"])
        self.assertFalse(self.output.exists())

    def test_header_only_produces_valid_empty_reports(self):
        self.write("id,name\n")
        report = clean_csv(self.source, self.output)
        self.assertEqual(report["input_rows"], 0)
        self.assertEqual(self.read("cleaned.csv"), [["id", "name"]])
        saved = json.loads((self.output / "quality_report.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, report)
        self.assertEqual(report["input_file"], "input.csv")


if __name__ == "__main__":
    unittest.main()
