from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .utils import backup_file, validate_env_syntax, is_ci_environment


class DoteqError(Exception):
    """Base exception for doteq operations"""


class FileNotFoundError(DoteqError):
    """Raised when .env.example is missing"""


class ParseError(DoteqError):
    """Raised when file parsing fails"""


class PermissionError(DoteqError):
    """Raised when file permissions are insufficient"""


@dataclass
class EnvLine:
    raw: str
    number: int
    type: str
    key: Optional[str]
    value: Optional[str]
    comment: Optional[str]


class DoteqSync:
    def __init__(self, env_path: str, example_path: str, check_orphans: bool = False):
        self.env_path = env_path
        self.example_path = example_path
        self.check_orphans = check_orphans
        self.env_lines: List[EnvLine] = []
        self.example_lines: List[EnvLine] = []
        self._missing_keys: List[str] = []
        self._orphaned_keys: List[str] = []
        self._added_keys: List[str] = []

    def _determine_type(self, line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return "BLANK"
        if stripped.startswith("#"):
            return "COMMENT"
        if stripped.startswith("export "):
            return "EXPORT"
        return "KEY_VALUE"

    def _extract_key_value_comment(self, line: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if self._determine_type(line) in {"BLANK", "COMMENT"}:
            return None, None, line if line.strip().startswith("#") else None
        working = line
        if working.strip().startswith("export "):
            working = working.strip()[7:]
        if "#" in working:
            # preserve inline comment after unescaped '#'
            parts = working.split("#", 1)
            kv_part = parts[0].rstrip()
            comment = "#" + parts[1]
        else:
            kv_part = working.rstrip("\n")
            comment = None
        if "=" not in kv_part:
            return None, None, comment
        key, value = kv_part.split("=", 1)
        return key.strip(), value.strip(), comment

    def parse_env_file(self, file_path: str) -> List[EnvLine]:
        if not os.path.exists(file_path):
            # .env may not exist; allow empty
            if os.path.basename(file_path) == ".env":
                return []
            raise FileNotFoundError(f"Missing required file: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except PermissionError as exc:  # type: ignore[no-redef]
            raise PermissionError(str(exc))
        except OSError as exc:
            raise DoteqError(str(exc))

        try:
            validate_env_syntax(content)
        except Exception as exc:
            raise ParseError(str(exc))

        lines: List[EnvLine] = []
        for idx, raw in enumerate(content.splitlines(True), start=1):
            line_type = self._determine_type(raw)
            key, value, comment = self._extract_key_value_comment(raw)
            lines.append(EnvLine(raw=raw, number=idx, type=line_type, key=key, value=value, comment=comment))
        return lines

    def _collect_keys(self, lines: List[EnvLine]) -> List[str]:
        keys: List[str] = []
        for line in lines:
            if line.type in {"KEY_VALUE", "EXPORT"} and line.key:
                keys.append(line.key)
        return keys

    def find_missing_keys(self) -> List[str]:
        if not self.example_lines:
            self.example_lines = self.parse_env_file(self.example_path)
        if not self.env_lines:
            self.env_lines = self.parse_env_file(self.env_path)
        example_keys = set(self._collect_keys(self.example_lines))
        env_keys = set(self._collect_keys(self.env_lines))
        self._missing_keys = sorted(list(example_keys - env_keys))
        return self._missing_keys

    def find_orphaned_keys(self) -> List[str]:
        if not self.check_orphans:
            self._orphaned_keys = []
            return self._orphaned_keys
        if not self.example_lines:
            self.example_lines = self.parse_env_file(self.example_path)
        if not self.env_lines:
            self.env_lines = self.parse_env_file(self.env_path)
        example_keys = set(self._collect_keys(self.example_lines))
        env_keys = set(self._collect_keys(self.env_lines))
        self._orphaned_keys = sorted(list(env_keys - example_keys))
        return self._orphaned_keys

    def _build_appended_lines(self) -> List[str]:
        # Preserve existing .env content order; append missing keys at the end with empty values
        appended: List[str] = []
        example_key_to_value = {l.key: l.value for l in self.example_lines if l.key}
        for key in self._missing_keys:
            example_value = example_key_to_value.get(key, "") or ""
            rendered = f"{key}={example_value}\n"
            appended.append(rendered)
        return appended

    def sync_files(self, dry_run: bool = False) -> None:
        self.example_lines = self.parse_env_file(self.example_path)
        self.env_lines = self.parse_env_file(self.env_path)
        missing = self.find_missing_keys()
        orphans = self.find_orphaned_keys()
        self._added_keys = missing[:]

        if dry_run:
            return

        # Ensure directory exists
        env_dir = os.path.dirname(self.env_path) or "."
        os.makedirs(env_dir, exist_ok=True)

        # Atomic write
        with tempfile.NamedTemporaryFile("w", delete=False, dir=env_dir, encoding="utf-8") as tmp:
            # write original content as-is
            for line in self.env_lines:
                tmp.write(line.raw)
            # ensure there is a trailing newline before appending new keys
            if self.env_lines and not self.env_lines[-1].raw.endswith("\n"):
                tmp.write("\n")
            # append new keys
            for rendered in self._build_appended_lines():
                tmp.write(rendered)
            tmp_path = tmp.name

        # Backup then replace
        backup_file(self.env_path)
        try:
            os.replace(tmp_path, self.env_path)
        except PermissionError as exc:  # type: ignore[no-redef]
            raise PermissionError(str(exc))

    def generate_report(self) -> str:
        if is_ci_environment():
            report = {
                "status": "success",
                "added_keys": self._added_keys,
                "existing_keys": len(self._collect_keys(self.env_lines)),
                "orphaned_keys": self._orphaned_keys,
                "changes_count": len(self._added_keys),
            }
            return json.dumps(report)

        added_count = len(self._added_keys)
        existing_count = len(self._collect_keys(self.env_lines))
        orphan_hint = (
            f"⚠ Found {len(self._orphaned_keys)} orphaned key(s): {', '.join(self._orphaned_keys)}"
            if self._orphaned_keys
            else ""
        )
        lines = [
            "Doteq Report:",
            f"✓ Added {added_count} new keys to {os.path.basename(self.env_path)}",
            f"✓ Preserved {existing_count} existing values",
        ]
        if orphan_hint:
            lines.append(orphan_hint)
        if self._added_keys:
            lines.append("")
            lines.append("Changes made:")
            for key in self._added_keys:
                lines.append(f"  + {key} (added)")
        return "\n".join(lines)

