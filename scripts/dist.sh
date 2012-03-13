#!/bin/bash

# exit on error
set -e
cd "`dirname $0`/.."

[ -z "$APPNAME" ] && { echo "APPNAME variable not set" ; false ; }

# remove dist directory if exists
[ -d ./dist ] && rm -Rf dist
mkdir dist

# copy source to dist
cp -Rf deploy build/

# create distribution tarball
cp -Rf build dist/$APPNAME

cd dist && tar -czf $APPNAME.tar.gz $APPNAME

