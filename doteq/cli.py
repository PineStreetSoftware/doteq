import json
import os
import sys
from typing import Optional

import click

from .sync import DoteqSync
from .utils import colorize_output, is_ci_environment, sanitize_for_ci


@click.command()
@click.option("--env-file", default=".env", help="Path to environment file")
@click.option("--example-file", default=None, help="Path to example file (defaults: .env.example or example.env)")
@click.option(
    "--create-example",
    is_flag=True,
    help="If example file is missing, create it from keys in --env-file with empty values",
)
@click.option(
    "--example-name",
    type=click.Choice([".env.example", "example.env"]),
    default=".env.example",
    show_default=True,
    help="When creating an example, choose the filename (ignored if --example-file is provided)",
)
@click.option("--check-orphans", is_flag=True, help="Warn about keys in .env not in .env.example")
@click.option("--dry-run", is_flag=True, help="Show what would be changed without making changes")
@click.option("--quiet", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def main(env_file: str, example_file: Optional[str], create_example: bool, example_name: str, check_orphans: bool, dry_run: bool, quiet: bool, verbose: bool) -> None:
    # Resolve example file: prefer explicit, otherwise try .env.example then example.env
    if example_file is None:
        env_dir = os.path.dirname(env_file) or "."
        candidates = [os.path.join(env_dir, ".env.example"), os.path.join(env_dir, "example.env")]
        resolved_example = None
        for path in candidates:
            if os.path.exists(path):
                resolved_example = path
                break
        # If nothing exists, choose based on --example-name
        example_path = resolved_example or os.path.join(env_dir, example_name)
    else:
        # If explicitly provided, use as-is (even if missing, to surface a clear error)
        example_path = example_file

    # Optionally create an example file if missing
    if create_example and not os.path.exists(example_path):
        try:
            # Collect keys from the provided env file, if present
            keys: list[str] = []
            if os.path.exists(env_file):
                tmp_sync = DoteqSync(env_file, env_file)
                env_lines = tmp_sync.parse_env_file(env_file)
                for line in env_lines:
                    if line.key:
                        keys.append(line.key)

            os.makedirs(os.path.dirname(example_path) or ".", exist_ok=True)
            with open(example_path, "w", encoding="utf-8") as f:
                for key in keys:
                    f.write(f"{key}=\n")
            # If no keys were found, still create an empty file
        except Exception as exc:  # pragma: no cover
            message = f"Failed to create example file at {example_path}: {exc}"
            if is_ci_environment():
                click.echo(json.dumps({"status": "error", "message": message}))
            else:
                click.echo(colorize_output(f"Error: {message}", "red"), err=True)
            sys.exit(1)

    syncer = DoteqSync(env_file, example_path, check_orphans=check_orphans)

    try:
        syncer.sync_files(dry_run=dry_run)
    except Exception as exc:
        message = str(exc)
        if is_ci_environment():
            payload = {"status": "error", "message": sanitize_for_ci(message)}
            click.echo(json.dumps(payload))
        else:
            click.echo(colorize_output(f"Error: {message}", "red"), err=True)
        sys.exit(1)

    report = syncer.generate_report() if not dry_run else None

    if is_ci_environment():
        if dry_run:
            payload = {
                "status": "dry-run",
                "message": "Preview only - no changes applied",
                "added_keys": syncer.find_missing_keys(),
            }
            click.echo(json.dumps(payload))
        else:
            click.echo(report)
        sys.exit(0)

    if quiet:
        sys.exit(0)

    if dry_run:
        missing = syncer.find_missing_keys()
        lines = [
            "Doteq Preview (--dry-run):",
            f"Would add {len(missing)} keys to {env_file}:",
        ]
        for key in missing:
            lines.append(f"  + {key}=")
        lines.append("")
        lines.append("No changes made. Run without --dry-run to apply changes.")
        click.echo("\n".join(lines))
        sys.exit(0)

    click.echo(report)

