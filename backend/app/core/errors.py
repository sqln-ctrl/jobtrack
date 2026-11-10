class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFound(AppError):
    status_code = 404


class Conflict(AppError):
    status_code = 409


class BadRequest(AppError):
    status_code = 400
