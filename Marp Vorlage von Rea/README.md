# Slide-Erstellung mit Marp

Die Angaben hier sind auf Debian-basierten Systemen getestet, sollten aber auf anderen Systemen auch funktionieren.

## Slides erstellen

### Technischer Hintergrund

* Die Slides werden in Markdown geschrieben, und mittels [Marp](https://marp.app/) gerendert.

### Setup

#### VS Code Plugin

Es gibt ein [VS Code plugin](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode), das u.a. eine Live-Vorschau bietet.

In den Settings des Plugins ist das Theme als "theme/your_theme.css" hinzuzufügen. Unbedingt auch html erlauben.

Durch das package.json reicht es, ```npm install``` zu verwenden um marp-cli zu installieren. Vulnerabilities können derweil ignoriert werden.

Manuell funktioniert die Installation so:

Es gibt ein [Marp CLI](https://www.npmjs.com/package/@marp-team/marp-cli), das mit npm installiert werden kann.

```console
npm install @marp-team/marp-cli
```

### Erstellen

Die Slides sind in `input/*.md` und sind in Markdown geschrieben: [Markdown](https://marpit.marp.app/markdown).

#### Vorspann / Preamble

Dateien beginnen mit dem Vorspann

```markdown
---
marp: true
theme: your_theme
author: <Name>
footer: <Name des Kurses> | <Studiengang>
paginate: true
---
```

#### Slides

Slides werden durch `---` voneinander getrennt. Vor und nach `---` ist eine Leerzeile.

Im ersten Slide (Titelseite) sollte man folgendes vor den Titel schreiben (damit es als Titelslide gerendert wird)

``` console
<!--
_paginate: skip
_footer: ''
_class : lead
-->
```

#### Bilder

Bilder werden eingefügt mit

``` console
![alt text](pfad/zum/bild.png)
```

Der Pfad ist relativ zum markdown file, in unserem fall ```../imgs/bildname.png```

### Markdown Lint

Es bietet sich an, einen [Markdown Linter für VSCode](https://open-vsx.org/extension/DavidAnson/vscode-markdownlint) zu verwenden.

### Rendering/Building

Um eine einzige Datei zu rendern, kann so vorgegangen werden:

```console
marp input.md -o output.pdf
```

oder, inklusive marp update

```console
npx @marp-team/marp-cli@latest input.md -o output.pdf
```

Oder man kann das VSCode-Plugin verwenden.

Um alle Slides zu bauen, bietet sich das Makefile an.

```console
make --makefile=SlidesMakefile all  # alle slides kompilieren
$ make --makefile=SlidesMakefile clean  # alle pdfs entfernen
$ make --makefile=SlidesMakefile help  # für Hilfe und andere Optionen
```

Die PDFs befinden sich dann im Ordner `output/`

### Rechtschreibung

[CSpell](https://cspell.org/) kann für Rechtschreibprüfung verwendet werden.

* Es gibt eine [extension für VS Code](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker),
* ein [deutsches Wörterbuch](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker-german), sowie
* ein [österreichisches Wörterbuch](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker-austrian-german).
