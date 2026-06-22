# common/exceptions/base.py — Root domain exception (no HTTP knowledge)


class DomainError(Exception):
    """Base class for all domain errors.

    Attributes:
        status_code: HTTP 状态码，由各子类覆盖。
        biz_code:    业务码（对应 BizCode 常量）。
                     为 None 时由异常处理器按 status_code * 100 推算。
    """

    status_code: int = 400
    biz_code: int | None = None

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)
