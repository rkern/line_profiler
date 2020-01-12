#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import dirname, join, abspath
import sys
import os

if __name__ == '__main__':
    cwd = os.getcwd()
    repo_dir = abspath(dirname(__file__))
    test_dir = join(repo_dir, 'tests')
    print('cwd = {!r}'.format(cwd))

    import pytest

    # Prefer testing the installed version, but fallback to testing the
    # development version.
    try:
        import ubelt as ub
    except ImportError:
        print('running this test script requires ubelt')
        raise
    # Statically check if ``line_profiler`` is installed outside of the repo.
    # To do this, we make a copy of PYTHONPATH, remove the repodir, and use
    # ubelt to check to see if ``line_profiler`` can be resolved to a path.
    temp_path = list(map(abspath, sys.path))
    if repo_dir in temp_path:
        temp_path.remove(repo_dir)
    modpath = ub.modname_to_modpath('line_profiler', sys_path=temp_path)
    if modpath is not None:
        # If it does, then import it. This should cause the installed version
        # to be used on further imports even if the repo_dir is in the path.
        print('Using installed version of line_profiler')
        module = ub.import_module_from_path(modpath, index=0)
        print('Installed module = {!r}'.format(module))
    else:
        print('No installed version of line_profiler found')

    try:
        print('Changing dirs to test_dir={!r}'.format(test_dir))
        os.chdir(test_dir)

        package_name = 'line_profiler'
        pytest_args = [
            '--cov-config', '../.coveragerc',
            '--cov-report', 'html',
            '--cov-report', 'term',
            '--cov=' + package_name,
        ]
        pytest_args = pytest_args + sys.argv[1:]
        sys.exit(pytest.main(pytest_args))
    finally:
        os.chdir(cwd)
        print('Restoring cwd = {!r}'.format(cwd))
