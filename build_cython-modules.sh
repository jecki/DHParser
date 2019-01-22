#!/bin/sh

rm DHParser/*.c
rm DHParser/*.so

# CFLAGS="-O3 -march=native -mtune=native" 
python3 setup.py build_ext --inplace
strip `ls DHParser/*.so`
