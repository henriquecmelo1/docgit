"""Clock implementations."""

from datetime import UTC, datetime


class SystemClock:
    """Provide the current UTC time."""

    def now(self) -> datetime:
        """Return the current UTC datetime."""
        return datetime.now(UTC)
