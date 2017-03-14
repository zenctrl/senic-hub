#!/bin/sh

# "piggyback" on the existing tox environment
DEVPI="$TRAVIS_BUILD_DIR/application/.tox/py35/bin/devpi"
PIP="$TRAVIS_BUILD_DIR/application/.tox/py35/bin/pip"

if [ "$TRAVIS_BRANCH" = "master" ] && [ "$TRAVIS_PULL_REQUEST" = "false" ] ; then
    $PIP install senic.nuimo_hub[development]
    $DEVPI use https://pypi.senic.com/$devpi_index
    $DEVPI login $devpi_user --password="$devpi_password"
    $DEVPI upload --no-vcs --with-docs --formats bdist_wheel
else
    echo "Not building for $TRAVIS_BRANCH"
fi