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

