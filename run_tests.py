#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import dirname, join, abspath
import sqlite3
import sys
import os
import re

def is_cibuildwheel():
    """Check if run with cibuildwheel."""
    return 'CIBUILDWHEEL' in os.environ

def temp_rename_kernprof(repo_dir):
    """
    Hacky workaround so kernprof.py doesn't get covered twice (installed and local).
    This needed to combine the .coverage files, since file paths need to be unique.

    """
    original_path = repo_dir + '/kernprof.py'
    tmp_path = original_path + '.tmp'
    if os.path.isfile(original_path):
        os.rename(original_path, tmp_path)
    elif os.path.isfile(tmp_path):
        os.rename(tmp_path, original_path)

def replace_docker_path(path, runner_project_dir):
    """Update path to a file installed in a temp venv to runner_project_dir."""
    pattern = re.compile(r"\/tmp\/.+?\/site-packages")
    return pattern.sub(runner_project_dir, path)

def update_coverag_file(coverage_path, runner_project_dir):
    """
    Since the paths inside of docker vary from the runner paths,
    the paths in the .coverage file need to be adjusted to combine them,
    since 'coverage combine <folder>' checks if the file paths exist.
    """
    try:
        sqliteConnection = sqlite3.connect(coverage_path)
        cursor = sqliteConnection.cursor()
        print('Connected to Coverage SQLite')

        read_file_query = 'SELECT id, path from file'
        cursor.execute(read_file_query)

        old_records = cursor.fetchall()
        new_records = [(replace_docker_path(path, runner_project_dir), _id) for _id, path in old_records]
        print('Updated coverage file paths:\n', new_records)

        sql_update_query = 'Update file set path = ? where id = ?'
        cursor.executemany(sql_update_query, new_records)
        sqliteConnection.commit()
        print('Coverage Updated successfully')
        cursor.close()

    except sqlite3.Error as error:
        print('Failed to coverage: ', error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print('The sqlite connection is closed')

def copy_coverage_cibuildwheel_docker(runner_project_dir):
    """
    When run with cibuildwheel under linux, the tests run in the folder /project 
    inside docker and the coverage files need to be copied to the output folder.
    """
    coverage_path = '/project/tests/.coverage'
    if os.path.isfile(coverage_path):
        update_coverag_file(coverage_path, runner_project_dir)
        env_hash = hash((sys.version, os.environ.get('AUDITWHEEL_PLAT', '')))
        os.makedirs('/output', exist_ok=True)
        os.rename(coverage_path, '/output/.coverage.{}'.format(env_hash))



if __name__ == '__main__':
    cwd = os.getcwd()
    repo_dir = abspath(dirname(__file__))
    test_dir = join(repo_dir, 'tests')
    print('cwd = {!r}'.format(cwd))

    if is_cibuildwheel():
        # rename kernprof.py to kernprof.py.tmp
        temp_rename_kernprof(repo_dir)

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
            '--cov-config', '../pyproject.toml',
            '--cov-report', 'html',
            '--cov-report', 'term',
            '--cov-report', 'xml',
            '--cov=' + package_name,
            '--cov=' + 'kernprof',
        ]
        if is_cibuildwheel():
            pytest_args.append('--cov-append')

        pytest_args = pytest_args + sys.argv[1:]
        sys.exit(pytest.main(pytest_args))
    finally:
        os.chdir(cwd)
        if is_cibuildwheel():
            # restore kernprof.py from kernprof.py.tmp
            temp_rename_kernprof(repo_dir)
            # for CIBW under linux
            copy_coverage_cibuildwheel_docker('/home/runner/work/line_profiler/line_profiler')
        print('Restoring cwd = {!r}'.format(cwd))
