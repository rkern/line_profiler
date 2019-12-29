#!/bin/bash
__heredoc__="""


notes:

    Manylinux repo: https://github.com/pypa/manylinux 

    Win + Osx repo: https://github.com/mavlink/MAVSDK-Python

    # TODO: use dind as the base image,
    # Then run the multibuild in docker followed by a test in a different
    # docker container

    # BETTER TODO: 
    # Use a build stage to build in the multilinux environment and then
    # use a test stage with a different image to test and deploy the wheel
    docker run --rm -it --entrypoint="" docker:dind sh
    docker run --rm -it --entrypoint="" docker:latest sh
    docker run --rm -v $PWD:/io -it --entrypoint="" docker:latest sh

    docker run --rm -v $PWD:/io -it python:2.7 bash
     
        cd /io
        pip install -r requirements.txt
        pip install pygments
        pip install wheelhouse/pyflann_ibeis-0.5.0-cp27-cp27mu-manylinux1_x86_64.whl

        cd /
        xdoctest pyflann_ibeis
        pytest io/tests

        cd /io
        python run_tests.py


MB_PYTHON_TAG=cp38-cp38 ./run_manylinux_build.sh
MB_PYTHON_TAG=cp37-cp37m ./run_manylinux_build.sh
MB_PYTHON_TAG=cp36-cp36m ./run_manylinux_build.sh
MB_PYTHON_TAG=cp35-cp35m ./run_manylinux_build.sh
MB_PYTHON_TAG=cp27-cp27m ./run_manylinux_build.sh

# MB_PYTHON_TAG=cp27-cp27mu ./run_nmultibuild.sh

docker pull quay.io/erotemic/manylinux-opencv:manylinux1_i686-opencv4.1.0-py3.6
docker pull quay.io/pypa/manylinux2010_x86_64:latest

"""


#DOCKER_IMAGE=${DOCKER_IMAGE:="quay.io/erotemic/manylinux-for:x86_64-opencv4.1.0-v2"}
DOCKER_IMAGE=${DOCKER_IMAGE:="quay.io/pypa/manylinux2010_x86_64:latest"}
# Valid multibuild python versions are:
# cp27-cp27m  cp27-cp27mu  cp34-cp34m  cp35-cp35m  cp36-cp36m  cp37-cp37m, cp38-cp38m
MB_PYTHON_TAG=${MB_PYTHON_TAG:=$(python -c "import setup; print(setup.native_mb_python_tag())")}
NAME=${NAME:=$(python -c "import setup; print(setup.NAME)")}
VERSION=${VERSION:=$(python -c "import setup; print(setup.VERSION)")}
echo "
MB_PYTHON_TAG = $MB_PYTHON_TAG
DOCKER_IMAGE = $DOCKER_IMAGE
VERSION = $VERSION
NAME = $NAME
"

if [ "$_INSIDE_DOCKER" != "YES" ]; then

    set -e
    docker run --rm \
        -v $PWD:/io \
        -e _INSIDE_DOCKER="YES" \
        -e MB_PYTHON_TAG="$MB_PYTHON_TAG" \
        -e NAME="$NAME" \
        -e VERSION="$VERSION" \
        $DOCKER_IMAGE bash -c 'cd /io && ./run_manylinux_build.sh'

    __interactive__='''
    docker run --rm \
        -v $PWD:/io \
        -e _INSIDE_DOCKER="YES" \
        -e MB_PYTHON_TAG="$MB_PYTHON_TAG" \
        -e NAME="$NAME" \
        -e VERSION="$VERSION" \
        -it $DOCKER_IMAGE bash

    set +e
    set +x
    '''

    BDIST_WHEEL_PATH=$(ls wheelhouse/$NAME-$VERSION-$MB_PYTHON_TAG*.whl)
    echo "BDIST_WHEEL_PATH = $BDIST_WHEEL_PATH"
else
    set -x
    set -e

    VENV_DIR=/root/venv-$MB_PYTHON_TAG

    # Setup a virtual environment for the target python version
    /opt/python/$MB_PYTHON_TAG/bin/python -m pip install pip
    /opt/python/$MB_PYTHON_TAG/bin/python -m pip install setuptools pip virtualenv scikit-build cmake ninja ubelt wheel
    /opt/python/$MB_PYTHON_TAG/bin/python -m virtualenv $VENV_DIR

    source $VENV_DIR/bin/activate 

    cd /io
    pip install -r requirements/build.txt
    python setup.py bdist_wheel

    chmod -R o+rw _skbuild
    chmod -R o+rw dist

    /opt/python/cp37-cp37m/bin/python -m pip install auditwheel
    /opt/python/cp37-cp37m/bin/python -m auditwheel show dist/$NAME-$VERSION-$MB_PYTHON_TAG*.whl
    /opt/python/cp37-cp37m/bin/python -m auditwheel repair dist/$NAME-$VERSION-$MB_PYTHON_TAG*.whl
    chmod -R o+rw wheelhouse
    chmod -R o+rw $NAME.egg-info
fi
