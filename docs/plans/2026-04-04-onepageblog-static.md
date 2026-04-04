# onepageblog-static Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python static site generator that takes a directory of Markdown posts and produces a one-page blog with HTMX/Alpine.js expand-collapse, RSS feed, and per-post permalink pages.

**Architecture:** Dataclass pipeline — `load_config()` → `load_posts()` → `render()` → `write()`. Each stage takes plain data in and returns plain data out. No shared state, no side effects until `write()`. Jinja2 templates live inside the package under `onepageblog/templates/`.

**Tech Stack:** Python 3.11+ (tomllib stdlib), Jinja2, Markdown, PyYAML, HTMX 2.0.4, Alpine.js 3.14.9, pytest, pytest-unmagic

---

## File Map

| File | Purpose |
|------|---------|
| `pyproject.toml` | Build config, dependencies, console_scripts entry point |
| `onepageblog/__init__.py` | Empty package marker |
| `onepageblog/__main__.py` | `python -m onepageblog` entry point |
| `onepageblog/cli.py` | Argument parsing, wires pipeline stages |
| `onepageblog/config.py` | `Config` dataclass, `load_config(path)` |
| `onepageblog/posts.py` | `Post` dataclass, `load_posts(posts_dir)` |
| `onepageblog/renderer.py` | `render(config, posts) → dict[str, str]` |
| `onepageblog/writer.py` | `write(pages, output_dir)` |
| `onepageblog/templates/index.html.j2` | Main listing page template |
| `onepageblog/templates/post.html.j2` | Standalone permalink page template |
| `onepageblog/templates/ajax.html.j2` | HTMX partial (post body only) |
| `onepageblog/templates/feed.xml.j2` | RSS 2.0 feed template |
| `tests/__init__.py` | Empty |
| `tests/conftest.py` | Unmagic fence installation |
| `tests/test_config.py` | Tests for config loading |
| `tests/test_posts.py` | Tests for post parsing and loading |
| `tests/test_renderer.py` | Tests for template rendering |
| `tests/test_writer.py` | Tests for file writing |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `onepageblog/__init__.py`
- Create: `onepageblog/__main__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "onepageblog"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "jinja2",
    "markdown",
    "pyyaml",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-unmagic",
]

[project.scripts]
onepageblog = "onepageblog.cli:main"

[tool.setuptools.package-data]
onepageblog = ["templates/*"]
```

- [ ] **Step 2: Create package skeleton**

`onepageblog/__init__.py` — empty file.

`onepageblog/__main__.py`:
```python
from onepageblog.cli import main

main()
```

`tests/__init__.py` — empty file.

- [ ] **Step 3: Create `tests/conftest.py`**

```python
from unmagic import fence

fence.install(["tests"])
```

This warns if any test in the `tests` package uses magic (name-matching) pytest fixtures instead of explicit unmagic fixtures.

- [ ] **Step 4: Install in development mode**

```bash
pip install -e ".[dev]"
```

Expected: installs `onepageblog`, `jinja2`, `markdown`, `pyyaml`, `pytest`, `pytest-unmagic`.

- [ ] **Step 5: Verify pytest runs**

```bash
pytest tests/ -v
```

Expected: `no tests ran` (no test files yet).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml onepageblog/ tests/
git commit -m "feat: add project scaffolding"
```

---

## Task 2: Config

**Files:**
- Create: `onepageblog/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_config.py`:
```python
import tempfile
from pathlib import Path

import pytest

from onepageblog.config import Config, load_config


VALID_TOML = """\
site_title = "Test Blog"
site_description = "A test blog"
parent_url = "https://example.com"
base_path = "/blog/"
posts_dir = "posts"
output_dir = "output"
"""


def test_load_config_fields():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert isinstance(config, Config)
    assert config.site_title == "Test Blog"
    assert config.site_description == "A test blog"
    assert config.parent_url == "https://example.com"
    assert config.base_path == "/blog/"


def test_load_config_resolves_paths_relative_to_config():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert config.posts_dir == Path(tmp) / "posts"
    assert config.output_dir == Path(tmp) / "output"


def test_base_url_trailing_slash():
    config = Config(
        site_title="T",
        site_description="D",
        parent_url="https://example.com",
        base_path="/blog/",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/blog/"


def test_base_url_normalises_slashes():
    config = Config(
        site_title="T",
        site_description="D",
        parent_url="https://example.com/",
        base_path="blog",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/blog/"


def test_missing_field_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(
            'site_title = "Test"\n'
            'parent_url = "https://example.com"\n'
            'base_path = "/blog/"\n'
            'posts_dir = "posts"\n'
            'output_dir = "output"\n'
        )
        with pytest.raises(KeyError):
            load_config(path)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'onepageblog.config'`

- [ ] **Step 3: Implement `onepageblog/config.py`**

```python
from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass
class Config:
    site_title: str
    site_description: str
    parent_url: str
    base_path: str
    posts_dir: Path
    output_dir: Path

    @property
    def base_url(self) -> str:
        return self.parent_url.rstrip("/") + "/" + self.base_path.strip("/") + "/"


def load_config(path: Path) -> Config:
    path = Path(path)
    with open(path, "rb") as f:
        data = tomllib.load(f)
    base = path.parent
    return Config(
        site_title=data["site_title"],
        site_description=data["site_description"],
        parent_url=data["parent_url"],
        base_path=data["base_path"],
        posts_dir=(base / data["posts_dir"]).resolve(),
        output_dir=(base / data["output_dir"]).resolve(),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add onepageblog/config.py tests/test_config.py
git commit -m "feat: add Config dataclass and load_config()"
```

---

## Task 3: Posts

**Files:**
- Create: `onepageblog/posts.py`
- Create: `tests/test_posts.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_posts.py`:
```python
import tempfile
from datetime import date
from pathlib import Path

import pytest

from onepageblog.posts import Post, load_posts


def make_post_file(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


def test_load_single_post():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        make_post_file(d, "my-post.md", """\
---
title: My Post
date: 2024-03-15
author: Norman
---

Hello world.
""")
        posts = load_posts(d)
    assert len(posts) == 1
    post = posts[0]
    assert isinstance(post, Post)
    assert post.title == "My Post"
    assert post.date == date(2024, 3, 15)
    assert post.author == "Norman"
    assert post.slug == "my-post"
    assert "<p>Hello world.</p>" in post.body_html
    assert post.source_path == d / "my-post.md"


def test_slug_derived_from_filename():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        make_post_file(d, "hello-world.md", """\
---
title: A Different Title
date: 2024-01-01
author: Norman
---
""")
        posts = load_posts(d)
    assert posts[0].slug == "hello-world"


def test_posts_sorted_by_date_descending():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        make_post_file(d, "older.md", """\
---
title: Older
date: 2023-01-01
author: Norman
---
""")
        make_post_file(d, "newer.md", """\
---
title: Newer
date: 2024-06-01
author: Norman
---
""")
        posts = load_posts(d)
    assert posts[0].slug == "newer"
    assert posts[1].slug == "older"


def test_missing_frontmatter_field_raises():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        make_post_file(d, "bad.md", """\
---
title: No Author
date: 2024-01-01
---
""")
        with pytest.raises(ValueError, match="author"):
            load_posts(d)


def test_missing_frontmatter_block_raises():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        make_post_file(d, "no-front.md", "Just some text\n")
        with pytest.raises(ValueError, match="frontmatter"):
            load_posts(d)


def test_empty_directory_returns_empty_list():
    with tempfile.TemporaryDirectory() as tmp:
        posts = load_posts(Path(tmp))
    assert posts == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_posts.py -v
```

Expected: `ModuleNotFoundError: No module named 'onepageblog.posts'`

- [ ] **Step 3: Implement `onepageblog/posts.py`**

```python
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import markdown
import yaml


@dataclass
class Post:
    title: str
    date: date
    author: str
    slug: str
    body_html: str
    source_path: Path


def load_posts(posts_dir: Path) -> list[Post]:
    posts = [_parse_post(p) for p in sorted(Path(posts_dir).glob("*.md"))]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def _parse_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path}: malformed frontmatter")
    _, raw_front, body = parts
    meta = yaml.safe_load(raw_front)
    for field in ("title", "date", "author"):
        if field not in meta:
            raise ValueError(f"{path}: missing required frontmatter field '{field}'")
    post_date = meta["date"]
    if isinstance(post_date, str):
        post_date = date.fromisoformat(post_date)
    return Post(
        title=meta["title"],
        date=post_date,
        author=meta["author"],
        slug=path.stem,
        body_html=markdown.markdown(body.strip()),
        source_path=path,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_posts.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add onepageblog/posts.py tests/test_posts.py
git commit -m "feat: add Post dataclass and load_posts()"
```

---

## Task 4: Templates

**Files:**
- Create: `onepageblog/templates/index.html.j2`
- Create: `onepageblog/templates/post.html.j2`
- Create: `onepageblog/templates/ajax.html.j2`
- Create: `onepageblog/templates/feed.xml.j2`

The renderer tests in Task 5 will verify these templates produce correct output.

- [ ] **Step 1: Create `onepageblog/templates/index.html.j2`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ config.site_title }}</title>
  <link rel="alternate" type="application/rss+xml"
        title="{{ config.site_title }} RSS Feed"
        href="{{ config.base_url }}feed.xml">
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <script defer src="https://unpkg.com/alpinejs@3.14.9/dist/cdn.min.js"></script>
  <style>[x-cloak] { display: none; }</style>
</head>
<body>
  <header>
    <h1><a href="{{ config.parent_url }}">{{ config.site_title }}</a></h1>
  </header>
  <nav>
    [<a href="{{ config.base_url }}feed.xml">Feed</a>]
  </nav>
  <main>
    {% for post in posts %}
    <div class="post" x-data="{ open: false }">
      <div class="post-header"
           hx-get="{{ config.base_url }}{{ post.slug }}/ajax.html"
           hx-target="next .post-body"
           hx-swap="innerHTML"
           hx-trigger="click once"
           @click="open = !open">
        <span x-text="open ? '∧' : '∨'">∨</span>
        <a href="{{ config.base_url }}{{ post.slug }}/" @click.stop>🔗</a>
        <h2>{{ post.title }}</h2>
        <span>by {{ post.author }} | {{ post.date.strftime('%d %b %Y') }}</span>
      </div>
      <div class="post-body" x-show="open" x-cloak></div>
    </div>
    {% endfor %}
  </main>
  <footer>
    <a href="{{ config.parent_url }}">← {{ config.parent_url }}</a>
  </footer>
</body>
</html>
```

**How the HTMX/Alpine interaction works:** `hx-trigger="click once"` on the header fires the HTMX fetch on the first click only. `@click="open = !open"` runs on every click — Alpine controls show/hide. Both handlers respond to the same click event. The content `<div class="post-body">` starts hidden (`x-cloak` hides it until Alpine initialises; `x-show="open"` keeps it hidden until opened). HTMX injects the fetched `ajax.html` into that div via `innerHTML` swap.

- [ ] **Step 2: Create `onepageblog/templates/post.html.j2`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ config.site_title }} – {{ post.title }}</title>
</head>
<body>
  <header>
    <h1><a href="{{ config.base_url }}">{{ config.site_title }}</a></h1>
    <h2>{{ post.title }}</h2>
    <h3>{{ post.date.strftime('%d %b %Y') }} | {{ post.author }}</h3>
  </header>
  <main>
    {{ post.body_html | safe }}
  </main>
  <p>[<a href="{{ config.base_url }}">Back To List</a>]</p>
</body>
</html>
```

- [ ] **Step 3: Create `onepageblog/templates/ajax.html.j2`**

```html
{{ post.body_html | safe }}
<p>[<a href="{{ config.base_url }}{{ post.slug }}/">Permalink</a>]</p>
```

- [ ] **Step 4: Create `onepageblog/templates/feed.xml.j2`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{{ config.site_title }}</title>
    <link>{{ config.base_url }}</link>
    <description>{{ config.site_description }}</description>
    {% for post in posts %}
    <item>
      <title>{{ post.title }}</title>
      <link>{{ config.base_url }}{{ post.slug }}/</link>
      <pubDate>{{ post.date.strftime('%a, %d %b %Y 00:00:00 +0000') }}</pubDate>
      <author>{{ post.author }}</author>
      <description><![CDATA[{{ post.body_html | safe }}]]></description>
    </item>
    {% endfor %}
  </channel>
</rss>
```

- [ ] **Step 5: Commit**

```bash
git add onepageblog/templates/
git commit -m "feat: add Jinja2 templates"
```

---

## Task 5: Renderer

**Files:**
- Create: `onepageblog/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_renderer.py`:
```python
from datetime import date
from pathlib import Path

from unmagic import fixture

from onepageblog.config import Config
from onepageblog.posts import Post
from onepageblog.renderer import render


@fixture
def config():
    yield Config(
        site_title="Test Blog",
        site_description="A test blog",
        parent_url="https://example.com",
        base_path="/blog/",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )


@fixture
def posts():
    yield [
        Post(
            title="First Post",
            date=date(2024, 3, 15),
            author="Norman",
            slug="first-post",
            body_html="<p>Hello world.</p>",
            source_path=Path("/tmp/posts/first-post.md"),
        ),
        Post(
            title="Second Post",
            date=date(2024, 1, 1),
            author="Norman",
            slug="second-post",
            body_html="<p>Another post.</p>",
            source_path=Path("/tmp/posts/second-post.md"),
        ),
    ]


def test_render_returns_expected_keys():
    pages = render(config(), posts())
    assert set(pages.keys()) == {
        "index.html",
        "feed.xml",
        "first-post/index.html",
        "first-post/ajax.html",
        "second-post/index.html",
        "second-post/ajax.html",
    }


def test_index_contains_post_titles():
    pages = render(config(), posts())
    assert "First Post" in pages["index.html"]
    assert "Second Post" in pages["index.html"]


def test_index_htmx_ajax_url():
    pages = render(config(), posts())
    assert "https://example.com/blog/first-post/ajax.html" in pages["index.html"]


def test_index_permalink_url():
    pages = render(config(), posts())
    assert "https://example.com/blog/first-post/" in pages["index.html"]


def test_post_page_contains_body():
    pages = render(config(), posts())
    assert "<p>Hello world.</p>" in pages["first-post/index.html"]


def test_post_page_has_back_link():
    pages = render(config(), posts())
    assert "https://example.com/blog/" in pages["first-post/index.html"]


def test_ajax_contains_body_only():
    pages = render(config(), posts())
    assert "<p>Hello world.</p>" in pages["first-post/ajax.html"]
    assert "<!DOCTYPE html>" not in pages["first-post/ajax.html"]


def test_ajax_contains_permalink():
    pages = render(config(), posts())
    assert "https://example.com/blog/first-post/" in pages["first-post/ajax.html"]


def test_feed_contains_post_items():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    assert "<title>First Post</title>" in feed
    assert "<link>https://example.com/blog/first-post/</link>" in feed
    assert "<![CDATA[<p>Hello world.</p>]]>" in feed


def test_feed_channel_fields():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    assert "<title>Test Blog</title>" in feed
    assert "<link>https://example.com/blog/</link>" in feed
    assert "<description>A test blog</description>" in feed
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_renderer.py -v
```

Expected: `ModuleNotFoundError: No module named 'onepageblog.renderer'`

- [ ] **Step 3: Implement `onepageblog/renderer.py`**

```python
from jinja2 import Environment, PackageLoader

from .config import Config
from .posts import Post


def render(config: Config, posts: list[Post]) -> dict[str, str]:
    env = Environment(
        loader=PackageLoader("onepageblog", "templates"),
        autoescape=True,
    )
    pages: dict[str, str] = {}

    pages["index.html"] = env.get_template("index.html.j2").render(
        config=config, posts=posts
    )
    pages["feed.xml"] = env.get_template("feed.xml.j2").render(
        config=config, posts=posts
    )

    for post in posts:
        pages[f"{post.slug}/index.html"] = env.get_template("post.html.j2").render(
            config=config, post=post
        )
        pages[f"{post.slug}/ajax.html"] = env.get_template("ajax.html.j2").render(
            config=config, post=post
        )

    return pages
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_renderer.py -v
```

Expected: 10 tests PASSED.

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add onepageblog/renderer.py tests/test_renderer.py
git commit -m "feat: add renderer"
```

---

## Task 6: Writer

**Files:**
- Create: `onepageblog/writer.py`
- Create: `tests/test_writer.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_writer.py`:
```python
import tempfile
from pathlib import Path

from onepageblog.writer import write


def test_write_creates_files():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write(
            {
                "index.html": "<html>index</html>",
                "my-post/index.html": "<html>post</html>",
                "my-post/ajax.html": "<p>body</p>",
            },
            d,
        )
        assert (d / "index.html").read_text() == "<html>index</html>"
        assert (d / "my-post" / "index.html").read_text() == "<html>post</html>"
        assert (d / "my-post" / "ajax.html").read_text() == "<p>body</p>"


def test_write_creates_nested_subdirectories():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write({"deep/nested/file.html": "content"}, d)
        assert (d / "deep" / "nested" / "file.html").read_text() == "content"


def test_write_overwrites_existing_file():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "index.html").write_text("old content")
        write({"index.html": "new content"}, d)
        assert (d / "index.html").read_text() == "new content"


def test_write_creates_output_dir_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "new_output"
        write({"index.html": "hello"}, d)
        assert (d / "index.html").read_text() == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_writer.py -v
```

Expected: `ModuleNotFoundError: No module named 'onepageblog.writer'`

- [ ] **Step 3: Implement `onepageblog/writer.py`**

```python
from pathlib import Path


def write(pages: dict[str, str], output_dir: Path) -> None:
    output_dir = Path(output_dir)
    for relative_path, content in pages.items():
        dest = output_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_writer.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add onepageblog/writer.py tests/test_writer.py
git commit -m "feat: add writer"
```

---

## Task 7: CLI & Entry Points

**Files:**
- Create: `onepageblog/cli.py`
- Modify: `onepageblog/__main__.py` (already created in Task 1, no change needed)

- [ ] **Step 1: Implement `onepageblog/cli.py`**

```python
import argparse
import sys
from pathlib import Path

from .config import load_config
from .posts import load_posts
from .renderer import render
from .writer import write


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="onepageblog",
        description="Generate a static one-page blog.",
    )
    parser.add_argument("config", type=Path, help="Path to config.toml")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (KeyError, FileNotFoundError) as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        posts = load_posts(config.posts_dir)
    except ValueError as e:
        print(f"Error loading posts: {e}", file=sys.stderr)
        sys.exit(1)

    pages = render(config, posts)
    write(pages, config.output_dir)
    print(f"Generated {len(pages)} files in {config.output_dir}")
```

- [ ] **Step 2: Smoke-test the CLI with a sample site**

Create a temporary test directory:

```bash
mkdir /tmp/testblog
mkdir /tmp/testblog/posts

cat > /tmp/testblog/config.toml << 'EOF'
site_title = "Test Blog"
site_description = "Testing the generator"
parent_url = "https://example.com"
base_path = "/blog/"
posts_dir = "posts"
output_dir = "output"
EOF

cat > /tmp/testblog/posts/hello-world.md << 'EOF'
---
title: Hello World
date: 2024-03-15
author: Norman
---

This is my first post.
EOF

onepageblog /tmp/testblog/config.toml
```

Expected output:
```
Generated 4 files in /tmp/testblog/output
```

- [ ] **Step 3: Verify the output structure**

```bash
find /tmp/testblog/output -type f
```

Expected:
```
/tmp/testblog/output/index.html
/tmp/testblog/output/feed.xml
/tmp/testblog/output/hello-world/index.html
/tmp/testblog/output/hello-world/ajax.html
```

- [ ] **Step 4: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add onepageblog/cli.py
git commit -m "feat: add CLI entry point"
```
