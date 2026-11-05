from pathlib import Path
import subprocess
import sys
import yaml
import re

BASE_DIR = Path(__file__).resolve().parent.parent

MODULES_DIR = BASE_DIR / "Modules"
BUILD_DIR = BASE_DIR / "build"
OUTPUT_DIR = BASE_DIR / "output"


def load_manifest(manifest_path):
    """Read the course manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file)

    if not manifest:
        raise ValueError("Course manifest is empty.")

    if "modules" not in manifest or not manifest["modules"]:
        raise ValueError("Course manifest does not contain modules.")

    return manifest


def combine_modules(manifest):
    """Combine modules in the order defined in the manifest."""
    contents = []

    for module_name in manifest["modules"]:
        module_path = MODULES_DIR / module_name

        if not module_path.exists():
            raise FileNotFoundError(
                f"Module not found: {module_name}"
            )

        module_content = module_path.read_text(encoding="utf-8")
        contents.append(module_content)

    return "\n\n---\n\n".join(contents)


def safe_filename(title):
    """Create a safe filename from the course title."""
    name = title.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-") or "course"


def create_pdf(markdown_file, output_file):
    """Generate PDF with Marp using Docker."""

    markdown_path = markdown_file.resolve()
    output_path = output_file.resolve()

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{markdown_path.parent}:/work",
        "-v",
        f"{output_path.parent}:/output",
        "marpteam/marp-cli",
        f"/work/{markdown_path.name}",
        "--pdf",
        "--allow-local-files",
        "-o",
        f"/output/{output_path.name}"
    ]

    print("Generating PDF with Marp...")
    subprocess.run(command, check=True)


def build_course(manifest_path):
    """Build a PDF from a course manifest."""

    manifest = load_manifest(manifest_path)

    course_title = manifest.get("title", "Course")
    filename = safe_filename(course_title)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    combined_markdown = combine_modules(manifest)

    build_file = BUILD_DIR / f"{filename}.md"
    pdf_file = OUTPUT_DIR / f"{filename}.pdf"

    build_file.write_text(
        combined_markdown,
        encoding="utf-8"
    )

    print(f"Combined Markdown created: {build_file}")

    create_pdf(build_file, pdf_file)

    print(f"PDF created successfully: {pdf_file}")

    return pdf_file


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python Scripts/build_course.py "
            "courses/software-engineering.yml"
        )
        return

    manifest_path = Path(sys.argv[1])

    try:
        build_course(manifest_path)

    except (
        FileNotFoundError,
        ValueError,
        subprocess.CalledProcessError,
        OSError
    ) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()