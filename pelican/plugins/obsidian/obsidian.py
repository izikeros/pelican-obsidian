#!/usr/bin/env python
"""Plugin for Pelican to support Obsidian links, images, breadcrumbs and correcting tags."""

import logging
import os
import re
from itertools import chain
from pathlib import Path

from pelican import signals
from pelican.plugins.yaml_metadata.yaml_metadata import HEADER_RE, YAMLMetadataReader
from pelican.urlwrappers import Tag
from pelican.utils import pelican_open

__log__ = logging.getLogger(__name__)

ARTICLE_PATHS = {}
ARTICLE_TITLES = {}
FILE_PATHS = {}

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


def get_file_and_linkname(match):
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


def breadcrumb_replacement(b_match):
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
        path = ARTICLE_PATHS.get(filename)
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

    def replace_obsidian_links(self, text):
        """
        Replace Obsidian-style links with Pelican-compatible format.

        Args:
            text: The full text content

        Returns:
            str: Text with links replaced
        """

        def link_replacement(match):
            filename, linkname = get_file_and_linkname(match)
            path = ARTICLE_PATHS.get(filename)
            if path:
                # Use article title if available, otherwise use linkname
                title = ARTICLE_TITLES.get(filename, linkname)
                link_structure = f"[{title}]({{filename}}{path}{filename}.md)"
                __log__.debug(f"Replacing link {filename} with title: {title}")
            else:
                link_structure = f"{linkname}"
                __log__.debug(f"No article found for filename: {filename}")
            return link_structure

        def file_replacement(match):
            filename, linkname = get_file_and_linkname(match)
            path = FILE_PATHS.get(filename)
            if path:
                link_structure = f"![{linkname}]({{static}}{path}{filename})"
                __log__.debug(f"Replacing file link: {filename}")
            else:
                # Don't show broken image links
                link_structure = ""
                __log__.debug(f"No file found for filename: {filename}")
            return link_structure

        text = file_re.sub(file_replacement, text)
        text = link_re.sub(link_replacement, text)
        return text

    def remove_non_existing_breadcrumbs(self, text):
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
        text = self.remove_non_existing_breadcrumbs(text)
        content = self.replace_obsidian_links(text)

        return (self._md.reset().convert(content), metadata)


def populate_files_and_articles(generator):
    """
    Populate ARTICLE_PATHS, ARTICLE_TITLES, and FILE_PATHS dictionaries.

    Args:
        generator: The Pelican generator instance
    """
    global ARTICLE_PATHS
    global ARTICLE_TITLES
    global FILE_PATHS

    # Clear previous values
    ARTICLE_PATHS.clear()
    ARTICLE_TITLES.clear()
    FILE_PATHS.clear()

    base_path = Path(generator.path)
    articles = base_path.glob("**/*.md")

    # Process all markdown files
    for article in articles:
        full_path, filename_w_ext = os.path.split(article)
        filename, ext = os.path.splitext(filename_w_ext)
        path = str(full_path).replace(str(base_path), "") + "/"

        # Windows compatibility
        if os.sep == "\\":
            path = path.replace("\\", "/")

        ARTICLE_PATHS[filename] = path

        # Extract title from frontmatter
        try:
            with open(article, encoding="utf-8") as f:
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

    # Process static files
    extensions = ["png", "jpg", "jpeg", "svg", "apkg", "gif", "webp", "avif"]
    globs = [base_path.glob(f"**/*.{ext}") for ext in extensions]
    files = chain(*globs)

    for _file in files:
        full_path, filename_w_ext = os.path.split(_file)
        path = str(full_path).replace(str(base_path), "") + "/"

        # Windows compatibility
        if os.sep == "\\":
            path = path.replace("\\", "/")

        FILE_PATHS[filename_w_ext] = path

    __log__.debug("Found %d files", len(FILE_PATHS))


def modify_generator(generator):
    """
    Modify the generator to use ObsidianMarkdownReader.

    Args:
        generator: The Pelican generator instance
    """
    populate_files_and_articles(generator)
    generator.readers.readers["md"] = ObsidianMarkdownReader(generator.settings)


def modify_metadata(generator, metadata):
    """
    Modify tags to handle Obsidian-style hashtags.

    Args:
        generator: The Pelican generator instance
        metadata: Article/page metadata
    """
    for tag in metadata.get("tags", []):
        if "#" in tag.name:
            tag.name = tag.name.replace("#", "")


def register():
    """
    Register the plugin with Pelican.
    """
    # Register for articles
    signals.article_generator_context.connect(modify_metadata)
    signals.article_generator_init.connect(modify_generator)

    # Register for pages
    signals.page_generator_context.connect(modify_metadata)
    signals.page_generator_init.connect(modify_generator)
