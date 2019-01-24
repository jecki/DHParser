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

# CFLAGS="-O3 -march=native -mtune=native" 
python3 setup.py build_ext --inplace
strip `ls DHParser/*.so`
