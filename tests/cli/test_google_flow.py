"""Google runtime CLI integration test using an injected fake provider."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from docgit.cli import Runtime, app, configure_runtime_factory
from docgit.core.ports import IdentityNormalizer

runner = CliRunner()


class FakeGoogleProvider:
    def __init__(self) -> None:
        self.content = b"google-initial"
        self.version = 1

    def export_docx(self) -> bytes:
        return self.content

    def replace_content(self, docx: bytes) -> None:
        self.content = docx
        self.version += 1

    def modified_time(self) -> str:
        return f"google-{self.version}"


@dataclass(frozen=True)
class FixedClock:
    value: datetime = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.value


class GoogleFactory:
    def __init__(self, provider: FakeGoogleProvider) -> None:
        self.provider = provider

    def create(self, document_id: str) -> Runtime:
        assert document_id
        return Runtime(
            provider=self.provider,
            author="Henri <henri@example.com>",
            clock=FixedClock(),
            normalizer=IdentityNormalizer(),
        )


def test_google_runtime_flow(tmp_path: Path, monkeypatch) -> None:
    provider = FakeGoogleProvider()
    configure_runtime_factory(GoogleFactory(provider))
    monkeypatch.chdir(tmp_path)

    initialized = runner.invoke(app, ["init", "document-id"])
    provider.content = b"google-change"
    committed = runner.invoke(app, ["commit", "-m", "Google update"])
    branched = runner.invoke(app, ["branch", "feature"])
    checked_out = runner.invoke(app, ["checkout", "feature"])
    history = runner.invoke(app, ["log"])

    assert initialized.exit_code == 0
    assert committed.exit_code == 0
    assert branched.exit_code == 0
    assert checked_out.exit_code == 0
    assert history.exit_code == 0
    assert "Google update" in history.stdout
