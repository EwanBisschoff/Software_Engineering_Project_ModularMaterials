# Software_Engineering_Project_ModularMaterials

## Compose a course (US-1.2)

A course is a YAML manifest in `Courses/`. Its `modules` list defines the
teaching order and references existing Markdown files; no content is copied.
The same module can be referenced by any number of courses.

```yaml
title: Introduction to software engineering
modules:
  - path: ../Modules/introduction.md
  - id: exercises
```

Create the referenced modules first with `python Scripts/create_module.py`.
Each entry contains exactly one `path` or `id`:

- `path`: a relative path from the manifest's directory to a `.md` file.
- `id`: the filename without `.md` directly inside `Modules/`, for example
  `intro-to-python` for `Modules/intro-to-python.md`. IDs use lowercase letters,
  digits and single hyphens, matching the module generator's filenames.

Use a non-empty `title` and at least one module. Reorder the list to change the
course order. Editing a shared module updates the content referenced by all
courses. YAML manifests contain only `title` and `modules` fields.

Install the Python dependency and validate/resolve a manifest:

```sh
python -m pip install -r requirements.txt
python Scripts/compose_course.py Courses/example-course.yaml
python Scripts/compose_course.py Courses/example-reuse.yaml
```

The command prints the course title and resolved module paths in teaching
order. Invalid YAML, duplicate mapping keys, invalid references and missing files produce an error and
a non-zero exit code. It does not merge or render slides. In Python,
`Scripts.compose_course.load_course(path)` returns a `Course` with `title` and
an ordered `modules` tuple of paths. Use `--modules-dir DIRECTORY` to resolve
IDs against a different module directory; path references are still relative
to the manifest. Commands work from any working directory when the script and
manifest arguments point to the correct files.

Alternatively, use Docker (no local Python installation required):

```sh
docker compose run --build --rm course-composer Courses/example-course.yaml
```

The `Courses/` and `Modules/` directories are mounted read-only. Both checked-in
examples reference the existing placeholder module to demonstrate reuse.

Run the tests with `python -m unittest discover -s tests -v`.

Roles:

Sprint 1-3:
Fatma: Requirements Engineer / Tester
Aylin: Requirements Engineer / Software Designer
Daniela: Projektmanager / developer
Ewan: developer / devops engineer


# Startup Linux:
systemctl --user start docker-desktop
docker compose up
docker compose run --rm module-generator

___RUN Script create_module.py:
python3 Scripts/create_module.py

___create_module should ask in the console:

    python3 Scripts/create_module.py
    === Create a New Learning Module ===
    Module title: 
    Author: 
    Version [1.0]: 
    Tags (comma-separated): 

    If Error: Title, author and version are required.


# Startup Windows in Powershell:
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker compose up

Run module generator (in a separate terminal)
docker compose run --rm module-generator

____RUN Script create_module.py:

python Scripts/create_module.py 
ODER
py Scripts/create_module.py

____create_module should ask in the console:

    === Create a New Learning Module ===
    Module title: 
    Author: 
    Version [1.0]: 
    Tags (comma-separated): 

    If Error: Title, author and version are required.

