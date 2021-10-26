"""
mkinit ~/code/line_profiler/line_profiler/__init__.py --relative
mkinit ~/code/line_profiler/line_profiler/__init__.py --relative -w
"""

__submodules__ = [
    'line_profiler',
]

from .line_profiler import __version__

from .line_profiler import (LineProfiler, LineProfilerMagics,
                            load_ipython_extension, load_stats, main,
                            show_func, show_text,)

__all__ = ['LineProfiler', 'LineProfilerMagics', 'line_profiler',
           'load_ipython_extension', 'load_stats', 'main', 'show_func',
           'show_text', '__version__']
