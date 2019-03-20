import sys

import distutils.errors
from distutils.core import setup
from distutils.extension import Extension

try:
    from Cython.Distutils import build_ext
    cmdclass = dict(build_ext=build_ext)
    line_profiler_source = '_line_profiler.pyx'
except ImportError:
    raise distutils.errors.DistutilsError("""\
You need Cython to build the line_profiler from a git checkout, or
alternatively use a release tarball from PyPI to build it without Cython.""")


long_description = """\
line_profiler will profile the time individual lines of code take to execute.
The profiler is implemented in C via Cython in order to reduce the overhead of
profiling.

Also included is the script kernprof.py which can be used to conveniently
profile Python applications and scripts either with line_profiler or with the
function-level profiling tools in the Python standard library.
"""


py_modules = ['line_profiler', 'kernprof']
if sys.version_info > (3, 4):
    py_modules += ['line_profiler_py35']

setup(
    name = 'line_profiler',
    version = '2.1.1',
    author = 'Robert Kern',
    author_email = 'robert.kern@enthought.com',
    description = 'Line-by-line profiler.',
    long_description = long_description,
    url = 'https://github.com/rkern/line_profiler',
    download_url = 'https://github.com/rkern/line_profiler/tarball/2.1',
    ext_modules = [
        Extension('_line_profiler',
                  sources=[line_profiler_source, 'timers.c', 'unset_trace.c'],
                  depends=['python25.pxd'],
        ),
    ],
    license = "BSD",
    keywords = ['timing', 'timer', 'profiling', 'profiler', 'line_profiler'],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: C",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        "Topic :: Software Development",
    ],
    py_modules = py_modules,
    entry_points = {
        'console_scripts': [
            'kernprof=kernprof:main',
        ],
    },
    setup_requires = [
        'cython',
    ],
    install_requires = [
        'IPython>=0.13',
    ],
    cmdclass = cmdclass,
)
