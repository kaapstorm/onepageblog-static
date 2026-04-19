from datetime import date
from pathlib import Path

from unmagic import fixture

from onepageblog.config import Config
from onepageblog.posts import Post
from onepageblog.renderer import copy_static, render


@fixture
def config():
    yield Config(
        site_title="Test Blog",
        site_description="A test blog",
        site_url="https://example.com",
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
    expected = {
        "index.html",
        "feed.xml",
        "posts/first-post/index.html",
        "posts/first-post/ajax.html",
        "posts/second-post/index.html",
        "posts/second-post/ajax.html",
    }
    assert expected == set(pages.keys())


def test_index_contains_post_titles():
    pages = render(config(), posts())
    assert "First Post" in pages["index.html"]
    assert "Second Post" in pages["index.html"]


def test_index_htmx_ajax_url():
    pages = render(config(), posts())
    assert "https://example.com/posts/first-post/ajax.html" in pages["index.html"]


def test_post_page_contains_body():
    pages = render(config(), posts())
    assert "<p>Hello world.</p>" in pages["posts/first-post/index.html"]


def test_post_page_has_back_link():
    pages = render(config(), posts())
    assert "https://example.com/" in pages["posts/first-post/index.html"]


def test_ajax_contains_body_only():
    pages = render(config(), posts())
    assert "<p>Hello world.</p>" in pages["posts/first-post/ajax.html"]
    assert "<!DOCTYPE html>" not in pages["posts/first-post/ajax.html"]


def test_ajax_contains_permalink():
    pages = render(config(), posts())
    assert "https://example.com/posts/first-post/" in pages["posts/first-post/ajax.html"]


def test_feed_contains_post_items():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    assert "<title>First Post</title>" in feed
    assert "<link>https://example.com/posts/first-post/</link>" in feed
    assert "<![CDATA[<p>Hello world.</p>]]>" in feed


def test_feed_channel_fields():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    assert "<title>Test Blog</title>" in feed
    assert "<link>https://example.com/</link>" in feed
    assert "<description>A test blog</description>" in feed


def test_feed_pubdate_rfc822_format():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    # 2024-03-15 is a Friday
    assert "<pubDate>Fri, 15 Mar 2024 00:00:00 +0000</pubDate>" in feed
    # 2024-01-01 is a Monday
    assert "<pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate>" in feed


def test_copy_static_copies_assets(tmp_path):
    count = copy_static(tmp_path)
    assert count >= 5
    assert (tmp_path / "default.css").is_file()
    assert (tmp_path / "fonts.css").is_file()
    assert (tmp_path / "htmx.min.js").is_file()
    assert (tmp_path / "alpinejs.min.js").is_file()
    woff2 = list(tmp_path.rglob("*.woff2"))
    assert len(woff2) >= 5
    with (tmp_path / "fonts" / "lora-latin-400-normal.woff2").open("rb") as f:
        assert f.read(4) == b"wOF2"


def test_index_has_no_cdn_dependencies():
    pages = render(config(), posts())
    assert "unpkg.com" not in pages["index.html"]
    assert "cdn.jsdelivr.net" not in pages["index.html"]


