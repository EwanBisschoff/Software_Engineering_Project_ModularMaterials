"""Contract tests for ordered, reusable course references (US-1.2)."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from Scripts.compose_course import BASE_DIR, load_course, main
from Scripts import create_module
from unittest.mock import patch


class CourseManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.modules = self.root / "Modules"
        self.modules.mkdir()
        self.courses = self.root / "Courses"
        self.courses.mkdir()
        self.first = self.modules / "first.md"
        self.second = self.modules / "second.md"
        self.first.write_text("# First\n", encoding="utf-8")
        self.second.write_text("# Second\n", encoding="utf-8")
        self.manifest = self.courses / "course.yaml"

    def write_manifest(self, references, title="Test course"):
        self.manifest.write_text(
            yaml.safe_dump({"title": title, "modules": references}), encoding="utf-8"
        )
        return self.manifest

    def test_mixed_references_preserve_teaching_order(self):
        self.write_manifest([{"id": "second"}, {"path": "../Modules/first.md"}])
        course = load_course(self.manifest, self.modules)
        self.assertEqual(course.title, "Test course")
        self.assertEqual(course.modules, (self.second.resolve(), self.first.resolve()))

    def test_reuse_keeps_original_files_and_reflects_edits(self):
        self.write_manifest([{"id": "first"}])
        other = self.courses / "other.yaml"
        other.write_text(
            "title: Other course\nmodules:\n  - path: ../Modules/first.md\n",
            encoding="utf-8",
        )
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        first_course = load_course(self.manifest, self.modules)
        second_course = load_course(other, self.modules)
        self.assertEqual(first_course.modules, second_course.modules)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.first.write_text("# Updated shared module\n", encoding="utf-8")
        for course in (first_course, second_course):
            self.assertEqual(course.modules[0].read_text(encoding="utf-8"), "# Updated shared module\n")

    def test_generated_module_can_be_referenced_by_id(self):
        with patch.object(create_module, "MODULES_DIR", self.modules), redirect_stdout(io.StringIO()):
            generated = create_module.create_module("Introduction to Python", "Lecturer", "1.0", ["python"])
        self.write_manifest([{"id": generated.stem}])
        self.assertEqual(load_course(self.manifest, self.modules).modules, (generated.resolve(),))

    def test_invalid_manifest_shapes(self):
        for content in ("", "[]", "title: Course", "title: Course\nmodules: []", "title: Course\nmodules: first"):
            with self.subTest(content=content):
                self.manifest.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_course(self.manifest, self.modules)

    def test_invalid_titles(self):
        for title in (None, "", "  ", 42, ["Course"]):
            with self.subTest(title=title):
                self.write_manifest([{"id": "first"}], title)
                with self.assertRaisesRegex(ValueError, "title"):
                    load_course(self.manifest, self.modules)

    def test_invalid_references(self):
        references = [
            "first", None, {}, {"id": "first", "path": "../Modules/first.md"},
            {"unknown": "first"}, {"id": ""}, {"path": " "}, {"id": 1},
            {"id": "../first"}, {"id": "first.md"}, {"id": "missing"},
            {"path": "../Modules/missing.md"}, {"path": "../Modules/first.txt"},
            {"path": str(self.first.resolve())},
        ]
        directory = self.modules / "directory.md"
        directory.mkdir()
        references.append({"path": "../Modules/directory.md"})
        for reference in references:
            with self.subTest(reference=reference):
                self.write_manifest([reference])
                with self.assertRaisesRegex(ValueError, "Module 1"):
                    load_course(self.manifest, self.modules)

    def test_unknown_fields_are_reported(self):
        self.manifest.write_text("title: Course\nmoduels: []\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unknown course fields: moduels"):
            load_course(self.manifest)

    def test_invalid_yaml_and_unsafe_yaml_are_rejected(self):
        for content in ("modules: [", "!!python/object/apply:builtins.print ['unsafe']"):
            with self.subTest(content=content):
                self.manifest.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Invalid YAML"):
                    load_course(self.manifest)

    def test_cli_from_another_working_directory(self):
        self.write_manifest([{"path": "../Modules/second.md"}, {"id": "first"}], "Kurs für Anfänger")
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "Scripts" / "compose_course.py"),
             str(self.manifest), "--modules-dir", str(self.modules)],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "Course: Kurs für Anfänger")
        self.assertEqual(lines[1], f"1. {self.second.resolve()}")
        self.assertEqual(lines[2], f"2. {self.first.resolve()}")

    def test_duplicate_yaml_keys_are_rejected(self):
        contents = [
            "title: Course\nmodules: [{id: first}]\nmodules: [{id: second}]\n",
            "title: Course\nmodules:\n  - path: ../Modules/first.md\n    path: ../Modules/second.md\n",
            "title: Course\nmodules:\n  - id: first\n    id: second\n",
            "title: First\ntitle: Second\nmodules: [{id: first}]\n",
        ]
        for content in contents:
            with self.subTest(content=content):
                self.manifest.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "duplicate key"):
                    load_course(self.manifest, self.modules)
                with redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(main([str(self.manifest)]), 1)
                    self.assertIn("duplicate key", stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())

    def test_non_string_yaml_keys_are_rejected(self):
        for key in ("42", "[title, modules]"):
            with self.subTest(key=key):
                self.manifest.write_text(f"{key}: value\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "field names must be strings"):
                    load_course(self.manifest)

    def test_cli_errors_return_failure_without_tracebacks(self):
        missing = self.courses / "missing.yaml"
        self.write_manifest([{"id": "missing"}])
        invalid_encoding = self.courses / "invalid.yaml"
        invalid_encoding.write_bytes(b"\xff\xfe")
        for manifest in (missing, self.manifest, invalid_encoding):
            with self.subTest(manifest=manifest), redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(main([str(manifest)]), 1)
                self.assertIn("Error:", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())

    def test_repository_examples_share_a_module(self):
        first = load_course(BASE_DIR / "Courses" / "example-course.yaml")
        second = load_course(BASE_DIR / "Courses" / "example-reuse.yaml")
        self.assertEqual(first.modules, second.modules)


if __name__ == "__main__":
    unittest.main()
