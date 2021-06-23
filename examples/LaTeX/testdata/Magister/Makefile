#
# Makefile to convert the LaTeX-source file to dvi, pdf and html respectively
#


HTMLTITLE = "Eric Voegelins Bewuﬂtseinsphilosophie als Grundlage politischer Ordnung"


all: Voegelin_ueberarbeitet.dvi Voegelin_ueberarbeitet.pdf Voegelin_ueberarbeitet/Voegelin_ueberarbeitet.html Voegelin_ueberarbeitet_html.tgz Voegelin_ueberarbeitet_tex.tgz package tidy

Voegelin_ueberarbeitet.dvi: Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex
	latex Voegelin_ueberarbeitet.tex       # 1st pass
	latex Voegelin_ueberarbeitet.tex       # 2nd pass

Voegelin_ueberarbeitet.pdf: Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex
	pdflatex Voegelin_ueberarbeitet.tex    # 1st pass
	pdflatex Voegelin_ueberarbeitet.tex    # 2nd pass

Voegelin_ueberarbeitet/Voegelin_ueberarbeitet.html: Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex
	./latex2html.py -p "http://www.eckhartarnold.de/papers/Voegelin_ueberarbeitet/Voegelin_ueberarbeitet.pdf" -l "de" -s "Voegelin_ueberarbeitet" -a "Eckhart Arnold" -r 'von <a href="http://www.eckhartarnold.de">Eckhart Arnold</a>' -k "Voegelin, Eric Voegelin, Bewusstseinsphilosophie, Politische Ordnung, Gnosis, Anamnesis, Periagoge, Religion, Politik" -d "Eine kritische Untersuchung von Eric Voegelins Bewusstseinsphilosophie." Voegelin_ueberarbeitet.tex
	cp Voegelin_ueberarbeitet/Voegelin_ueberarbeitet.html Voegelin_ueberarbeitet/index.html
# ./latex2html -t $(HTMLTITLE) -no_footnode -numbered_footnotes Voegelin_ueberarbeitet.tex

Voegelin_ueberarbeitet_html.tgz: Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Voegelin_ueberarbeitet/Voegelin_ueberarbeitet.html
	tar -cvf Voegelin_ueberarbeitet_html.tar Voegelin_ueberarbeitet
	gzip --best Voegelin_ueberarbeitet_html.tar
	mv Voegelin_ueberarbeitet_html.tar.gz Voegelin_ueberarbeitet_html.tgz

Voegelin_ueberarbeitet_tex.tgz: Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex
	tar -cvf Voegelin_ueberarbeitet_tex.tar Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex
	gzip --best Voegelin_ueberarbeitet_tex.tar
	mv Voegelin_ueberarbeitet_tex.tar.gz Voegelin_ueberarbeitet_tex.tgz

tidy: 
	rm -f *.flc
	rm -f *.toc
	rm -f *.aux
	rm -f *.log

clean: tidy
	rm -f *.dvi
	rm -f *.pdf
	rm -f *.tgz
	rm -f Voegelin_ueberarbeitet/*
	rmdir Voegelin_ueberarbeitet

package: Makefile latex2html.py Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex
	tar -cvf Voegelin_ueberarbeitet.tar Voegelin_ueberarbeitet.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Makefile latex2html.py 
	gzip --best Voegelin_ueberarbeitet.tar
	mv Voegelin_ueberarbeitet.tar.gz Voegelin_ueberarbeitet.tgz


