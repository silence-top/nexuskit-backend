# common/exceptions/base.py — Root domain exception (no HTTP knowledge)


class DomainError(Exception):
    """Base class for all domain errors."""

    status_code: int = 400

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)
