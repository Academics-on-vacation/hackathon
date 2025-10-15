"""
Middleware для профилирования HTTP запросов
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.profiler import profiler_manager

logger = logging.getLogger(__name__)


class ProfilingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для автоматического профилирования HTTP запросов
    
    Профилирует только те запросы, для которых включено профилирование
    через profiler_manager.enable()
    """
    
    def __init__(
        self,
        app: ASGIApp,
        profiler_type: str = "cprofile",
        profile_all: bool = False,
        min_duration: float = 0.0
    ):
        """
        Args:
            app: ASGI приложение
            profiler_type: Тип профайлера ('cprofile' или 'pyinstrument')
            profile_all: Профилировать все запросы (игнорируя флаг enabled)
            min_duration: Минимальная длительность запроса для профилирования (секунды)
        """
        super().__init__(app)
        self.profiler_type = profiler_type
        self.profile_all = profile_all
        self.min_duration = min_duration
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обработка запроса с профилированием"""
        
        # Пропускаем статические файлы и health check
        if self._should_skip_profiling(request):
            return await call_next(request)
        
        # Проверяем, нужно ли профилировать
        should_profile = self.profile_all or profiler_manager.is_enabled()
        
        if not should_profile:
            return await call_next(request)
        
        # Создаем имя профиля на основе метода и пути
        profile_name = f"{request.method}_{request.url.path.replace('/', '_')}"
        
        # Замеряем время выполнения
        start_time = time.time()
        
        # Профилируем запрос
        with profiler_manager.profile_context(profile_name, self.profiler_type):
            response = await call_next(request)
        
        elapsed_time = time.time() - start_time
        
        # Логируем информацию о запросе
        if elapsed_time >= self.min_duration:
            logger.info(
                f"Profiled request: {request.method} {request.url.path} "
                f"- {elapsed_time:.4f}s - Status: {response.status_code}"
            )
        
        # Добавляем заголовок с временем выполнения
        response.headers["X-Process-Time"] = str(elapsed_time)
        
        return response
    
    def _should_skip_profiling(self, request: Request) -> bool:
        """Определить, нужно ли пропустить профилирование для этого запроса"""
        path = request.url.path
        
        # Пропускаем статические файлы
        static_extensions = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp')
        if any(path.endswith(ext) for ext in static_extensions):
            return True
        
        # Пропускаем служебные эндпоинты
        skip_paths = ['/health', '/docs', '/redoc', '/openapi.json', '/favicon.ico']
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            return True
        
        return False