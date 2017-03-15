#!/bin/sh

# "piggyback" on the existing tox environment
PATH="$TRAVIS_BUILD_DIR/application/.tox/py35/bin/:$PATH"


if [ "$TRAVIS_BRANCH" = "master" ] && [ "$TRAVIS_PULL_REQUEST" = "false" ] ; then
    devpi use "https://pypi.senic.com/${TRAVIS_REPO_SLUG%/*}/master"
    devpi login $devpi_user --password="$devpi_password"
    devpi upload --no-vcs --with-docs --formats bdist_wheel
else
    echo "Not building for branch '$TRAVIS_BRANCH'"
fi