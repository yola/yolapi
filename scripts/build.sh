#!/bin/bash

set -efxu

cd "$(dirname "$0")/.."

dirname=${1:-build}

# remove build directory if exists
[ -d "$dirname" ] && rm -Rf "$dirname"
mkdir "$dirname"

# copy source to build
cp requirements.txt "$dirname"/
cp -R yolapi "$dirname"/
