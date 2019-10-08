#!/bin/sh

rm DHParser/*.c
rm DHParser/*.so

# for testing:
# rm DHParser/parse.c
# rm DHParser/parse.cpython*.so
# rm DHParser/syntaxtree.c
# rm DHParser/syntaxtree.cpython*.so
# rm DHParser/transform.c
# rm DHParser/transform.cpython*.so

export CFLAGS="-O3 -march=native -mtune=native"

if hash clang 2>/dev/null; then
  export CC=clang; python3 setup.py build_ext --inplace
else
  python3 setup.py build_ext --inplace
fi
strip `ls DHParser/*.so`

