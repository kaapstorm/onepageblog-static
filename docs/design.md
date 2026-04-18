# onepageblog-static Design

A static site generator for a one-page blog. Posts are written in Markdown,
the output is a directory of static HTML/XML files. The landing page is a
one-page listing of all posts, and each post also has its own permalink
under `posts/`.

## Overview

The generator is a Python package (`onepageblog`) that can be invoked as a
module (`python -m onepageblog config.toml`) or as a CLI command
(`onepageblog config.toml`) after installation.

It follows a dataclass pipeline: each stage takes plain data in and returns
plain data out, with no shared state and no side effects until the final write
step.

```
load_config(path) → Config
load_posts(config.posts_dir) → list[Post]
render(config, posts) → dict[str, str]   # {relative_path: content}
write(pages, config.output_dir)
```

## Module Structure

```
onepageblog/
  __init__.py
  __main__.py        # python -m onepageblog entry point
  cli.py             # argument parsing, wires pipeline stages together
  config.py          # loads and validates config.toml → Config
  posts.py           # discovers, parses, validates posts → list[Post]
  renderer.py        # renders Jinja2 templates → dict[str, str]
  writer.py          # writes rendered output to the output directory
  templates/
    index.html.j2    # main listing page
    post.html.j2     # standalone permalink page
    ajax.html.j2     # HTMX partial (post body only)
    feed.xml.j2      # RSS 2.0 feed

tests/
  fixtures/          # sample posts and configs for tests
  test_config.py
  test_posts.py
  test_renderer.py
  test_writer.py

pyproject.toml       # [console_scripts] onepageblog = onepageblog.cli:main
```

## Data Models

```python
@dataclass
class Config:
    site_title: str
    site_description: str
    site_url: str          # e.g. "https://example.com"
    posts_dir: Path
    output_dir: Path

    @property
    def base_url(self) -> str:
        return self.site_url.rstrip("/") + "/"


@dataclass
class Post:
    title: str
    date: date
    author: str
    slug: str              # derived from filename (without extension)
    body_html: str         # Markdown rendered to HTML
    source_path: Path      # for error messages
```

## Post Format

Posts are Markdown files with YAML frontmatter in the configured `posts_dir`.
The filename (without extension) is used as the URL slug, giving the author
explicit control and enforcing uniqueness via the filesystem.

```markdown
---
title: My Post
date: 2024-03-15
author: Norman
---

Post content here...
```

`load_posts()` globs `posts_dir` for `*.md`, parses each file, renders the
Markdown body to HTML, and returns posts sorted by date descending. Missing
required frontmatter fields raise a clear error with the source path.

## Config Format

```toml
site_title = "Norman's Blog"
site_description = "Thoughts on things"
site_url = "https://example.com"
```

`posts_dir` and `output_dir` are optional (defaulting to `posts` and
`_output`) and are resolved relative to the config file's location, so
`onepageblog config.toml` works from any directory.

## Output Structure

```
_output/
  index.html              # main one-page listing
  feed.xml                # RSS 2.0 feed
  posts/
    my-post/
      index.html          # standalone permalink page
      ajax.html           # HTMX partial (post body only, no <html> wrapper)
    another-post/
      index.html
      ajax.html
```

## Frontend: HTMX + Alpine.js

Each post in `index.html` is an Alpine.js component managing open/closed
state. HTMX fetches `ajax.html` lazily the first time a post is expanded;
subsequent toggles are Alpine.js show/hide only.

```html
<div x-data="{ open: false }">
  <div @click="open = !open" style="cursor: pointer">
    <span x-text="open ? '∧' : '∨'"></span>
    <a href="/posts/my-post/">🔗</a>
    <h2>My Post</h2>
    <span>by Norman | 15 Mar 2024</span>
  </div>
  <div x-show="open"
       hx-get="/posts/my-post/ajax.html"
       hx-trigger="click[!open] from:previous div"
       hx-swap="innerHTML">
  </div>
</div>
```

`ajax.html` contains only the rendered post body. `post/index.html` is a
full standalone page for direct linking, showing the same body with a
"Back to list" link pointing to the site root.

## RSS Feed

`feed.xml` is an RSS 2.0 feed. Channel fields:

- `<title>` — `site_title`
- `<link>` — `base_url`
- `<description>` — `site_description`

Per-item fields:

- `<title>` — post title
- `<link>` — absolute URL: `base_url/posts/slug/`
- `<pubDate>` — post date in RFC 2822 format
- `<author>` — post author
- `<description>` — full post body HTML in a CDATA block

## Testing

Tests use pytest and pytest-unmagic (explicit fixture imports, no name-matching
magic). Each pipeline stage is tested independently:

- `test_config.py` — parses valid TOML; raises on missing required fields
- `test_posts.py` — parses frontmatter; renders Markdown; raises on missing
  fields; orders posts by date descending
- `test_renderer.py` — renders templates with fixture `Config` and `Post`
  objects; checks generated HTML/XML contains expected content; no filesystem
  access
- `test_writer.py` — writes a fixture `dict[str, str]` to a temp directory;
  asserts files exist with correct content

Tests use real in-memory or temp-dir data rather than mocks. The pipeline
stages are pure enough that this is straightforward.
