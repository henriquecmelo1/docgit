"""Command-line interface for docgit."""

import typer

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Git-style version control for Google Docs.",
)

_NOT_IMPLEMENTED = "[NOT IMPLEMENTED]"


def _not_implemented(command: str) -> None:
    """Report that a command is reserved for a later implementation phase."""
    typer.echo(
        f"{command}: projeto ainda está em desenvolvimento. "
        "Execute `docgit --help` para ver os comandos disponíveis.",
        err=True,
    )
    raise typer.Exit(code=1)


def _register_stub(
    name: str,
    help_text: str,
) -> None:
    """Register a command whose behavior belongs to a later phase."""

    def command() -> None:
        _not_implemented(name)

    command.__name__ = name
    app.command(name=name, help=f"{_NOT_IMPLEMENTED} {help_text}")(command)


_register_stub("auth", "Autenticar no Google.")
_register_stub("init", "Inicializar um repositório ligado a um Google Doc.")
_register_stub("status", "Mostrar alterações não commitadas.")
_register_stub("commit", "Criar um commit com mensagem.")
_register_stub("log", "Listar o histórico da branch ativa.")
_register_stub("branch", "Criar ou listar branches.")
_register_stub("checkout", "Trocar de branch.")
_register_stub("restore", "Restaurar um commit em um novo commit.")

__all__ = ["app"]
