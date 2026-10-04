from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


class AppError(Exception):
    """Business-rule error with a user-friendly message."""

    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        self.message, self.status_code, self.code = message, status_code, code


class MissingFinancialData(AppError):
    def __init__(self, field_label: str):
        super().__init__(
            f"I don't have enough information to calculate that. Please enter your {field_label}.",
            422, "missing_data",
        )


def _body(code: str, message: str, details=None):
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(_: Request, exc: AppError):
        return JSONResponse(_body(exc.code, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        problems = [
            f"{'.'.join(str(p) for p in e['loc'] if p != 'body')}: {e['msg']}" for e in exc.errors()
        ]
        return JSONResponse(
            _body("validation_error", "Some of the information you entered is not valid.", problems),
            status_code=422,
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_error(_: Request, exc: SQLAlchemyError):
        return JSONResponse(
            _body("database_error", "Something went wrong while saving your data. Please try again."),
            status_code=500,
        )