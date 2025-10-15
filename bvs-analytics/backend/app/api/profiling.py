"""
API endpoints для управления профилированием
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import logging

from ..utils.profiler import profiler_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/profiling", tags=["profiling"])


class ProfilingStatus(BaseModel):
    """Статус профилирования"""
    enabled: bool
    output_directory: str
    total_profiles: int


class ProfilingConfig(BaseModel):
    """Конфигурация профилирования"""
    enabled: bool


class ProfileInfo(BaseModel):
    """Информация о профиле"""
    name: str
    size: int
    created: str


@router.post("/enable", response_model=ProfilingStatus)
async def enable_profiling():
    """
    Включить профилирование
    
    После включения все запросы будут профилироваться автоматически.
    Результаты сохраняются в директорию profiling_results/
    """
    profiler_manager.enable()
    stats = profiler_manager.get_stats_summary()
    
    logger.info("Profiling enabled via API")
    
    return ProfilingStatus(
        enabled=stats["profiling_enabled"],
        output_directory=stats["output_directory"],
        total_profiles=stats["total_profiles"]
    )


@router.post("/disable", response_model=ProfilingStatus)
async def disable_profiling():
    """
    Выключить профилирование
    
    После выключения запросы не будут профилироваться.
    """
    profiler_manager.disable()
    stats = profiler_manager.get_stats_summary()
    
    logger.info("Profiling disabled via API")
    
    return ProfilingStatus(
        enabled=stats["profiling_enabled"],
        output_directory=stats["output_directory"],
        total_profiles=stats["total_profiles"]
    )


@router.get("/status", response_model=ProfilingStatus)
async def get_profiling_status():
    """
    Получить текущий статус профилирования
    """
    stats = profiler_manager.get_stats_summary()
    
    return ProfilingStatus(
        enabled=stats["profiling_enabled"],
        output_directory=stats["output_directory"],
        total_profiles=stats["total_profiles"]
    )


@router.get("/profiles", response_model=List[ProfileInfo])
async def list_profiles():
    """
    Получить список всех сохраненных профилей
    """
    stats = profiler_manager.get_stats_summary()
    
    return [
        ProfileInfo(
            name=profile["name"],
            size=profile["size"],
            created=profile["created"]
        )
        for profile in stats["recent_profiles"]
    ]


@router.get("/profiles/{profile_name}")
async def download_profile(profile_name: str):
    """
    Скачать файл профиля
    
    Args:
        profile_name: Имя файла профиля (например, "my_function_20250115_123456.txt")
    """
    profile_path = profiler_manager.output_dir / profile_name
    
    if not profile_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile file '{profile_name}' not found"
        )
    
    # Проверяем, что файл находится в директории профилирования (безопасность)
    try:
        profile_path.resolve().relative_to(profiler_manager.output_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return FileResponse(
        path=profile_path,
        filename=profile_name,
        media_type="application/octet-stream"
    )


@router.delete("/profiles/{profile_name}")
async def delete_profile(profile_name: str):
    """
    Удалить файл профиля
    
    Args:
        profile_name: Имя файла профиля
    """
    profile_path = profiler_manager.output_dir / profile_name
    
    if not profile_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile file '{profile_name}' not found"
        )
    
    # Проверяем, что файл находится в директории профилирования (безопасность)
    try:
        profile_path.resolve().relative_to(profiler_manager.output_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    profile_path.unlink()
    logger.info(f"Deleted profile: {profile_name}")
    
    return {"message": f"Profile '{profile_name}' deleted successfully"}


@router.delete("/profiles")
async def clear_all_profiles():
    """
    Удалить все файлы профилей
    """
    deleted_count = 0
    
    for profile_file in profiler_manager.output_dir.glob("*"):
        if profile_file.is_file():
            profile_file.unlink()
            deleted_count += 1
    
    logger.info(f"Cleared all profiles: {deleted_count} files deleted")
    
    return {"message": f"Deleted {deleted_count} profile files"}