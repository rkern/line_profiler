#!/bin/bash
echo "start clean"

rm -rf _skbuild
rm -rf _line_profiler.c
rm -rf *.so
rm -rf line_profiler/_line_profiler.c
rm -rf line_profiler/*.so
rm -rf build
rm -rf line_profiler.egg-info
rm -rf dist
rm -rf mb_work
rm -rf wheelhouse
rm -rf pip-wheel-metadata
rm -rf htmlcov

rm distutils.errors || echo "skip rm"

CLEAN_PYTHON='find . -regex ".*\(__pycache__\|\.py[co]\)" -delete || find . -iname *.pyc -delete || find . -iname *.pyo -delete'
bash -c "$CLEAN_PYTHON"

echo "finish clean"
