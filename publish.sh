#!/bin/bash
__heredoc__='''
Script to publish a new version of this library on PyPI. 

If your script has binary dependencies then we assume that you have built a
proper binary wheel with auditwheel and it exists in the wheelhouse directory.
Otherwise, for source tarballs and universal wheels this script runs the
setup.py script to create the wheels as well.

Running this script with the default arguments will perform any builds and gpg
signing, but nothing will be uploaded to pypi unless the user explicitly sets
DO_UPLOAD=True or answers yes to the prompts.

Args:
    # These environment variables must / should be set
    TWINE_USERNAME : username for pypi
    TWINE_PASSWORD : password for pypi
    DO_GPG : defaults to True

Requirements:
     twine >= 1.13.0
     gpg2 >= 2.2.4
     OpenSSL >= 1.1.1c

Notes:
    # NEW API TO UPLOAD TO PYPI
    # https://docs.travis-ci.com/user/deployment/pypi/
    # https://packaging.python.org/tutorials/distributing-packages/
    # https://stackoverflow.com/questions/45188811/how-to-gpg-sign-a-file-that-is-built-by-travis-ci

Usage:
    cd <YOUR REPO>

    # Set your variables or load your secrets
    export TWINE_USERNAME=<pypi-username>
    export TWINE_PASSWORD=<pypi-password>
    TWINE_REPOSITORY_URL="https://test.pypi.org/legacy/" 

    source $(secret_loader.sh)

    MB_PYTHON_TAG=cp38-cp38m 
    MB_PYTHON_TAG=cp37-cp37m 
    MB_PYTHON_TAG=cp36-cp36m 
    MB_PYTHON_TAG=cp35-cp35m 
    MB_PYTHON_TAG=cp27-cp27mu

    echo "MB_PYTHON_TAG = $MB_PYTHON_TAG"
    MB_PYTHON_TAG=$MB_PYTHON_TAG ./run_multibuild.sh
    DEPLOY_REMOTE=ibeis MB_PYTHON_TAG=$MB_PYTHON_TAG ./publish.sh yes

    MB_PYTHON_TAG=py3-none-any ./publish.sh
'''

check_variable(){
    KEY=$1
    HIDE=$2
    VAL=${!KEY}
    if [[ "$HIDE" == "" ]]; then
        echo "[DEBUG] CHECK VARIABLE: $KEY=\"$VAL\""
    else
        echo "[DEBUG] CHECK VARIABLE: $KEY=<hidden>"
    fi
    if [[ "$VAL" == "" ]]; then
        echo "[ERROR] UNSET VARIABLE: $KEY=\"$VAL\""
        exit 1;
    fi
}


normalize_boolean(){
    ARG=$1
    ARG=$(echo "$ARG" | awk '{print tolower($0)}')
    if [ "$ARG" = "true" ] || [ "$ARG" = "1" ] || [ "$ARG" = "yes" ] || [ "$ARG" = "on" ]; then
        echo "True"
    elif [ "$ARG" = "false" ] || [ "$ARG" = "0" ] || [ "$ARG" = "no" ] || [ "$ARG" = "off" ]; then
        echo "False"
    else
        echo "$ARG"
    fi
}

# Options
DEPLOY_REMOTE=${DEPLOY_REMOTE:=origin}
NAME=${NAME:=$(python -c "import setup; print(setup.NAME)")}
VERSION=$(python -c "import setup; print(setup.VERSION)")
MB_PYTHON_TAG=${MB_PYTHON_TAG:=py3-none-any}

# The default should change depending on the application
#DEFAULT_MODE_LIST=("sdist" "universal" "bdist")
#DEFAULT_MODE_LIST=("sdist" "native" "universal")
DEFAULT_MODE_LIST=("sdist" "bdist")

check_variable DEPLOY_REMOTE

ARG_1=$1

DO_UPLOAD=${DO_UPLOAD:=$ARG_1}
DO_TAG=${DO_TAG:=$ARG_1}
DO_GPG=${DO_GPG:="auto"}
DO_BUILD=${DO_BUILD:="auto"}

DO_GPG=$(normalize_boolean "$DO_GPG")
DO_BUILD=$(normalize_boolean "$DO_BUILD")
DO_UPLOAD=$(normalize_boolean "$DO_UPLOAD")
DO_TAG=$(normalize_boolean "$DO_TAG")

TWINE_USERNAME=${TWINE_USERNAME:=""}
TWINE_PASSWORD=${TWINE_PASSWORD:=""}

if [[ "$(cat .git/HEAD)" != "ref: refs/heads/release" ]]; then 
    # If we are not on release, then default to the test pypi upload repo
    TWINE_REPOSITORY_URL=${TWINE_REPOSITORY_URL:="https://test.pypi.org/legacy/"}
else
    TWINE_REPOSITORY_URL=${TWINE_REPOSITORY_URL:="https://upload.pypi.org/legacy/"}
fi

if [[ "$(which gpg2)" != "" ]]; then
    GPG_EXECUTABLE=${GPG_EXECUTABLE:=gpg2}
else
    GPG_EXECUTABLE=${GPG_EXECUTABLE:=gpg}
fi

GPG_KEYID=${GPG_KEYID:=$(git config --local user.signingkey)}
GPG_KEYID=${GPG_KEYID:=$(git config --global user.signingkey)}

WAS_INTERACTION="False"


echo "
=== PYPI BUILDING SCRIPT ==
VERSION='$VERSION'
TWINE_USERNAME='$TWINE_USERNAME'
TWINE_REPOSITORY_URL = $TWINE_REPOSITORY_URL
GPG_KEYID = '$GPG_KEYID'
MB_PYTHON_TAG = '$MB_PYTHON_TAG'

DO_UPLOAD=${DO_UPLOAD}
DO_TAG=${DO_TAG}
DO_GPG=${DO_GPG}
DO_BUILD=${DO_BUILD}
"


# Verify that we want to tag
if [[ "$DO_TAG" == "True" ]]; then
    echo "About to tag VERSION='$VERSION'" 
else
    if [[ "$DO_TAG" == "False" ]]; then
        echo "We are NOT about to tag VERSION='$VERSION'" 
    else
        read -p "Do you want to git tag and push version='$VERSION'? (input 'yes' to confirm)" ANS
        echo "ANS = $ANS"
        WAS_INTERACTION="True"
        DO_TAG="$ANS"
        DO_TAG=$(normalize_boolean "$DO_TAG")
        if [ "$DO_BUILD" == "auto" ]; then
            DO_BUILD=""
            DO_GPG=""
        fi
    fi
fi


# Verify that we want to build
if [ "$DO_BUILD" == "auto" ]; then
    DO_BUILD="True"
fi
# Verify that we want to build
if [ "$DO_GPG" == "auto" ]; then
    DO_GPG="True"
fi

if [[ "$DO_BUILD" == "True" ]]; then
    echo "About to build wheels"
else
    if [[ "$DO_UPLOAD" == "False" ]]; then
        echo "We are NOT about to build wheels"
    else
        read -p "Do you need to build wheels? (input 'yes' to confirm)" ANS
        echo "ANS = $ANS"
        WAS_INTERACTION="True"
        DO_BUILD="$ANS"
        DO_BUILD=$(normalize_boolean "$DO_BUILD")
    fi
fi


# Verify that we want to publish
if [[ "$DO_UPLOAD" == "True" ]]; then
    echo "About to directly publish VERSION='$VERSION'" 
else
    if [[ "$DO_UPLOAD" == "False" ]]; then
        echo "We are NOT about to directly publish VERSION='$VERSION'" 
    else
        read -p "Are you ready to directly publish version='$VERSION'? ('yes' will twine upload)" ANS
        echo "ANS = $ANS"
        WAS_INTERACTION="True"
        DO_UPLOAD="$ANS"
        DO_UPLOAD=$(normalize_boolean "$DO_UPLOAD")
    fi
fi


if [[ "$WAS_INTERACTION" == "True" ]]; then
    echo "
    === PYPI BUILDING SCRIPT ==
    VERSION='$VERSION'
    TWINE_USERNAME='$TWINE_USERNAME'
    TWINE_REPOSITORY_URL = $TWINE_REPOSITORY_URL
    GPG_KEYID = '$GPG_KEYID'
    MB_PYTHON_TAG = '$MB_PYTHON_TAG'

    DO_UPLOAD=${DO_UPLOAD}
    DO_TAG=${DO_TAG}
    DO_GPG=${DO_GPG}
    DO_BUILD=${DO_BUILD}
    "
    read -p "Look good? Ready? Enter any text to continue" ANS
fi



MODE=${MODE:=all}

if [[ "$MODE" == "all" ]]; then
    MODE_LIST=("${DEFAULT_MODE_LIST[@]}")
else
    MODE_LIST=("$MODE")
fi

MODE_LIST_STR=$(printf '"%s" ' "${MODE_LIST[@]}")



if [ "$DO_BUILD" == "True" ]; then

    echo "
    === <BUILD WHEEL> ===
    "

    echo "LIVE BUILDING"
    # Build wheel and source distribution

    #WHEEL_PATHS=()
    for _MODE in "${MODE_LIST[@]}"
    do
        echo "_MODE = $_MODE"
        if [[ "$_MODE" == "sdist" ]]; then
            python setup.py sdist || { echo 'failed to build sdist wheel' ; exit 1; }
            WHEEL_PATH=$(ls dist/$NAME-$VERSION*.tar.gz)
            #WHEEL_PATHS+=($WHEEL_PATH)
        elif [[ "$_MODE" == "native" ]]; then
            python setup.py bdist_wheel || { echo 'failed to build native wheel' ; exit 1; }
            WHEEL_PATH=$(ls dist/$NAME-$VERSION*.whl)
            #WHEEL_PATHS+=($WHEEL_PATH)
        elif [[ "$_MODE" == "universal" ]]; then
            python setup.py bdist_wheel --universal || { echo 'failed to build universal wheel' ; exit 1; }
            UNIVERSAL_TAG="py3-none-any"
            WHEEL_PATH=$(ls dist/$NAME-$VERSION-$UNIVERSAL_TAG*.whl)
            #WHEEL_PATHS+=($WHEEL_PATH)
        elif [[ "$_MODE" == "bdist" ]]; then
            echo "Assume wheel has already been built"
            WHEEL_PATH=$(ls wheelhouse/$NAME-$VERSION-$MB_PYTHON_TAG*.whl)
            #WHEEL_PATHS+=($WHEEL_PATH)
        else
            echo "bad mode"
            exit 1
        fi
        echo "WHEEL_PATH = $WHEEL_PATH"
    done

    echo "
    === <END BUILD WHEEL> ===
    "

else
    echo "DO_BUILD=False, Skipping build"
fi


WHEEL_PATHS=()
for _MODE in "${MODE_LIST[@]}"
do
    echo "_MODE = $_MODE"
    if [[ "$_MODE" == "sdist" ]]; then
        WHEEL_PATH=$(ls dist/$NAME-$VERSION*.tar.gz)
        WHEEL_PATHS+=($WHEEL_PATH)
    elif [[ "$_MODE" == "native" ]]; then
        WHEEL_PATH=$(ls dist/$NAME-$VERSION*.whl)
        WHEEL_PATHS+=($WHEEL_PATH)
    elif [[ "$_MODE" == "universal" ]]; then
        UNIVERSAL_TAG="py3-none-any"
        WHEEL_PATH=$(ls dist/$NAME-$VERSION-$UNIVERSAL_TAG*.whl)
        WHEEL_PATHS+=($WHEEL_PATH)
    elif [[ "$_MODE" == "bdist" ]]; then
        WHEEL_PATH=$(ls wheelhouse/$NAME-$VERSION-$MB_PYTHON_TAG*.whl)
        WHEEL_PATHS+=($WHEEL_PATH)
    else
        echo "bad mode"
        exit 1
    fi
    echo "WHEEL_PATH = $WHEEL_PATH"
done

WHEEL_PATHS_STR=$(printf '"%s" ' "${WHEEL_PATHS[@]}")

echo "
MODE=$MODE
VERSION='$VERSION'
WHEEL_PATHS='$WHEEL_PATHS_STR'
"



if [ "$DO_GPG" == "True" ]; then

    echo "
    === <GPG SIGN> ===
    "

    for WHEEL_PATH in "${WHEEL_PATHS[@]}"
    do
        echo "WHEEL_PATH = $WHEEL_PATH"
        check_variable WHEEL_PATH
            # https://stackoverflow.com/questions/45188811/how-to-gpg-sign-a-file-that-is-built-by-travis-ci
            # secure gpg --export-secret-keys > all.gpg

            # REQUIRES GPG >= 2.2
            check_variable GPG_EXECUTABLE || { echo 'failed no gpg exe' ; exit 1; }
            check_variable GPG_KEYID || { echo 'failed no gpg key' ; exit 1; }

            echo "Signing wheels"
            GPG_SIGN_CMD="$GPG_EXECUTABLE --batch --yes --detach-sign --armor --local-user $GPG_KEYID"
            echo "GPG_SIGN_CMD = $GPG_SIGN_CMD"
            $GPG_SIGN_CMD --output $WHEEL_PATH.asc $WHEEL_PATH

            echo "Checking wheels"
            twine check $WHEEL_PATH.asc $WHEEL_PATH || { echo 'could not check wheels' ; exit 1; }

            echo "Verifying wheels"
            $GPG_EXECUTABLE --verify $WHEEL_PATH.asc $WHEEL_PATH || { echo 'could not verify wheels' ; exit 1; }
    done
    echo "
    === <END GPG SIGN> ===
    "
else
    echo "DO_GPG=False, Skipping GPG sign"
fi


if [[ "$DO_TAG" == "True" ]]; then
    TAG_NAME="v${VERSION}"
    # if we messed up we can delete the tag
    # git push origin :refs/tags/$TAG_NAME
    # and then tag with -f
    # 
    git tag $TAG_NAME -m "tarball tag $VERSION"
    git push --tags $DEPLOY_REMOTE
    echo "Should also do a: git push $DEPLOY_REMOTE main:release"
    echo "For github should draft a new release: https://github.com/PyUtils/line_profiler/releases/new"
else
    echo "Not tagging"
fi


if [[ "$DO_UPLOAD" == "True" ]]; then
    check_variable TWINE_USERNAME
    check_variable TWINE_PASSWORD "hide"

    for WHEEL_PATH in "${WHEEL_PATHS[@]}"
    do
        if [ "$DO_GPG" == "True" ]; then
            twine upload --username $TWINE_USERNAME --password=$TWINE_PASSWORD  \
                --repository-url $TWINE_REPOSITORY_URL \
                --sign $WHEEL_PATH.asc $WHEEL_PATH --skip-existing --verbose || { echo 'failed to twine upload' ; exit 1; }
        else
            twine upload --username $TWINE_USERNAME --password=$TWINE_PASSWORD \
                --repository-url $TWINE_REPOSITORY_URL \
                $WHEEL_PATH --skip-existing --verbose || { echo 'failed to twine upload' ; exit 1; }
        fi
    done
    echo """
        !!! FINISH: LIVE RUN !!!
    """
else
    echo """
        DRY RUN ... Skiping upload

        DEPLOY_REMOTE = '$DEPLOY_REMOTE'
        DO_UPLOAD = '$DO_UPLOAD'
        WHEEL_PATH = '$WHEEL_PATH'
        WHEEL_PATHS_STR = '$WHEEL_PATHS_STR'
        MODE_LIST_STR = '$MODE_LIST_STR'

        VERSION='$VERSION'
        NAME='$NAME'
        TWINE_USERNAME='$TWINE_USERNAME'
        GPG_KEYID = '$GPG_KEYID'
        MB_PYTHON_TAG = '$MB_PYTHON_TAG'

        To do live run set DO_UPLOAD=1 and ensure deploy and current branch are the same

        !!! FINISH: DRY RUN !!!
    """
fi
