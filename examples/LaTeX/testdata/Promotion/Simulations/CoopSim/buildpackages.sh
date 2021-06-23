#!/bin/sh

cd ..

cp CoopSim/MANIFEST.in .
cp CoopSim/setup.py .
cp CoopSim/setup.cfg .

cd CoopSim
sh cleanup.sh
cd docs
#sh makedocs.sh
cd ../..
python setup.py bdist_rpm 
python setup.py bdist_wininst 
python setup.py sdist --formats=bztar
zip -r dist/CoopSim-0.9.9beta2.zip CoopSim

rm MANIFEST
rm MANIFEST.in
rm setup.py
rm setup.cfg
rm -rd build
