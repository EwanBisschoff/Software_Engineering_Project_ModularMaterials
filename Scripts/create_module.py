from pathlib import Path                                        # uses pathing for Windows/Linux/Mac (Alternative import os)
from string import Template                                     # allows for placeholders like "author"
import json                                                     # for reading and creating json and YAML
import re                                                       # regular expressions - for handling of sonderzeichen etc.
import unicodedata                                              # same as re for unicode
import uuid                                                     # UUID generator for module names

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATE_FILE = BASE_DIR / "Templates" / "module_template.md"   #path to template 
MODULES_DIR = BASE_DIR / "Modules"                              #path to store created modules

def create_filename(title):                                     #FUNKTION FILENAME
    """Convert a module title into a safe filename."""          # drei " für Docstring für help(create_title)
    text = unicodedata.normalize("NFKD", title)
    text = text.replace("ß", "ss")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)

    return text.strip("-") or f"module-{uuid.uuid4().hex[:12]}" # names module with UUID if no name was given 

def create_module(title, author, version, tags):                #FUNKTION CREATE MODULE
    """Generate a Markdown module using the template."""

    if not all([title.strip(), author.strip(), version.strip()]):
        raise ValueError(
            "Title, author and version are required."
        )

    if not tags:
        raise ValueError("At least one tag is required.")

    template_text = TEMPLATE_FILE.read_text(                    # Read the Markdown template
        encoding="utf-8"
    )  

    print(f"Template path: {TEMPLATE_FILE}")                    # DEBUG: Check which template is being read
    print(f"Template length: {len(template_text)}")

    
    if not template_text.strip():                               # Prevent creating modules from an empty template
        raise ValueError("The module template is empty.")
    
    template = Template(template_text)

  
    content = template.substitute(                              # Replace placeholders with metadata, remove ascii 
        title=json.dumps(title, ensure_ascii=False),
        author=json.dumps(author, ensure_ascii=False),
        version=json.dumps(version, ensure_ascii=False),
        tags=json.dumps(tags, ensure_ascii=False),
        heading=title
    )

    print(f"Generated content length: {len(content)}")           # DEBUG: Check the generated Markdown content
    print(f"Content preview: {repr(content[:150])}")

    MODULES_DIR.mkdir(parents=True, exist_ok=True)              # Create the module directory if necessary

    filename = create_filename(title) + ".md"                   # name from FUNKT create_filename

    output_file = MODULES_DIR / filename

    if output_file.exists():                                    # Prevent overwriting existing modules
        raise FileExistsError(
            f"Module already exists: {output_file}"
        )

    output_file.write_text(content, encoding="utf-8")           # Save the generated Markdown file

    return output_file


def main():                                                     # FUNKTION MAIN 
    print("=== Create a New Learning Module ===")

    title = input("Module title: ").strip()                     # asks for meta data currently from console
    author = input("Author: ").strip()
    version = input("Version [1.0]: ").strip() or "1.0"

    tags_input = input("Tags (comma-separated): ")              # asks for TAGS (like history, maths, geography, etc.)
    tags = []

    for tag in tags_input.split(","):                           # addes the TAGS to modules
        cleaned_tag = tag.strip()

        if cleaned_tag:
            tags.append(cleaned_tag)



    try:
        output_file = create_module(                                            # uses FUNKT create_module
            title, author, version, tags
        )
        print(f"\nModule created successfully: {output_file}")

    except (ValueError, FileExistsError, OSError, KeyError) as error:           # error handling
        print(f"\nError: {error}")

# The following is a common Python pattern that ensures main() only runs when this
# script is executed directly (e.g. python scripts/create_module.py).
# When the file is imported into another script, main() is not executed.
# This allows us to import and test functions like create_module()
# without triggering interactive user input.
if __name__ == "__main__":
    main()

