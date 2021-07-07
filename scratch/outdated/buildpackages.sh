#!/bin/sh
cd documentation_src
make html
cd ..

python3 setup.py sdist # bdist_wheel

