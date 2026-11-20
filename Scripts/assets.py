"""Embed local images before modules move into the build directory."""

import base64
import html
from html.parser import HTMLParser
import mimetypes
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.rules_inline import backtick, image as parse_image
from markdown_it.rules_inline.state_inline import StateInline


def embed_asset(url, source):
    """Resolve a module/theme-relative image and return a portable data URI."""
    url = html.unescape(url)
    parts = urlsplit(url)
    if parts.scheme in {"http", "https", "data"}:
        return url
    if parts.scheme or parts.netloc or Path(unquote(parts.path)).is_absolute():
        raise ValueError(f"{source}: asset must use a relative path: {url}")
    asset = (Path(source).parent / unquote(parts.path)).resolve()
    if not parts.path or not asset.is_file():
        raise ValueError(f"{source}: missing asset '{url}' (resolved to {asset})")
    mime = mimetypes.guess_type(asset.name)[0]
    if not mime or not mime.startswith("image/"):
        raise ValueError(f"{source}: asset is not a supported image: {url}")
    encoded = base64.b64encode(asset.read_bytes()).decode("ascii")
    fragment = f"#{parts.fragment}" if parts.fragment else ""
    return f"data:{mime};base64,{encoded}{fragment}"


def embed_css_assets(css, source):
    def replace(match):
        url = match.group(2).strip()
        return f'url("{embed_asset(url, source)}")'

    return re.sub(r"url\(\s*(['\"]?)(.*?)\1\s*\)", replace, css)


def embed_markdown_assets(markdown, source):
    """Support inline/reference Markdown images and HTML img src attributes.

    Code examples are kept verbatim. Remote images remain remote and therefore
    need a network connection when rendered. Local images are embedded once per
    reference so modules with identical relative filenames remain independent.
    """
    parser = MarkdownIt("commonmark", {"html": True, "store_labels": True})
    environment = {}
    tokens = parser.parse(markdown, environment)
    lines = markdown.splitlines(keepends=True)
    protected = []
    for token in tokens:
        if token.type in {"fence", "code_block"} and token.map:
            start, end = token.map
            protected.append((sum(map(len, lines[:start])), sum(map(len, lines[:end]))))
    # Reparse each inline block's original source to retain document offsets.
    # Markdown's escape/backtick rules decide which spans are actually code;
    # delimiters cannot pair across separate paragraphs or other block types.
    code_parser = MarkdownIt("commonmark", {"html": True})
    for token in tokens:
        if token.type != "inline" or not token.map:
            continue
        first_line, last_line = token.map
        offset = sum(map(len, lines[:first_line]))
        segment = "".join(lines[first_line:last_line])

        def protect_backticks(state, silent):
            start = state.pos
            count = len(state.tokens)
            matched = backtick(state, silent)
            if (not silent and state.src is segment and len(state.tokens) > count
                    and state.tokens[-1].type == "code_inline"):
                protected.append((offset + start, offset + state.pos))
            return matched

        code_parser.inline.ruler.at("backticks", protect_backticks)
        code_parser.inline.parse(segment, code_parser, environment, [])

    def is_protected(position):
        return any(start <= position < end for start, end in protected)

    image_urls = set()
    for token in tokens:
        for child in token.children or []:
            if child.type == "image":
                image_urls.add(child.attrGet("src"))

    edits = []
    # Use Markdown's own image rule for inline, reference and shortcut forms.
    # Expand references here so labels reused by other modules cannot collide.
    for match in re.finditer(r"!\[", markdown):
        if is_protected(match.start()):
            continue
        prefix = markdown[:match.start()]
        if (len(prefix) - len(prefix.rstrip("\\"))) % 2:
            continue
        state = StateInline(markdown, parser, environment, [])
        state.pos = match.start()
        if not parse_image(state, False):
            continue
        token = state.tokens[-1]
        original_url = token.attrGet("src")
        if original_url not in image_urls:
            continue
        url = embed_asset(original_url, source)
        if url == original_url and "label" not in token.meta:
            continue
        title = token.attrGet("title")
        if url.startswith("data:image/svg+xml"):
            # CommonMark disallows SVG data URLs in Markdown destinations;
            # HTML images work with Marp's explicit --html build option.
            title_attribute = f' title="{html.escape(title, quote=True)}"' if title else ""
            replacement = f'<span><img src="{url}" alt="{html.escape(token.content, quote=True)}"{title_attribute}></span>'
        else:
            title_suffix = ' "' + title.replace('"', '\\"') + '"' if title else ""
            replacement = f'![{token.content}](<{url}>{title_suffix})'
        edits.append((match.start(), state.pos, replacement))

    tags = []

    class ImageTags(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag.lower() == "img":
                line, column = self.getpos()
                start = sum(map(len, lines[:line - 1])) + column
                tags.append((start, self.get_starttag_text(), attrs))

        handle_startendtag = handle_starttag

    ImageTags(convert_charrefs=True).feed(markdown)
    for start, tag, attrs in tags:
        if is_protected(start):
            continue
        if any(name == "srcset" for name, _ in attrs):
            raise ValueError(f"{source}: img srcset is unsupported; use a single src image")
        if any(name == "src" for name, _ in attrs):
            rewritten = []
            for name, value in attrs:
                if name == "src":
                    value = embed_asset(value or "", source)
                rewritten.append(name if value is None else f'{name}="{html.escape(value, quote=True)}"')
            edits.append((start, start + len(tag), "<img " + " ".join(rewritten) + ">"))

    for start, end, replacement in sorted(edits, reverse=True):
        markdown = markdown[:start] + replacement + markdown[end:]
    return markdown
