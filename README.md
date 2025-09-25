# Doteq

Keep `.env` files synchronized with `.env.example` across environments.

## Features

- Syncs missing keys from example to env without overwriting existing values
- Preserves comments and blank lines; appends new keys at the end
- Understands `KEY=VALUE`, quoted values, `export KEY=VALUE`, and basic multiline values
- Auto-detects example file: `.env.example` or `example.env` (relative to the env file directory)
- Can create a missing example file (with empty values) from your existing `.env` using `--create-example`
- Dry-run preview with no changes
- Orphan check to warn about keys present in `.env` but not in the example
- Atomic writes with timestamped backups (mode 600)
- CI-friendly JSON output when `CI` env var is present (e.g., GitHub Actions)

## Installation

```bash
pip install git+https://github.com/PineStreetSoftware/doteq.git@main

```

## Quick Start

```bash
doteq                      # Basic sync using .env and .env.example
doteq --dry-run            # Preview changes
doteq --check-orphans      # Warn about keys present only in .env
doteq --create-example     # If example is missing, create it from .env keys (empty values)
doteq --create-example --example-name example.env   # Create example as example.env instead of .env.example
doteq --env-file .env.local              # Auto-detects .env.example or example.env
doteq --example-file example.env         # Explicit example file path
```

## CLI Options

- `--env-file` (default: `.env`)
- `--example-file` (default: auto-detect `.env.example` or `example.env`)
- `--check-orphans` (flag)
- `--dry-run` (flag)
- `--quiet` (flag)
- `--verbose` (flag)

## Examples

```bash
# Auto-detect example file (.env.example or example.env)
doteq --env-file .env --dry-run
doteq --env-file .env

# Explicit example file path
doteq --env-file .env --example-file example.env --dry-run

# Warn about keys in .env that are not in the example
doteq --check-orphans
```

## How it works

1. Parses both files while preserving raw lines, comments, and spacing.
2. Finds keys present in the example but missing from the target `.env`.
3. Appends missing keys at the end of `.env` without changing existing values.
4. Writes atomically (temp file + rename) and creates a timestamped backup of the original `.env`.
5. When `--create-example` is used and no example file is found, it generates one next to your `.env` with the same keys but empty values (e.g., `FOO=bar` becomes `FOO=`). You can choose the filename with `--example-name` (default: `.env.example`; alternative: `example.env`).

## CI usage

When `CI` is set (or running on GitHub Actions/CircleCI/GitLab CI), output is JSON.

```bash
doteq --env-file .env | jq
# {
#   "status": "success",
#   "added_keys": ["FOO", "BAR"],
#   "existing_keys": 12,
#   "orphaned_keys": [],
#   "changes_count": 2
# }
```

## Safety

- Creates backups like `.env.bak.20250101-120000` with permissions `600`.
- Never prints values, only key names and counts.

## Development

```bash
pip install -e .[dev]
pytest --cov=doteq
```

## License

MIT

