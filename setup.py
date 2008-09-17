from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    name = 'line_profiler',
    version = "0.1",
    ext_modules = [ 
        Extension('_line_profiler',
                  sources=['_line_profiler.pyx', 'timers.c'],
        ),
    ],
    license = "BSD",
    py_modules = ['line_profiler'],
    cmdclass = {'build_ext': build_ext},
)

