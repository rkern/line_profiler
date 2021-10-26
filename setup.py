#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import exists
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
    class Finished(Exception):
        pass
    class VersionVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if getattr(target, 'id', None) == '__version__':
                    self.version = node.value.s
                    raise Finished
    visitor = VersionVisitor()
    try:
        visitor.visit(pt)
    except Finished:
        pass
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


def parse_requirements(fname='requirements.txt', with_version=True):
    """
    Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    Args:
        fname (str): path to requirements file
        with_version (bool, default=True): if true include version specs

    Returns:
        List[str]: list of requirements items

    References:
        https://pip.pypa.io/en/stable/reference/pip_install/#requirement-specifiers
        https://www.python.org/dev/peps/pep-0440/#version-specifiers

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

        Ignore:
            line = 'foobar >=1.0, <= 2.1'
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
                cmp_ops = ['>=', '>', '<=', '<', '!=', '~=', '==', '===']
                pat = '(' + '|'.join(cmp_ops) + ')'
                parts = re.split(pat, line, maxsplit=1)
                parts = [p.strip() for p in parts]

                info['package'] = parts[0]
                if len(parts) > 1:
                    op1, rest = parts[1:]
                    if ';' in rest:
                        # Handle platform specific dependencies
                        # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                        version_rest, platform_deps = map(str.strip, rest.split(';'))
                        info['platform_deps'] = platform_deps
                    else:
                        version_rest = rest  # NOQA
                    # Multiple version requirments may be specified
                    version = []
                    version_text = op1 + version_rest
                    for clause in version_text.split(','):
                        cparts = [p.strip() for p in re.split(pat, clause)]
                        cparts = [p for p in cparts if p]
                        version.append(cparts)
                    info['version'] = version
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
                if 'version' in info:
                    # FIXME: add mode that lets you exclude minimum reqs
                    clauses = []
                    for clause in info['version']:
                        op, arg = clause
                        if with_version:
                            clauses.append(op + arg)
                    version_part = ','.join(clauses)
                    parts.append(version_part)
                if not sys.version.startswith('3.4'):
                    # apparently package_deps are broken in 3.4
                    platform_deps = info.get('platform_deps')
                    if platform_deps is not None:
                        parts.append(';' + platform_deps)
                item = ''.join(parts)
                yield item

    packages = list(gen_packages_items())
    return packages


def native_mb_python_tag(plat_impl=None, version_info=None):
    """
    Get the correct manylinux python version tag for this interpreter

    Example:
        >>> print(native_mb_python_tag())
        >>> print(native_mb_python_tag('PyPy', (2, 7)))
        >>> print(native_mb_python_tag('CPython', (3, 8)))
    """
    if plat_impl is None:
        import platform
        plat_impl = platform.python_implementation()

    if version_info is None:
        import sys
        version_info = sys.version_info

    major, minor = version_info[0:2]
    if minor > 9:
        ver = '{}_{}'.format(major, minor)
    else:
        ver = '{}{}'.format(major, minor)

    if plat_impl == 'CPython':
        # TODO: get if cp27m or cp27mu
        impl = 'cp'
        if ver == '27':
            IS_27_BUILT_WITH_UNICODE = True  # how to determine this?
            if IS_27_BUILT_WITH_UNICODE:
                abi = 'mu'
            else:
                abi = 'm'
        else:
            if sys.version_info[:2] >= (3, 8):
                # bpo-36707: 3.8 dropped the m flag
                abi = ''
            else:
                abi = 'm'
        mb_tag = '{impl}{ver}-{impl}{ver}{abi}'.format(**locals())
    elif plat_impl == 'PyPy':
        abi = ''
        impl = 'pypy'
        ver = '{}{}'.format(major, minor)
        mb_tag = '{impl}-{ver}'.format(**locals())
    else:
        raise NotImplementedError(plat_impl)
    return mb_tag


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
NAME = 'line_profiler'


if __name__ == '__main__':
    if '--universal' in sys.argv:
        # Dont use scikit-build for universal wheels
        # if 'develop' in sys.argv:
        sys.argv.remove('--universal')
        from setuptools import setup  # NOQA
    else:
        from skbuild import setup
    setupkw = dict(
        name=NAME,
        version=VERSION,
        author='Robert Kern',
        author_email='robert.kern@enthought.com',
        description='Line-by-line profiler.',
        long_description=long_description,
        long_description_content_type='text/x-rst',
        url='https://github.com/pyutils/line_profiler',
        license='BSD',
        license_files=['LICENSE.txt', 'LICENSE_Python.txt'],
        keywords=['timing', 'timer', 'profiling', 'profiler', 'line_profiler'],
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: C',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: Implementation :: CPython',
            'Topic :: Software Development',
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
    )
    setup(**setupkw)
