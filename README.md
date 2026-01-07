# Pelican Obsidian

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A [Pelican](https://getpelican.com/) plugin that transforms [Obsidian](https://obsidian.md/) markdown syntax into Pelican-compatible HTML. Write your blog posts in Obsidian using familiar wiki-links and callouts, then publish them seamlessly with Pelican.

## Features

| Feature | Obsidian Syntax | Description |
|---------|-----------------|-------------|
| Wiki Links | `[[article-name]]` | Links to other articles |
| Custom Link Text | `[[article\|Display Text]]` | Links with custom display text |
| Image Embedding | `![[image.png]]` | Embeds images |
| File Embedding | `![[document.pdf]]` | Links to static files |
| Callouts | `> [!note]` | Converts to styled admonitions |
| Inline Hashtags | `#tag-name` | Removes bare hashtags from content |
| Breadcrumbs | `Up::[[parent]]` | Navigation elements |
| Tag Cleanup | `tags: #python` | Strips `#` from frontmatter tags |

## Installation

```bash
pip install git+https://github.com/jonathan-s/pelican-obsidian.git
```

**Requirements:** Python 3.9+, Pelican, pelican-yaml-metadata

## Quick Start

Add to your `pelicanconf.py`:

```python
PLUGINS = ['obsidian']
```

That's it! The plugin works with sensible defaults.

---

## Transformation Guide

### Wiki Links

Convert Obsidian `[[wiki-links]]` to standard markdown links with Pelican's `{filename}` directive.

**Obsidian Markdown:**
```markdown
Check out my [[getting-started]] guide.
Read about [[python-tips|Python Tips and Tricks]].
```

**Generated HTML:**
```html
<p>Check out my <a href="/getting-started.html">Getting Started with Pelican</a> guide.</p>
<p>Read about <a href="/python-tips.html">Python Tips and Tricks</a>.</p>
```

**Behavior:**
- Links use the target article's title (from frontmatter) as link text
- Custom text after `|` overrides the title
- Non-existent targets become plain text (no broken links)
- Case-insensitive matching: `[[My Article]]` finds `my-article.md`

---

### Image and File Embedding

Embed images and link to files using Obsidian's `![[filename]]` syntax.

**Obsidian Markdown:**
```markdown
Here's a screenshot:
![[screenshot.png]]

Download the presentation:
![[slides.pdf|Download Slides]]
```

**Generated HTML:**
```html
<p>Here's a screenshot:</p>
<p><img alt="screenshot.png" src="/images/screenshot.png"></p>

<p>Download the presentation:</p>
<p><img alt="Download Slides" src="/files/slides.pdf"></p>
```

**Supported Extensions:**
- **Images:** png, jpg, jpeg, svg, gif, webp, avif
- **Files:** apkg, pdf, doc, docx, txt

---

### Callouts / Admonitions

Convert Obsidian callout blocks to HTML admonitions compatible with Pelican themes.

**Obsidian Markdown:**
```markdown
> [!note] Important Information
> This is a note callout.
> It can span multiple lines.

> [!warning]
> Be careful with this operation!

> [!tip] Pro Tip
> Use keyboard shortcuts to save time.
```

**Generated HTML (default admonition format):**
```html
<div class="admonition note">
<p class="admonition-title">Important Information</p>
<p>This is a note callout.
It can span multiple lines.</p>
</div>

<div class="admonition warning">
<p class="admonition-title">Warning</p>
<p>Be careful with this operation!</p>
</div>

<div class="admonition tip">
<p class="admonition-title">Pro Tip</p>
<p>Use keyboard shortcuts to save time.</p>
</div>
```

**Supported Callout Types:**

| Obsidian Type | Admonition Class | Visual Style |
|---------------|------------------|--------------|
| `note`, `info` | `note` | Blue |
| `tip`, `success` | `tip` | Green |
| `warning`, `caution`, `attention` | `warning` | Orange |
| `danger`, `failure`, `bug`, `error` | `danger` | Red |
| `important` | `important` | Purple |
| `question` | `hint` | Cyan |
| `example`, `abstract`, `quote` | `note` | Blue |

---

### Inline Hashtag Removal

Removes bare hashtags from article content while preserving code.

**Obsidian Markdown:**
```markdown
This article covers #python and #web-development topics.

Here's some code: `#this-stays`

```python
# This comment stays too
print("Hello")
```
```

**Generated HTML:**
```html
<p>This article covers  and  topics.</p>

<p>Here's some code: <code>#this-stays</code></p>

<pre><code class="python"># This comment stays too
print("Hello")
</code></pre>
```

**Preserved contexts:**
- Inside backticks (inline code)
- Inside code fences
- URL anchors (`http://example.com/#section`)

---

### Breadcrumb Navigation

Handle Obsidian breadcrumb-style navigation elements.

**Obsidian Markdown:**
```markdown
Up::[[parent-category]]
X::[[related-article]]
Down::[[subtopic]]

The main content starts here...
```

**Generated HTML:**
```html
<p><a href="/parent-category.html">Parent Category</a></p>
<p><a href="/related-article.html">Related Article</a></p>
<p><a href="/subtopic.html">Subtopic Guide</a></p>

<p>The main content starts here...</p>
```

**Behavior:**
- Prefixes (`Up::`, `X::`, `Down::`) are removed
- If target article doesn't exist, entire breadcrumb line is removed
- Case-insensitive prefix matching

---

### Tag Processing

Cleans up Obsidian-style hashtag tags in frontmatter.

**Obsidian Markdown:**
```yaml
---
title: My Article
tags: #python, #web-dev, #tutorial
---
```

**Result:** Tags become `python`, `web-dev`, `tutorial` (without `#`)

Also supports YAML list format:
```yaml
tags:
  - python
  - web-dev
```

---

### Draft Handling

Articles with `status: draft` skip all Obsidian processing.

**Obsidian Markdown:**
```yaml
---
title: Work in Progress
status: draft
---

This [[wiki-link]] stays as-is until published.
```

**Generated HTML:**
```html
<p>This [[wiki-link]] stays as-is until published.</p>
```

This lets you preview drafts in their raw Obsidian format.

---

## Configuration

All settings are optional. Add to `pelicanconf.py`:

```python
# Plugin activation
PLUGINS = ['obsidian']

# Hashtag removal (default: True)
OBSIDIAN_REMOVE_HASHTAGS = True

# Callout conversion (default: True)
OBSIDIAN_CALLOUTS_ENABLED = True

# Use standard admonition format (default: True)
# Set to False for custom callout CSS classes
OBSIDIAN_CALLOUTS_USE_ADMONITION = True

# Custom image extensions (default shown)
OBSIDIAN_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'svg', 'gif', 'webp', 'avif']

# Custom file extensions (default shown)
OBSIDIAN_FILE_EXTENSIONS = ['apkg', 'pdf', 'doc', 'docx', 'txt']
```

### Callout Styling

**With `OBSIDIAN_CALLOUTS_USE_ADMONITION = True` (default):**

Works automatically with Pelican themes that support admonitions (Flex, Elegant, etc.). The generated HTML uses standard `div.admonition` classes.

**With `OBSIDIAN_CALLOUTS_USE_ADMONITION = False`:**

Generates `div.callout.callout-{type}` classes. Include the provided `obsidian-callouts.css` in your theme:

```html
<link rel="stylesheet" href="{{ SITEURL }}/theme/css/obsidian-callouts.css">
```

---

## Troubleshooting

### Links Not Converting?

1. **File must exist** - Target `.md` file must be in your content directory
2. **Check filename** - Link text must match filename (without `.md`)
3. **Frontmatter required** - Articles need YAML frontmatter for title extraction

### Images Not Showing?

1. **Check STATIC_PATHS** - Image directory must be in Pelican's static paths
2. **Verify extension** - Must be in `OBSIDIAN_IMAGE_EXTENSIONS` list
3. **Case sensitivity** - Filename case must match (or use exact case)

### Enable Debug Logging

```python
import logging
logging.getLogger('pelican.plugins.obsidian').setLevel(logging.DEBUG)
```

---

## How It Works

1. **Initialization** - Scans content directory, builds article/file index
2. **Title Extraction** - Reads YAML frontmatter to get article titles  
3. **Content Processing** (in order):
   - Remove inline hashtags
   - Convert callouts to HTML
   - Process breadcrumb elements
   - Replace wiki-links with Pelican links
4. **Tag Cleanup** - Strips `#` from frontmatter tags

---

## License

[MIT License](LICENSE)

## Credits

- Original author: [Jonathan Sundqvist](https://github.com/jonathan-s)
- Contributors: [Krystian Safjan](https://github.com/izikeros)
