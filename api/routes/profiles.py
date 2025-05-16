from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_engine
from free_vigilance_reduction.core import FreeVigilanceReduction
from typing import List

router = APIRouter()

@router.get("/profiles", summary="Получить список профилей", tags=["Profiles"])
def get_profiles(engine: FreeVigilanceReduction = Depends(get_engine)) -> List[str]:
    """
    Возвращает список всех доступных профилей конфигурации.
    """
    profile_ids = engine.config_manager.get_profile_list()
    profiles = [engine.config_manager.get_profile(pid).to_dict() for pid in profile_ids]

    if not profiles:
        raise HTTPException(status_code=404, detail="Нет доступных профилей")
    return [profile["profile_id"] for profile in profiles]
