#!/bin/sh

# "piggyback" on the existing tox environment
PATH="$TRAVIS_BUILD_DIR/.tox/py35/bin/:$HOME/nodejs/node-v6.10.2-linux-x64/bin/:$PATH"
REPO_OWNER="${TRAVIS_REPO_SLUG%/*}"

# build and publish for
if  [ "$TRAVIS_PULL_REQUEST" = "false" ] ; then
    if [ "$TRAVIS_BRANCH" = "master" ] || [ "$REPO_OWNER" != "getsenic" ]; then
        devpi use "https://pypi.senic.com/$REPO_OWNER/master"
        devpi login $devpi_user --password="$devpi_password"
        make upload
    else
        echo "Not building for branch '$TRAVIS_BRANCH'"
    fi
else
    echo "Not building for pullrequest"
fi
