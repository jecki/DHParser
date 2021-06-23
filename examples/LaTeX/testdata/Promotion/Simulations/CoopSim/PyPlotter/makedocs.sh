#!/bin/sh

sh cleanup.sh

pdflatex PyPlotter_Doc.tex
pdflatex PyPlotter_Doc.tex

latex2html -local_icons PyPlotter_Doc.tex
#tar -cvf PyPlotter_Doc.html.tar PyPlotter_Doc
#gzip PyPlotter_Doc.html.tar
mv PyPlotter_Doc html_docs

rm PyPlotter_Doc.log
rm PyPlotter_Doc.aux
rm PyPlotter_Doc.toc
