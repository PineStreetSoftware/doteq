from doteq.sync import DoteqSync


def test_parse_simple_env(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / ".env.example"
    env.write_text("FOO=bar\n")
    example.write_text("FOO=bar\nBAR=baz\n")

    syncer = DoteqSync(str(env), str(example))
    env_lines = syncer.parse_env_file(str(env))
    assert any(l.key == "FOO" for l in env_lines)


def test_preserve_comments(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / ".env.example"
    env.write_text("# comment\nFOO=bar\n")
    example.write_text("# sample\nFOO=bar\nBAR=baz\n")

    syncer = DoteqSync(str(env), str(example))
    syncer.sync_files(dry_run=False)
    result = env.read_text()
    assert "# comment" in result
    assert "BAR=" in result


def test_handle_multiline_values(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / ".env.example"
    env.write_text("FOO=bar\n")
    example.write_text("FOO=bar\nMULTI='line1\\nline2'\n")

    syncer = DoteqSync(str(env), str(example))
    syncer.sync_files(dry_run=False)
    result = env.read_text()
    assert "MULTI=" in result


def test_append_with_missing_trailing_newline(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / ".env.example"
    # .env without trailing newline
    env.write_text("EXISTING=value")
    # example includes an additional key
    example.write_text("EXISTING=value\nNEW_KEY=123\n")

    syncer = DoteqSync(str(env), str(example))
    syncer.sync_files(dry_run=False)

    result = env.read_text()
    # Ensure existing line preserved exactly and new key starts on a new line
    assert result.startswith("EXISTING=value\n")
    assert "\nNEW_KEY=123\n" in result or result.endswith("\nNEW_KEY=123\n")

