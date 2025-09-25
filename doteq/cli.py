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
@click.option("--check-orphans", is_flag=True, help="Warn about keys in .env not in .env.example")
@click.option("--dry-run", is_flag=True, help="Show what would be changed without making changes")
@click.option("--quiet", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def main(env_file: str, example_file: Optional[str], check_orphans: bool, dry_run: bool, quiet: bool, verbose: bool) -> None:
    # Resolve example file: prefer explicit, otherwise try .env.example then example.env
    if example_file is None:
        env_dir = os.path.dirname(env_file) or "."
        candidates = [os.path.join(env_dir, ".env.example"), os.path.join(env_dir, "example.env")]
        resolved_example = None
        for path in candidates:
            if os.path.exists(path):
                resolved_example = path
                break
        example_path = resolved_example or candidates[0]
    else:
        # If explicitly provided, use as-is (even if missing, to surface a clear error)
        example_path = example_file

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

