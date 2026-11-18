"""Command-line interface for docgit."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import typer

from docgit.core.branch_service import BranchService
from docgit.core.checkout_service import CheckoutService
from docgit.core.commit_service import CommitService
from docgit.core.exceptions import (
    DocgitError,
    ProviderNotConfiguredError,
)
from docgit.core.init_service import InitService
from docgit.core.log_service import LogService
from docgit.core.ports import Clock, DocumentProvider, Normalizer
from docgit.core.refs import Repository

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Git-style version control for Google Docs.",
)

_NOT_IMPLEMENTED = "[NOT IMPLEMENTED]"


@dataclass(frozen=True)
class Runtime:
    """Dependencies used to construct core services."""

    provider: DocumentProvider
    author: str
    clock: Clock
    normalizer: Normalizer


class RuntimeFactory(Protocol):
    """Factory injected by an adapter or integration test."""

    def create(self, document_id: str) -> Runtime:
        """Create runtime dependencies for a document."""


class _UnavailableRuntimeFactory:
    """Default factory until a document adapter is configured."""

    def create(self, document_id: str) -> Runtime:
        """Report that the phase-two provider is not configured."""
        raise ProviderNotConfiguredError(
            "Nenhum provider de documento foi configurado nesta fase."
        )


_runtime_factory: RuntimeFactory = _UnavailableRuntimeFactory()


def _configure_google_runtime_factory() -> None:
    """Configure the default runtime factory for Google-backed commands."""
    global _runtime_factory
    try:
        from docgit.gdocs.factory import GoogleRuntimeFactory
    except ImportError:
        return
    _runtime_factory = GoogleRuntimeFactory()


_configure_google_runtime_factory()


def configure_runtime_factory(factory: RuntimeFactory) -> None:
    """Inject a provider factory for the CLI."""
    global _runtime_factory
    _runtime_factory = factory


def _runtime(document_id: str) -> Runtime:
    return _runtime_factory.create(document_id)


def _existing_runtime() -> tuple[Runtime, Repository]:
    repository = Repository(Path.cwd())
    config = repository.read_config()
    return _runtime(config.document_id), repository


def _handle_error(error: DocgitError) -> None:
    """Translate a domain error into the CLI contract."""
    typer.echo(str(error), err=True)
    raise typer.Exit(code=1)


@app.command(help="Inicializar um repositório ligado a um Google Doc.")
def init(
    document_id: str = typer.Argument(..., help="URL ou ID do documento."),
) -> None:
    """Initialize a repository with the current document."""
    try:
        runtime = _runtime(document_id)
        commit = InitService(
            Path.cwd(),
            runtime.provider,
            runtime.author,
            runtime.clock,
            runtime.normalizer,
        ).initialize(document_id, Path.cwd().name)
    except DocgitError as error:
        _handle_error(error)
    typer.echo(f"Repositório criado. Commit inicial: {commit.hash[:7]}")


@app.command(help="Criar um commit com mensagem.")
def commit(
    message: str = typer.Option(..., "-m", help="Mensagem do commit."),
) -> None:
    """Create a commit for the current document."""
    try:
        runtime, _ = _existing_runtime()
        result = CommitService(
            Path.cwd(),
            runtime.provider,
            runtime.author,
            runtime.clock,
            runtime.normalizer,
        ).create(message)
    except (DocgitError, ValueError) as error:
        if isinstance(error, DocgitError):
            _handle_error(error)
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    if result.changed:
        typer.echo(f"{result.message} {result.commit_hash[:7]}")
    else:
        typer.echo(result.message)


@app.command(help="Listar o histórico da branch ativa.")
def log() -> None:
    """Print the active branch history."""
    try:
        history = LogService(Path.cwd()).history()
    except DocgitError as error:
        _handle_error(error)
    for item in history:
        typer.echo(
            f"commit {item.hash[:7]}\n"
            f"Author: {item.author}\n"
            f"Date: {item.timestamp}\n\n"
            f"    {item.message}\n"
        )


@app.command(help="Criar ou listar branches.")
def branch(
    name: str | None = typer.Argument(None, help="Nome da nova branch."),
    commit_reference: str | None = typer.Argument(
        None,
        help="Commit inicial da branch.",
    ),
) -> None:
    """List or create branches."""
    try:
        service = BranchService(Path.cwd())
        if name is None:
            for branch_name, active in service.list():
                typer.echo(f"{'*' if active else ' '} {branch_name}")
            return
        created_from = service.create(name, commit_reference)
    except DocgitError as error:
        _handle_error(error)
    typer.echo(f"Branch criada: {name} ({created_from[:7]})")


@app.command(help="Trocar de branch.")
def checkout(
    branch_name: str = typer.Argument(..., help="Branch de destino."),
    force: bool = typer.Option(False, "--force", help="Descartar alterações."),
) -> None:
    """Switch branches."""
    try:
        runtime, _ = _existing_runtime()
        target_hash = CheckoutService(
            Path.cwd(),
            runtime.provider,
            runtime.normalizer,
        ).checkout(branch_name, force)
    except DocgitError as error:
        _handle_error(error)
    if force:
        typer.echo("Aviso: alterações não commitadas foram descartadas.")
    typer.echo(f"Agora em {branch_name} ({target_hash[:7]}).")


def _not_implemented(command: str) -> None:
    """Report that a command belongs to a later implementation phase."""
    typer.echo(
        f"{command}: projeto ainda está em desenvolvimento. "
        "Execute `docgit --help` para ver os comandos disponíveis.",
        err=True,
    )
    raise typer.Exit(code=1)


@app.command(help="Autenticar no Google.")
def auth() -> None:
    """Authenticate with Google and persist the OAuth token."""
    try:
        from docgit.gdocs.auth import authenticate

        authenticate()
    except DocgitError as error:
        _handle_error(error)
    typer.echo("Autenticação concluída.")


@app.command(help=f"{_NOT_IMPLEMENTED} Mostrar alterações não commitadas.")
def status() -> None:
    """Show workspace status in a later phase."""
    _not_implemented("status")


@app.command(help=f"{_NOT_IMPLEMENTED} Restaurar um commit em um novo commit.")
def restore() -> None:
    """Restore a commit in a later phase."""
    _not_implemented("restore")


__all__ = ["Runtime", "app", "configure_runtime_factory"]
