#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import exists
import os
import sys
import setuptools  # NOQA
from setuptools import find_packages


def parse_version(fpath):
    """
    Statically parse the version number from a python file
    """
    import ast
    if not exists(fpath):
        raise ValueError('fpath={!r} does not exist'.format(fpath))
    with open(fpath, 'r') as file_:
        sourcecode = file_.read()
    pt = ast.parse(sourcecode)
    class VersionVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if getattr(target, 'id', None) == '__version__':
                    self.version = node.value.s
    visitor = VersionVisitor()
    visitor.visit(pt)
    return visitor.version


def parse_description():
    """
    Parse the description in the README file

    CommandLine:
        pandoc --from=markdown --to=rst --output=README.rst README.md
        python -c "import setup; print(setup.parse_description())"
    """
    from os.path import dirname, join, exists
    readme_fpath = join(dirname(__file__), 'README.rst')
    # This breaks on pip install, so check that it exists.
    if exists(readme_fpath):
        with open(readme_fpath, 'r') as f:
            text = f.read()
        return text
    return ''


def parse_requirements(fname='requirements.txt', with_version=False):
    """
    Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    Args:
        fname (str): path to requirements file
        with_version (bool, default=False): if true include version specs

    Returns:
        List[str]: list of requirements items

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
        python -c "import setup; print(chr(10).join(setup.parse_requirements(with_version=True)))"
    """
    from os.path import exists
    import re
    require_fpath = fname

    def parse_line(line):
        """
        Parse information from a line in a requirements text file
        """
        if line.startswith('-r '):
            # Allow specifying requirements in other files
            target = line.split(' ')[1]
            for info in parse_require_file(target):
                yield info
        else:
            info = {'line': line}
            if line.startswith('-e '):
                info['package'] = line.split('#egg=')[1]
            else:
                # Remove versioning from the package
                pat = '(' + '|'.join(['>=', '==', '>']) + ')'
                parts = re.split(pat, line, maxsplit=1)
                parts = [p.strip() for p in parts]

                info['package'] = parts[0]
                if len(parts) > 1:
                    op, rest = parts[1:]
                    if ';' in rest:
                        # Handle platform specific dependencies
                        # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                        version, platform_deps = map(str.strip, rest.split(';'))
                        info['platform_deps'] = platform_deps
                    else:
                        version = rest  # NOQA
                    info['version'] = (op, version)
            yield info

    def parse_require_file(fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    for info in parse_line(line):
                        yield info

    def gen_packages_items():
        if exists(require_fpath):
            for info in parse_require_file(require_fpath):
                parts = [info['package']]
                if with_version and 'version' in info:
                    parts.extend(info['version'])
                if not sys.version.startswith('3.4'):
                    # apparently package_deps are broken in 3.4
                    platform_deps = info.get('platform_deps')
                    if platform_deps is not None:
                        parts.append(';' + platform_deps)
                item = ''.join(parts)
                yield item

    packages = list(gen_packages_items())
    return packages


def native_mb_python_tag():
    import sys
    import platform
    major = sys.version_info[0]
    minor = sys.version_info[1]
    ver = '{}{}'.format(major, minor)
    if platform.python_implementation() == 'CPython':
        # TODO: get if cp27m or cp27mu
        impl = 'cp'
        if ver == '27':
            IS_27_BUILT_WITH_UNICODE = True  # how to determine this?
            if IS_27_BUILT_WITH_UNICODE:
                abi = 'mu'
            else:
                abi = 'm'
        else:
            if ver == '38':
                # no abi in 38?
                abi = ''
            else:
                abi = 'm'
    else:
        raise NotImplementedError(impl)
    mb_tag = '{impl}{ver}-{impl}{ver}{abi}'.format(**locals())
    return mb_tag


USE_SKBUILD = True
if USE_SKBUILD:

    if '--universal' in sys.argv:
        # Dont use scikit-build for universal wheels
        if 'develop' in sys.argv:
            sys.argv.remove('--universal')
        from setuptools import setup
    else:
        from skbuild import setup

    setupkw = dict(
        # include_package_data=False,
        # package_dir={
        #     '': '.',
        #     # Note: this requires that FLANN_LIB_INSTALL_DIR is set to pyflann/lib
        #     # in the src/cpp/CMakeLists.txt
        #     # 'line_profiler.lib': 'line_profiler/lib',
        # },
    )
else:
    # Monkeypatch distutils.
    import distutils.errors
    # from distutils.core import setup
    from distutils.extension import Extension
    from distutils.log import warn
    from setuptools import setup
    # use setuptools
    try:
        from Cython.Distutils import build_ext
        cmdclass = dict(build_ext=build_ext)
        line_profiler_source = '_line_profiler.pyx'
    except ImportError:
        cmdclass = {}
        line_profiler_source = '_line_profiler.c'
        if not os.path.exists(line_profiler_source):
            raise distutils.errors.DistutilsError("""\
    You need Cython to build the line_profiler from a git checkout, or
    alternatively use a release tarball from PyPI to build it without Cython.""")
        else:
            warn("Could not import Cython. "
                 "Using the available pre-generated C file.")

    setupkw = dict(
        cmdclass=cmdclass,
        ext_modules=[
            Extension('_line_profiler',
                      sources=[line_profiler_source, 'timers.c', 'unset_trace.c'],
                      depends=['python25.pxd']),
        ],
    )

long_description = """\
line_profiler will profile the time individual lines of code take to execute.
The profiler is implemented in C via Cython in order to reduce the overhead of
profiling.

Also included is the script kernprof.py which can be used to conveniently
profile Python applications and scripts either with line_profiler or with the
function-level profiling tools in the Python standard library.
"""

VERSION = parse_version('line_profiler/line_profiler.py')
MB_PYTHON_TAG = native_mb_python_tag()
# note: name is temporary until line_profiler pypi name is transfered
NAME = 'line_profiler'


# py_modules = ['line_profiler', 'kernprof']
# if sys.version_info > (3, 4):
#     py_modules += ['line_profiler_py35']


if __name__ == '__main__':
    setupkw.update(dict(
        name=NAME,
        version=VERSION,
        author='Robert Kern',
        author_email='robert.kern@enthought.com',
        description='Line-by-line profiler.',
        long_description=long_description,
        long_description_content_type='text/x-rst',
        url='https://github.com/pyutils/line_profiler',
        license="BSD",
        keywords=['timing', 'timer', 'profiling', 'profiler', 'line_profiler'],
        classifiers=[
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
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: Implementation :: CPython',
            "Topic :: Software Development",
        ],
        # py_modules=find_packages(),
        packages=list(find_packages()),
        py_modules=['kernprof', 'line_profiler'],
        entry_points={
            'console_scripts': [
                'kernprof=kernprof:main',
            ],
        },
        install_requires=parse_requirements('requirements/runtime.txt'),
        extras_require={
            'all': parse_requirements('requirements.txt'),
            'tests': parse_requirements('requirements/tests.txt'),
            'build': parse_requirements('requirements/build.txt'),
        },
    ))
    setup(**setupkw)
