# Author Guide

This guide explains how to use ModularMaterials to:

1. Create a reusable Markdown learning module.
2. Import an existing Markdown file as a module.
3. Combine modules into a course.
4. Check the course.
5. Create and open a PDF.

No programming experience is required. Run the commands in a terminal opened in the project folder.

## 1. Before you begin

### Required software

Use Docker, if possible. Docker provides the required Python and Marp software without installing it separately.

You need:

- Docker Desktop on Windows.
- Docker Engine and Docker Compose on Linux.
- Git to download updates.
- VS Code or another text editor.

The project can also be used without Docker if Python 3.12+, Node.js 20+, and Chrome or Chromium are installed, but Docker is the simplest option.

## 2. Download or open the project

### Get the project for the first time

```sh
git clone https://github.com/EwanBisschoff/Software_Engineering_Project_ModularMaterials.git
cd Software_Engineering_Project_ModularMaterials
```

### Open an existing copy

Open the `Software_Engineering_Project_ModularMaterials` folder in VS Code. Open a terminal with:

- **Terminal → New Terminal** in VS Code.
- `PowerShell` or `Terminal` outside VS Code.

Change to the project folder and confirm that `docker-compose.yml` is present:

```sh
ls
```

Windows PowerShell:

```powershell
Get-ChildItem
```

### Update an existing copy

Before starting work, retrieve the latest project changes:

```sh
git pull
```

Do not start a build while Docker reports that it is stopped or not running.

### Start Docker

Windows:

1. Open Docker Desktop.
2. Wait until Docker displays **Engine running**.

Linux:

```sh
systemctl --user start docker-desktop
```

Docker Desktop must be running. If Docker requires administrator permission, ask the responsible technical team member for help.

### Build the Docker images

This first build can take several minutes:

```sh
docker compose build
```

The Docker images are normally not rebuilt after every small text change.

## 3. Understand the project folders

- `Modules/` contains finished learning modules.
- `Courses/` contains YAML course manifests.
- `Assets/images/` contains shared images.
- `Theme/` contains the shared FHTW theme.
- `Templates/` contains the template used to create new modules.
- `Import/` contains existing Markdown files waiting to be imported.
- `build/` contains generated combined Markdown and CSS files.
- `output/` contains generated PDF files.
- `Scripts/` contains the project scripts.
- `Tests/` contains automated tests.

Folder names are case-sensitive on Linux. Always use `Modules`, `Courses`, `Templates`, `Assets`, `Theme`, `Scripts`, `Tests`, `build`, and `output` with the spelling shown here.

## 4. Create a new module

A new module is a Markdown file with metadata at the top.

Start the module generator:

```sh
docker compose run --build --rm module-generator
```

Enter the requested information:

- **Module title:** A clear title, for example `Introduction to Python`.
- **Author:** The author or lecturing team.
- **Version [1.0]:** Press Enter for `1.0`, or enter another version.
- **Tags:** Keywords separated by commas, for example `Python, programming, fundamentals`.

Example:

```text
=== Create a New Learning Module ===
Module title: Introduction to Python
Author: Maria Muster
Version [1.0]: 1.0
Tags (comma-separated): Python, programming, fundamentals
```

The generator creates a file in `Modules/`, for example:

```text
Modules/introduction-to-python.md
```

The title determines the filename. The filename is lowercase and uses hyphens instead of spaces.

The generator requires:

- a title,
- an author,
- a version, and
- at least one tag.

It will not overwrite an existing module. Use a different title or rename the existing module before trying again.

You can also run the generator locally when Docker is not used:

Linux:

```sh
python3 Scripts/create_module.py
```

Windows PowerShell:

```powershell
python Scripts/create_module.py
```

or:

```powershell
py Scripts/create_module.py
```

## 5. Edit a module

Open the generated Markdown file in VS Code or another text editor.

A module begins with metadata in front matter:

```yaml
---
marp: true
theme: fhtw
paginate: true
title: Introduction to Python
author: Maria Muster
version: 1.0
tags: [Python, programming, fundamentals]
---
```

Do not remove `---` around the metadata.

The module content can use normal Markdown:

```markdown
# Introduction to Python

## Learning Objectives

- Understand variables.
- Use basic control structures.

## Main Content

Write the teaching content here.

- A list item
- Another list item
```

Each horizontal separator starts a new slide:

```markdown
---

## New Slide

Add the content for this slide.
```

Save the file with **Ctrl+S**.

## 6. Import an existing Markdown module

Use this option to convert an existing Markdown file into a project module.

### Prepare the file

1. Copy the Markdown file into `Import/`.
2. Only `.md` files are imported.
3. Add a descriptive filename. It will be used to create the module ID if no title is available.

Create the `Import/` folder if it does not exist:

```sh
mkdir -p Import
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force Import
```

Then copy the Markdown file into `Import/`.

### Run the importer

With Docker:

```sh
docker compose run --build --rm module-importer
```

The importer searches the `Import/` folder for Markdown files. For every file, it:

- reads the existing front matter,
- keeps existing title, author, version, and tags values,
- asks for missing required author or tags information,
- adds Marp and module metadata,
- creates a module in `Modules/`, and
- moves successfully imported files to `Import/done/`.

Files containing an incomplete or invalid front matter are not imported safely.

The importer can also process one specified file locally:

Linux:

```sh
python3 Scripts/import_module.py Import/example.md
```

Windows:

```powershell
python Scripts/import_module.py Import\example.md
```

To provide missing metadata directly:

```sh
python3 Scripts/import_module.py Import/example.md --author "Maria Muster" --tags "Python, fundamentals"
```

The existing module is not overwritten. A message is shown if the generated module already exists.

## 7. Add shared images

Store reusable images in `Assets/images/`.

For a module in `Modules/`, reference an image with:

```markdown
![Description](../Assets/images/my-image.png)
```

For a filename containing spaces:

```markdown
![Description](<../Assets/images/my image.png>)
```

Supported formats include PNG, JPEG, GIF, WebP, and SVG.

Rules:

- Use forward slashes in image paths.
- Store one reusable copy instead of duplicating the image.
- Do not place images in generated `build/` or `output/` folders.
- Include the correct filename and extension.
- Local image references are checked before PDF generation.

If an image is missing, the build stops and reports:

- the module containing the image,
- the original image reference, and
- the expected file path.

## 8. Create a course

A course is a YAML file in `Courses/`. It references modules but does not copy their content.

Create a file named `Courses/my-course.yaml`.

### Windows PowerShell

```powershell
New-Item Courses\my-course.yaml
```

### Linux

```sh
nano Courses/my-course.yaml
```

Add a title and an ordered module list:

```yaml
title: My Course
modules:
  - id: introduction-to-python
  - id: advanced-python-topics
```

The module entries determine the order of the course.

### Reference a module by ID

Use the module filename without `.md`:

```yaml
- id: introduction-to-python
```

IDs:

- contain only lowercase letters and digits,
- may contain single hyphens,
- refer directly to files in `Modules/`,
- must match the module filename.

Valid ID examples:

```text
introduction-to-python
python-exercise-2
software-engineering
```

### Reference a module by path

A path is relative to the course manifest:

```yaml
title: My Course
modules:
  - path: ../Modules/introduction-to-python.md
```

Path references are useful for modules outside the standard `Modules/` lookup directory. For new courses, ID references are simpler.

A manifest must contain:

- only `title` and `modules`,
- a non-empty title,
- at least one module, and
- exactly one `id` or `path` in every module entry.

Duplicate YAML keys are rejected.

## 9. Check a course

Checking a course does not create a PDF:

```sh
docker compose run --build --rm course-composer Courses/my-course.yaml
```

A successful check prints:

- the course title, and
- every module path in teaching order.

It reports missing modules, invalid YAML, duplicate keys, invalid IDs, and invalid paths.

Local Python alternative:

```sh
python3 Scripts/compose_course.py Courses/my-course.yaml
```

Windows:

```powershell
python Scripts/compose_course.py Courses\my-course.yaml
```

## 10. Validate assets before creating a PDF

This prepares the Markdown and theme without starting Marp:

```sh
python3 Scripts/build_course.py Courses/my-course.yaml --prepare-only
```

It checks local images and creates:

- `build/my-course.md`
- `build/my-course.css`

Use this mode to find missing assets before rendering.

No PDF is created in prepare-only mode.

## 11. Create a PDF

The simplest Docker build is:

```sh
docker compose run --build --rm marp Courses/my-course.yaml --renderer local
```

The Docker service mounts the project folders and uses the Marp installation inside the container.

The PDF is saved in:

```text
output/my-course.pdf
```

The course title is used to generate the filename. For example, `My Course` becomes `my-course.pdf`.

### Build with local Python and Node.js instead of Docker

Linux or macOS:

```sh
python3 Scripts/build_course.py Courses/my-course.yaml --renderer local --marp "./Marp Vorlage von Rea/node_modules/.bin/marp"
```

Windows PowerShell:

```powershell
python Scripts/build_course.py Courses\my-course.yaml --renderer local --marp ".\Marp Vorlage von Rea\node_modules\.bin\marp.cmd"
```

Do not specify `--renderer local` unless the local Marp executable is installed.

### Build the example course

```sh
docker compose run --build --rm marp
```

The example PDF is written to:

```text
output/shared-assets-and-fhtw-design.pdf
```

## 12. Update the project

Retrieve new changes and update Docker images if the project files changed:

```sh
git pull
docker compose build
```

Do not use `git reset --hard` unless all local work can be discarded.

## 13. Run tests

Test the project after changes to scripts or manifests:

```sh
python3 -m unittest discover -s Tests -v
```

Validate Docker configuration:

```sh
docker compose config --quiet
```

Windows can use `python` or `py` instead of `python3`.

## 14. Troubleshooting

### Docker is not running

Start Docker Desktop on Windows or Docker Engine/Docker Desktop on Linux, then retry the command.

### Permission denied on Linux

Temporary workaround:

```sh
sudo docker compose run --build --rm module-generator
```

For regular use, configure Docker for the current Linux user according to the Docker documentation.

### Module or course not found

Check:

1. The terminal is in the repository root.
2. The filename is spelled correctly.
3. Module files are in `Modules/`.
4. Course files are in `Courses/`.
5. Module filenames end in `.md`.
6. Course filenames end in `.yaml`.
7. Linux uses exact capitalization.

### A module already exists

The generator and importer do not overwrite existing modules. Rename or edit the existing file instead.

### A PDF is not created

1. Check the course manifest.
2. Check every module ID and path.
3. Check all image paths.
4. Run prepare-only mode.
5. Run the PDF command again.

### Docker Compose reports a missing `Import` folder

Create it:

```sh
mkdir -p Import
```

Then copy a Markdown file into `Import/` before running the importer.

### The build reports missing front matter

The first and closing lines must be exactly `---`. Required title, author, version, and tags should be present.

## 15. Quick workflows

### Create a module and PDF

```sh
docker compose run --build --rm module-generator
# Edit the generated file in Modules/

# Create Courses/my-course.yaml

docker compose run --build --rm course-composer Courses/my-course.yaml
docker compose run --build --rm marp Courses/my-course.yaml --renderer local
```

### Import an existing module and PDF

```sh
mkdir -p Import
# Copy the existing Markdown file into Import/

docker compose run --build --rm module-importer
docker compose run --build --rm course-composer Courses/my-course.yaml
docker compose run --build --rm marp Courses/my-course.yaml --renderer local
```

Open the generated PDF in `output/`.
