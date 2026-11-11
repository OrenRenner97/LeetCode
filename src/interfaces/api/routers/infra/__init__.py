"""Отрасль infra: один файл = один модуль из biz.infra."""
from fastapi import APIRouter

from . import rowkeys

router = APIRouter(prefix="/infra")
router.include_router(rowkeys.router)
