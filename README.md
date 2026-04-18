# onepageblog-static

A static site generator for a one-page blog. Posts are written in Markdown
and the output is a directory of static files. The landing page is a
one-page listing of all posts, and each post also has its own permalink
under `posts/`.

## Installation

Requires Python 3.11+.

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

This installs the `onepageblog` command. Alternatively, run without
installing:

```bash
python -m onepageblog config.toml
```

## Setup

Create a directory for your blog with a config file and a `posts/`
subdirectory:

```
myblog/
  config.toml
  posts/
    my-first-post.md
    another-post.md
```

**`config.toml`:**

```toml
site_title = "My Blog"
site_description = "Thoughts on things"
site_url = "https://example.com"
```

`posts_dir` and `output_dir` are optional and resolved relative to the
config file. They default to `posts` and `_output` respectively.

**Post format** (`posts/my-first-post.md`):

```markdown
---
title: My First Post
date: 2024-03-15
author: Your Name
---

Post content goes here. Markdown is supported.
```

The filename (without `.md`) becomes the URL slug. Filenames must be unique.

## Usage

```bash
onepageblog config.toml
```

Or without installation:

```bash
python -m onepageblog config.toml
```

The generator writes the output to the directory specified by `output_dir`
in your config.

## Output

```
_output/
  index.html        # one-page listing with expandable posts
  feed.xml          # RSS 2.0 feed
  posts/
    my-first-post/
      index.html    # standalone permalink page
      ajax.html     # post body fragment (loaded by HTMX)
    another-post/
      index.html
      ajax.html
```

Deploy the contents of the output directory to your web server.

## Development

```bash
uv pip install -e ".[dev]"
pytest
```
