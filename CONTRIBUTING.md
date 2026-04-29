# Contributing

## Testing

Uses [testsweet](https://test.pypi.org/project/testsweet/). Mark tests with
`@test` (functions or classes). Class-style tests can implement the
context-manager protocol for shared setup; the runner enters the class once
per class. Use `catch_exceptions()` to assert raised exceptions, and
`@test_params` for parametrized tests. Run with `uv run python -m testsweet`.

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
