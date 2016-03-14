#!/bin/bash

set -efx

cd "$(dirname "$0")/.."

# setup test environment
scripts/build.sh test_build

cp configuration.json test_build/

. virtualenv/bin/activate
cd test_build/

mkdir -p reports

# configure nose to generate an xunit report
cat <<eof > setup.cfg
[nosetests]
with-xunit=1
xunit-file=reports/xunit.xml
eof

yolapi/manage.py test
