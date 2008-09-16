from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    name = 'line_profiler',
    ext_modules=[ 
        Extension('_line_profiler',
                  sources=['_line_profiler.pyx', 'timers.c'],
                  extra_compile_args=['-fno-inline'],
        ),
    ],
    py_modules=['line_profiler'],
    cmdclass = {'build_ext': build_ext},
)

