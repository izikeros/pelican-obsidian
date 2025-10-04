# Pelican Obsidian Plugin

> **Transform your Obsidian notes into beautiful Pelican blog posts with seamless linking and media embedding.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Black](https://img.shields.io/badge/format-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/lint-ruff-4b37ff.svg)](https://github.com/ruff-dev/ruff)

Write your blog posts in [Obsidian](https://obsidian.md/) using familiar double-bracket links and hash tags, then publish them effortlessly with [Pelican](https://getpelican.com/). This plugin bridges the gap between your note-taking workflow and your static site generation.

## Key Features

- **Obsidian-style links**: `[[article-name]]` and `[[article-name | Custom Text]]`
- **Media embedding**: `![[image.jpg]]` and `![[document.pdf | Alt text]]`
- **Clean hashtags**: `#my-tag` becomes `my-tag` (no hash symbol in output)
- **Breadcrumb navigation**: `X::[[parent]]`, `Up::[[category]]`, `Down::[[child]]`
- **Smart title extraction**: Uses article titles in generated links
- **Case-insensitive matching**: `[[Article]]` matches `article.md`
- **Configurable file extensions**: Support for custom file types
- **Draft handling**: Skip processing for draft articles


## Quick Start

### Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/jonathan-s/pelican-obsidian.git
```

### Configuration

Add the plugin to your `pelicanconf.py`:

```python
PLUGINS = ['obsidian']

# Optional: Configure custom file extensions
OBSIDIAN_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']
OBSIDIAN_FILE_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt', 'apkg']
```

## Usage Examples

### Internal Links

Create seamless links between your articles:

```markdown
---
title: My Blog Post
---

Check out my [[previous-article]] or read about [[python-tips | Python Tips and Tricks]].
```

**Result:** Links to `previous-article.md` using its title, and `python-tips.md` with custom text.

### Media Embedding

Embed images and files with ease:

```markdown
![[screenshot.png]]
![[diagram.svg | Architecture Overview]]
![[presentation.pdf | Download Slides]]
```

**Result:** Images display inline, files become download links with proper alt text.

### Hashtag Tags

Use natural hashtag syntax:

```yaml
---
title: Travel Blog
tags: #travel #photography #europe
---
```

**Result:** Creates tags `travel`, `photography`, `europe` (without hash symbols).

### Breadcrumb Navigation

Organize content hierarchy:

```markdown
---
title: Advanced Python
---

X::[[python-basics]]
Up::[[programming]]
Down::[[python-frameworks]]

This article builds on [[python-basics]] concepts...
```

**Result:** Creates navigation links; removes breadcrumbs if targets don't exist.

### Draft Handling

Control what gets published:

```yaml
---
title: Work in Progress
status: draft  # or DRAFT, Draft - case insensitive
---

This [[internal-link]] won't be processed until published.
```

**Result:** Obsidian syntax remains unchanged in draft articles.

## Advanced Configuration

### Custom File Extensions

```python
# Support additional file types
OBSIDIAN_IMAGE_EXTENSIONS = ['png', 'jpg', 'webp', 'avif', 'heic']
OBSIDIAN_FILE_EXTENSIONS = ['pdf', 'zip', 'epub', 'pptx', 'xlsx']
```

### Case-Insensitive Matching

Links automatically match files regardless of case:

- `[[My Article]]` → matches `my-article.md`
- `[[SETUP-GUIDE]]` → matches `setup-guide.md`

## Troubleshooting

### Links Not Working?

1. **Check file names**: Ensure your markdown files exist in the content directory
2. **Verify frontmatter**: Articles need proper YAML frontmatter with titles
3. **Case sensitivity**: The plugin handles case-insensitive matching automatically

### Images Not Displaying?

1. **File location**: Place images in your `STATIC_PATHS` directory
2. **Supported formats**: Default extensions are `png`, `jpg`, `jpeg`, `svg`, `gif`, `webp`, `avif`
3. **Custom extensions**: Add them to `OBSIDIAN_IMAGE_EXTENSIONS` setting

### Debug Mode

Enable debug logging to see what the plugin is doing:

```python
# In pelicanconf.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## How It Works

1. **Article Discovery**: Scans your content directory for markdown files
2. **Title Extraction**: Reads frontmatter to get article titles
3. **Link Processing**: Converts `[[article]]` to proper Pelican links
4. **Media Handling**: Transforms `![[file]]` to static file references
5. **Breadcrumb Cleanup**: Removes navigation elements for missing targets

## Contributing

Contributions are welcome! This plugin supports:

- Internal article linking with custom text
- Media file embedding (images, documents)
- Hashtag tag processing
- Breadcrumb navigation
- Draft article handling
- Case-insensitive file matching
- Configurable file extensions
- Comprehensive error handling

### Ideas for Future Enhancements

- Block/section embedding: `![[article#section]]`
- Task list processing (todo-style checkboxes)
- reStructuredText support
- Backlink generation

## 📄 License

This project is licensed under the [MIT License](LICENSE).
