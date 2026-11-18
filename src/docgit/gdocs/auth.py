"""Google OAuth authentication for the CLI."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any

from docgit.core.exceptions import ProviderError

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
CONFIG_DIR = Path.home() / ".config" / "docgit"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"


class GoogleAuthError(ProviderError):
    """Raised when Google OAuth cannot be completed safely."""


def read_authorized_credentials(
    credentials_path: Path = CREDENTIALS_PATH,
    token_path: Path = TOKEN_PATH,
) -> Any:
    """Load a token or report the expected setup problem."""
    if not credentials_path.is_file():
        raise GoogleAuthError("Credenciais do Google não encontradas.")
    if not token_path.is_file():
        raise GoogleAuthError("Autenticação ainda não foi realizada.")
    try:
        token_path.read_text(encoding="utf-8")
        json.loads(token_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise GoogleAuthError("Token OAuth inválido.") from error

    try:
        from google.oauth2.credentials import Credentials
    except ImportError as error:
        raise GoogleAuthError("Dependências do Google não estão instaladas.") from error

    try:
        return Credentials.from_authorized_user_file(str(token_path), [DRIVE_SCOPE])
    except (ValueError, KeyError) as error:
        raise GoogleAuthError("Token OAuth inválido.") from error


def authenticate(
    credentials_path: Path = CREDENTIALS_PATH,
    token_path: Path = TOKEN_PATH,
) -> Any:
    """Authenticate and persist the OAuth token with restricted permissions."""
    if not credentials_path.is_file():
        raise GoogleAuthError("Credenciais do Google não encontradas.")

    credentials = None
    if token_path.is_file():
        try:
            credentials = read_authorized_credentials(credentials_path, token_path)
        except GoogleAuthError:
            credentials = None

    if credentials is not None:
        try:
            from google.auth.transport.requests import Request

            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            if credentials.valid:
                return credentials
        except (OSError, ValueError) as error:
            raise GoogleAuthError("Não foi possível renovar a autenticação.") from error

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as error:
        raise GoogleAuthError("Dependências do Google não estão instaladas.") from error

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), [DRIVE_SCOPE]
    )
    credentials = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    try:
        token_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return credentials


def document_id(value: str) -> str:
    """Extract a document ID from a Drive URL or return the provided ID."""
    value = value.strip()
    if "/d/" in value:
        return value.split("/d/", 1)[1].split("/", 1)[0]
    if value.startswith("https://"):
        return value
    return value
