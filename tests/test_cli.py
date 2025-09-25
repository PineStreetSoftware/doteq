from click.testing import CliRunner

from doteq.cli import main


def test_basic_sync(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / ".env.example"
    env.write_text("FOO=bar\n")
    example.write_text("FOO=bar\nBAR=baz\n")

    runner = CliRunner()
    result = runner.invoke(main, ["--env-file", str(env), "--example-file", str(example)])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_dry_run_mode(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / ".env.example"
    env.write_text("FOO=bar\n")
    example.write_text("FOO=bar\nBAR=baz\n")

    runner = CliRunner()
    result = runner.invoke(
        main, ["--env-file", str(env), "--example-file", str(example), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Would add" in result.output


def test_auto_detect_example_env(tmp_path):
    env = tmp_path / ".env"
    example = tmp_path / "example.env"
    env.write_text("FOO=bar\n")
    example.write_text("FOO=bar\nBAR=baz\n")

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=str(tmp_path)):
        result = runner.invoke(main, ["--env-file", str(env)])
        assert result.exit_code == 0
        assert "Added" in result.output


def test_create_example_when_missing(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAZ=qux\n")
    # Do not create example file on purpose

    runner = CliRunner()
    result = runner.invoke(main, ["--env-file", str(env), "--create-example", "--dry-run"])
    assert result.exit_code == 0
    # The CLI should have created an example at .env.example by default
    example = tmp_path / ".env.example"
    assert example.exists()
    content = example.read_text()
    # Keys should be written with empty values
    assert "FOO=\n" in content
    assert "BAZ=\n" in content


def test_create_example_env_name_option(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    # Ask for example.env instead of .env.example
    runner = CliRunner()
    result = runner.invoke(main, ["--env-file", str(env), "--create-example", "--example-name", "example.env", "--dry-run"])
    assert result.exit_code == 0
    example = tmp_path / "example.env"
    assert example.exists()
    content = example.read_text()
    assert "FOO=\n" in content

