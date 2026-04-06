# Documentation for Claude Code

## Commands

The project uses a virtualenv in `.venv/` managed with uv. Activate it
with `source .venv/bin/activate`. Alternatively use `uv run ...` before
commands.

- Install (dev): `uv pip install -e ".[dev]"`
- Python: `uv run python ...`
- Run tests: `uv run pytest tests/ -v`
- Generate a site: `uv run onepageblog path/to/config.toml`
  Or: `uv run python -m onepageblog path/to/config.toml`

Static assets (fonts, HTMX, Alpine.js) are pre-built and committed to
`onepageblog/static/`. To rebuild them after updating npm dependencies:

- Install npm deps: `npm install`
- Rebuild assets: `npm run build`

## Architecture

Dataclass pipeline — each stage takes plain data in, returns plain data out:

```
load_config(path)              → Config
load_posts(config.posts_dir)   → list[Post]
render(config, posts)          → dict[str, str]  # {relative_path: content}
write(pages, config.output_dir)
```

Modules: `config.py`, `posts.py`, `renderer.py`, `writer.py`, `cli.py`.
Templates in `onepageblog/templates/*.j2` (Jinja2, loaded via `PackageLoader`).

## Post and config format

See `README.md` for the post frontmatter format and `config.toml` fields.
Key non-obvious point: the URL slug comes from the **filename** (not the title),
and `date` must be an unquoted `YYYY-MM-DD` value so PyYAML parses it as a
`datetime.date`.

See `CONTRIBUTING.md` for testing conventions and gotchas.
