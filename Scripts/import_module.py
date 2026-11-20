from pathlib import Path
import argparse
import json
import re
import sys
import yaml

try:
    from Scripts.create_module import MODULES_DIR, create_filename
except ModuleNotFoundError:
    from create_module import MODULES_DIR, create_filename

FENCE = re.compile(r"^(---|\.\.\.)\s*$") # line that is only "---" or "...": end of front matter
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
    if source.suffix.lower != ".md":
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
            raise ValueError(f"Metadata field '{required}' is missing: please provide it.")

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
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Import markdown file as a whole module"
    )
    parser.add_argument("source", type=Path, help="Path to the .md file")
    parser.add_argument("--author", help="Author (needed if the file has none)")
    parser.add_argument("--version", default="1.0", help="Version if missing (default 1.0)")
    parser.add_argument("--tags", default="", help="Comma-separated tags (needed if the file has none)")
    parser.add_argument("--modules-dir", type=Path, default=MODULES_DIR)
    args = parser.parse_args(argv)
    try:
        target = import_module(args.source, args.author, args.version,
                               args.tags.split(","), args.modules_dir)
    except (ValueError, OSError) as error:  # FileNotFoundError/FileExistsError are OSErrors
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Module imported successfully: {target}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) #to see exit code when errors occur
