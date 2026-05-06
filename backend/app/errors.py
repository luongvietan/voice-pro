"""Domain errors surfaced through API / tasks."""


class CreditExhaustedError(Exception):
    """Free-tier user lacks balance for billed minutes after STT."""

