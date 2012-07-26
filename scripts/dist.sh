#!/bin/bash

set -efxu

[ -z "$APPNAME" ] && { echo "APPNAME variable not set" ; false ; }

cd "$(dirname "$0")/.."

# remove dist directory if exists
[ -d ./dist ] && rm -Rf dist
mkdir dist

# copy source to dist
cp -Rf deploy build/

# create distribution tarball
cp -Rf build dist/$APPNAME

cd dist && tar -czf $APPNAME.tar.gz $APPNAME
