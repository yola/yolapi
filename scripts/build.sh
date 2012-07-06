#!/bin/bash

set -efxu

# remove dist directory if exists
[ -d ./build ] && rm -Rf build
mkdir build

# copy source to dist
cp manage.py initial_data.json requirements.txt build
cp -R yolapi build
