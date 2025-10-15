"""
Профилирование кода для анализа производительности
"""
import cProfile
import pstats
import io
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

try:
    from pyinstrument import Profiler as PyInstrumentProfiler
except ImportError:
    PyInstrumentProfiler = None

try:
    from memory_profiler import profile as memory_profile
except ImportError:
    memory_profile = None

logger = logging.getLogger(__name__)


class ProfilerManager:
    """Менеджер профилирования для управления различными профайлерами"""
    
    def __init__(self, output_dir: str = "profiling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.active_profilers: Dict[str, Any] = {}
        self.profiling_enabled = False
        self._lock = threading.Lock()
        
    def enable(self):
        """Включить профилирование"""
        with self._lock:
            self.profiling_enabled = True
            logger.info("Profiling enabled")
    
    def disable(self):
        """Выключить профилирование"""
        with self._lock:
            self.profiling_enabled = False
            logger.info("Profiling disabled")
    
    def is_enabled(self) -> bool:
        """Проверить, включено ли профилирование"""
        return self.profiling_enabled
    
    @contextmanager
    def profile_context(self, name: str, profiler_type: str = "cprofile"):
        """
        Контекстный менеджер для профилирования блока кода
        
        Args:
            name: Имя профиля
            profiler_type: Тип профайлера ('cprofile', 'pyinstrument')
        """
        if not self.profiling_enabled:
            yield
            return
        
        profiler = None
        start_time = time.time()
        
        try:
            if profiler_type == "cprofile":
                profiler = cProfile.Profile()
                profiler.enable()
            elif profiler_type == "pyinstrument" and PyInstrumentProfiler:
                profiler = PyInstrumentProfiler()
                profiler.start()
            
            yield profiler
            
        finally:
            elapsed_time = time.time() - start_time
            
            if profiler:
                if profiler_type == "cprofile":
                    profiler.disable()
                    self._save_cprofile_results(profiler, name, elapsed_time)
                elif profiler_type == "pyinstrument" and PyInstrumentProfiler:
                    profiler.stop()
                    self._save_pyinstrument_results(profiler, name, elapsed_time)
    
    def _save_cprofile_results(self, profiler: cProfile.Profile, name: str, elapsed_time: float):
        """Сохранить результаты cProfile"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем в текстовый файл
        txt_file = self.output_dir / f"{name}_{timestamp}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"Profile: {name}\n")
            f.write(f"Elapsed time: {elapsed_time:.4f} seconds\n")
            f.write("=" * 80 + "\n\n")
            
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats(pstats.SortKey.CUMULATIVE)
            ps.print_stats(50)  # Top 50 functions
            f.write(s.getvalue())
        
        # Сохраняем в бинарный формат для дальнейшего анализа
        prof_file = self.output_dir / f"{name}_{timestamp}.prof"
        profiler.dump_stats(str(prof_file))
        
        logger.info(f"cProfile results saved: {txt_file}")
    
    def _save_pyinstrument_results(self, profiler: PyInstrumentProfiler, name: str, elapsed_time: float):
        """Сохранить результаты PyInstrument"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # HTML отчет
        html_file = self.output_dir / f"{name}_{timestamp}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(profiler.output_html())
        
        # Текстовый отчет
        txt_file = self.output_dir / f"{name}_{timestamp}_pyinstrument.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"Profile: {name}\n")
            f.write(f"Elapsed time: {elapsed_time:.4f} seconds\n")
            f.write("=" * 80 + "\n\n")
            f.write(profiler.output_text(unicode=True, color=False))
        
        logger.info(f"PyInstrument results saved: {html_file}")
    
    def profile_function(self, name: Optional[str] = None, profiler_type: str = "cprofile"):
        """
        Декоратор для профилирования функции
        
        Args:
            name: Имя профиля (по умолчанию - имя функции)
            profiler_type: Тип профайлера ('cprofile', 'pyinstrument')
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                profile_name = name or func.__name__
                
                if not self.profiling_enabled:
                    return func(*args, **kwargs)
                
                with self.profile_context(profile_name, profiler_type):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    async def profile_async_function(self, name: Optional[str] = None, profiler_type: str = "cprofile"):
        """
        Декоратор для профилирования асинхронной функции
        
        Args:
            name: Имя профиля (по умолчанию - имя функции)
            profiler_type: Тип профайлера ('cprofile', 'pyinstrument')
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                profile_name = name or func.__name__
                
                if not self.profiling_enabled:
                    return await func(*args, **kwargs)
                
                with self.profile_context(profile_name, profiler_type):
                    return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Получить сводку по сохраненным профилям"""
        profiles = list(self.output_dir.glob("*.txt"))
        
        return {
            "profiling_enabled": self.profiling_enabled,
            "output_directory": str(self.output_dir),
            "total_profiles": len(profiles),
            "recent_profiles": [
                {
                    "name": p.name,
                    "size": p.stat().st_size,
                    "created": datetime.fromtimestamp(p.stat().st_ctime).isoformat()
                }
                for p in sorted(profiles, key=lambda x: x.stat().st_ctime, reverse=True)[:10]
            ]
        }


# Глобальный экземпляр менеджера профилирования
profiler_manager = ProfilerManager()


def profile(name: Optional[str] = None, profiler_type: str = "cprofile"):
    """
    Удобный декоратор для профилирования функций
    
    Usage:
        @profile(name="my_function", profiler_type="pyinstrument")
        def my_function():
            # your code here
            pass
    """
    return profiler_manager.profile_function(name, profiler_type)


@contextmanager
def profile_block(name: str, profiler_type: str = "cprofile"):
    """
    Контекстный менеджер для профилирования блока кода
    
    Usage:
        with profile_block("my_code_block"):
            # your code here
            pass
    """
    with profiler_manager.profile_context(name, profiler_type):
        yield