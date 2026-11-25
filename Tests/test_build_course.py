"""Regression tests for shared images and the common PDF theme."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from Scripts import build_course as builder
from Scripts.assets import embed_css_assets, embed_markdown_assets


class BuildCourseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.modules = self.root / "Modules"
        self.modules.mkdir()
        self.assets = self.root / "Assets"
        self.assets.mkdir()
        self.image = self.assets / "shared diagram(1).svg"
        self.image.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        self.source = self.modules / "module.md"
        self.manifest = self.root / "course.yaml"
        self.manifest.write_text("title: Test course\nmodules:\n  - path: Modules/module.md\n", encoding="utf-8")
        self.source.write_text("---\nmarp: true\n---\n# Title\n\n---\n\n## Content\n", encoding="utf-8")
        self.patchers = [
            patch.object(builder, "BUILD_DIR", self.root / "build"),
            patch.object(builder, "OUTPUT_DIR", self.root / "output"),
            patch.object(builder, "MODULES_DIR", self.modules),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def embed(self, text):
        return embed_markdown_assets(text, self.source)

    def test_inline_images_with_spaces_parentheses_and_titles(self):
        result = self.embed('![bg contain diagram](<../Assets/shared diagram(1).svg> "Caption")')
        self.assertIn('<img src="data:image/svg+xml;base64,', result)
        self.assertIn('title="Caption"', result)
        self.assertIn("data:image/svg+xml;base64,", self.embed('![x](../Assets/shared%20diagram(1).svg)'))

    def test_full_collapsed_and_shortcut_reference_images(self):
        for image in ("![Diagram][shared]", "![shared][]", "![shared]"):
            with self.subTest(image=image):
                result = self.embed(image + '\n\n[shared]:\n  <../Assets/shared diagram(1).svg> "Title"\n')
                self.assertIn('src="data:image/svg+xml;base64,', result)
                self.assertIn(' "Title"', result)

    def test_html_image_and_theme_resources(self):
        result = self.embed('<img alt="Diagram" src="../Assets/shared%20diagram(1).svg" width="400">')
        self.assertIn('src="data:image/svg+xml;base64,', result)
        self.assertIn('width="400"', result)
        result = embed_css_assets("section { background: url('../Assets/shared%20diagram(1).svg'); }", self.source)
        self.assertIn('url("data:image/svg+xml;base64,', result)

    def test_html_attribute_names_and_quoted_text_do_not_hide_src(self):
        result = self.embed('<img data-src="unused.png" alt="src=example.png" src="../Assets/shared%20diagram(1).svg">')
        self.assertIn('data-src="unused.png"', result)
        self.assertIn('alt="src=example.png"', result)
        self.assertIn('src="data:image/svg+xml;base64,', result)

    def test_code_examples_and_html_comments_do_not_require_assets(self):
        examples = [
            "```md\n![Example](missing.png)\n```\n",
            "    ![Example](missing.png)\n",
            "Use `![Example](missing.png)` as a template.",
            '<!-- <img src="missing.png"> -->',
        ]
        for text in examples:
            with self.subTest(text=text):
                self.assertEqual(self.embed(text), text)

    def test_remote_and_data_images_are_unchanged(self):
        for url in ("https://example.com/image.png", "data:image/png;base64,YQ=="):
            result = self.embed(f"![image]({url})")
            self.assertIn(url, result)

    def test_escaped_and_cross_paragraph_backticks_do_not_hide_images(self):
        templates = [
            r"Literal \` marker. ![diagram](URL) Another \` marker.",
            "Unmatched ` in paragraph.\n\n![diagram](URL)\n\nAnother ` marker.",
        ]
        for template in templates:
            with self.subTest(template=template):
                result = self.embed(template.replace("URL", "../Assets/shared%20diagram(1).svg"))
                self.assertIn('src="data:image/svg+xml;base64,', result)
                with self.assertRaisesRegex(ValueError, "missing asset"):
                    self.embed(template.replace("URL", "../Assets/missing.png"))

    def test_real_code_spans_with_multiline_content_and_escape_characters(self):
        examples = [
            '`example\n![diagram](missing.png)\nexample`',
            '``example ` ![diagram](missing.png) ``',
            '`escaped closing \\` ![diagram](<../Assets/shared diagram(1).svg>)',
        ]
        for text in examples[:2]:
            with self.subTest(text=text):
                self.assertEqual(self.embed(text), text)
        # Inside code, a backslash does not escape the closing delimiter.
        self.assertIn('src="data:image/svg+xml;base64,', self.embed(examples[2]))

    def test_missing_assets_name_the_module_and_resolved_path(self):
        for markdown in ('![Missing](../Assets/missing.png)', '<img src="../Assets/missing.png">',
                         '![Missing][m]\n\n[m]: ../Assets/missing.png'):
            with self.subTest(markdown=markdown), self.assertRaises(ValueError) as error:
                self.embed(markdown)
            self.assertIn(str(self.source), str(error.exception))
            self.assertIn("missing asset", str(error.exception))
            self.assertIn(str(self.assets / "missing.png"), str(error.exception))

    def test_same_filename_in_different_module_directories_is_not_confused(self):
        results = []
        for name in ("first", "second"):
            folder = self.modules / name
            folder.mkdir()
            (folder / "image.svg").write_text(name, encoding="utf-8")
            results.append(embed_markdown_assets("![diagram](image.svg)", folder / "module.md"))
        self.assertNotEqual(*results)

    def test_reference_labels_from_different_modules_cannot_collide(self):
        from markdown_it import MarkdownIt
        parts = []
        for name in ("first", "second"):
            folder = self.modules / name
            folder.mkdir()
            (folder / "image.png").write_bytes(name.encode())
            parts.append(embed_markdown_assets("![diagram][same]\n\n[same]: image.png\n", folder / "module.md"))
        tokens = MarkdownIt().parse("\n\n---\n\n".join(parts))
        urls = [child.attrGet("src") for token in tokens for child in token.children or [] if child.type == "image"]
        self.assertEqual(len(urls), 2)
        self.assertNotEqual(*urls)

    def test_raster_image_preserves_marp_background_modifiers(self):
        (self.assets / "image.png").write_bytes(b"png")
        result = self.embed('![bg contain](../Assets/image.png "Title")')
        self.assertIn('![bg contain](<data:image/png;base64,', result)
        self.assertIn(' "Title")', result)

    def test_shared_image_across_modules_is_embedded_without_source_changes(self):
        text = '---\nmarp: true\n---\n# Shared\n\n![image](<../Assets/shared diagram(1).svg>)\n'
        self.source.write_text(text, encoding="utf-8")
        second = self.modules / "second.md"
        second.write_text(text, encoding="utf-8")
        self.manifest.write_text("title: Shared\nmodules:\n  - path: Modules/module.md\n  - path: Modules/second.md\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            result = builder.build_course(self.manifest, prepare_only=True)
        combined = result.read_text(encoding="utf-8")
        self.assertEqual(combined.count("data:image/svg+xml;base64,"), 2)
        self.assertEqual(combined.count("marp: true"), 1)
        self.assertEqual(self.source.read_text(encoding="utf-8"), text)
        self.assertEqual(second.read_text(encoding="utf-8"), text)

    def test_course_defaults_and_overview(self):
        with redirect_stdout(io.StringIO()):
            path = builder.build_course(self.manifest, prepare_only=True)
        text = path.read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        self.assertEqual(metadata["theme"], "fhtw")
        self.assertTrue(metadata["paginate"])
        self.assertEqual(metadata["footer"], "Test course | FH Technikum Wien")
        self.assertLess(text.index("# Title"), text.index("# All Titles"))
        self.assertLess(text.index("# All Titles"), text.index("## Content"))
        css = path.with_suffix(".css").read_text(encoding="utf-8")
        self.assertIn("data:image/jpeg;base64,", metadata["header"])
        self.assertNotIn("/project/Theme", css)

    def test_missing_asset_prevents_renderer_and_output_creation(self):
        self.source.write_text("![Missing](../Assets/missing.png)", encoding="utf-8")
        with patch.object(builder, "create_pdf") as render, redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(builder.main([str(self.manifest)]), 1)
        render.assert_not_called()
        self.assertIn("missing asset", stderr.getvalue())
        self.assertFalse((self.root / "build").exists())

    def test_legacy_filename_manifests_still_build(self):
        self.manifest.write_text("title: Legacy\nmodules:\n  - module.md\n", encoding="utf-8")
        self.assertEqual(builder.load_manifest(self.manifest)["modules"], [self.source.resolve()])

    def test_both_renderers_receive_theme_html_and_pagination_source(self):
        markdown = builder.BASE_DIR / "build" / "course.md"
        theme = markdown.with_suffix(".css")
        output = builder.OUTPUT_DIR / "course.pdf"
        for renderer in ("local", "docker"):
            with self.subTest(renderer=renderer), patch.object(builder.subprocess, "run") as run:
                builder.create_pdf(markdown, output, theme, renderer, "custom-marp")
                command = run.call_args.args[0]
                self.assertIn("--html", command)
                self.assertIn("--theme", command)
                self.assertIn("--pdf", command)
                self.assertEqual(command[command.index("--template") + 1], "bare")
                self.assertTrue(run.call_args.kwargs["check"])

    def test_renderer_failures_return_nonzero(self):
        with patch.object(builder, "create_pdf", side_effect=subprocess.CalledProcessError(1, "marp")):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(builder.main([str(self.manifest)]), 1)


if __name__ == "__main__":
    unittest.main()
