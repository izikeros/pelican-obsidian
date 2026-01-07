#!/usr/bin/env python
"""Plugin for Pelican to support Obsidian links, images, breadcrumbs and correcting tags."""

import logging
import re
from itertools import chain
from pathlib import Path

from pelican import signals
from pelican.plugins.yaml_metadata.yaml_metadata import HEADER_RE, YAMLMetadataReader
from pelican.urlwrappers import Tag
from pelican.utils import pelican_open

__log__ = logging.getLogger(__name__)

# Type-annotated global dictionaries
ARTICLE_PATHS: dict[str, str] = {}
ARTICLE_TITLES: dict[str, str] = {}
FILE_PATHS: dict[str, str] = {}

# Case-insensitive lookup dictionaries for better Obsidian compatibility
ARTICLE_PATHS_CI: dict[str, tuple[str, str]] = (
    {}
)  # lowercase -> (original_filename, path)
FILE_PATHS_CI: dict[str, tuple[str, str]] = {}  # lowercase -> (original_filename, path)

# Default file extensions (configurable via settings)
DEFAULT_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "svg", "gif", "webp", "avif"]
DEFAULT_FILE_EXTENSIONS = ["apkg", "pdf", "doc", "docx", "txt"]

# Regex for links. The first group is the filename, the second is the linkname.
# The linkname is optional. If it is not present, the filename is used.
link = r"\[\[\s*(?P<filename>[^|\]]+)(\|\s*(?P<linkname>.+))?\]\]"
file_re = re.compile(r"!" + link)
link_re = re.compile(link)
title_re = re.compile(r"(?i)^title:\s*(.*)$", re.MULTILINE)

# Regex for breadcrumb elements (X::, Up::, Down:: prefixes)
x_element_re = re.compile(rf"(?i)X::\s*{link}")
up_element_re = re.compile(rf"(?i)Up::\s*{link}")
down_element_re = re.compile(rf"(?i)Down::\s*{link}")

# Regex for inline hashtags (e.g., #agile, #python-dev, #37-signals)
# Matches hashtags surrounded by whitespace or at start/end of line
# Does not match hashtags in code blocks or inline code (handled separately)
# Allows first character to be letter or digit (e.g., #37signals)
inline_hashtag_re = re.compile(r"(?<=\s)#([a-zA-Z0-9][a-zA-Z0-9_/-]*)(?=\s|$|[.,;:!?)])")
inline_hashtag_start_re = re.compile(
    r"^#([a-zA-Z0-9][a-zA-Z0-9_/-]*)(?=\s|$|[.,;:!?)])", re.MULTILINE
)

# Regex for code blocks and inline code (to protect from hashtag removal)
code_fence_re = re.compile(r"```[\s\S]*?```", re.MULTILINE)
inline_code_re = re.compile(r"`[^`]+`")

# Regex for Obsidian callouts
# Matches: > [!type] optional title\n> content lines (stops at empty line or non-> line)
# Uses [ \t]* instead of \s* to avoid matching across newlines for the title
callout_re = re.compile(
    r"^(?P<indent>\s*)>\s*\[!(?P<type>\w+)\](?:[ \t]*(?P<title>.+?))?[ \t]*\n"
    r"(?P<content>(?:>\s?[^\n]*\n?)*)",
    re.MULTILINE,
)

# Supported callout types
CALLOUT_TYPES = [
    "note",
    "tip",
    "warning",
    "danger",
    "info",
    "question",
    "example",
    "quote",
    "abstract",
    "success",
    "failure",
    "bug",
    "important",
    "caution",
    "attention",
]

# Map Obsidian callout types to standard admonition types
# These match the CSS classes in Pelican themes (Flex, etc.)
CALLOUT_TO_ADMONITION = {
    "note": "note",
    "info": "note",
    "tip": "tip",
    "success": "tip",
    "warning": "warning",
    "caution": "warning",
    "attention": "attention",
    "danger": "danger",
    "failure": "danger",
    "bug": "danger",
    "error": "danger",
    "important": "important",
    "question": "hint",
    "example": "note",
    "abstract": "note",
    "quote": "note",
}

"""
# Test cases for links
[[my link]]
[[ my work ]]
[[ my work | is finished ]]

# Test cases for files
![[ a file.jpg ]]
![[file.jpg]]

# Test cases for breadcrumbs
X::[[some-article]]
up::[[parent-topic]]
down::[[child-topic]]
"""


def get_file_and_linkname(match: re.Match[str]) -> tuple[str, str]:
    """
    Get the filename and linkname (visible label) from the match object.

    Examples:
        [[my link]] -> filename: my link, linkname: my link
        [[ my work | is finished ]] -> filename: my work, linkname: is finished

    Args:
        match: The match object from the regex.

    Returns:
        tuple: The filename and linkname.
    """
    group = match.groupdict()
    filename = group["filename"].strip()
    linkname = group["linkname"] if group["linkname"] else filename
    linkname = linkname.strip()
    return filename, linkname


def breadcrumb_replacement(b_match: re.Match[str]) -> str:
    """
    Handle breadcrumb elements (X::, Up::, Down::) by removing prefixes.

    If the linked article exists: remove the prefix and keep just the link
    If the linked article doesn't exist: remove the entire breadcrumb element

    Args:
        b_match: The match for the breadcrumb element

    Returns:
        str: Link without prefix if target exists, empty string if target doesn't exist
    """
    if match := link_re.search(str(b_match.group())):
        filename, _ = get_file_and_linkname(match)

        # Try exact match first, then case-insensitive
        path = ARTICLE_PATHS.get(filename)
        if not path and filename.lower() in ARTICLE_PATHS_CI:
            _, path = ARTICLE_PATHS_CI[filename.lower()]

        if not path:
            __log__.debug(
                f"Removing entire breadcrumb element (target not found): {b_match.group()}"
            )
            return ""
        else:
            # Remove prefix and keep just the link part
            __log__.debug(f"Removing breadcrumb prefix from: {b_match.group()}")
            return match.group()
    return b_match.group()


class ObsidianMarkdownReader(YAMLMetadataReader):
    """
    Custom markdown reader that converts Obsidian-style links to Pelican format.
    """

    enabled = YAMLMetadataReader.enabled

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def replace_obsidian_links(self, text: str) -> str:
        """
        Replace Obsidian-style links with Pelican-compatible format.

        Args:
            text: The full text content

        Returns:
            str: Text with links replaced
        """

        def link_replacement(match):
            filename, linkname = get_file_and_linkname(match)

            # Try exact match first, then case-insensitive
            path = ARTICLE_PATHS.get(filename)
            original_filename = filename
            if not path and filename.lower() in ARTICLE_PATHS_CI:
                original_filename, path = ARTICLE_PATHS_CI[filename.lower()]

            if path:
                # Use article title if available, otherwise use linkname
                title = ARTICLE_TITLES.get(original_filename, linkname)
                link_structure = f"[{title}]({{filename}}{path}{original_filename}.md)"
                __log__.debug(f"Replacing link {filename} with title: {title}")
            else:
                link_structure = f"{linkname}"
                __log__.debug(f"No article found for filename: {filename}")
            return link_structure

        def file_replacement(match):
            filename, linkname = get_file_and_linkname(match)

            # Try exact match first, then case-insensitive
            path = FILE_PATHS.get(filename)
            original_filename = filename
            if not path and filename.lower() in FILE_PATHS_CI:
                original_filename, path = FILE_PATHS_CI[filename.lower()]

            if path:
                link_structure = f"![{linkname}]({{static}}{path}{original_filename})"
                __log__.debug(f"Replacing file link: {filename}")
            else:
                # Don't show broken image links
                link_structure = ""
                __log__.debug(f"No file found for filename: {filename}")
            return link_structure

        text = file_re.sub(file_replacement, text)
        text = link_re.sub(link_replacement, text)
        return text

    def remove_non_existing_breadcrumbs(self, text: str) -> str:
        """
        Remove breadcrumb elements when the target article doesn't exist.

        Args:
            text: The content text

        Returns:
            str: Text with non-existing breadcrumbs removed
        """
        text = x_element_re.sub(breadcrumb_replacement, text)
        text = up_element_re.sub(breadcrumb_replacement, text)
        text = down_element_re.sub(breadcrumb_replacement, text)
        return text

    def remove_inline_hashtags(self, text: str) -> str:
        """
        Remove inline hashtags from text while preserving code blocks and inline code.

        Examples:
            "text #agile text" -> "text  text"
            "#python at start" -> " at start"
            "`#preserved`" -> "`#preserved`"
            "```python\n#comment\n```" -> preserved

        Args:
            text: The content text

        Returns:
            str: Text with inline hashtags removed
        """
        if not self.settings.get("OBSIDIAN_REMOVE_HASHTAGS", True):
            return text

        # Store code blocks and inline code with placeholders
        placeholders: list[tuple[str, str]] = []
        placeholder_counter = 0

        def store_placeholder(match: re.Match[str]) -> str:
            nonlocal placeholder_counter
            # Use unlikely string pattern instead of control characters (XML-safe)
            placeholder = f"__OBSIDIAN_CODEBLOCK_{placeholder_counter}__"
            placeholders.append((placeholder, match.group(0)))
            placeholder_counter += 1
            return placeholder

        # Protect code fences first (they may contain inline code syntax)
        text = code_fence_re.sub(store_placeholder, text)
        # Then protect inline code
        text = inline_code_re.sub(store_placeholder, text)

        # Remove hashtags - handle both mid-line and start-of-line cases
        text = inline_hashtag_re.sub("", text)
        text = inline_hashtag_start_re.sub("", text)

        # Restore code blocks and inline code
        for placeholder, original in placeholders:
            text = text.replace(placeholder, original)

        return text

    def convert_callouts(self, text: str) -> str:
        """
        Convert Obsidian callouts to HTML div blocks.

        Example input:
            > [!note] My Title
            > Some content here
            > More content

        Example output (admonition format - default):
            <div class="admonition note">
            <p class="admonition-title">My Title</p>
            <p>Some content here
            More content</p>
            </div>

        Example output (callout format - legacy):
            <div class="callout callout-note">
            <div class="callout-title">My Title</div>
            <div class="callout-content">
            Some content here
            More content
            </div>
            </div>

        Args:
            text: The content text

        Returns:
            str: Text with callouts converted to HTML
        """
        if not self.settings.get("OBSIDIAN_CALLOUTS_ENABLED", True):
            return text

        use_admonition = self.settings.get("OBSIDIAN_CALLOUTS_USE_ADMONITION", True)

        def callout_replacement(match: re.Match[str]) -> str:
            callout_type = match.group("type").lower()
            title = match.group("title")
            content = match.group("content")

            # If not a recognized callout type, return unchanged
            if callout_type not in CALLOUT_TYPES:
                return match.group(0)

            # Use provided title or capitalize the type
            display_title = title.strip() if title else callout_type.capitalize()

            # Process content - remove leading "> " from each line
            content_lines = []
            for line in content.split("\n"):
                # Remove the leading > and optional space
                stripped = re.sub(r"^\s*>\s?", "", line)
                content_lines.append(stripped)

            # Remove trailing empty lines
            while content_lines and not content_lines[-1].strip():
                content_lines.pop()

            processed_content = "\n".join(content_lines)

            if use_admonition:
                # Map to standard admonition type for theme compatibility
                admonition_type = CALLOUT_TO_ADMONITION.get(callout_type, "note")
                html = (
                    f'<div class="admonition {admonition_type}">\n'
                    f'<p class="admonition-title">{display_title}</p>\n'
                    f"<p>{processed_content}</p>\n"
                    f"</div>\n"
                )
            else:
                # Legacy callout format (requires custom CSS)
                html = (
                    f'<div class="callout callout-{callout_type}">\n'
                    f'<div class="callout-title">{display_title}</div>\n'
                    f'<div class="callout-content">\n'
                    f"{processed_content}\n"
                    f"</div>\n"
                    f"</div>\n"
                )

            __log__.debug(f"Converted callout type '{callout_type}' with title '{display_title}'")
            return html

        return callout_re.sub(callout_replacement, text)

    def _load_yaml_metadata(self, text, source_path):
        """
        Load YAML metadata and process tags.

        Args:
            text: YAML metadata text
            source_path: Path to the source file

        Returns:
            dict: Processed metadata
        """
        metadata = super()._load_yaml_metadata(text, source_path)

        # Handle comma-separated tags
        tags = metadata.get("tags", [])
        mod_tags = []
        for tag in tags:
            if "," in tag.name:
                str_tags = tag.name.split(",")
                for str_tag in str_tags:
                    url_tag = Tag(str_tag.strip(), settings=self.settings)
                    mod_tags.append(url_tag)
            else:
                mod_tags.append(tag)
        metadata["tags"] = mod_tags

        return metadata

    def read(self, source_path):
        """
        Parse content and metadata of markdown files.

        Args:
            source_path: Path to the source file

        Returns:
            tuple: (content, metadata)
        """
        with pelican_open(source_path) as text:
            m = HEADER_RE.fullmatch(text)

        if not m:
            return super().read(source_path)

        # Extract metadata first to check for draft status
        metadata = self._load_yaml_metadata(m.group("metadata"), source_path)

        # Skip Obsidian processing for draft articles
        if metadata.get("status", "").lower() == "draft":
            __log__.debug(f"Skipping Obsidian processing for draft: {source_path}")
            return (self._md.reset().convert(m.group("content")), metadata)

        # Process content for published articles
        text = m.group("content")
        text = self.remove_inline_hashtags(text)
        text = self.convert_callouts(text)
        text = self.remove_non_existing_breadcrumbs(text)
        content = self.replace_obsidian_links(text)

        return (self._md.reset().convert(content), metadata)


def populate_files_and_articles(generator) -> None:
    """
    Populate ARTICLE_PATHS, ARTICLE_TITLES, and FILE_PATHS dictionaries.

    Args:
        generator: The Pelican generator instance
    """
    global ARTICLE_PATHS
    global ARTICLE_TITLES
    global FILE_PATHS
    global ARTICLE_PATHS_CI
    global FILE_PATHS_CI

    # Clear previous values
    ARTICLE_PATHS.clear()
    ARTICLE_TITLES.clear()
    FILE_PATHS.clear()
    ARTICLE_PATHS_CI.clear()
    FILE_PATHS_CI.clear()

    base_path = Path(generator.path)

    # Error handling for missing base path
    if not base_path.exists():
        __log__.error(f"Base path does not exist: {base_path}")
        return

    if not base_path.is_dir():
        __log__.error(f"Base path is not a directory: {base_path}")
        return

    articles = base_path.glob("**/*.md")

    # Process all markdown files
    for article in articles:
        article_path = Path(article)
        filename = article_path.stem
        relative_path = article_path.parent.relative_to(base_path)
        path = "/" + str(relative_path).replace("\\", "/") + "/"

        # Normalize path separators for consistency
        if path == "/./" or path == "/./":
            path = "/"

        ARTICLE_PATHS[filename] = path
        # Store case-insensitive mapping
        ARTICLE_PATHS_CI[filename.lower()] = (filename, path)

        # Extract title from frontmatter
        try:
            with article_path.open(encoding="utf-8") as f:
                content = f.read()

                # Look for title in YAML frontmatter
                if m := HEADER_RE.fullmatch(content):
                    yaml_content = m.group("metadata")
                    title_match = title_re.search(yaml_content)
                else:
                    # Fallback to searching entire content
                    title_match = title_re.search(content)

                if title_match:
                    title = title_match.group(1).strip()
                    # Remove quotes if present
                    if (title.startswith('"') and title.endswith('"')) or (
                        title.startswith("'") and title.endswith("'")
                    ):
                        title = title[1:-1]
                else:
                    title = filename

                ARTICLE_TITLES[filename] = title
                __log__.debug(f"Article {filename} has title: {title}")

        except Exception as e:
            __log__.warning(f"Could not read title from {article}: {e}")
            ARTICLE_TITLES[filename] = filename

    __log__.debug("Found %d articles", len(ARTICLE_PATHS))

    # Process static files - get extensions from settings or use defaults
    image_extensions = generator.settings.get(
        "OBSIDIAN_IMAGE_EXTENSIONS", DEFAULT_IMAGE_EXTENSIONS
    )
    file_extensions = generator.settings.get(
        "OBSIDIAN_FILE_EXTENSIONS", DEFAULT_FILE_EXTENSIONS
    )
    extensions = image_extensions + file_extensions
    globs = [base_path.glob(f"**/*.{ext}") for ext in extensions]
    files = chain(*globs)

    for _file in files:
        file_path = Path(_file)
        filename_w_ext = file_path.name
        relative_path = file_path.parent.relative_to(base_path)
        path = "/" + str(relative_path).replace("\\", "/") + "/"

        # Normalize path separators for consistency
        if path == "/./" or path == "/./":
            path = "/"

        FILE_PATHS[filename_w_ext] = path
        # Store case-insensitive mapping
        FILE_PATHS_CI[filename_w_ext.lower()] = (filename_w_ext, path)

    # Provide helpful summary
    __log__.info(
        f"Obsidian plugin indexed: {len(ARTICLE_PATHS)} articles, "
        f"{len(FILE_PATHS)} static files from {base_path}"
    )

    # Warn about articles without explicit titles
    articles_without_titles = [
        filename for filename, title in ARTICLE_TITLES.items() if filename == title
    ]
    if articles_without_titles:
        __log__.warning(
            f"Articles without explicit titles: {', '.join(articles_without_titles[:5])}"
            f"{' and more...' if len(articles_without_titles) > 5 else ''}"
        )


def modify_generator(generator) -> None:
    """
    Modify the generator to use ObsidianMarkdownReader.

    Args:
        generator: The Pelican generator instance
    """
    populate_files_and_articles(generator)
    generator.readers.readers["md"] = ObsidianMarkdownReader(generator.settings)


def modify_metadata(generator, metadata) -> None:
    """
    Modify tags to handle Obsidian-style hashtags.

    Args:
        generator: The Pelican generator instance
        metadata: Article/page metadata
    """
    for tag in metadata.get("tags", []):
        if "#" in tag.name:
            tag.name = tag.name.replace("#", "")


def register() -> None:
    """
    Register the plugin with Pelican.
    """
    # Register for articles
    signals.article_generator_context.connect(modify_metadata)
    signals.article_generator_init.connect(modify_generator)

    # Register for pages
    signals.page_generator_context.connect(modify_metadata)
    signals.page_generator_init.connect(modify_generator)
