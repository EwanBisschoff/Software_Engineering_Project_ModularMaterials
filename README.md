# ModularMaterials

Create reusable Markdown learning modules, arrange them in YAML courses, and
build consistently themed Marp PDFs with shared images.

## Quick start: build the example PDF

With Docker Desktop/the Docker engine running:

```sh
docker compose run --build --rm marp
```

This builds `Courses/shared-assets-demo.yaml` and writes
`output/shared-assets-and-fhtw-design.pdf`. It demonstrates **US-3.1
(FHTW-CI-Grundtheme)** and **US-1.3 (Gemeinsame Assets)**: two modules use the
same centrally stored diagram, with a shared theme, branding, footer and page
numbers. Sources are mounted read-only; `build/` and `output/` are writable.
Generated files are ignored by Git.

Build your own course with the same Docker workflow:

```sh
docker compose run --build --rm marp Courses/example-course.yaml --renderer local
```

`local` here means Marp runs inside the container. No local Python, Node.js or
Chrome installation is needed. Use the exact directory capitalization shown
in the repository, particularly `Modules/`, `Courses/`, `Templates/` and `Theme/`.

### Local installation

Requires Python 3.12+, Node.js 20+, and Chrome/Chromium or Edge supported by Marp.
Install the Python requirements and the repository's locked Marp dependency:

```sh
python -m pip install -r requirements.txt
npm ci --prefix "Marp Vorlage von Rea"
```

Windows PowerShell:

```powershell
python Scripts/build_course.py Courses/shared-assets-demo.yaml --renderer local --marp ".\Marp Vorlage von Rea\node_modules\.bin\marp.cmd"
```

Linux/macOS:

```sh
python Scripts/build_course.py Courses/shared-assets-demo.yaml --renderer local --marp "./Marp Vorlage von Rea/node_modules/.bin/marp"
```

If `marp` is already on PATH, omit `--marp`. Alternatively, install only the
Python requirements and use the Docker renderer:

```sh
docker compose build marp
python Scripts/build_course.py Courses/shared-assets-demo.yaml
```

The default renderer uses the locally built `modularmaterials-marp` image.
Commands above run from the repository root. The script also works from another
directory when given correct script, manifest and executable paths.

## Shared images (US-1.3)

Store reusable images in `Assets/images/`. Each image path is relative to the
**module containing it**, never to the manifest or generated `build/` directory:

```markdown
![Course diagram](../Assets/images/module-reuse.svg)
```

Reference-style Markdown and HTML images also work:

```markdown
![Course diagram][diagram]

[diagram]: ../Assets/images/module-reuse.svg

<img src="../Assets/images/module-reuse.svg" alt="Course diagram" width="600">
```

Any number of modules can reference the same file. Edit that one file and
rebuild the affected courses. Paths with spaces can use `<../Assets/my image.png>`
in Markdown or URL encoding. Use forward slashes for cross-platform paths.

The builder validates local images before rendering and embeds them in the
generated Markdown/CSS. Moving modules into a combined course therefore does
not break their paths, and identical reference labels in different modules do
not select the wrong image. Original module and asset files remain unchanged.
Inline/reference images, HTML `img src`, and theme CSS `url(...)` resources are
supported. PNG/JPEG/GIF/WebP images keep Marp image modifiers. SVGs are embedded
as HTML images; use HTML `width`/`height` to size them rather than Marp background
modifiers. SVG files must be self-contained. HTML `srcset` is rejected with an
error; use one `src` per image.

For a missing image, the build exits with status 1 and reports the source module,
original reference and resolved file path. It does not invoke Marp. Images in
fenced/indented code blocks and inline code examples are not loaded. Remote
HTTP(S) URLs stay remote and require network access during rendering; the
local-file existence check does not validate remote availability. Prefer local
assets for reproducible, offline builds.

Validate images and prepare the combined Markdown/theme without starting Marp:

```sh
python Scripts/build_course.py Courses/shared-assets-demo.yaml --prepare-only
```

## Shared FHTW theme (US-3.1)

`Theme/your.css` declares the Marp theme `fhtw`. PDF builds use Marp's `bare`
template to avoid slideshow navigation/transition styles in print. All course builds select the theme and
set the course title, `paginate: true`, and the footer
`<course title> | FH Technikum Wien`. Module front matter is removed before
combining, so each module's metadata does not create extra slides or replace
course-wide metadata. The existing automatic overview slide is retained.

The theme provides a white background, the existing FHTW blue `#00689d`, dark
text, an Arial/Liberation Sans/Helvetica font stack, a reserved branding area,
a footer and page numbers on every normal slide. It reuses the repository's
supplied `Theme/images/fh_technikum_wien_bg+logo_gross.jpg`, displaying its logo
region with CSS. Theme image paths resolve relative to the CSS file and are
embedded during the build, so the theme works locally and in Docker without
hard-coded `/project/` asset paths. Existing `.columns` layouts remain supported.
The module generator's template also selects `fhtw` and pagination for previews;
register `Theme/your.css` as a custom theme in your editor if using a Marp preview.

**CI acceptance status:** implementation uses the supplied repository theme and
branding. No authoritative CI manual or recorded Requirements Engineer approval
is included in the repository. Formal acceptance for US-3.1 remains pending:
the Requirements Engineer must compare the rendered demo against the current
FHTW specifications for colors, fonts, logo clear space, footer and page numbers,
and record approval in issue #36. Do not treat this implementation as formal
approval. Update the shared CSS/assets if that review specifies different values.

## Create a module (US-1.1)

```sh
python Scripts/create_module.py
```

Or use Docker:

```sh
docker compose run --rm module-generator
```

The interactive generator asks for title, author, version (default `1.0`) and
comma-separated tags. Required metadata and at least one tag must be supplied.
It writes a new `.md` file into `Modules/` using `Templates/module_template.md`
and refuses to overwrite an existing module. Edit that file to add teaching
content and shared image references.

## Compose a course (US-1.2)

A manifest's ordered `modules` list defines the teaching order without copying
module sources. Modules can be reused in multiple courses:

```yaml
title: My course
modules:
  - id: shared-assets-demo
  - path: ../Modules/shared-assets-reuse.md
```

Save this in `Courses/my-course.yaml`. Each entry contains exactly one `id` or
`path`. An ID is a lowercase filename stem directly in `Modules/`, using letters,
digits and single hyphens. A path is relative to the manifest. Supply only
`title` and `modules`, with a non-empty title and list. Reorder the list to change
the course order. Duplicate YAML keys and missing modules are rejected.

Inspect ordered paths without building a PDF:

```sh
python Scripts/compose_course.py Courses/my-course.yaml
docker compose run --build --rm course-composer Courses/shared-assets-demo.yaml
```

`compose_course.py --modules-dir DIRECTORY` changes ID lookup. The Python
`Scripts.compose_course.load_course(path)` API returns the course title and an
ordered tuple of module paths. Existing US-2.1 filename-only manifests such as
`Courses/software-engineering.yml` remain supported by `build_course.py`;
their filenames resolve inside `Modules/`. Use path/ID entries for new courses.

## Tests

```sh
python -m unittest discover -s Tests -v
docker compose config --quiet
```

Tests cover course references, image resolution/reuse, missing-asset errors,
module metadata removal, theme selection and renderer error handling. For visual
verification, build the demo and inspect the logo, footer, page numbers and the
same diagram on both content slides. The historical `Marp Vorlage von Rea/`
sample remains in the repository; current course builds use the root `Theme/`,
`Assets/`, `build/` and `output/` directories.

## Team roles (Sprints 1-3)

- Fatma: Requirements Engineer / Tester
- Aylin: Requirements Engineer / Software Designer
- Daniela: Project Manager / Developer
- Ewan: Developer / DevOps Engineer
