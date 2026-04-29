# Testsweet migration implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace pytest + pytest-unmagic with testsweet across the test suite, consolidating the post-loading error tests with `@test_params`.

**Architecture:** Swap dev dependencies in `pyproject.toml`, drop the unmagic fence (`tests/conftest.py`), rename each test file to drop the `test_` prefix, and rewrite each file to use the `@test`/`@test_params`/`catch_exceptions` API. Renderer tests become a single `@test`-decorated class with shared setup; the others remain flat functions.

**Tech Stack:** Python 3.11+, uv, testsweet (sourced from testpypi, fallback to GitHub).

**Spec:** `claude/specs/2026-04-28-testsweet-migration-design.md`

---

## Task 1: Swap dev dependencies and add testsweet config

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Replace the `[project.optional-dependencies]` block and add testsweet sources/index/discovery config**

Locate the existing `[project.optional-dependencies]` block in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-unmagic",
]
```

Replace it (and append the new sections at the end of the file) so that the file ends up containing:

```toml
[project.optional-dependencies]
dev = [
    "testsweet",
]
```

Add (append to end of file):

```toml
[tool.uv.sources]
testsweet = { index = "testpypi" }

[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
explicit = true

[tool.testsweet.discovery]
include_paths = ["tests"]
test_files = ["*.py"]
```

Leave all other sections (`[build-system]`, `[project]`, `[project.scripts]`, `[tool.setuptools.*]`) untouched.

- [ ] **Step 2: Reinstall dev deps**

Run: `uv pip install -e ".[dev]"`

Expected: testsweet is downloaded from testpypi and installed; pytest and pytest-unmagic are no longer pinned.

If the install fails with a missing dependency (testpypi often lacks transitive packages), edit `pyproject.toml` and replace the testsweet source/index blocks with the GitHub fallback:

```toml
[tool.uv.sources]
testsweet = { git = "https://github.com/kaapstorm/testsweet" }
```

(Delete the `[[tool.uv.index]]` block in that case — it's not needed.) Then re-run `uv pip install -e ".[dev]"`.

- [ ] **Step 3: Verify the testsweet runner is importable**

Run: `uv run python -c "import testsweet; print(testsweet.__name__)"`

Expected: prints `testsweet`, exits 0.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: replace pytest with testsweet in dev deps"
```

If `uv.lock` was not modified by the install, drop it from the `git add`.

---

## Task 2: Delete the unmagic conftest

**Files:**
- Delete: `tests/conftest.py`

- [ ] **Step 1: Delete the file**

Run: `rm tests/conftest.py`

- [ ] **Step 2: Commit**

```bash
git add -A tests/conftest.py
git commit -m "test: drop unmagic fence conftest"
```

---

## Task 3: Rewrite `tests/test_config.py` → `tests/config.py`

**Files:**
- Delete: `tests/test_config.py`
- Create: `tests/config.py`

- [ ] **Step 1: Delete the old file**

Run: `rm tests/test_config.py`

- [ ] **Step 2: Create the new file**

Write `tests/config.py` with this exact content:

```python
import tempfile
from pathlib import Path

from testsweet import catch_exceptions, test

from onepageblog.config import Config, load_config


VALID_TOML = """\
site_title = "Test Blog"
site_description = "A test blog"
site_url = "https://example.com"
posts_dir = "posts"
output_dir = "output"
"""


@test
def load_config_fields():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert isinstance(config, Config)
    assert config.site_title == "Test Blog"
    assert config.site_description == "A test blog"
    assert config.site_url == "https://example.com"


@test
def load_config_resolves_paths_relative_to_config():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert config.posts_dir == Path(tmp) / "posts"
    assert config.output_dir == Path(tmp) / "output"


@test
def load_config_defaults_paths():
    minimal_toml = (
        'site_title = "Test Blog"\n'
        'site_description = "A test blog"\n'
        'site_url = "https://example.com"\n'
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(minimal_toml)
        config = load_config(path)
    assert config.posts_dir == Path(tmp) / "posts"
    assert config.output_dir == Path(tmp) / "_output"


@test
def base_url_trailing_slash():
    config = Config(
        site_title="T",
        site_description="D",
        site_url="https://example.com",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/"


@test
def base_url_strips_trailing_slash_from_site_url():
    config = Config(
        site_title="T",
        site_description="D",
        site_url="https://example.com/",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/"


@test
def invalid_site_url_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(
            'site_title = "T"\n'
            'site_description = "D"\n'
            'site_url = "example.com"\n'
        )
        with catch_exceptions() as excs:
            load_config(path)
    assert type(excs[0]) is ValueError
    assert "site_url" in str(excs[0])


@test
def missing_field_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(
            'site_title = "Test"\n'
            'site_url = "https://example.com"\n'
            'posts_dir = "posts"\n'
            'output_dir = "output"\n'
        )
        with catch_exceptions() as excs:
            load_config(path)
    assert type(excs[0]) is KeyError
```

- [ ] **Step 3: Run the file's tests**

Run: `uv run python -m testsweet tests/config.py`

Expected: 7 tests pass, exit 0.

- [ ] **Step 4: Commit**

```bash
git add tests/config.py tests/test_config.py
git commit -m "test: port config tests to testsweet"
```

---

## Task 4: Rewrite `tests/test_posts.py` → `tests/posts.py`

**Files:**
- Delete: `tests/test_posts.py`
- Create: `tests/posts.py`

- [ ] **Step 1: Delete the old file**

Run: `rm tests/test_posts.py`

- [ ] **Step 2: Create the new file**

Write `tests/posts.py` with this exact content:

```python
import tempfile
from datetime import date
from pathlib import Path

from testsweet import catch_exceptions, test, test_params

from onepageblog.posts import Post, load_posts


def _make_post_file(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


@test
def load_single_post():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _make_post_file(d, "my-post.md", """\
---
title: My Post
date: 2024-03-15
author: Norman
---

Hello world.
""")
        posts = load_posts(d)
        source = d / "my-post.md"
        assert len(posts) == 1
        post = posts[0]
        assert isinstance(post, Post)
        assert post.title == "My Post"
        assert post.date == date(2024, 3, 15)
        assert post.author == "Norman"
        assert post.slug == "my-post"
        assert "<p>Hello world.</p>" in post.body_html
        assert post.source_path == source


@test
def slug_derived_from_filename():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _make_post_file(d, "hello-world.md", """\
---
title: A Different Title
date: 2024-01-01
author: Norman
---
""")
        posts = load_posts(d)
    assert posts[0].slug == "hello-world"


@test
def posts_sorted_by_date_descending():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _make_post_file(d, "older.md", """\
---
title: Older
date: 2023-01-01
author: Norman
---
""")
        _make_post_file(d, "newer.md", """\
---
title: Newer
date: 2024-06-01
author: Norman
---
""")
        posts = load_posts(d)
    assert posts[0].slug == "newer"
    assert posts[1].slug == "older"


@test
def author_is_optional():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _make_post_file(d, "no-author.md", """\
---
title: Anonymous
date: 2024-01-01
---

Body.
""")
        posts = load_posts(d)
    assert posts[0].author is None


@test
def empty_directory_returns_empty_list():
    with tempfile.TemporaryDirectory() as tmp:
        posts = load_posts(Path(tmp))
    assert posts == []


@test
def leading_bom_and_whitespace_are_tolerated():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _make_post_file(
            d,
            "bom.md",
            "\ufeff\n---\ntitle: BOM\ndate: 2024-01-01\n---\nBody.\n",
        )
        posts = load_posts(d)
    assert posts[0].title == "BOM"


@test_params([
    ("missing_title",     "---\nauthor: N\ndate: 2024-01-01\n---\n",            "title"),
    ("missing_block",     "Just some text\n",                                   "frontmatter"),
    ("empty_frontmatter", "---\n---\nsome body\n",                              "YAML mapping"),
    ("datetime_date",     "---\ntitle: T\ndate: 2024-03-15T12:00:00Z\n---\n",   "date"),
    ("invalid_date_type", "---\ntitle: T\ndate: not-a-date\n---\n",             "date"),
])
def load_posts_rejects_bad_input(label, content, expected_match):
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / f"{label}.md").write_text(content)
        with catch_exceptions() as excs:
            load_posts(d)
    assert type(excs[0]) is ValueError
    assert expected_match in str(excs[0])
```

Note: `load_single_post` keeps its assertions inside the `with` block because `post.source_path == d / "my-post.md"` is evaluated against a `Path` constructed from the same string — this works either way, but keeping the assertions inside the block matches the source-of-truth path while it still exists.

- [ ] **Step 3: Run the file's tests**

Run: `uv run python -m testsweet tests/posts.py`

Expected: 6 standalone tests pass + 5 parametrized rows pass (11 total), exit 0.

- [ ] **Step 4: Commit**

```bash
git add tests/posts.py tests/test_posts.py
git commit -m "test: port posts tests to testsweet, parametrize error cases"
```

---

## Task 5: Rewrite `tests/test_renderer.py` → `tests/renderer.py`

**Files:**
- Delete: `tests/test_renderer.py`
- Create: `tests/renderer.py`

- [ ] **Step 1: Delete the old file**

Run: `rm tests/test_renderer.py`

- [ ] **Step 2: Create the new file**

Write `tests/renderer.py` with this exact content:

```python
import tempfile
from contextlib import AbstractContextManager
from datetime import date
from pathlib import Path

from testsweet import test

from onepageblog.config import Config
from onepageblog.posts import Post
from onepageblog.renderer import copy_static, render


@test
class Renderer(AbstractContextManager):
    def __enter__(self):
        self.config = Config(
            site_title="Test Blog",
            site_description="A test blog",
            site_url="https://example.com",
            posts_dir=Path("/tmp/posts"),
            output_dir=Path("/tmp/output"),
        )
        self.posts = [
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
        self.pages = render(self.config, self.posts)
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def returns_expected_keys(self):
        expected = {
            "index.html",
            "feed.xml",
            "posts/first-post/index.html",
            "posts/first-post/ajax.html",
            "posts/second-post/index.html",
            "posts/second-post/ajax.html",
        }
        assert expected == set(self.pages.keys())

    def index_contains_post_titles(self):
        assert "First Post" in self.pages["index.html"]
        assert "Second Post" in self.pages["index.html"]

    def index_htmx_ajax_url(self):
        assert (
            "https://example.com/posts/first-post/ajax.html"
            in self.pages["index.html"]
        )

    def post_page_contains_body(self):
        assert "<p>Hello world.</p>" in self.pages["posts/first-post/index.html"]

    def post_page_has_back_link(self):
        assert "https://example.com/" in self.pages["posts/first-post/index.html"]

    def ajax_contains_body_only(self):
        assert "<p>Hello world.</p>" in self.pages["posts/first-post/ajax.html"]
        assert "<!DOCTYPE html>" not in self.pages["posts/first-post/ajax.html"]

    def ajax_contains_permalink(self):
        assert (
            "https://example.com/posts/first-post/"
            in self.pages["posts/first-post/ajax.html"]
        )

    def feed_contains_post_items(self):
        feed = self.pages["feed.xml"]
        assert "<title>First Post</title>" in feed
        assert "<link>https://example.com/posts/first-post/</link>" in feed
        assert "<![CDATA[<p>Hello world.</p>]]>" in feed

    def feed_channel_fields(self):
        feed = self.pages["feed.xml"]
        assert "<title>Test Blog</title>" in feed
        assert "<link>https://example.com/</link>" in feed
        assert "<description>A test blog</description>" in feed

    def feed_pubdate_rfc822_format(self):
        feed = self.pages["feed.xml"]
        # 2024-03-15 is a Friday
        assert "<pubDate>Fri, 15 Mar 2024 00:00:00 +0000</pubDate>" in feed
        # 2024-01-01 is a Monday
        assert "<pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate>" in feed

    def index_has_no_cdn_dependencies(self):
        assert "unpkg.com" not in self.pages["index.html"]
        assert "cdn.jsdelivr.net" not in self.pages["index.html"]


@test
def copy_static_copies_assets():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        count = copy_static(d)
        assert count >= 5
        assert (d / "default.css").is_file()
        assert (d / "fonts.css").is_file()
        assert (d / "htmx.min.js").is_file()
        assert (d / "alpinejs.min.js").is_file()
        woff2 = list(d.rglob("*.woff2"))
        assert len(woff2) >= 5
        with (d / "fonts" / "lora-latin-400-normal.woff2").open("rb") as f:
            assert f.read(4) == b"wOF2"
```

- [ ] **Step 3: Run the file's tests**

Run: `uv run python -m testsweet tests/renderer.py`

Expected: 11 class methods + 1 standalone test pass (12 total), exit 0.

- [ ] **Step 4: Commit**

```bash
git add tests/renderer.py tests/test_renderer.py
git commit -m "test: port renderer tests to testsweet class with shared setup"
```

---

## Task 6: Rewrite `tests/test_writer.py` → `tests/writer.py`

**Files:**
- Delete: `tests/test_writer.py`
- Create: `tests/writer.py`

- [ ] **Step 1: Delete the old file**

Run: `rm tests/test_writer.py`

- [ ] **Step 2: Create the new file**

Write `tests/writer.py` with this exact content:

```python
import tempfile
from pathlib import Path

from testsweet import test

from onepageblog.writer import clean_stale_posts, write


@test
def write_creates_files():
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


@test
def write_creates_nested_subdirectories():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write({"deep/nested/file.html": "content"}, d)
        assert (d / "deep" / "nested" / "file.html").read_text() == "content"


@test
def write_overwrites_existing_file():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "index.html").write_text("old content")
        write({"index.html": "new content"}, d)
        assert (d / "index.html").read_text() == "new content"


@test
def write_creates_output_dir_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "new_output"
        write({"index.html": "hello"}, d)
        assert (d / "index.html").read_text() == "hello"


@test
def clean_stale_posts_removes_missing_slugs():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "posts" / "keep").mkdir(parents=True)
        (d / "posts" / "keep" / "index.html").write_text("x")
        (d / "posts" / "stale").mkdir(parents=True)
        (d / "posts" / "stale" / "index.html").write_text("x")
        removed = clean_stale_posts(d, ["keep"])
        assert removed == ["stale"]
        assert (d / "posts" / "keep").is_dir()
        assert not (d / "posts" / "stale").exists()


@test
def clean_stale_posts_with_no_posts_dir():
    with tempfile.TemporaryDirectory() as tmp:
        assert clean_stale_posts(Path(tmp), ["anything"]) == []
```

- [ ] **Step 3: Run the file's tests**

Run: `uv run python -m testsweet tests/writer.py`

Expected: 6 tests pass, exit 0.

- [ ] **Step 4: Commit**

```bash
git add tests/writer.py tests/test_writer.py
git commit -m "test: port writer tests to testsweet"
```

---

## Task 7: Final full-suite run

- [ ] **Step 1: Discover and run everything**

Run: `uv run python -m testsweet`

Expected: all tests across `tests/config.py`, `tests/posts.py`, `tests/renderer.py`, `tests/writer.py` pass. Total: 7 + 11 + 12 + 6 = 36. Exit 0.

If any test fails, stop and report rather than patching ad hoc. The previous per-file runs already verified each file passes in isolation; a discovery-time failure usually indicates a configuration issue.

---

## Task 8: Update docs

**Files:**
- Modify: `CLAUDE.md`
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Update `CLAUDE.md`**

Replace the test-running line:

Old:
```
- Run tests: `uv run pytest tests/ -v`
```

New:
```
- Run tests: `uv run python -m testsweet`
```

Leave the alternative invocation note (`uv run python -m onepageblog ...`) untouched.

- [ ] **Step 2: Replace the Testing section in `CONTRIBUTING.md`**

Replace the entire `## Testing` section (from the heading through the unmagic example block and the conftest paragraph) with:

```markdown
## Testing

Uses [testsweet](https://test.pypi.org/project/testsweet/). Mark tests with
`@test` (functions or classes). Class-style tests can implement the
context-manager protocol for shared setup; the runner enters the class once
per class. Use `catch_exceptions()` to assert raised exceptions, and
`@test_params` for parametrized tests. Run with `uv run python -m testsweet`.
```

Leave the `## Gotchas` section untouched.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md CONTRIBUTING.md
git commit -m "docs: update testing instructions for testsweet"
```

---

## Acceptance

After all tasks complete:

- `uv run python -m testsweet` passes with 36 tests.
- No file under `tests/` starts with `test_`.
- `tests/conftest.py` does not exist.
- `pyproject.toml` does not mention `pytest` or `pytest-unmagic`.
- `CLAUDE.md` and `CONTRIBUTING.md` no longer mention pytest or unmagic.
- Each of the seven code-changing tasks (1, 2, 3, 4, 5, 6, 8) is its own commit.
