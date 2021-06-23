#
# Makefile to convert the LaTeX-source file to dvi, pdf and html respectively
#


HTMLTITLE = "Religiöses Bewusstsein und Politische Ordnung. Eine Kritik von Eric Voegelins Bewusstseinsphilosophie"


all: Voegelins_Bewusstseinsphilosophie.dvi Voegelins_Bewusstseinsphilosophie.pdf Voegelins_Bewusstseinsphilosophie/Voegelins_Bewusstseinsphilosophie.html Voegelins_Bewusstseinsphilosophie_html.tgz Voegelins_Bewusstseinsphilosophie_tex.tgz package tidy

Voegelins_Bewusstseinsphilosophie.dvi: Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex
	latex Voegelins_Bewusstseinsphilosophie.tex       # 1st pass
	latex Voegelins_Bewusstseinsphilosophie.tex       # 2nd pass

Voegelins_Bewusstseinsphilosophie.pdf: Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex
	pdflatex Voegelins_Bewusstseinsphilosophie.tex    # 1st pass
	pdflatex Voegelins_Bewusstseinsphilosophie.tex    # 2nd pass

Voegelins_Bewusstseinsphilosophie/Voegelins_Bewusstseinsphilosophie.html: Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex
	./latex2html.py -l "de" -s "Voegelins_Bewusstseinsphilosophie" -a "Eckhart Arnold" -r 'von <a href="http://www.eckhartarnold.de">Eckhart Arnold</a>' -k "Voegelin, Eric Voegelin, Bewusstseinsphilosophie, Politische Ordnung, Gnosis, Anamnesis, Periagoge, Religion, Politik" -d "Eine kritische Untersuchung von Eric Voegelins Bewusstseinsphilosophie." Voegelins_Bewusstseinsphilosophie.tex
	cp Voegelins_Bewusstseinsphilosophie/Voegelins_Bewusstseinsphilosophie.html Voegelins_Bewusstseinsphilosophie/index.html

Voegelins_Bewusstseinsphilosophie_html.tgz: Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex Voegelins_Bewusstseinsphilosophie/Voegelins_Bewusstseinsphilosophie.html
	tar -cvf Voegelins_Bewusstseinsphilosophie_html.tar Voegelins_Bewusstseinsphilosophie
	gzip --best Voegelins_Bewusstseinsphilosophie_html.tar
	mv Voegelins_Bewusstseinsphilosophie_html.tar.gz Voegelins_Bewusstseinsphilosophie_html.tgz

Voegelins_Bewusstseinsphilosophie_tex.tgz: Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex
	tar -cvf Voegelins_Bewusstseinsphilosophie_tex.tar Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex
	gzip --best Voegelins_Bewusstseinsphilosophie_tex.tar
	mv Voegelins_Bewusstseinsphilosophie_tex.tar.gz Voegelins_Bewusstseinsphilosophie_tex.tgz

tidy: 
	rm -f *.flc
	rm -f *.toc
	rm -f *.aux
	rm -f *.log

clean: tidy
	rm -f *.dvi
	rm -f *.pdf
	rm -f *.tgz
	rm -f Voegelins_Bewusstseinsphilosophie/*
	rmdir Voegelins_Bewusstseinsphilosophie

package: Makefile latex2html.py Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex Zusammenfassung.txt
	tar -cvf Voegelins_Bewusstseinsphilosophie.tar Voegelins_Bewusstseinsphilosophie.tex Einleitung.tex Kapitel2.tex Kapitel31.tex Kapitel32.tex Kapitel33.tex Kapitel34.tex Kapitel35.tex Kapitel4.tex Literatur.tex Abstract.tex Zusammenfassung.txt Autorinformation.txt Makefile latex2html.py 
	gzip --best Voegelins_Bewusstseinsphilosophie.tar
	mv Voegelins_Bewusstseinsphilosophie.tar.gz Voegelins_Bewusstseinsphilosophie.tgz


