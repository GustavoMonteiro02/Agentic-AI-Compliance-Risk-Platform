from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar

from fastapi import Query, Response

T = TypeVar("T")


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int


def get_pagination(
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


def paginate(items: Sequence[T], pagination: PaginationParams, response: Response) -> list[T]:
    total = len(items)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(pagination.limit)
    response.headers["X-Offset"] = str(pagination.offset)
    return list(items[pagination.offset : pagination.offset + pagination.limit])
