# Contributing

## Testing

Uses pytest + pytest-unmagic. Fixtures are explicit imports — **import from
`unmagic`, not `pytest_unmagic`**:

```python
from unmagic import fixture

@fixture
def my_fixture():
    yield value

def test_something():
    val = my_fixture()   # calling fixture() triggers setup; no @use needed
    assert val == expected
```

`tests/conftest.py` installs an unmagic fence that warns if any test uses
magic (name-matching) pytest fixtures.

## Gotchas

- **Slug from filename:** post URL slug = filename stem, not title. Filename
  uniqueness is enforced by the filesystem.
- **`| safe` in templates:** `post.body_html` is pre-rendered HTML. Templates
  use `{{ post.body_html | safe }}` to bypass Jinja2 autoescape. Don't remove it.
- **`rfc822_date` filter:** `renderer.py` registers a custom Jinja2 filter for
  locale-safe RFC 822 date formatting. `feed.xml.j2` uses
  `{{ post.date | rfc822_date }}`; do not replace with `strftime` (locale-sensitive
  on non-English servers).
- **Templates are package data:** declared in `pyproject.toml` under
  `[tool.setuptools.package-data]`. After adding a template, re-run
  `uv pip install -e .` so `PackageLoader` can find it.
