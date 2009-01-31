
from distutils.core import setup
from distutils.extension import Extension
from distutils.log import warn
import os
import sys

try:
    from Cython.Distutils import build_ext
    cmdclass = dict(build_ext=build_ext)
    line_profiler_source = '_line_profiler.pyx'
except ImportError, e:
    warn("Could not import Cython. Using pre-generated C file if available.")
    cmdclass = {}
    line_profiler_source = '_line_profiler.c'

long_description = """\
line_profiler will profile the time individual lines of code take to execute.
The profiler is implemented in C via Cython in order to reduce the overhead of
profiling.

Also included is the script kernprof.py which can be used to conveniently
profile Python applications and scripts either with line_profiler or with the
function-level profiling tools in the Python standard library.
"""

setup(
    name = 'line_profiler',
    version = '1.0b2',
    author = 'Robert Kern',
    author_email = 'robert.kern@enthought.com',
    description = 'Line-by-line profiler.',
    long_description = long_description,
    url = 'http://packages.python.org/line_profiler',
    ext_modules = [ 
        Extension('_line_profiler',
                  sources=[line_profiler_source, 'timers.c'],
                  depends=['python25.pxd'],
        ),
    ],
    license = "BSD",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: C",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
    py_modules = ['line_profiler'],
    scripts = ['kernprof.py'],
    cmdclass = cmdclass,
)

