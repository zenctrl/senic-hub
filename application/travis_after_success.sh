#!/bin/sh

# "piggyback" on the existing tox environment
DEVPI="$TRAVIS_BUILD_DIR/application/.tox/py35/bin/devpi"
PIP="/home/travis/virtualenv/python3.5.2/bin/pip"

echo $PIP
echo $DEVPI
echo $PWD
echo $TRAVIS_BRANCH
echo $TRAVIS_PULL_REQUEST
echo "https://pypi.senic.com/${TRAVIS_REPO_SLUG%/*}/master"

if [ "$TRAVIS_BRANCH" = "master" ] && [ "$TRAVIS_PULL_REQUEST" = "false" ] ; then
    $PIP install senic.nuimo_hub[development]
    $DEVPI use "https://pypi.senic.com/${TRAVIS_REPO_SLUG%/*}/master"
    $DEVPI login $devpi_user --password="$devpi_password"
    $DEVPI upload --no-vcs --with-docs --formats bdist_wheel
else
    echo "Not building for branch '$TRAVIS_BRANCH'"
fi