"""Единый формат ошибок API и их документация в OpenAPI.

Коды:
  400 — запрос корректен по схеме, но не выполним (например, backend недоступен на этом сервере);
  422 — запрос не прошёл валидацию схемы (FastAPI генерирует сам).
Доменные ошибки «внутри» операции (нехватка баланса и т.п.) — не HTTP-ошибки, а часть ответа:
так клиент получает результат пакета целиком, а не падение на первой проблеме.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from algos import BackendUnavailable


class ErrorResponse(BaseModel):
    detail: str = Field(description="Человекочитаемое описание ошибки",
                        examples=["find_pair_with_sum: backend 'quantum' недоступен, есть ['numba', 'python']"])


BAD_BACKEND = {400: {"model": ErrorResponse, "description": "Запрошенный backend недоступен на этом сервере (см. `GET /backends`)"}}


def install(app: FastAPI) -> None:
    @app.exception_handler(BackendUnavailable)
    async def _backend_unavailable(_: Request, exc: BackendUnavailable) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
