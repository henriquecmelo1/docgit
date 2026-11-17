"""Git author configuration."""

import subprocess

from docgit.core.exceptions import AuthorNotConfiguredError


def git_author() -> str:
    """Read the repository-local Git author configuration."""
    try:
        name = subprocess.run(
            ["git", "config", "--local", "--get", "user.name"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "--local", "--get", "user.email"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise AuthorNotConfiguredError(
            "Configure git user.name e user.email antes de criar commits."
        ) from error
    if not name or not email:
        raise AuthorNotConfiguredError(
            "Configure git user.name e user.email antes de criar commits."
        )
    return f"{name} <{email}>"
