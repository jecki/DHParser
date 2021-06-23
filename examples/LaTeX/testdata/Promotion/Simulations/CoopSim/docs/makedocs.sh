#!/bin/sh

sh cleanup.sh

cp big_images/* .
pdflatex CoopSim_Doc.tex
pdflatex CoopSim_Doc.tex

cp small_images/* .
latex2html -local_icons -show_section_numbers CoopSim_Doc.tex

# tar -cvf CoopSim_Doc.html.tar CoopSim_Doc
# gzip CoopSim_Doc.html.tar

rm *.png
rm CoopSim_Doc.log
rm CoopSim_Doc.aux
rm CoopSim_Doc.toc
