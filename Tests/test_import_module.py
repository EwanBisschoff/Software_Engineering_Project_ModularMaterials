"""Tests for importing existing markdown files as modules"""
from pathlib import Path
import tempfile
import unittest
import yaml

from Scripts.import_module import import_module

def front_matter(path):
    text = Path(path).read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---")[1])


class ImportModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.modules = self.root / "Modules"
        self.source = self.root / "Java Basics.md"

    def run_import(self, **kwargs):
        kwargs.setdefault("author", "Author")
        kwargs.setdefault("tags", ["java"])
        return import_module(self.source, modules_dir=self.modules, **kwargs)

    def test_file_without_front_matter_gets_all_fields_and_keeps_text(self):
        body = "# Java Basics\n\nÜbung: ß und Umlaute\n"
        self.source.write_text(body, encoding="utf-8")
        target = self.run_import(author="Ada")
        self.assertEqual(target.name, "java-basics.md")
        meta = front_matter(target)
        self.assertEqual(meta["title"], "Java Basics")
        self.assertEqual(meta["author"], "Ada")
        self.assertEqual(meta["version"], "1.0")
        self.assertEqual(meta["tags"], ["java"])
        self.assertIs(meta["marp"], True)
        self.assertTrue(target.read_text(encoding="utf-8").endswith(body))

    def test_existing_values_are_kept_and_missing_ones_added(self):
        original = "---\ntitle: 'My   Title'  # comment\nauthor: Bob\n---\n\n# Body\n"
        self.source.write_text(original, encoding="utf-8")
        target = self.run_import(author="Ignored")
        text = target.read_text(encoding="utf-8")
        self.assertIn("title: 'My   Title'  # comment\nauthor: Bob\n", text)
        self.assertTrue(text.endswith("---\n\n# Body\n"))
        meta = front_matter(target)
        self.assertEqual(meta["author"], "Bob")
        self.assertEqual(meta["tags"], ["java"])
        self.assertEqual(target.name, "my-title.md")

    def test_windows_line_endings_are_preserved(self):
        self.source.write_bytes(b"# Titel\r\n\r\nText\r\n")
        target = self.run_import()
        data = target.read_bytes()
        self.assertTrue(data.endswith(b"# Titel\r\n\r\nText\r\n"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_existing_module_is_not_overwritten(self):
        self.source.write_text("# Java Basics\n", encoding="utf-8")
        target = self.run_import()
        before = target.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_import()
        self.assertEqual(target.read_bytes(), before)

    def test_missing_author_or_tags_is_an_error(self):
        self.source.write_text("# T\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_module(self.source, author=None, tags=["a.md"], modules_dir=self.modules)
        with self.assertRaises(ValueError):
            import_module(self.source, author="A", tags=[], modules_dir=self.modules)
        self.assertFalse(self.modules.exists() and any(self.modules.iterdir()))

    def test_invalid_sources_are_rejected(self):
        with self.assertRaises(FileNotFoundError):
            self.run_import()
        folder = self.root / "folder.md"
        folder.mkdir()
        with self.assertRaises(ValueError):
            import_module(folder, "A", tags=["a.md"], modules_dir=self.modules)
        txt = self.root / "notes.txt"
        txt.write_text("# T\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_module(txt, "A", tags=["a.md"], modules_dir=self.modules)
        empty = self.root / "empty.md"
        empty.write_text("  \n", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_module(empty, "A", tags=["a.md"], modules_dir=self.modules)
        binary = self.root / "bin.md"
        binary.write_bytes(b"\xff\xfe\x00bad")
        with self.assertRaises(ValueError):
            import_module(binary, "A", tags=["a.md"], modules_dir=self.modules)

    def test_broken_front_matter_is_rejected(self):
        self.source.write_text("---\ntitle: [unclosed\n---\n# T\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_import()
        self.source.write_text("---\ntitle: T\n# never closed\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_import()

    def test_empty_existing_field_is_rejected(self):
        self.source.write_text("---\nauthor:\n---\n# T\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_import()

    def test_title_falls_back_to_file_name(self):
        self.source.write_text("Only text, no heading\n", encoding="utf-8")
        self.assertEqual(front_matter(self.run_import())["title"], "Java Basics")


if __name__ == "__main__":
    unittest.main()