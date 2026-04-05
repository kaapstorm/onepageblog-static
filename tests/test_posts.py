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
