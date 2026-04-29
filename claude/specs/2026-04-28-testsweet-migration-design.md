# Testsweet migration design

Date: 2026-04-28

## Goal

Replace pytest + pytest-unmagic with [testsweet](https://test.pypi.org/project/testsweet/)
as the project's test framework. Take the opportunity to consolidate
similar tests with `@test_params`.

## Scope

- Swap dev dependencies in `pyproject.toml`.
- Rewrite the four files under `tests/` to use testsweet idioms.
- Drop `tests/conftest.py` (the unmagic fence is no longer applicable).
- Update `CLAUDE.md` and `CONTRIBUTING.md`.

## Conventions

- **No `test_` prefix** on test files, functions, or methods. The
  `@test` decorator is what marks tests; the prefix is redundant.
- **No `Test` prefix** on test classes.
- Test files keep their current contents one-to-one with source modules:
  `tests/config.py`, `tests/posts.py`, `tests/renderer.py`,
  `tests/writer.py`.

## File layout

```
tests/
  __init__.py     (kept)
  config.py       (renamed from test_config.py)
  posts.py        (renamed from test_posts.py)
  renderer.py     (renamed from test_renderer.py)
  writer.py       (renamed from test_writer.py)
```

`tests/conftest.py` is deleted.

## `pyproject.toml`

```toml
[project.optional-dependencies]
dev = [
    "testsweet",
]

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

`explicit = true` keeps testpypi resolution scoped to packages
listed in `[tool.uv.sources]`.

`tests/__init__.py` matches `*.py` but contains no `@test`
decorators, so it is a harmless no-op for discovery.

**Fallback if testpypi is incomplete:** install testsweet from
GitHub instead.

```toml
[tool.uv.sources]
testsweet = { git = "https://github.com/kaapstorm/testsweet" }
```

In that case the `[[tool.uv.index]]` block is unnecessary.

## Replacement idioms

### `pytest.raises(Exc, match="x")` → `catch_exceptions()`

```python
with catch_exceptions() as excs:
    load_config(path)
assert type(excs[0]) is ValueError
assert "site_url" in str(excs[0])
```

`pytest.raises`'s `match` is a regex `search`; the existing matches
are plain substrings, so substring containment is equivalent.

### `tmp_path` → `tempfile.TemporaryDirectory`

The single use of pytest's `tmp_path` (in `copy_static_copies_assets`)
is converted to the same `tempfile.TemporaryDirectory` pattern the
rest of the suite already uses.

### `@unmagic.fixture` → class `__enter__`

`tests/renderer.py` is the only file with shared fixtures. It
becomes a `@test`-decorated class subclassing
`AbstractContextManager`, building `self.config`, `self.posts`, and
`self.pages = render(self.config, self.posts)` in `__enter__`.
The runner enters the class once per class (semantics like
`unittest.setUpClass`/`tearDownClass`), so `render()` runs once for
all assertions.

## Per-file rewrites

### `tests/config.py`

Seven flat `@test` functions, no consolidation:

- `load_config_fields`
- `load_config_resolves_paths_relative_to_config`
- `load_config_defaults_paths`
- `base_url_trailing_slash`
- `base_url_strips_trailing_slash_from_site_url`
- `invalid_site_url_raises`
- `missing_field_raises`

### `tests/posts.py`

Flat `@test` functions for happy paths:

- `load_single_post`
- `slug_derived_from_filename`
- `posts_sorted_by_date_descending`
- `author_is_optional`
- `empty_directory_returns_empty_list`
- `leading_bom_and_whitespace_are_tolerated`

One `@test_params` consolidating the five error cases (currently
`missing_frontmatter_field`, `missing_frontmatter_block`,
`empty_frontmatter`, `datetime_date_is_rejected`,
`invalid_date_type`):

```python
@test_params([
    ("missing_title",     "---\nauthor: N\ndate: 2024-01-01\n---\n",          "title"),
    ("missing_block",     "Just some text\n",                                   "frontmatter"),
    ("empty_frontmatter", "---\n---\nbody\n",                                   "YAML mapping"),
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

The `label` argument both names the test file written to disk and
distinguishes parameter rows in test output.

### `tests/renderer.py`

One `@test class Renderer(AbstractContextManager)` whose
`__enter__` constructs `self.config`, `self.posts`, and
`self.pages = render(self.config, self.posts)`. Methods:

- `returns_expected_keys`
- `index_contains_post_titles`
- `index_htmx_ajax_url`
- `post_page_contains_body`
- `post_page_has_back_link`
- `ajax_contains_body_only`
- `ajax_contains_permalink`
- `feed_contains_post_items`
- `feed_channel_fields`
- `feed_pubdate_rfc822_format`
- `index_has_no_cdn_dependencies`

One standalone `@test def copy_static_copies_assets()` using
`tempfile.TemporaryDirectory` — it has no need for the shared
render output, so it stays outside the class.

### `tests/writer.py`

Six flat `@test` functions, names matching the current ones with
the `test_` prefix removed:

- `write_creates_files`
- `write_creates_nested_subdirectories`
- `write_overwrites_existing_file`
- `write_creates_output_dir_if_missing`
- `clean_stale_posts_removes_missing_slugs`
- `clean_stale_posts_with_no_posts_dir`

## Documentation updates

### `CLAUDE.md`

Replace the test-running line with:

```
- Run tests: uv run python -m testsweet
```

### `CONTRIBUTING.md`

Replace the "Testing" section with:

> Uses [testsweet](https://test.pypi.org/project/testsweet/). Mark
> tests with `@test` (functions or classes). Class-style tests can
> implement the context-manager protocol for shared setup; the
> runner enters the class once per class. Use `catch_exceptions()`
> to assert raised exceptions, and `@test_params` for parametrized
> tests. Run with `uv run python -m testsweet`.

Drop the unmagic-specific paragraph and the "import from `unmagic`,
not `pytest_unmagic`" warning entirely.

## Order of work and verification

1. Update `pyproject.toml`. **Commit.**
2. Run `uv pip install -e ".[dev]"` to pull testsweet from
   testpypi. Verify with `uv run python -m testsweet --help` (or
   import). If testpypi is missing transitive deps, switch the
   source to the GitHub fallback above and reinstall.
3. Verify the install works.
4. Delete `tests/conftest.py`. **Commit.**
5. Rewrite the four test files, one at a time, running
   `uv run python -m testsweet tests/<file>.py` after each.
   **Commit after each file** (four commits).
6. Final full run: `uv run python -m testsweet`.
7. Update `CLAUDE.md` and `CONTRIBUTING.md`. **Commit.**
