"""Отрасль biotech: один файл = один модуль из biz.biotech."""
from fastapi import APIRouter

from . import cloning

router = APIRouter(prefix="/biotech")
router.include_router(cloning.router)
