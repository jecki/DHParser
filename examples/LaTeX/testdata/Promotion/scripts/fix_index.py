#!/usr/bin/python
# fix_index.py - create an index.html file for all html files in a directory

import sys, os

if len(sys.argv) > 1:  
    path = sys.argv[1]
    title = os.path.basename(path)
else:
    path = "."
    title = os.path.basename(os.getcwd())

raw_dir = os.listdir(path)
html_files = [entry for entry in raw_dir if entry.endswith(".html") and entry.startswith("0")]
html_files.sort()

htmlHead = ["<html>\n<head>\n<title>" + title + "</title>\n<a/head>\n<body>\n" + \
"<h1>Index of " + title + "</h1>\n"]
htmlTail = ["</body>\n</html>"]

index_entries = []
for entry in html_files:
    link = '<a href="' + entry + '">' + entry[:-5] + '</a><br />\n'
    index_entries.append(link)

page = "".join(htmlHead + index_entries + htmlTail)
f = file("index.html", "w")
f.write(page)
f.close()

print "index.html has benn writen to disk!"



