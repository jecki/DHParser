#!/usr/bin/python
# fix_automata_names.py - fix the names of the two state automata in the
# html pages

import sys, os, re

if len(sys.argv) > 1:  path = sys.argv[1]
else:  path = "."

trans1 = {
    "AM: HDHDH \(PAVLOV 2\):":    "AM: HDHDH:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;",
    "AM: HDHHD \(TATFORTIT 2\):": "AM: HDHHD (PAVLOV):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;",
    "AM: HHDHD:           ":      "AM: HHDHD (INVERTED):",
    "AM: HHDHD:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;":
    "AM: HHDHD (INVERTED):"}

trans2 = {
    "AM: HDHDH \(PAVLOV 2\),":    "AM: HDHDH,",
    "AM: HDHHD \(TATFORTIT 2\),": "AM: HDHHD (PAVLOV),",
    "AM: HHDHD,":               "AM: HHDHD (INVERTED),"}

trans3 = {
    "AM: HDHDH \(PAVLOV 2\) :":    "AM: HDHDH :",
    "AM: HDHHD \(TATFORTIT 2\) :": "AM: HDHHD (PAVLOV) :",
    "AM: HHDHD :":               "AM: HHDHD (INVERTED) :"}

trans4 = {
    ": AM: HDHDH \(PAVLOV 2\)":    ": AM: HDHDH           ",
    ": AM: HDHHD \(TATFORTIT 2\)": ": AM: HDHHD (PAVLOV)     ",
    ": AM: HHDHD  ":               ": AM: HHDHD (INVERTED)"}

trans5 = {
    ".AM: HDHDH \(PAVLOV 2\) ":      ".AM: HDHDH            ",
    ".AM: HDHHD \(TATFORTIT 2\) ":   ".AM: HDHHD (PAVLOV)      ",
    ".AM: HHDHD            ":      ".AM: HHDHD (INVERTED) "}

trans6 = {
    "AM__HDHDH_\(PAVLOV_2\)":    "AM__HDHDH",
    "AM__HDHHD_\(TATFORTIT_2\)": "AM__HDHHD_(PAVLOV)",
    "AM__HHDHD":               "AM__HHDHD_(INVERTED)"}

trans7 = {
    "AM: HDHDH \(PAVLOV 2\)":    "AM: HDHDH&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;",
    "AM: HDHHD \(TATFORTIT 2\)": "AM: HDHHD (PAVLOV)&nbsp;",
    "AM: HHDHD&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;=>":
                                 "AM: HHDHD (INVERTED) =>",
    "=> AM: HHDHD            ": "=> AM: HHDHD (INVERTED)"}


trans_tables = [trans1, trans2, trans3, trans4, trans5, trans6, trans7]

raw_dir = os.listdir(path)
pages = [entry for entry in raw_dir if entry.endswith(".html") and \
         entry.find("Automata") > -1]
pages.sort()

for page_name in pages:
    print "fixing page: ", page_name
    f = file(page_name, "r")
    page = f.read()
    f.close()
    for t in trans_tables:
        for k in t.keys():
            page = re.sub(k, t[k], page)
    f = file(page_name, "w")
    f.write(page)
    f.close()


working_dir = os.getcwd()
os.chdir(path)
os.chdir("Matchlogs")
raw_dir = os.listdir(path)
pages = [entry for entry in raw_dir if entry.endswith(".html")]

for page_name in pages:
    new_name = page_name
    for k in trans6.keys():
        new_name = re.sub(k, trans6[k], new_name)
    if new_name != page_name:
        print "changing ", page_name, "->", new_name
        os.rename(page_name, new_name)
        f = file(new_name, "r")
        page = f.read()
        f.close()
        for t in [trans3, trans4]:
            for k in t.keys():
                page = re.sub(k, t[k], page)
        f = file(new_name, "w")
        f.write(page)
        f.close()

os.chdir(working_dir)

