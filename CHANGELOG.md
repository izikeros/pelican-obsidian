# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-07

### Added
- **Inline hashtag removal**: Automatically removes bare hashtags (e.g., `#agile`, `#python`, `#37-signals`) from article content while preserving hashtags in code blocks, inline code, and URL anchors
- **Obsidian callouts conversion**: Converts Obsidian callout syntax (`> [!note]`, `> [!warning]`, etc.) to standard Pelican admonition HTML format
- **Admonition format support**: Callouts convert to `div.admonition` format by default, compatible with existing Pelican themes (Flex, etc.)
- New configuration options:
  - `OBSIDIAN_REMOVE_HASHTAGS` (default: `True`) - Enable/disable inline hashtag removal
  - `OBSIDIAN_CALLOUTS_ENABLED` (default: `True`) - Enable/disable callout conversion
  - `OBSIDIAN_CALLOUTS_USE_ADMONITION` (default: `True`) - Use standard admonition format vs custom callout divs
- Sample CSS file (`obsidian-callouts.css`) for custom callout styling (when not using admonition format)
- Comprehensive tests for new features

### Supported Callout Types
note, tip, warning, danger, info, question, example, quote, abstract, success, failure, bug, important, caution, attention

Callout types are mapped to admonition classes: tip→tip, warning/caution/attention→warning, danger/failure/bug→danger, etc.

## [0.3.0] - 2025-01-03

### Added
- Case-insensitive link matching for better Obsidian compatibility
- Article title extraction from frontmatter for use in link text
- Draft status detection - skips Obsidian processing for draft articles
- Breadcrumb element handling (X::, Up::, Down:: prefixes)
- Configurable file extensions via settings:
  - `OBSIDIAN_IMAGE_EXTENSIONS`
  - `OBSIDIAN_FILE_EXTENSIONS`
- Improved error handling and logging
- Type annotations throughout the codebase
- `py.typed` marker for type hints support

### Changed
- Migrated to PEP 621 project configuration in pyproject.toml
- Removed setup.py and setup.cfg
- Enhanced path normalization for cross-platform compatibility

## [0.2.0] - 2024-01-15

### Added
- Support for wiki-style image links (`![[image.jpg]]`)
- Comma-delimited tags support (Pelican style)
- CI workflow for automated testing
- Unit tests for plugin functionality

### Fixed
- Wiki image and wiki links handling (#12)
- First letter removal in normal tags
- String formatting when colon is used in metadata

## [0.1.0] - 2023-06-01

### Added
- Initial release
- Convert Obsidian `[[wiki-links]]` to Pelican `{filename}` links
- Support for custom link text `[[file|display text]]`
- Remove `#` from tag names in frontmatter
- Support for pages in addition to articles
- Only link to posts that actually exist
