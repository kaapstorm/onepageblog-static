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
            "﻿\n---\ntitle: BOM\ndate: 2024-01-01\n---\nBody.\n",
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
