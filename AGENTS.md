# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `src/power_age/`. CLI entry points are in `src/power_age/cli.py`; data loading, validation, compute, and plotting are split into focused modules. Raw inputs go in `data/raw/`, generated tables in `data/processed/`, and charts in `outputs/figures/`. Static site assets for GitHub Pages live in `docs/`. Tests are in `tests/`.

## Build, Test, and Development Commands
Use the local virtual environment:

```bash
.venv/bin/python -m power_age.cli build
.venv/bin/python -m power_age.cli plot
.venv/bin/python -m power_age.cli summary
.venv/bin/python -m power_age.cli diagnostics
.venv/bin/pytest
.venv/bin/ruff check src tests
```

`build` regenerates processed CSVs, `plot` regenerates PNGs, and `summary`/`diagnostics` print sanity checks. For the docs site, run `cd docs && python3 -m http.server 8008`.

## Coding Style & Naming Conventions
Use Python 3.11+ style with 4-space indentation and type hints where they already fit the module. Prefer small, explicit functions and keep transformations in the existing module boundaries. Use `snake_case` for Python names, CSV columns, and file names. Preserve the current ASCII-first convention unless a file already uses localized text.

## Testing Guidelines
`pytest` is the test runner. Keep tests in `tests/test_*.py` and name new cases by behavior, not implementation. Add coverage for parsing, yearly aggregation, and any new chart or dataset logic that can fail silently. Run tests after data-model changes and before updating generated artifacts.

## Commit & Pull Request Guidelines
Commit history uses short, imperative prefixes such as `feat:`, `docs:`, and `fix:`. Keep commits scoped to one logical change. PRs should explain what changed, what data or outputs were regenerated, and include screenshots or links when `docs/` or chart output changes. Mention any assumptions if the dataset is incomplete.

## Data & Docs Notes
Do not edit generated files by hand if they are produced by the pipeline; regenerate them through the CLI instead. Keep `docs/` in sync with `data/processed/` when chart or summary logic changes.
