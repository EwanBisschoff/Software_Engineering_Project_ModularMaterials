"""Resolve an ordered YAML course manifest without copying module content."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = BASE_DIR / "Modules"


class ManifestLoader(yaml.SafeLoader):
    """Keep safe YAML parsing while rejecting silently overwritten fields."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.constructor.ConstructorError(
                    "while constructing a manifest mapping", node.start_mark,
                    "manifest field names must be strings", key_node.start_mark,
                )
            if key in keys:
                raise yaml.constructor.ConstructorError(
                    "while constructing a manifest mapping", node.start_mark,
                    f"duplicate key: {key}", key_node.start_mark,
                )
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class Course:
    title: str
    modules: tuple[Path, ...]


def load_course(manifest_path, modules_dir=MODULES_DIR):
    """Load a course; list order is course order, and paths are references only.

    A path is relative to the manifest. An ID is the filename stem of a module
    directly inside modules_dir (the same name used by create_module.py).
    """
    manifest_path = Path(manifest_path).resolve()
    try:
        manifest = yaml.load(
            manifest_path.read_text(encoding="utf-8"), Loader=ManifestLoader
        )
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in {manifest_path}: {error}") from error

    if not isinstance(manifest, dict):
        raise ValueError("The course manifest must be a YAML mapping.")
    unknown = manifest.keys() - {"title", "modules"}
    if unknown:
        raise ValueError(f"Unknown course fields: {', '.join(map(str, unknown))}")
    title = manifest.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("The course title must be a non-empty string.")
    references = manifest.get("modules")
    if not isinstance(references, list) or not references:
        raise ValueError("The course modules must be a non-empty ordered list.")

    modules = []
    for position, reference in enumerate(references, start=1):
        label = f"Module {position}"
        if not isinstance(reference, dict) or set(reference) not in ({"path"}, {"id"}):
            raise ValueError(f"{label} must contain exactly one of 'path' or 'id'.")
        kind, value = next(iter(reference.items()))
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} {kind} must be a non-empty string.")
        if kind == "id":
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
                raise ValueError(f"{label} ID must be a lowercase filename stem, e.g. 'intro-to-python'.")
            module = Path(modules_dir) / f"{value}.md"
        else:
            module = Path(value)
            if module.is_absolute():
                raise ValueError(f"{label} path must be relative to the manifest.")
            module = manifest_path.parent / module
        module = module.resolve()
        if module.suffix.lower() != ".md":
            raise ValueError(f"{label} must reference a Markdown (.md) module: {module}")
        if not module.is_file():
            raise ValueError(f"{label} does not exist or is not a file: {module}")
        modules.append(module)

    return Course(title=title.strip(), modules=tuple(modules))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to a YAML course manifest")
    parser.add_argument(
        "--modules-dir", type=Path, default=MODULES_DIR,
        help="Directory for filename-based module IDs (default: repository Modules/)",
    )
    args = parser.parse_args(argv)
    try:
        course = load_course(args.manifest, args.modules_dir)
    except (ValueError, OSError, UnicodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Course: {course.title}")
    for position, module in enumerate(course.modules, start=1):
        print(f"{position}. {module}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
