from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from docgit.cli import Runtime, app, configure_runtime_factory
from docgit.core.ports import IdentityNormalizer

runner = CliRunner()


class FakeProvider:
    def __init__(self) -> None:
        self.content = b"initial"
        self.version = 1

    def export_docx(self) -> bytes:
        return self.content

    def replace_content(self, docx: bytes) -> None:
        self.content = docx
        self.version += 1

    def modified_time(self) -> str:
        return f"version-{self.version}"


@dataclass
class FixedClock:
    value: datetime = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.value


class Factory:
    def __init__(self, provider: FakeProvider) -> None:
        self.provider = provider

    def create(self, document_id: str) -> Runtime:
        return Runtime(
            self.provider,
            "Henri <henri@example.com>",
            FixedClock(),
            IdentityNormalizer(),
        )


def test_cli_core_flow(tmp_path: Path, monkeypatch) -> None:
    provider = FakeProvider()
    configure_runtime_factory(Factory(provider))
    monkeypatch.chdir(tmp_path)

    initialized = runner.invoke(app, ["init", "document-id"])
    provider.content = b"committed-change"
    committed = runner.invoke(app, ["commit", "-m", "Update document"])
    created = runner.invoke(app, ["branch", "feature"])
    listed = runner.invoke(app, ["branch"])
    checked_out = runner.invoke(app, ["checkout", "feature"])
    history = runner.invoke(app, ["log"])

    assert initialized.exit_code == 0
    assert committed.exit_code == 0
    assert created.exit_code == 0
    assert listed.exit_code == 0
    assert "* main" in listed.stdout
    assert checked_out.exit_code == 0
    assert history.exit_code == 0
    assert "Initial commit" in history.stdout
