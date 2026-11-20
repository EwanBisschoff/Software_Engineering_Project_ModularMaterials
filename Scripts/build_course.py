"""Build portable course slides with the shared FHTW theme and images."""

import argparse
from pathlib import Path
import re
import subprocess
import sys

import yaml

if __package__:
    from .assets import embed_asset, embed_css_assets, embed_markdown_assets
    from .compose_course import ManifestLoader, load_course
else:
    from assets import embed_asset, embed_css_assets, embed_markdown_assets
    from compose_course import ManifestLoader, load_course


BASE_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = BASE_DIR / "Modules"
BUILD_DIR = BASE_DIR / "build"
OUTPUT_DIR = BASE_DIR / "output"
THEME_FILE = BASE_DIR / "Theme" / "your.css"


def load_manifest(manifest_path):
    """Accept canonical path/ID manifests and the US-2.1 filename-list format."""
    manifest_path = Path(manifest_path).resolve()
    manifest = yaml.load(manifest_path.read_text(encoding="utf-8"), Loader=ManifestLoader)
    if not isinstance(manifest, dict):
        raise ValueError("The course manifest must be a YAML mapping.")
    references = manifest.get("modules")
    if isinstance(references, list) and references and all(isinstance(ref, str) for ref in references):
        # Preserve the existing builder's Modules/-relative filename convention.
        if set(manifest) != {"title", "modules"} or not isinstance(manifest["title"], str) or not manifest["title"].strip():
            raise ValueError("A course needs a title and modules list only.")
        modules = []
        for ref in references:
            module = (MODULES_DIR / ref).resolve()
            if not module.is_relative_to(MODULES_DIR.resolve()) or module.suffix.lower() != ".md" or not module.is_file():
                raise ValueError(f"Invalid or missing module: {ref}")
            modules.append(module)
        return {"title": manifest["title"].strip(), "modules": modules}
    course = load_course(manifest_path)
    return {"title": course.title, "modules": list(course.modules)}


def module_body(text, source):
    """Remove per-module metadata so it cannot become slides in a combined deck."""
    if text.startswith("---\n"):
        match = re.match(r"\A---\n.*?\n---(?:\n|$)", text, re.DOTALL)
        if not match:
            raise ValueError(f"{source}: unterminated YAML front matter")
        text = text[match.end():]
    return text.strip()


def combine_modules(manifest):
    contents = []
    for module_path in manifest["modules"]:
        module_path = Path(module_path)
        body = module_body(module_path.read_text(encoding="utf-8-sig"), module_path)
        contents.append(embed_markdown_assets(body, module_path))
    return "\n\n---\n\n".join(contents)


def safe_filename(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-") or "course"


def create_pdf(markdown_file, output_file, theme_file, renderer="docker", marp="marp"):
    """Run the same themed build through Docker or an installed Marp CLI."""
    # Exclude slideshow navigation/transition styles from printable slides.
    options = ["--pdf", "--html", "--template", "bare", "--allow-local-files", "--theme"]
    if renderer == "docker":
        def project_path(path):
            return "/project/" + path.resolve().relative_to(BASE_DIR).as_posix()
        command = [
            "docker", "run", "--rm", "-v", f"{BASE_DIR}:/project:ro",
            "-v", f"{output_file.parent.resolve()}:/output",
            "modularmaterials-marp", project_path(markdown_file),
            *options, project_path(theme_file), "-o", f"/output/{output_file.name}",
        ]
    else:
        command = [marp, str(markdown_file.resolve()), *options,
                   str(theme_file.resolve()), "-o", str(output_file.resolve())]
    subprocess.run(command, check=True)


def build_course(manifest_path, renderer="docker", marp="marp", prepare_only=False):
    manifest = load_manifest(manifest_path)
    combined = combine_modules(manifest)
    # Resolve theme resources before invoking a renderer, just like module images.
    theme = embed_css_assets(THEME_FILE.read_text(encoding="utf-8"), THEME_FILE)
    logo = embed_asset("images/fh_technikum_wien_bg+logo_gross.jpg", THEME_FILE)
    headings = list(dict.fromkeys(re.findall(r"^## (.+)$", combined, re.MULTILINE)))
    if headings:
        overview = "# All Titles\n\n" + "\n".join(f"- {heading}" for heading in headings)
        parts = re.split(r"^---\s*$", combined, maxsplit=1, flags=re.MULTILINE)
        if len(parts) == 2:
            combined = parts[0] + "\n\n---\n\n" + overview + "\n\n---\n\n" + parts[1]
    metadata = yaml.safe_dump({
        "marp": True, "theme": "fhtw", "paginate": True,
        "title": manifest["title"], "footer": f'{manifest["title"]} | FH Technikum Wien',
        "header": f'![FH Technikum Wien]({logo})',
    }, allow_unicode=True, sort_keys=False)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = safe_filename(manifest["title"])
    build_file = BUILD_DIR / f"{filename}.md"
    theme_file = BUILD_DIR / f"{filename}.css"
    pdf_file = OUTPUT_DIR / f"{filename}.pdf"
    build_file.write_text(f"---\n{metadata}---\n\n{combined}\n", encoding="utf-8")
    theme_file.write_text(theme, encoding="utf-8")
    print(f"Prepared themed Markdown: {build_file}")
    if not prepare_only:
        create_pdf(build_file, pdf_file, theme_file, renderer, marp)
        print(f"PDF created successfully: {pdf_file}")
    return build_file if prepare_only else pdf_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--renderer", choices=["docker", "local"], default="docker")
    parser.add_argument("--marp", default="marp", help="Local Marp executable path")
    parser.add_argument("--prepare-only", action="store_true", help="Validate assets and write portable Markdown/CSS without rendering")
    args = parser.parse_args(argv)
    try:
        build_course(args.manifest, args.renderer, args.marp, args.prepare_only)
    except (ValueError, OSError, UnicodeError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
