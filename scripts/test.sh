#!/bin/bash

set -efx

cd "$(dirname "$0")/.."

# setup test environment
scripts/build.sh test_build

cp configuration.json test_build/

. virtualenv/bin/activate
cd test_build/yolapi

# Ensure the configuration is valid
./manage.py check

python -m pytest
