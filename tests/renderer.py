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
