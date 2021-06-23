#!/bin/sh

rm Voegelins_Bewusstseinsphilosophie.bbl
rm Voegelins_Bewusstseinsphilosophie.blg
rm Voegelins_Bewusstseinsphilosophie.aux
rm Voegelins_Bewusstseinsphilosophie.out
rm Voegelins_Bewusstseinsphilosophie.toc

pdflatex Voegelins_Bewusstseinsphilosophie.tex
#bibtex Voegelins_Bewusstseinsphilosophie
pdflatex Voegelins_Bewusstseinsphilosophie.tex
pdflatex Voegelins_Bewusstseinsphilosophie.tex
pdflatex Voegelins_Bewusstseinsphilosophie.tex

./latex2html.py -p "http://www.eckhartarnold.de/papers/2007_Voegelins_Bewusstseinsphilosophie/Voegelins_Bewusstseinsphilosophie.pdf" -l "de" -r '<a href="http://www.eckhartarnold.de">Eckhart Arnold</a>' Voegelins_Bewusstseinsphilosophie.tex

