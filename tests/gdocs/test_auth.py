"""Offline tests for Google OAuth credential handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from docgit.gdocs.auth import GoogleAuthError, read_authorized_credentials


def test_invalid_token_starts_from_untrusted_state(tmp_path: Path) -> None:
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text("{}", encoding="utf-8")
    token_path = tmp_path / "token.json"
    token_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(GoogleAuthError, match="inválido"):
        read_authorized_credentials(credentials_path, token_path)


def test_missing_credentials_is_reported_without_secrets(tmp_path: Path) -> None:
    with pytest.raises(GoogleAuthError, match="Credenciais"):
        read_authorized_credentials(
            tmp_path / "credentials.json", tmp_path / "token.json"
        )
