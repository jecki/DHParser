#!/bin/sh

cd ..

cp PyPlotter/MANIFEST.in .
cp PyPlotter/setup.py .
cp PyPlotter/setup.cfg .

cd PyPlotter
sh makedocs.sh
cd ..
python setup.py bdist --formats=rpm,wininst

cd PyPlotter
sh cleanup.sh
cd ..
cp PyPlotter/MANIFEST.short ./MANIFEST.in
python setup.py sdist --formats=bztar

rm MANIFEST
rm MANIFEST.in
rm setup.py
rm setup.cfg
rm -rd build

cd PyPlotter
sh cleanup.sh
cd ..
