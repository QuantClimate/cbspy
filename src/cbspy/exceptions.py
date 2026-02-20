class CBSError(Exception):
    """Base exception for cbspy."""


class TableNotFoundError(CBSError):
    """Raised when a CBS table ID does not exist.

    Use client.list_tables() to discover available tables.
    """


class APIError(CBSError):
    """Raised when the CBS API returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"CBS API error {status_code}: {message}")
