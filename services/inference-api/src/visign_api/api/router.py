"""Main API v1 router combining system and prediction controllers (T026)."""

from fastapi import APIRouter
from visign_api.api.predictions import predictions_router
from visign_api.api.system import system_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(system_router)
api_v1_router.include_router(predictions_router)
