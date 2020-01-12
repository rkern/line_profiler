"""
mkinit ~/code/line_profiler/line_profiler/__init__.py --relative
mkinit ~/code/line_profiler/line_profiler/__init__.py --relative -w
"""

__submodules__ = [
    'line_profiler',
]

from .line_profiler import __version__

from .line_profiler import (CO_GENERATOR, LineProfiler, LineProfilerMagics,
                            PY3, PY35, exec_, is_coroutine, is_generator,
                            load_ipython_extension, load_stats, main,
                            show_func, show_text,)

__all__ = ['CO_GENERATOR', 'LineProfiler', 'LineProfilerMagics', 'PY3', 'PY35',
           'exec_', 'is_coroutine', 'is_generator', 'line_profiler',
           'load_ipython_extension', 'load_stats', 'main', 'show_func',
           'show_text', '__version__']
