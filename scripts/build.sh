#!/bin/bash

set -efxu

# remove dist directory if exists
[ -d ./build ] && rm -Rf build
mkdir build

# copy source to dist
cp -Rf src build/
cp -Rf libs build/
