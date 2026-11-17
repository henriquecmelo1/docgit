"""Run the user-assisted Google Drive integration spike."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import stat
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "docgit"
DEFAULT_CREDENTIALS_PATH = DEFAULT_CONFIG_DIR / "credentials.json"
DEFAULT_TOKEN_PATH = DEFAULT_CONFIG_DIR / "token.json"
VOLATILE_CORE_TAGS = frozenset({"lastModifiedBy", "created", "modified"})


class SpikeError(RuntimeError):
    """Raised when the spike cannot complete safely."""


@dataclass(frozen=True)
class ExportEvidence:
    """Safe evidence captured for one export."""

    byte_count: int
    normalized_hash: str
    fallback_hash: str


def _normalize_core_xml(content: bytes) -> bytes:
    """Remove volatile core properties without exposing document content."""
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError:
        return content

    for parent in root.iter():
        for child in list(parent):
            local_name = child.tag.rsplit("}", 1)[-1]
            if local_name in VOLATILE_CORE_TAGS:
                parent.remove(child)
    return ElementTree.tostring(root, encoding="utf-8")


def normalize_docx(docx: bytes) -> bytes:
    """Return deterministic DOCX bytes with volatile metadata removed."""
    try:
        source = zipfile.ZipFile(io.BytesIO(docx))
    except zipfile.BadZipFile as error:
        raise SpikeError("The exported content is not a valid DOCX archive.") from error

    entries: list[tuple[str, bytes]] = []
    with source:
        for info in source.infolist():
            content = source.read(info)
            if info.filename == "docProps/core.xml":
                content = _normalize_core_xml(content)
            entries.append((info.filename, content))

    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as target:
        for filename, content in sorted(entries):
            info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            target.writestr(info, content)
    return output.getvalue()


def normalized_hash(docx: bytes) -> str:
    """Hash deterministic DOCX bytes."""
    return hashlib.sha256(normalize_docx(docx)).hexdigest()


def fallback_hash(docx: bytes) -> str:
    """Hash document XML and styles as the plan-B normalization experiment."""
    try:
        source = zipfile.ZipFile(io.BytesIO(docx))
    except zipfile.BadZipFile as error:
        raise SpikeError("The exported content is not a valid DOCX archive.") from error

    selected: list[tuple[str, bytes]] = []
    with source:
        for filename in ("word/document.xml", "word/styles.xml"):
            try:
                content = source.read(filename)
            except KeyError:
                continue
            selected.append((filename, _normalize_core_xml(content)))

    digest = hashlib.sha256()
    for filename, content in selected:
        digest.update(filename.encode("utf-8"))
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _safe_file_permissions(path: Path) -> None:
    """Restrict local OAuth files when the platform supports POSIX modes."""
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _load_credentials(
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> Any:
    """Load or create OAuth credentials without exposing their contents."""
    if not credentials_path.is_file():
        raise SpikeError(f"Credentials file not found: {credentials_path}")

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as error:
        raise SpikeError(
            "Google dependencies are not installed; run pip install -e '.[dev]'."
        ) from error

    credentials = None
    if token_path.is_file():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(token_path), [DRIVE_SCOPE]
            )
        except (ValueError, KeyError):
            credentials = None
    if credentials is not None and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif credentials is None or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), [DRIVE_SCOPE]
        )
        credentials = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    _safe_file_permissions(token_path)
    return credentials


def _build_drive_service(credentials_path: Path, token_path: Path) -> Any:
    """Build a Drive API client using local OAuth credentials."""
    try:
        from googleapiclient.discovery import build
    except ImportError as error:
        raise SpikeError(
            "Google dependencies are not installed; run pip install -e '.[dev]'."
        ) from error
    credentials = _load_credentials(credentials_path, token_path)
    return build("drive", "v3", credentials=credentials)


def _export(service: Any, document_id: str) -> bytes:
    """Export a Google Doc as DOCX."""
    response = (
        service.files().export(fileId=document_id, mimeType=DOCX_MIME_TYPE).execute()
    )
    if not isinstance(response, bytes):
        raise SpikeError("Drive returned a non-binary DOCX export.")
    return response


def _evidence(docx: bytes) -> ExportEvidence:
    """Create safe evidence from exported bytes."""
    return ExportEvidence(
        byte_count=len(docx),
        normalized_hash=normalized_hash(docx),
        fallback_hash=fallback_hash(docx),
    )


def run_spike(
    document_id: str,
    *,
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> dict[str, Any]:
    """Run metadata, export, update, and repeated-export probes."""
    service = _build_drive_service(credentials_path, token_path)
    metadata = (
        service.files()
        .get(
            fileId=document_id,
            fields="id,webViewLink,modifiedTime,headRevisionId",
        )
        .execute()
    )
    first_export = _export(service, document_id)
    second_export = _export(service, document_id)
    first_evidence = _evidence(first_export)
    second_evidence = _evidence(second_export)
    update_response = (
        service.files()
        .update(
            fileId=document_id,
            media_body=_media_upload(first_export),
            fields="id,webViewLink",
        )
        .execute()
    )
    third_evidence = _evidence(_export(service, document_id))

    return {
        "auth": {"scope": DRIVE_SCOPE, "token_saved": token_path.is_file()},
        "export": {
            "first": _as_dict(first_evidence),
            "second": _as_dict(second_evidence),
            "third_after_update": _as_dict(third_evidence),
        },
        "update": {
            "same_file_id": update_response.get("id") == metadata.get("id"),
            "same_link": update_response.get("webViewLink")
            == metadata.get("webViewLink"),
        },
        "consecutive_hash_equal": (
            first_evidence.normalized_hash == second_evidence.normalized_hash
        ),
    }


def _media_upload(content: bytes) -> Any:
    """Create a Drive media upload lazily."""
    try:
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError as error:
        raise SpikeError(
            "Google dependencies are not installed; run pip install -e '.[dev]'."
        ) from error
    return MediaIoBaseUpload(
        io.BytesIO(content),
        mimetype=DOCX_MIME_TYPE,
        resumable=False,
    )


def _as_dict(evidence: ExportEvidence) -> dict[str, Any]:
    return {
        "byte_count": evidence.byte_count,
        "normalized_hash": evidence.normalized_hash,
        "fallback_hash": evidence.fallback_hash,
    }


def _parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document-id", required=True)
    parser.add_argument(
        "--results",
        type=Path,
        help="Optional path for safe JSON evidence; defaults to stdout.",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Run the spike and report safe evidence."""
    args = _parse_args(arguments)
    try:
        result = run_spike(args.document_id)
    except (OSError, SpikeError) as error:
        print(f"Spike failed: {error}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.results is None:
        print(rendered, end="")
    else:
        args.results.parent.mkdir(parents=True, exist_ok=True)
        args.results.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
