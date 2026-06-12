from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _status_title(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Error"


def _error_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        413: "request_too_large",
        422: "validation_error",
        429: "rate_limit_exceeded",
    }.get(status_code, "api_error")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def problem_response(
    request: Request,
    *,
    status_code: int,
    detail: Any,
    code: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    error = {
        "code": code or _error_code(status_code),
        "message": detail if isinstance(detail, str) else _status_title(status_code),
        "request_id": request_id,
    }
    payload = {
        "type": "about:blank",
        "title": _status_title(status_code),
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "request_id": request_id,
        "error": error,
    }
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return problem_response(
        request,
        status_code=exc.status_code,
        detail=exc.detail,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem_response(
        request,
        status_code=422,
        code="validation_error",
        detail=exc.errors(),
    )
