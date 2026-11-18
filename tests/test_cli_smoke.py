from typer.testing import CliRunner

from docgit.cli import app

runner = CliRunner()


def test_help_lists_all_phase_one_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in (
        "auth",
        "init",
        "status",
        "commit",
        "log",
        "branch",
        "checkout",
        "restore",
    ):
        assert command in result.stdout


def test_help_marks_unimplemented_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert result.stdout.count("[NOT IMPLEMENTED]") == 2


def test_unimplemented_command_explains_development_status() -> None:
    result = runner.invoke(app, ["status"])

    assert result.exit_code != 0
    assert "projeto ainda está em desenvolvimento" in result.output
    assert "docgit --help" in result.output
