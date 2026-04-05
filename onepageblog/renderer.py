from jinja2 import Environment, PackageLoader

from .config import Config
from .posts import Post

_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _rfc822_date(d):
    return f"{_DAYS[d.weekday()]}, {d.day:02d} {_MONTHS[d.month - 1]} {d.year} 00:00:00 +0000"


def render(config: Config, posts: list[Post]) -> dict[str, str]:
    env = Environment(
        loader=PackageLoader("onepageblog", "templates"),
        autoescape=True,
    )
    env.filters["rfc822_date"] = _rfc822_date

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
