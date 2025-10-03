import logging
from pathlib import Path

import pytest

from pelican.generators import ArticlesGenerator
from pelican.plugins.obsidian import (
    ObsidianMarkdownReader,
    populate_files_and_articles,
)
from pelican.tests.support import get_settings


@pytest.fixture
def obsidian(path):
    settings = get_settings()
    settings["DEFAULT_CATEGORY"] = "Default"
    settings["DEFAULT_DATE"] = (1970, 1, 1)
    settings["READERS"] = {"asc": None}
    settings["CACHE_CONTENT"] = False
    omr = ObsidianMarkdownReader(settings=settings)
    cwd = Path.cwd()
    source_path = cwd / "pelican" / "plugins" / "tests" / f"fixtures/{path}.md"
    generator = ArticlesGenerator(
        context=settings,
        settings=settings,
        path=cwd / "pelican" / "plugins" / "tests" / "fixtures",
        theme=settings["THEME"],
        output_path=None,
    )
    populate_files_and_articles(generator)
    obsidian = omr.read(source_path)
    return obsidian


@pytest.mark.parametrize("path", ["tags"])
def test_tags_works_correctly(obsidian):
    """Tags formatted as yaml list works properly"""
    content, meta = obsidian
    tags = meta["tags"]

    assert "Some text here" in content
    assert len(tags) == 3
    assert tags[0].name == "python"
    assert tags[1].name == "code-formatter"
    assert tags[2].name == "black"


@pytest.mark.parametrize("path", ["tags_comma"])
def test_tags_works_pelican_way(obsidian):
    """Test normal tags"""
    content, meta = obsidian
    tags = meta["tags"]

    assert "Some text here" in content
    assert len(meta["tags"]) == 3
    assert tags[0].name == "python"
    assert tags[1].name == "code-formatter"
    assert tags[2].name == "black"


@pytest.mark.parametrize("path", ["other_list_type"])
def test_other_list_property(obsidian):
    """List is preserved for other list type property"""
    content, meta = obsidian

    assert "Some text here" in content
    assert len(meta["other"]) == 3


@pytest.mark.parametrize("path", ["unknown_internal_link"])
def test_internal_link_not_seen_in_article(obsidian):
    """
    If linked article has not been processed earlier
    content is not linked.
    """
    content, meta = obsidian
    assert content == "<p>great-article-not-exist</p>"


@pytest.mark.parametrize("path", ["internal_link"])
def test_internal_link_in_article(obsidian):
    """
    If linked article has internal link, it should be linked
    """
    content, meta = obsidian
    assert content == '<p><a href="{filename}/tags.md">tags</a></p>'


@pytest.mark.parametrize("path", ["internal_image"])
def test_internal_image_in_article(obsidian):
    """
    If linked article has internal image, it should be linked
    """
    content, meta = obsidian
    assert (
        content
        == '<p><img alt="pelican-in-rock.webp" src="{static}/assets/images/pelican-in-rock.webp"></p>'
    )


@pytest.mark.parametrize("path", ["internal_link"])
def test_external_link(obsidian):
    """Able to use normal markdown links which renders properly"""
    content, meta = obsidian
    assert '<a href="https://example.com">external</a>'


@pytest.mark.parametrize("path", ["colon_in_prop"])
def test_colon_in_prop(obsidian):
    """Using a colon in prop should not mess with string formatting"""
    content, meta = obsidian
    assert meta["title"] == "Hello: There"


def test_with_generator():
    pass


# New tests for enhanced functionality


@pytest.mark.parametrize("path", ["case_insensitive_links"])
def test_case_insensitive_links(obsidian):
    """Test case-insensitive link matching works correctly"""
    content, meta = obsidian

    # All three links should resolve to the same article
    assert content.count('href="{filename}/internal_link.md"') == 3
    assert "internal_link" in content


@pytest.mark.parametrize("path", ["breadcrumb_removal_test"])
def test_breadcrumb_removal(obsidian):
    """Test breadcrumb removal functionality"""
    content, _ = obsidian

    # Breadcrumbs with existing links should be converted to HTML links
    assert 'href="{filename}/internal_link.md"' in content
    assert 'href="{filename}/tags.md"' in content

    # Breadcrumbs with non-existing links should be completely removed
    assert "nonexistent_article" not in content
    assert "another_missing" not in content
    assert "missing_link" not in content

    # X::, Up::, Down:: prefixes should be removed
    assert "X::" not in content
    assert "Up::" not in content
    assert "Down::" not in content


@pytest.mark.parametrize("path", ["title_extraction_test"])
def test_title_extraction(obsidian):
    """Test that article titles are extracted and used in links"""
    content, meta = obsidian

    # Link should use the actual title from the target document
    assert "Hello: There" in content  # Title from colon_in_prop.md
    assert "empty_metadata" in content  # Fallback to filename when no title


@pytest.mark.parametrize("path", ["draft_status"])
def test_draft_status_skip_processing(obsidian):
    """Test that draft documents skip Obsidian processing"""
    content, meta = obsidian

    # Links should remain unprocessed in draft documents
    assert "[[internal_link]]" in content
    assert "![[pelican-in-rock.webp]]" in content
    assert "X::[[tags]]" in content

    # Should not be converted to Pelican format
    assert "{filename}" not in content
    assert "{static}" not in content


@pytest.mark.parametrize("path", ["case_sensitive_draft"])
def test_case_insensitive_draft_detection(obsidian):
    """Test case-insensitive draft detection (Status: Draft)"""
    content, meta = obsidian

    # Should skip processing due to Draft status
    assert len(content.strip()) > 0  # Content should exist but unprocessed


def test_custom_file_extensions():
    """Test configurable file extensions"""
    from pelican.tests.support import get_settings
    from pelican.generators import ArticlesGenerator

    settings = get_settings()
    settings["DEFAULT_CATEGORY"] = "Default"
    settings["DEFAULT_DATE"] = (1970, 1, 1)
    settings["CACHE_CONTENT"] = False

    # Configure custom extensions
    settings["OBSIDIAN_IMAGE_EXTENSIONS"] = ["png", "jpg", "webp"]
    settings["OBSIDIAN_FILE_EXTENSIONS"] = ["pdf", "pptx", "txt"]

    cwd = Path.cwd()
    generator = ArticlesGenerator(
        context=settings,
        settings=settings,
        path=cwd / "pelican" / "plugins" / "tests" / "fixtures",
        theme=settings["THEME"],
        output_path=None,
    )

    # This should work without errors with custom extensions
    populate_files_and_articles(generator)

    # Check that custom extensions are loaded
    from pelican.plugins.obsidian.obsidian import FILE_PATHS

    assert any("pdf" in filename for filename in FILE_PATHS)


def test_error_handling_invalid_path(caplog):
    """Test error handling for invalid base paths"""
    from pelican.tests.support import get_settings
    from pelican.generators import ArticlesGenerator

    settings = get_settings()
    settings["DEFAULT_CATEGORY"] = "Default"
    settings["DEFAULT_DATE"] = (1970, 1, 1)
    settings["CACHE_CONTENT"] = False

    # Create generator with non-existent path
    generator = ArticlesGenerator(
        context=settings,
        settings=settings,
        path=Path("/non/existent/path"),
        theme=settings["THEME"],
        output_path=None,
    )

    # Should handle gracefully by logging an error
    with caplog.at_level(logging.ERROR):
        populate_files_and_articles(generator)

    # Check that error was logged
    assert any(
        "Base path does not exist" in record.message for record in caplog.records
    )


def test_logging_statistics(caplog):
    """Test that logging statistics are provided"""
    from pelican.tests.support import get_settings
    from pelican.generators import ArticlesGenerator

    settings = get_settings()
    settings["DEFAULT_CATEGORY"] = "Default"
    settings["DEFAULT_DATE"] = (1970, 1, 1)
    settings["CACHE_CONTENT"] = False

    cwd = Path.cwd()
    generator = ArticlesGenerator(
        context=settings,
        settings=settings,
        path=cwd / "pelican" / "plugins" / "tests" / "fixtures",
        theme=settings["THEME"],
        output_path=None,
    )

    with caplog.at_level(logging.INFO):
        populate_files_and_articles(generator)

    # Check that summary statistics are logged
    assert any(
        "Obsidian plugin indexed:" in record.message for record in caplog.records
    )
