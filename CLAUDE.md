# Documentation for Claude Code

## Commands

Use `uv run ...` before commands to execure them in the uv virtualenv.

- Install (dev): `uv pip install -e ".[dev]"`
- Python: `uv run python ...`
- Run tests: `uv run python -m testsweet`
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
render(config, posts)          → dict[str, str | bytes]  # {relative_path: content}
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

## File locations

| File                 | Path                                           |
|----------------------|------------------------------------------------|
| Design specs         | claude/specs/YYYY-MM-DD_design-name.md         |
| Implementation plans | claude/plans/YYYY-MM-DD_implementation-name.md |
