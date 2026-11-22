import shutil
from pathlib import Path
import argparse
import json
import re
import sys
import yaml

try:
    from Scripts.create_module import BASE_DIR, MODULES_DIR, create_filename
except ModuleNotFoundError:
    from create_module import BASE_DIR, MODULES_DIR, create_filename
IMPORT_DIR = BASE_DIR / "Import"

FENCE = re.compile(r"^(---|\.\.\.)\s*$") # line that is only "---" or "...": end of front matter


class MissingMetadataError(ValueError):
    """A required metadata field (author, tags) is missing."""

    def __init__(self, field): #self = always first paramater of a class, start method
        super().__init__(f"Metadata field '{field}' is missing: please provide it.") #super for parent (value error)
        self.field = field

def split_front_matter(text):
    """Return (front_matter_lines, body_lines). front_matter_lines is None if absent."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, lines
    for index in range(1, len(lines)):
        if FENCE.match(lines[index]):
            return lines[1:index], lines[index:]  # body starts with the closing fence
    raise ValueError("The front matter is not closed (missing second '---').")

def first_heading(lines):
    """Return the text of the first level-1 heading, or None."""
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    return None

def import_module(source_path, author=None, version="1.0", tags=None, modules_dir=MODULES_DIR):
    """import markdown file as a module"""
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"{source_path} does not exist")
    if not source.is_file():
        raise ValueError(f"{source_path} is not a file")
    if source.suffix.lower() != ".md":
        raise ValueError(f"{source_path} is not a markdown file. Only markdown files may be imported")
    try:
        text = source.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"The file is not valid UTF-8 text: {source}") from error
    text = text.removeprefix("\ufeff")  # drop an invisible byte order mark
    if not text.strip():
        raise ValueError(f"The file is empty: {source}")
    newline = "\r\n" if "\r\n" in text else "\n"
    front_lines, body_lines = split_front_matter(text)

    #read existing metadata
    existing = {}
    if front_lines is not None:
        try:
            existing = yaml.safe_load("".join(front_lines)) or {}
        except yaml.YAMLError as error:
            raise ValueError(f"The front matter is not valid YAML: {error}") from error
        if not isinstance(existing, dict):
            raise ValueError("The front matter must be a YAML mapping.")
    for key in ("title", "author", "version", "tags"):
        if key in existing and existing[key] in (None, "", []):
            raise ValueError(f"Front matter field '{key}' is empty. Fill it in or remove it.")

    #fill missing fields
    title = first_heading(body_lines) or source.stem.replace("-", " ").replace("_", " ").title()
    tag_list = [t.strip() for t in (tags or []) if t and t.strip()]
    candidates = {
        "marp": True,
        "title": title,
        "author": (author or "").strip() or None,
        "version": (version or "").strip() or "1.0",
        "tags": tag_list or None,
    }
    missing = {i: j for i, j in candidates.items() if i not in existing}
    for required in ("author", "tags"):
        if required in missing and missing[required] is None:
            raise MissingMetadataError(required)

    new_lines = "".join(
        f"{key}: {'true' if value is True else json.dumps(value, ensure_ascii=False)}{newline}"
        for key, value in missing.items()
    )

    if front_lines is None:
        content = f"---{newline}{new_lines}---{newline}{newline}{text}"
    else:
        head = "---" + newline + "".join(front_lines) + new_lines
        content = head + "".join(body_lines)

    final_title = existing.get("title", title)
    target = Path(modules_dir) / (create_filename(str(final_title)) + ".md")
    Path(modules_dir).mkdir(parents=True, exist_ok=True)
    try:
        with open(target, "xb") as file:  # "x" = fail if the file exists
            file.write(content.encode("utf-8"))
    except FileExistsError:
        raise FileExistsError(f"Module already exists: {target}") from None
    return target

def find_import_files(import_dir=IMPORT_DIR):
    """Return (markdown_files, skipped_files) directly inside import_dir."""
    import_dir = Path(import_dir)
    if not import_dir.is_dir():
        raise FileNotFoundError(f"Import folder not found: {import_dir}")
    files, skipped = [], []
    for path in sorted(import_dir.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue  # ignore sub folders (e.g. done/) and hidden files
        if path.suffix.lower() == ".md" and path.name.lower() != "readme.md":
            files.append(path)
        elif path.name.lower() != "readme.md":
            skipped.append(path)
    return files, skipped


def move_to_done(path, done_dir):
    """Move an imported file into done_dir without replacing an older file."""
    done_dir = Path(done_dir)
    done_dir.mkdir(parents=True, exist_ok=True)
    target = done_dir / path.name
    counter = 2
    while target.exists():
        target = done_dir / f"{path.stem}-{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), str(target))
    return target

def ask_on_console(field):
    """Ask the user for a missing field; returns None if nobody can answer."""
    label = "Author" if field == "author" else "Tags (comma-separated)"
    try:
        return input(f"{label}: ")
    except EOFError:
        return None

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Import markdown file as a whole module"
    )
    parser.add_argument("source", nargs="*", type=Path, help="Path to the .md file") #nargs for 0,1, n files
    parser.add_argument("--author", help="Author (needed if the file has none)")
    parser.add_argument("--version", default="1.0", help="Version if missing (default 1.0)")
    parser.add_argument("--tags", default="", help="Comma-separated tags (needed if the file has none)")
    parser.add_argument("--modules-dir", type=Path, default=MODULES_DIR)
    parser.add_argument("--import-dir", type=Path, default=IMPORT_DIR)
    args = parser.parse_args(argv)

    skipped = []
    done_dir = None
    if args.source:
        files = args.source
    else:
        try:
            files, skipped = find_import_files(args.import_dir)
        except FileNotFoundError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        done_dir = args.import_dir / "done"
        if not files:
            print(f"No Markdown files found in {args.import_dir}.")
            return 0

    ask = ask_on_console if sys.stdin.isatty() else None
    author = args.author
    tags = args.tags.split(",")
    failed = 0

    for path in files:
        while True:
            try:
                target = import_module(path, author, args.version, tags, args.modules_dir)
            except MissingMetadataError as error:
                answer = ask(error.field) if ask else None
                if not answer or not answer.strip():
                    print(f"{'FAILED':8} {path.name}  ->  {error}")
                    failed += 1
                    break
                if error.field == "author":
                    author = answer.strip()
                else:
                    tags = answer.split(",")
                continue  # same file again, now with the new value
            except (ValueError, OSError) as error:
                print(f"{'FAILED':8} {path.name}  ->  {error}")
                failed += 1
                break
            print(f"{'OK':8} {path.name}  ->  {target}")
            if done_dir is not None:
                move_to_done(path, done_dir)
            break

    for path in skipped:
        print(f"{'SKIPPED':8} {path.name}  ->  not a .md file")
    print(f"\n{len(files) - failed} imported, {failed} failed.")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main()) #to see exit code when errors occur, 1 if anything failed


