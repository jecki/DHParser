#!/usr/bin/python

"""Extracts the tables of the average final population shares from the
given statistics directories and exports them as tex-tables."""

from __future__ import with_statement
import re

def extract(fileName):
    """-> [(name, share),...]"""
    table = []
    with file(fileName) as f:
        for line in f:
            if "Ranking by average population shares" in line: break
        else: print "No population shares found in file: ", fileName
        f.next()
        for line in f:
            chunks = line.split(" ")
            if chunks[-1] == "\n": break
            table.append((" ".join(chunks[:-1]), float(chunks[-1])*100))
    return table

def export(tables):
    """-> string with tables in LaTeX-format."""
    txt = []; pos = {}
    for k in xrange(len(tables)):
        for i in xrange(len(tables[k])):
            pos[(k, tables[k][i][0])] = i
    for i in xrange(len(tables[0])):
        s = re.sub("_", "\\_", (tables[0][i][0] + " "*30)[:27])
        txt.append(s)
        for k in xrange(len(tables)):
            p = pos[(k, tables[0][i][0])]
            txt.extend(["  & ", ("%2.2f" % tables[k][p][1]).rjust(7," ")," \\%"])
        txt.append(" \\\\\n")
    return txt

def createTabular(prefix, postfix, names, headings):
    """-> LaTeX-table"""
    assert len(names) == len(headings)
    tabular = ["\\begin{tabular}", "{|l|"+"r|"*len(headings)+"}", "\n\\hline\n"]
    tabular.append(" & \\multicolumn{" + str(len(headings)) + \
                   "}{c|}{{\\bf Average Final Population Share}} \\\\")
    tabular.extend(["\n\\hline\n","{\\bf Strategy}"])
    for h in headings: tabular.extend([" & ", h])
    tabular.append("\\\\ \\hline\n")
    table = [extract(prefix+name+postfix) for name in names]
    tabular.extend(export(table))
    tabular.extend(["\\hline\n", "\end{tabular}\n"])
    return tabular

def dump(fileName, tabular):
    f = file(fileName, "w")
    f.write("".join(tabular))
    f.close()

if __name__ == "__main__":
    destDir = "/home/eckhart/Documents/Arbeit/Promotion/tables/"
    prefix = "/home/eckhart/Simulations/BigSeries/Statistics"
    tfts = "/TFTs.txt"; automata = "/Automata.txt"

    names = [""]
    headings = ["overall results"]
    dump(destDir + "montecarlo_automata.tex",\
         createTabular("/home/eckhart/Simulations/MonteCarloSeries/Statistics",
                       automata, names, headings))
    dump(destDir + "montecarlo_tfts.tex",\
         createTabular("/home/eckhart/Simulations/MonteCarloSeries/Statistics",
                       tfts, names, headings))    

    names = [""]
    headings = ["overall results"]
    dump(destDir + "overall_automata.tex", \
         createTabular(prefix, automata, names, headings))
    dump(destDir + "overall_tfts.tex", \
         createTabular(prefix, tfts, names, headings))    

    names = ["", "_C0.000", "_C0.100", "_C0.200"]
    headings = ["overall", " c = 0.0", "c = 0.1", "c = 0.2"]
    dump(destDir + "correlation_automata.tex", \
         createTabular(prefix, automata, names, headings))
    dump(destDir + "correlation_tfts.tex", \
         createTabular(prefix, tfts, names, headings))

    names = ["", "_D0.000", "_D0.010", "_D0.050"]
    headings = ["overall", " m = 0.0", "m = 0.01", "m = 0.05"]
    dump(destDir + "mutation_automata.tex", \
         createTabular(prefix, automata, names, headings))
    dump(destDir + "mutation_tfts.tex", \
         createTabular(prefix, tfts, names, headings))

    names = ["", "_G0.000", "_G0.050", "_G0.100"]
    headings = ["overall", " g = 0.0", "g = 0.05", "g = 0.1"]
    dump(destDir + "gamenoise_automata.tex", \
         createTabular(prefix, automata, names, headings))
    dump(destDir + "gamenoise_tfts.tex", \
         createTabular(prefix, tfts, names, headings))    

    names = ["", "_N0.000", "_N0.050", "_N0.100", "_N0.150"]
    headings = ["overall", " n = 0.0", "n = 0.05", "n = 0.1", "n = 0.15"]
    dump(destDir + "noise_automata.tex", \
         createTabular(prefix, automata, names, headings))
    dump(destDir + "noise_tfts.tex", \
         createTabular(prefix, tfts, names, headings))

    names = ["", "_P3.50_3.00_1.00_0.00", "_P5.00_3.00_1.00_0.00",
             "_P5.50_3.00_1.00_0.00", "_P5.00_3.00_2.00_0.00"]
    headings = ["overall", " T = 3.5", "T = 5", "T = 5.5", "P = 2"]
    dump(destDir + "payoff_automata.tex", \
         createTabular(prefix, automata, names, headings))
    dump(destDir + "payoff_tfts.tex", \
         createTabular(prefix, tfts, names, headings))

    #tl = []
    #for name in l:  tl.append(extract(prefix+name+postfix))
    #print "".join(export(tl))
        

            
        
