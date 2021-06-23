#! /usr/bin/python3
# -*- encoding: utf-8 -*-

"""latex2html.py - Converts LaTeX documents into HTML documents.

Copyright 2015  by Eckhart Arnold

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Version 0.2 (May, 1st 2015)

WARNING: This program has hardly been tested and will most probably
not work as expected!
TODO: Support for mathematical formulae and MathML
"""


import os
import re
import string
import sys
import time
# Globals and predefined constants
PROJECT_TITLE = "title ?"
TOC_TITLE = "Table of Contents"
BIBLIOGRAPHY_TITLE = "Bibliography"
AUTHOR_STR = "Author"
DATE_STR = "Date"
AUTHOR = "author ?"
REFERENCE = "reference to author ?"  # don't edit! this is being used later
PDFURL = ""  # url of a PDF version of the document
DESCRIPTION = "description ?"
KEYWORDS = "keywords ?"
DATE = time.strftime("%Y-%m-%dT%H:%M:%S+01:00", time.localtime(time.time()))
LANG = "en"
INDEX_FILE = ""

# Tiefe bis zu der die Kapitelnummerierung angezeigt wird
CHAPTERNUMBERING_DEPTH = 3
DESTINATION_NAME = "destination ?"
ENDING = ".html"

CONVERTEPS = True  # convert postscript images to bitmap images

images = {"next.jpg": b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1fCreated by Ecki with The GIMP\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc2\x00\x11\x08\x00\x14\x00\x14\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x19\x00\x01\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x06\x03\x05\x07\xff\xc4\x00\x18\x01\x00\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x05\x03\x04\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\xb6\xed\xeaU*\xbc\xfd\xed\x15/|s\x84\xc0?\xff\xc4\x00\x1c\x10\x00\x03\x00\x01\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x04\x05\x01\x00\x06\x10\x13\x14\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\xbd]\x89\x8f\xa1]V\xb1\xad\xf6\xe0|\xf2eSs*\x0b\xa1b\xa8\xa9O\xc7\xff\xc4\x00\x17\x11\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01 "\xff\xda\x00\x08\x01\x03\x01\x01?\x01U\xc5\xce?\xff\xc4\x00\x1b\x11\x00\x01\x04\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x01\x11!\x02\x101\xff\xda\x00\x08\x01\x02\x01\x01?\x01\x10\x81\x90$\xb4\x9f\xb4\xa7_\xff\xc4\x00&\x10\x00\x01\x02\x03\x08\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x03\x00\x11\x12\x04\x10\x13\x14!1AQ"BRS\x81\xff\xda\x00\x08\x01\x01\x00\x06?\x02dp\xc7.\xe0\xe8R\xf6\xea\x13\xcb\x0c\xba]\xae\x0b\x01J\xb2Z\xe7\xf1\x846C.\xd7\xd8\xe7?\x90\xdb5\xa9\xd0\x92\x9a\xf3\x02\xfb\xb6v\xcd\xc1\xd8\x94uK\xff\x00\xff\xc4\x00\x1d\x10\x01\x00\x01\x04\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00\x10!A1Qaq\xff\xda\x00\x08\x01\x01\x00\x01?!i\xb6A)\x0eWX\x8a\x08J\xed\xcb\xe3`\x88\xc0\xd7 \xe2=i\\.\x88\x87\x9bR\xa0\x81\xda\xa1\xa8\xf89\x0b\xff\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10s\xdf\xbc\xff\xc4\x00\x1c\x11\x00\x01\x03\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x10\x11!1AQ\x91\xff\xda\x00\x08\x01\x03\x01\x01?\x10\xce{\x06\xddBb\xaa\x1b\xff\xc4\x00\x1c\x11\x01\x00\x01\x04\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x10\x111q!A\xc1\xff\xda\x00\x08\x01\x02\x01\x01?\x10\xce\x9fI\x97g\xad\xb7\x08!\\\x8axZ\x7f\xff\xc4\x00\x1f\x10\x01\x00\x01\x04\x02\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00!1AQ\x81\x10aq\xa1\xff\xda\x00\x08\x01\x01\x00\x01?\x10rG\x96\x08H\x13`\xce[5\x1f\xcd\x00\xa9\xc6\x1e\x98}QrJ\xc9\xeb]4[\xc9%\xb4<\xd4\x1dm]\xfa>\xf0R>\xcaP\x81\x98\xd7\xcd\x15\x7f\xbd\xf6\x89\x81NU\xa0\x82\x0cx\xff\xd9',
          "prev.jpg": b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1fCreated by Ecki with The GIMP\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc2\x00\x11\x08\x00\x14\x00\x14\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x19\x00\x01\x00\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x04\x07\x02\x06\xff\xc4\x00\x17\x01\x00\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x05\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\xd7<\x0c\xb9\xd6\xbc\xdb\xfb\xb6M\x12\xd4\x13\xb0\x03\xff\xc4\x00\x1b\x10\x00\x03\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x04\x05\x06\x00\x01\x11\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\xa6\x84\xce\x17\xec\x9e\x14\xdd\xb0\xa7\xd9\xf0\xd6X\xe8XPd\x92\xc1j\xb9L\xd3\xd4\x00"\x01\xff\xc4\x00\x19\x11\x00\x02\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x03\x10q\xff\xda\x00\x08\x01\x03\x01\x01?\x01\xb5\x9cr\r\xff\xc4\x00\x1d\x11\x00\x00\x05\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x041\x03\x10!"a\xff\xda\x00\x08\x01\x02\x01\x01?\x01cM\xa9\x96\xd9W`*o\xff\xc4\x00$\x10\x00\x02\x01\x04\x00\x05\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x00\x04\x11\x12\x10\x14!1a2Qq\x81\xd1\xff\xda\x00\x08\x01\x01\x00\x06?\x02\xdei\x15\x07\x9a\xd2\xd2?\xb6\xfc\xa8\xdaa\x89\n\x8d\x87\x9a\xe6\xac\xe7\x04\x85\xc1\x89\xbb\x1f\x8aA{nb\x91[!d\xa5\x91=,28iq\nJ\xbe\xcc3A\x10\x05Q\xd0\x01_\xff\xc4\x00\x1d\x10\x01\x00\x02\x02\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11Aq!1Q\x10a\xff\xda\x00\x08\x01\x01\x00\x01?!\xd9\xf9w\xa30yw5U\xae\xa0@\xb0\x0cS\x98\x18\x05n\xa8\xf5\x86\x19\xdb\x01B\x9e=;\x885\x8d\xbf\x1f\x99\x8f\x94\xe9\x05H\xd0P\x13\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10g\xff\x00\xbe\xff\xc4\x00\x19\x11\x00\x01\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x001\x00\x01\x10!Q\xff\xda\x00\x08\x01\x03\x01\x01?\x10\x15Zb\x82\x7f\xff\xc4\x00\x1c\x11\x00\x02\x02\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00!Qa1A\x81\xff\xda\x00\x08\x01\x02\x01\x01?\x10z\xd4\x14n\x86\xf1g\xc8\xce\xc2\xbe1\x01 \xb1\tvg\xff\xc4\x00\x1f\x10\x01\x00\x02\x02\x01\x05\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11!\x001Q\x10Aaq\x81\xb1\xff\xda\x00\x08\x01\x01\x00\x01?\x10F\'\xa6\xc5\xc6\xc5\xe00\xcc\x9aF\xeb\x8a\x1a\xfa\xcf\x8c\xd5\xe7n`\x8f\x8eA\xfa\xcbD\xb3\xdd&\xc6\x9erg\x10\x85\x9e\x91\xec*a\xca?\xe1l$\xfd\xe8t\x1d\x80E\xc9%>\xb0\xa0\x8e\x18D\x00\x1a\x03?\xff\xd9',
          "up.jpg": b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1fCreated by Ecki with The GIMP\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc2\x00\x11\x08\x00\x14\x00\x14\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x19\x00\x01\x01\x01\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x06\x05\x07\x08\xff\xc4\x00\x18\x01\x00\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x05\x03\x04\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\xed\xbc\xaf\x01\x8b\xab\xcf\xe8t\x12\xf7\x95\x00\xa8O\xff\xc4\x00\x1b\x10\x00\x03\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x04\x00\x05\x01\x06\x11\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\xb1\xe1,\xda\r\xc1^y\xde/\xf3\x99\x99V\xb6\xb9\xda/A\xcb9\xd1B\x13B\xd6\x02\xb0\xff\xc4\x00\x18\x11\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03 !\xff\xda\x00\x08\x01\x03\x01\x01?\x01\x91\xd8\x1c\xa7\xff\xc4\x00\x1d\x11\x01\x00\x01\x03\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00\x03\x04\x02\x10\x12!1\xff\xda\x00\x08\x01\x02\x01\x01?\x01\xc5\xc6\xb5\xaa\xd3\xcd\xed\xf2\x92\x18j]\xbf\xff\xc4\x00$\x10\x00\x02\x01\x04\x00\x05\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x00\x04\x11!\x05\x10\x12"12AQa\xb1\xff\xda\x00\x08\x01\x01\x00\x06?\x02\x92\xe2OJ\x0c\xd1I\x82\xab\x1d\xae?9E\xc3\xd4\xf9\xef\x7f\xbf\x81Q=\xc4\x12[\xf5m\x0b\x8d\x1aI\x97\xc3\x8c\xd0\xb8h#3(\xc0r\xbb\x14c\x9e$\x91\x0f\xb3\x0c\xd0DP\xaa4\x00\xaf\xff\xc4\x00\x1e\x10\x01\x00\x02\x02\x01\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x111\xf0a\x10Qq\xb1\xc1\xff\xda\x00\x08\x01\x01\x00\x01?!Zi\xef\x9e%\xf7@\x05j\xbe\xf4\x05k\xa1\x19\xd1\xea\\f\x94M;LF\xd3(\xbc\x84%\xe6d(\x87\x10/\x1d\x15\x01?\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10+\x1fB\xff\xc4\x00\x19\x11\x01\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11\x10!1\xff\xda\x00\x08\x01\x03\x01\x01?\x10"\x9d\x1d\x82%\x92\x8c\x7f\xff\xc4\x00\x1b\x11\x01\x00\x02\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x001\x11A!q\xb1\xff\xda\x00\x08\x01\x02\x01\x01?\x10\x0e#{I]g\xc8\xeda(\xe6\xa2\xab\x96\x7f\xff\xc4\x00\x1d\x10\x01\x01\x00\x02\x03\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00!1Aa\x10\x81\x91\xff\xda\x00\x08\x01\x01\x00\x01?\x10\xe43\'phz\xb0=p\xdf\xe2TM\xaa\xadtG\xcf\x84\x88\x9d\x9c*\x10m\xa8\xb3\xcc\x1au0@\xd2\xbc\x0fJ\xe9s\x8c\x02\x1e\xa9g\xd7\x19\xb2^\x08\x0b\x04S\x97\xf77ve\x0b\xd3\x1e\xfd\xc0\x11\xb1A\x10\x00\xe0\xcf\xff\xd9',
          "nextgrey.jpg": b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1fCreated by Ecki with The GIMP\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc2\x00\x11\x08\x00\x14\x00\x14\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x19\x00\x01\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x06\x03\x05\x07\xff\xc4\x00\x16\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x05\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\xb4m\xaa\x95]9\xfb\xa232\x8cs@\x0f\xff\xc4\x00\x1b\x10\x00\x03\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x04\x05\x00\x01\x06\x10\x13\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\xb9X\xf3^F\xaa\xac\xeb9\xc3a\xd2\xf2\xa5\xd2ok\x0b\xc5r\xaa\xb1M\xd7\xff\xc4\x00\x18\x11\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x12 "\xff\xda\x00\x08\x01\x03\x01\x01?\x01b\xf2\xcd?\xff\xc4\x00\x1a\x11\x01\x00\x01\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x01\x02\x10\x11!\xff\xda\x00\x08\x01\x02\x01\x01?\x01"\x1b\x87k\xc9\\\xff\x00\xff\xc4\x00\'\x10\x00\x01\x02\x04\x02\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x01\x03\x00\x10\x11\x12AQ\x04\x13\x14!"12BRS\x81\xff\xda\x00\x08\x01\x01\x00\x06?\x02dU\xb1\xd48=T\xee\xca\x13\x8a\xc2\xc9d\x1a\tR\xf2[\xeb\xe3\x08m\x0e\xce\xd7\xb1\xcc~@5r\x9d\xa9J\xae0/8\xc3f\xe0\xf2%\x1d\xe9?\xff\xc4\x00\x1c\x10\x01\x00\x01\x05\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00\x10!Aa1q\xff\xda\x00\x08\x01\x01\x00\x01?!h,E,\x1c\xf1\x88\xa0h\xbe\xdc?\x1b\x05\x8cMz\x0f#\xad/\xb5\xd1\x10\xe6\xd4\xcd\xb0\xf6\xa8=\xee\x0eB\xff\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10\xf4 \x80\xff\xc4\x00\x1a\x11\x01\x00\x01\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x101AQ\x91\xff\xda\x00\x08\x01\x03\x01\x01?\x106}\x8d\xbb\n\xff\x00\xff\xc4\x00\x1b\x11\x01\x00\x02\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11\x10!1Aq\xff\xda\x00\x08\x01\x02\x01\x01?\x10\xbf\xd7\xe99} \x07QW\x1f\xff\xc4\x00\x1f\x10\x01\x00\x01\x04\x03\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00!1A\x10Qqa\x81\xa1\xff\xda\x00\x08\x01\x01\x00\x01?\x10a\x8f\x9e\x92$D\xd8\x1b\xe5\xb3Vp\x90\x0c\xdda|a\xf8\xe3( T\xd1o$\x96\xd0\xf7P%\x95W\xe8\xfe\xf0S\x19\x9aQ\x01\x98\xd7\x9a\xab\xe7\x93\xa4L\nZ\xec\xf3\xff\xd9',
          "prevgrey.jpg": b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1fCreated by Ecki with The GIMP\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc2\x00\x11\x08\x00\x14\x00\x14\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x19\x00\x01\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x07\x02\x04\x06\xff\xc4\x00\x18\x01\x00\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x05\x03\x04\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\xb58Yk\xea\xbc\xf7\xc3$\xbd\xe5\xd5\x13\x9c\x07\xff\xc4\x00\x1a\x10\x00\x03\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x04\x01\x05\x06\x00\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\xa1\xea\x9c.\xf4Y\x85>\x9e\xa3\xd2r,\xb1\xb0\xb0\xa0\xe9(\xc5\x8b\xfa\x99\xd1H\x00\x88\x0f\xff\xc4\x00\x18\x11\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03 \x81\xff\xda\x00\x08\x01\x03\x01\x01?\x01\x94\xbeS\xff\xc4\x00\x1c\x11\x00\x01\x03\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x04\x03\x10!"1\xff\xda\x00\x08\x01\x02\x01\x01?\x01\x85N1\x1be\xc8\xf6\xff\x00\xff\xc4\x00!\x10\x00\x02\x01\x04\x02\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x00\x04\x11\x12!a\x101Qq\xd1\xff\xda\x00\x08\x01\x01\x00\x06?\x02\xdei\x02\x0e\xebKX\xf3\xdb~R\x19F\x1c\xa8\xd8wB\xe6\xd2q\xb0\\\x18\x9b\xd1\xfa\xa4\x17\x96\xe6)\x14\xe4\x07\xa5\x919V\x19\x1e4\xb8\x85%_\x86\x19\xa0\xaa\x00Q\xc0\x02\xbf\xff\xc4\x00\x1d\x10\x01\x00\x02\x02\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11Aq!1Q\x10a\xff\xda\x00\x08\x01\x01\x00\x01?!\xd9Ew\xafg)\xcb\xaa\xadu\x01\xb5\xc0b\x9c\x91\xdb\x00\xddP\xe5\x86\x00\xe8\x87B\x9e=;\x8a\xe5\x13~?2\xd9)\xd2\x01u\xa0\xa0\'\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10d\xd0\x00\xff\xc4\x00\x19\x11\x01\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01!1\x00\x10Q\xff\xda\x00\x08\x01\x03\x01\x01?\x10\x13\x11\xd1xV\xff\x00\xff\xc4\x00\x1c\x11\x00\x01\x04\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11!Q\x101a\xf0\xff\xda\x00\x08\x01\x02\x01\x01?\x103\'@0\x1e\xbb\xe8[\xa1\x90-\x8f\xff\xc4\x00\x1f\x10\x01\x00\x01\x04\x02\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00!1aAQ\x10q\x81\xa1\xff\xda\x00\x08\x01\x01\x00\x01?\x10xo\x86\xe2\xe8eh\xa2KB2\x0cXm\xf5\x9dV\x1f\xeds\x07\xe0\xc9Q\x02ZQ\x19\xe5&\xe3g\xba\x98\x8d\xe7g\xa4x\x16\x98ksQ \x91\xfd\xf1\x02\x15\x80\xc5\xd9%\x9d\x94\'\x93\x08"\x00\x0c\x01_\xff\xd9',
          "upgrey.jpg": b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe\x00\x1fCreated by Ecki with The GIMP\xff\xdb\x00C\x00\x05\x03\x04\x04\x04\x03\x05\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07\x07\x07\x0f\x0b\x0b\t\x0c\x11\x0f\x12\x12\x11\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11\x11\x18!\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17"$"\x1e$\x1c\x1e\x1f\x1e\xff\xdb\x00C\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc2\x00\x11\x08\x00\x14\x00\x14\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1a\x00\x01\x00\x02\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x06\x02\x05\x07\x08\xff\xc4\x00\x18\x01\x00\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x05\x03\x04\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\xeau\x8d\x156\xaf?\xa0\x10%\xef\x1e`H\x13\xff\xc4\x00\x1b\x10\x00\x03\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x04\x00\x05\x01\x06\x11\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\xa9\xe14\xda\x1d\xb9^y\xddn\xf3\x99\x99N\xb6\xb40\\\x92\x9ar\xa1\xe9S\xd6\x02 \x1f\xff\xc4\x00\x18\x11\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03 !\xff\xda\x00\x08\x01\x03\x01\x01?\x01\x91\xd8\x1c\xa7\xff\xc4\x00\x1d\x11\x01\x00\x01\x03\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00\x03\x04\x02\x10\x12!1\xff\xda\x00\x08\x01\x02\x01\x01?\x01\xc5\xc6\xb5\xaa\xd3\xcd\xed\xf2\x92\x18j]\xbf\xff\xc4\x00"\x10\x00\x02\x01\x04\x01\x04\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x00\x04\x11!1\x10\x12"2AQa\xff\xda\x00\x08\x01\x01\x00\x06?\x02\x92y=Pd\xd1IUU\xb9\\t\x8a\xc1O>o\xfb\xf4*\'\xb8\x82K~\xed\xa1q\xa3I*\xf0\xc34.\x1a\x18\xcc\xaa0\x1c\xae\xc5\x18\xe6\x8ddC\xf0\xc34\x11\x14*\x8d\x00+\xff\xc4\x00!\x10\x01\x00\x02\x00\x04\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11\x101\xb1\xf0!Qa\x81\x91\xc1\xd1\xff\xda\x00\x08\x01\x01\x00\x01?!h\xe9\xff\x00(\x82\x95\x86\x8f\x1e\xf0\x0e"T\x0c\xf64\x97Q%\x13g)\x96_=\xe5JX\x84\xba3;\xbe\x1cCP4\x14\x04\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10X\x1f~\xff\xc4\x00\x19\x11\x01\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11\x10!1\xff\xda\x00\x08\x01\x03\x01\x01?\x10\x02\x9d\x1d\x82%\x92\x8c\x7f\xff\xc4\x00\x1b\x11\x01\x00\x01\x05\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x11!1Aq\xb1\xff\xda\x00\x08\x01\x02\x01\x01?\x10\x06#{I\x8eW\xc8\xcc\x17&\x0b\xc5V\xac\xff\xc4\x00\x1c\x10\x01\x01\x00\x03\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x11\x00!1aA\x10\x91\xff\xda\x00\x08\x01\x01\x00\x01?\x10\xec\x86F\xd8hz\xb0=p\x06H\x14\x93k\xab]\x11\xd7?\x0e\x9e;XT \xdbQg\x989R\x00\x81\xa5x?\x15\xb8\xb9w#/@X\xfas6\n\x01\x01b\x14\xda\xff\x00s\xa8*\xc2\xfcbK\xee\x0ck\x8c\x08\x80\x07\x0c\xff\xd9'}

CSSStylesheet = '''
body { max-width: 760px; min-width: 320px;
       margin-left:auto; margin-right:auto; }

a,h1,h2,h3,h4,h5,div,td,th,address,blockquote,nobr,b,i {
    font-family:"Liberation Sans", Arial, Helvetica, sans-serif;
}

a.bibref { font-family: serif; color: #202070; }

p,ul,ol,li { font-family: serif;
             font-feature-settings: "liga";
             text-rendering: optimizeLegibility;
             letter-spacing: -0.02em;
             color: #303030; }

p, li           { font-size:1.4em; line-height:1.6em; }
li > p          { font-size:1.0em; }

/* ol.bibliography { font-size:0.8em; line-height:0.9em; } */

p.footnote      { font-size:1em; line-height:1.1em; }
p.figure        { font-size:1.1em; line-height:1.3em; text-align:center; }

div.caption     { font-size:1em; line-height:1.1em; text-align:center; }


td		{ font-size:1.2em; }
td.title        { background-color:#F4F4F4; }
td.toplink      { background-color:#F4F4F4; }
td.bottomlink   { background-color:#FFFFFF; }
td.toc          { background-color:#F4F4F4; }
td.tochilit     { background-color:#E7E6E7; }

a:link         { text-decoration:none; }
a:visited      { text-decoration:none; }
a:hover        { color:red; text-decoration:underline; }
a:active       { text-decoration:none; }

a.internal:link         { color:blue; }
a.internal:visited      { color:blue; }
a.internal:hover        { color:red; }
a.internal:active       { color:blue; }

h1 { font-size:1.6em; }
h2 { font-size:1.5em; }
h3 { font-size:1.4em; }
h4 { font-size:1.3em; font-weight:bold; }
h5 { font-size:1.2em; font-weight:bold; }

'''

HTMLPageHead = '''
<!DOCTYPE HTML>

<html lang="$lang">

<head>
<meta charset="utf-8" />

<title>$title</title>

<meta name="author"       content="$author" />
<meta name="description"  lang="$lang" content="$description" />
<meta name="keywords"     lang="$lang" content="$keywords" />
<meta name="date"         content="$date" />
<meta name="robots"       content="$robots" />

<meta http-equiv="content-type"        content="text/html; charset=UTF-8" />
<meta http-equiv="content-script-type" content="text/javascript" />
<meta http-equiv="content-style-type"  content="text/css" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />

<link rel="stylesheet" type="text/css" href="$stylesheetname" />
$prevpg
$nextpg
</head>

<body style="background-color:white">

'''

# <body style="background-color:#FFFFF0"> <!-- beige backgrounde -->
# <link rel=stylesheet type="text/css" media="screen" href="screenstyle.css">
# <link rel=stylesheet type="text/css" media="printer" href="printerstyle.css">
# <body marginwidth="8" marginheight="8" leftmargin="8" topmargin="8">

HTMLPageTop = '''
<table width="100%" border="0" frame="void" cellpadding="0" cellspacing="0"
 summary="page heading">
<tr>
<td class="title">
<h1 style="text-align:center;"><span id="pagetop" name="pagetop">$doctitle</span></h1>
</td>
</tr>
</table>
'''

HTMLTitlePageBottom = '''
<p align="center"><a href="$pdfurl" style="$style">$pdfmessage</a></p>
'''

HTMLPageTail = '''
</body>

</html>

'''

CHARS = string.ascii_letters + "äöüÄÖÜß" + "áàéèúùóòíìâêûôîÁÀÉÈÓÒÚÙÍÌÂÊÛÔÎ" + \
    "0123456789" + "!\"§$%&/()[]=?'`*+~'#<>|,.-;:_^°"

CROSSReferences = {}
IMAGENames = []
SCALEFactors = {}


class ScannerError(Exception):

    def __init__(self, error="Scanner Error"):
        Exception.__init__(self)
        self.error = error


class TexScanner:
    files = []
    fIndex = -1
    eof = 1
    line = ""
    pos = 0

    def __init__(self, fname):
        self.files.append(open(fname, "r"))
        self.fIndex = 0
        self.eof = 0
        self.patchBibFile = False

    def getRawLine(self):
        return self.files[self.fIndex].readline()

    def getLine(self):
        if self.eof:
            return ""

        while 1:
            while 1:
                s = self.getRawLine()
                if self.patchBibFile:
                    s = re.sub("~", " ", s)
                if s != "":
                    break

                self.files[self.fIndex].close()
                if self.patchBibFile:
                    self.patchBibFile = False
                self.files.remove(self.files[self.fIndex])
                self.fIndex = self.fIndex - 1

                if self.fIndex < 0:
                    self.eof = 1
                    break

            if self.eof:
                break

            s = s.replace("\t", " ")  # Tabulatoren eliminieren

            i, k = 0, len(s)                     # Führende Leerzeichen weg
            while (i < k) and (s[i] == " "):
                i = i + 1
            s = s[i:]

            if s[:1] == "%":
                continue           # Kommentarzeilen ignorieren
            i = s.find("%")             # Kommentare beseitigen
            while i > 0:
                if s[i - 1] == "\\":
                    i = s.find("%", i + 1)
                else:
                    s = s[:i]
                    i = -1
            s = re.sub(r"\\\%", "%", s)
            # if s.find("%") >= 0: print (s)

            while (s[-1:] == "\012") or (s[-1:] == "\015"):
                s = s[:-1]  # EOL

            i = s.find("\\input{")
            if i >= 0:
                i = i + 7
                k = s.find("}", i)
                fname = s[i:k]
                self.fIndex = self.fIndex + 1
                self.files.append(open(fname, "r"))
                continue

            i = s.find("\\bibliographystyle{")
            if i >= 0:
                i += 19
                k = s.find("}", i)
                bibstyle = s[i:k]
                if bibstyle != "plain":
                    fname = texFileName[:-4] + ".aux"
                    backupname = fname + ".latex2html.tmp"

                    os.rename(fname, backupname)
                    f = open(backupname, "r")
                    data = f.read()
                    f.close()
                    data = re.sub("\\\\bibstyle\\{" + bibstyle + "\\}",
                                  "\\\\bibstyle{plain}", data)
                    # print (fname, re.findall("\{plain\}", data))
                    f = open(fname, "w")
                    f.write(data)
                    f.close()

                    os.system("bibtex " + texFileName[:-4])
                    os.rename(backupname, fname)

                    continue

            i = s.find("\\bibliography{")
            if i >= 0:
                fname = texFileName[:-4] + ".bbl"
                self.fIndex += 1
                self.files.append(open(fname, "r"))
                self.patchBibFile = True
                continue

            break

        return s

    def getToken(self):

        def stripLine(s):
            s = re.sub(r"\\\-", "", s)
            s = re.sub(r"\\\_", "_", s)
            s = re.sub(r"\\\/", "", s)
            s = re.sub(r"\"`", '"', s)
            s = re.sub(r"\"'", '"', s)
            s = re.sub(r"``", '"', s)
            s = re.sub(r"''", '"', s)
            s = re.sub(r'""', "", s)
            s = re.sub(r"\\\~{ }", "~", s)
            s = re.sub(r"---", "-", s)
            s = re.sub(r"--", "-", s)
            # Sonderzeichen
            s = re.sub(r"\\\\'e", "é", s)
            s = re.sub(r"\\\\`e", "è", s)
            s = re.sub(r"\\\\'a", "á", s)
            s = re.sub(r"\\\\`a", "à", s)
            s = re.sub(r"\\\\u{g}", "&#287;", s)
            s = re.sub(r"\\\\i ", "&#305;", s)
            return s

        # if self.eof: return ""
        if self.eof:
            raise ScannerError("End of File reached")

        if self.pos >= len(self.line):
            self.line = self.getLine()
            self.pos = 0
            if self.line == "":
                while (self.line == "") and (not self.eof):
                    self.line = self.getLine()
                self.line = stripLine(self.line)
                return ""                               # Token "" = Absatzende
            else:
                self.line = stripLine(self.line)
                # Zeilenende als Leerzeichen interpretieren
                return " "

        if self.line[self.pos] == " ":
            while self.line[self.pos:self.pos + 1] == " ":
                self.pos = self.pos + 1
            return " "                                  # Einzelnes Leerzeichen

        if self.line[self.pos] in CHARS:
            word = ""
            while (self.pos < len(self.line)) and \
                  (self.line[self.pos] in CHARS):
                word = word + self.line[self.pos]
                self.pos = self.pos + 1
            return word                 # Token "Buchstabenfolge" = Wort

        if self.line[self.pos] == "\\":
            command = "\\"
            self.pos = self.pos + 1
            while (self.pos < len(self.line)) and \
                  (self.line[self.pos] in CHARS):
                command = command + self.line[self.pos]
                self.pos = self.pos + 1
            if self.line[self.pos:self.pos + 1] == "{":
                command = command + self.line[self.pos]
                self.pos = self.pos + 1
            elif (self.line[self.pos:self.pos + 1] == "\\") and \
                 (command == "\\"):
                command = command + self.line[self.pos]
                self.pos = self.pos + 1
                if (self.pos < len(self.line)) and \
                   (self.line[self.pos] == "["):
                    while (self.pos < len(self.line)) and \
                          (self.line[self.pos] != "]"):
                        self.pos = self.pos + 1
                    self.pos = self.pos + 1
            return command

        if self.line[self.pos:self.pos + 2] == "{\\":
            command = "{\\"
            self.pos = self.pos + 2
            while (self.pos < len(self.line)) and \
                  (self.line[self.pos] in string.ascii_letters):
                command = command + self.line[self.pos]
                self.pos = self.pos + 1
            if self.line[self.pos:self.pos + 1] == " ":
                self.pos = self.pos + 1
            return command

        self.pos = self.pos + 1
        return self.line[self.pos - 1:self.pos]


HTMLPageType = ["TitlePage", "TableOfContents", "NormalPage"]


class HTMLPage:
    # links to related Pages

    def __init__(self, name, title, page_type="NormalPage",
                 chapter=[0, 0, 0, 0, 0, 0]):
        self.next = None
        self.prev = None
        self.up = None
        self.contents = None
        self.index = None
        self.home = None

        self.head = []
        self.top = []
        self.body = []
        self.bottom = []
        self.foot = []
        self.end = []
        self.tail = []
        self.link = []
        self.toplink = []
        self.toc_dl = []

        self.name = name
        self.title = title
        self.type = page_type
        self.chapter = [chapter[0], chapter[1], chapter[2],
                        chapter[3], chapter[4], chapter[5]]  # workaround
        self.pageList = []
        self.bibpageNr = 0

        if self.title != "title ?":
            print("parsing: " + self.title)

    def createLink(self):
        self.link = [
            '\12<table width="100%" border="0" frame="void" cellpadding="0"'
            ' cellspacing="2" summary="navigation bar">\12<tr>\12']
        self.link.append(
            '<td class="bottomlink" align="center" valign="middle"'
            ' width="100%"><hr noshade="noshade" /></td>\12')
        if self.up is not None:
            self.link.append('<td class="bottomlink" align="center"'
                             ' valign="middle"><a class="internal" href="' +
                             self.name + '#pagetop' + '"><img width="40"'
                             ' height="40" border="0" align="middle"'
                             ' src="up.jpg" alt="page top" /></a></td>\12')
        if self.next is not None:
            self.link.append('<td class="bottomlink" align="center"'
                             ' valign="middle"><a class="internal" href="' +
                             self.next.name + '"><img width="40" height="40"'
                             ' border="0" align="middle" src="next.jpg"'
                             ' alt="next" /></a></td>\12')
        self.link.append("</tr>\12</table>\12\12")

        self.toplink = ['\12<table width="100%" border="0" frame="void"'
                        ' cellpadding="0" cellspacing="0"'
                        ' summary="navigation bar">\12<tr>\12']
        if self.prev is not None:
            self.toplink.append('<td class="toplink" align="center"'
                                ' valign="middle"><a class="internal"'
                                ' href="' + self.prev.name + '">'
                                '<img width="40" height="40" border="0"'
                                ' align="middle" src="prevgrey.jpg"'
                                ' alt="previous" /></a></td>\12')
        if self.up is not None:
            self.toplink.append('<td class="toplink" align="center" '
                                'valign="middle"><a class="internal" href="' +
                                self.up.name + '"><img width="40" height="40"'
                                ' border="0" align="middle" src="upgrey.jpg"'
                                ' alt="up" /></a></td>\12')
        if self.next is not None:
            self.toplink.append('<td class="toplink" align="center"'
                                ' valign="middle"><a class="internal" href="'
                                + self.next.name + '"><img width="40"'
                                ' height="40" border="0" align="middle"'
                                ' src="nextgrey.jpg" alt="next" />'
                                '</a></td>\12')
        self.toplink.append(
            '<td class="toplink" align="center" valign="middle" width="100%">'
            + REFERENCE + '</td>\12')
        if self.contents is not None:
            self.toplink.append('<td class="toplink" align="center"'
                                ' valign="middle"><a class="internal" href="'
                                + self.contents.name + '">' + TOC_TITLE +
                                '</a></td>\12')
        if self.index is not None:
            self.toplink.append(
                '<td class="toplink" align="center" valign="middle">'
                '<a class="internal" href="' + self.index.name + '">'
                'Index</a></td>\12')
        if self.home is not None:
            self.toplink.append(
                '<td class="toplink" align="center" valign="middle">'
                '<a class="internal" href="' + self.home.name +
                '">Home</a></td>\12')
        self.toplink.append("</tr>\12</table>\12\12")

    def activateLinksInStr(self, s):
        i = 0
        N = len(s)
        while i < N:
            i = s.find("http:", i)
            if i < 0:
                i = N
            else:
                k = i
                while (k < N) and (not (s[k] in ' "<>()[]{}')):
                    k += 1
                if s[k - 1] == ".":
                    k -= 1
                s2 = s[i:k]
                s = s[0:i] + '<a href="' + s2 + '">' + s2 + '</a>' + s[k:N]
                i += len(s2) * 2 + 15
        return (s)

    def activateLinks(self, l):
        for i in range(len(l)):
            l[i] = self.activateLinksInStr(l[i])

    def crossReferences(self, s):
        # global CROSSReferences
        i = 0
        offset = 0
        while i >= 0:
            i = s.find("TEXREF", offset)
            if i >= 0:
                k = s.find('"', i)
                if k >= 0:
                    tmpl = s[i:k]
                    name = tmpl[6:]
                    if name in CROSSReferences:
                        s = re.sub(s[i:k], CROSSReferences[name][1], s)
                offset = i + 1
        i = 0
        offset = 0
        while i >= 0:
            i = s.find("TEXLINK", offset)
            if i >= 0:
                k = s.find('<', i)
                if k >= 0:
                    tmpl = s[i:k]
                    name = tmpl[7:]
                    if name in CROSSReferences:
                        s = re.sub(s[i:k], CROSSReferences[name][0], s)
                offset = i + 1
        return s

    def fixReferences(self, l):
        for i in range(len(l)):
            l[i] = self.crossReferences(l[i])

    def postFix(self, page):
        page = re.sub("ä|\xe4", "&auml;", page)   # HTML-Umlaute
        page = re.sub("ö|\xf6", "&ouml;", page)
        page = re.sub("ü|\xfc", "&uuml;", page)
        page = re.sub("Ä|\xc4", "&Auml;", page)
        page = re.sub("Ö|\xd6", "&Ouml;", page)
        page = re.sub("Ü|\xdc", "&Uuml;", page)
        page = re.sub("ß|\xdf", "&szlig;", page)

        page = re.sub("é|\xe9", "&eacute;", page)
        page = re.sub("è|\xe8", "&egrave;", page)
        page = re.sub("á|\xe1", "&aacute;", page)
        page = re.sub("à|\xe0", "&agrave;", page)
        page = re.sub("â|\xe2", "&acirc;", page)
        page = re.sub("ò|\xf2", "&ograve;", page)
        page = re.sub("ó|\xf3", "&oacute;", page)

        page = re.sub("§|\xa7", "&sect;", page)
        page = page.replace("$bibnode", "node" + str(self.bibpageNr) + ".html")
        return page

    def genPDFMessage(self, style="font-weight:normal"):
        bottom = HTMLTitlePageBottom
        if PDFURL != "":
            bottom = re.sub(r"\$pdfurl", PDFURL, bottom)
            if LANG[0:2] == "de":
                message = "Ausdruckbare PDF-Version des Dokuments"
            else:
                message = "Printable PDF version of the document"
            bottom = re.sub(r"\$pdfmessage", message, bottom)
            bottom = re.sub(r"\$style", style, bottom)
        else:
            bottom = ""
        return bottom

    def flush(self):
        if self.title == "title ?":
            self.title = PROJECT_TITLE
        if len(self.title) > 64:
            self.title = self.title[0:64]

        pg_head = re.sub(r"\$title", self.title, HTMLPageHead)
        prev_pg = ""
        next_pg = ""
        if self.prev is not None:
            prev_pg = '<link rel="prev" href="' + self.prev.name + '">'
        if self.next is not None:
            next_pg = '<link rel="prev" href="' + self.next.name + '">'
        pg_head = re.sub(r"\$prevpg", prev_pg, pg_head)
        pg_head = re.sub(r"\$nextpg", next_pg, pg_head)
        self.head = [pg_head]

        self.tail = [HTMLPageTail]

        if self.type == "TitlePage":
            self.head = [re.sub("follow", "index, follow", self.head[0], 1)]
            self.createLink()
            mytoplink = "".join(self.toplink)
            self.top = [HTMLPageTop] + [mytoplink] + \
                ['<hr noshade="noshade" />\12']
            self.end = self.link
            self.activateLinks(self.body)
            page = self.head + self.top + self.body + self.end + \
                [self.genPDFMessage()] + self.tail

        elif self.type == "TableOfContents":
            self.createLink()
            self.top = [HTMLPageTop] + self.toplink + ['<hr noshade="noshade" />\12'] + \
                       ['<table width="100%" summary="table of contents">'
                        '\12<tr>\12<td class="toc">']
            self.end = ["</td>\12</tr>\12</table>\12"] + self.link

            self.top.append("<h1>" + self.title + "</h1>\012\012")

            currPage = self.next
            mind = 5
            while currPage is not None:
                for i in range(len(currPage.body)):
                    pos = currPage.body[i].find("<h")
                    if pos >= 0:
                        depth = int(currPage.body[i][pos + 2])
                        if depth < mind:
                            mind = depth
                        self.toc_dl.append(depth)
                        pos2 = currPage.body[i].find("</h")
                        entry = currPage.body[i][pos + 4:pos2]
                        tab = ""
                        for k in range((depth - mind) * 4):
                            tab = tab + "&#160;"
                        if depth == mind:
                            self.body.append(
                                '<br />\012' + tab + '<a class="internal"'
                                ' href="' + currPage.name + '"><b>' + entry +
                                '</b></a><br />\012')
                        else:
                            self.body.append(
                                tab + '<a class="internal" href="' +
                                currPage.name + '">' + entry +
                                '</a><br />\012')

                currPage = currPage.next

            page = self.head + self.top + self.body + self.end + \
                [self.genPDFMessage(style="font-weight:normal")] + self.tail

        elif self.type == "NormalPage":
            self.createLink()

            markl = []
            for i in range(len(self.contents.body)):
                markl.append(0)
            i, pos = 0, -1
            while (pos < 0) and (i < len(self.contents.body)):
                if self.contents.body[i].find(self.name) >= 0:
                    pos = i
                i += 1
            while (pos == (i - 1)) and (i < len(self.contents.body)):
                if self.contents.body[i].find(self.name) >= 0:
                    pos = i
                i += 1
            markl[pos] = 2
            mydepth = self.contents.toc_dl[pos]
            if pos < (len(self.contents.body) - 1):
                ratsche = self.contents.toc_dl[pos + 1]
            else:
                ratsche = mydepth
            for i in range(pos + 1, len(self.contents.body)):
                if self.contents.toc_dl[i] <= ratsche:
                    markl[i] = 1
                    ratsche = self.contents.toc_dl[i]
            ratsche = mydepth
            i = pos - 1
            while i >= 0:
                if self.contents.toc_dl[i] <= ratsche:
                    markl[i] = 1
                    ratsche = self.contents.toc_dl[i]
                i -= 1
            self.top.append(
                '<table width="100%" border="0" frame="void" cellpadding="0"'
                ' cellspacing="0" summary="abbreviated table of contents">'
                '\012')
            t1s = '<tr><td class="toc">'
            t1xs = '<tr><td class="tochilit">'
            t2s = "</td></tr>\012"
            for i in range(len(self.contents.body)):
                st = self.contents.body[i][0:]
                # str = re.sub("\012", "", str)
                st = re.sub(r"\n", "", st)
                st = re.sub(r"\<br /\>", "", st)
                st = re.sub(r"\<b\>", "", st)
                st = re.sub(r"\</b\>", "", st)
                if markl[i] == 1:
                    self.top.append(t1s + st + t2s)
                elif markl[i] == 2:
                    x1 = st.find("<a")
                    x2 = st.find("a>") + 2
                    self.top.append(
                        t1xs + st[:x1] + "<b>" + st[x1:x2] + "</b>" +
                        st[x2:] + t2s)
            self.top.append('</table>\012\012')

            self.top = [HTMLPageTop] + self.toplink + \
                ['<hr noshade="noshade" />\12'] + \
                self.top + ['<hr noshade="noshade" />\012']
            self.bottom = self.link
            self.end = self.link

            self.fixReferences(self.body)
            self.fixReferences(self.foot)
            self.activateLinks(self.body)
            self.activateLinks(self.foot)

            if self.foot != []:
                page = self.head + self.top + self.body + \
                    self.bottom + self.foot + self.end + self.tail
            else:
                page = self.head + self.top + self.body + self.end + self.tail

        page = self.postFix("".join(page))
        print("writing: " + self.name)
        f = open(self.name, "w")
        f.write(page)
        f.close()
        return page


SECTIONS = ["\\chapter{", "\\section{", "\\subsection{", "\\subsubsection{",
            "\\paragraph{", "\\subparagraph{"]

TermPSequence = SECTIONS + ["\\begin{document}", "\\end{document}",
                            "\\begin{titlepage}", "\\end{titlepage}",
                            "\\newpage", "\\maketitle"]

TermWSequence = TermPSequence + ["", "\\footnote{",  # "\\caption{"
                                 "\\begin{enumerate}", "\\end{enumerate}",
                                 "\\begin{quote}", "\\end{quote}",
                                 "\\begin{quotation}", "\\end{quotation}",
                                 "\\begin{enumeration}", "\\end{enumeration}",
                                 "\\begin{itemize}", "\\end{itemize}",
                                 "\\item",  # , "\\bibitem",
                                 "\\begin{center}", "\\end{center}",
                                 "\\begin{flushleft}", "\\end{flushleft}",
                                 "\\begin{flushright}", "\\end{flushright}",
                                 "\\begin{thebibliography}",
                                 "\\end{thebibliography}",
                                 "\\begin{abstract}", "\\end{abstract}",
                                 "\\begin{figure}", "\\end{figure}",
                                 "\\begin{verbatim}", "\\end{verbatim}"]


class ParserError(Exception):

    def __init__(self, error="Parser Error"):
        Exception.__init__(self)
        self.error = error

HeadT = ["<h1>",  "<h2>",  "<h3>",  "<h4>",  "<h5>",  "<h6>"]
HeadTE = ["</h1>", "</h2>", "</h3>", "</h4>", "</h5>",  "</h6>"]


class TexParser:

    def __init__(self, tex_scanner):
        self.scanner = tex_scanner
        self.token = ""
        self.tableOfContents = []
        self.pageList = []
        self.bibpageNr = 0
        self.currPage = None
        self.nodeCount = 0
        self.chapter = [0, 0, 0, 0, 0, 0]
        self.chapterName = ""
        self.footnoteNr = 0
        self.leadIn = 0
        self.depth = 0
        self.mindepth = 5
        self.citeFlag = False
        self.figureFlag = False
        self.figureNr = 0

    def copyImage(self, name):
        print("processing: " + name)
        if CONVERTEPS and name.endswith(".eps"):
            out = name[:-4] + ".png"
            if name in SCALEFactors:
                scale = SCALEFactors[name]
            else:
                scale = 1.0
            os.system('pstoimg "../' + name + '" -out "' + out +
                      '" -quiet -antialias -aaliastext -scale ' + str(scale))
        else:
            os.system('cp "../' + name + '" ./')

    def flushPageList(self):
        global HTMLPageHead, HTMLPageTop

        # nochmal lesen, da eingetragene Werte entscheidend
        if os.path.exists(basename + ".l2h"):
            with open(basename + ".l2h", "r") as f:
                print("reading metadata from file: " + basename + ".l2h")
                exec(f.read(), globals(), globals())

        HTMLPageHead = re.sub(r"\$author",
                              re.sub("\\n|(<.*?>)", "", REFERENCE),
                              HTMLPageHead)
        HTMLPageHead = re.sub(r"\$description", DESCRIPTION, HTMLPageHead)
        HTMLPageHead = re.sub(r"\$keywords", KEYWORDS, HTMLPageHead)
        HTMLPageHead = re.sub(r"\$date", DATE, HTMLPageHead)
        HTMLPageHead = re.sub(r"\$robots", "follow", HTMLPageHead)
        HTMLPageHead = re.sub(
            r"\$stylesheetname", DESTINATION_NAME + ".css", HTMLPageHead)
        HTMLPageHead = re.sub(r"\$lang", LANG, HTMLPageHead)

        HTMLPageTop = re.sub(r"\$author", AUTHOR, HTMLPageTop)
        HTMLPageTop = re.sub(r"\$doctitle", PROJECT_TITLE, HTMLPageTop)

        lastPage = None
        contentPage = self.pageList[1]
        upPage = [self.pageList[1], self.pageList[1], self.pageList[
            1], self.pageList[1], self.pageList[1], self.pageList[1]]

        for page in self.pageList:
            if lastPage is not None:
                lastPage.next = page
            page.contents = contentPage
            page.prev = lastPage
            lastPage = page

            depth = 0
            while (page.chapter[depth] == 0) and (depth < 5):
                depth = depth + 1
            while (page.chapter[depth] != 0) and (depth < 5):
                depth = depth + 1
            if depth > 0:
                for i in range(depth, 5):
                    upPage[i] = page
                page.up = upPage[depth - 1]
            else:
                page.up = upPage[0]

        contentPage.up = self.pageList[0]
        self.pageList[0].up = None

        if os.access(DESTINATION_NAME, os.F_OK) == 0:
            os.mkdir(DESTINATION_NAME)
        os.chdir(DESTINATION_NAME)

        f = open(DESTINATION_NAME + ".css", "w")
        f.writelines(CSSStylesheet)
        f.close()

        for page in self.pageList:
            page.pageList = self.pageList
            page.bibpageNr = self.bibpageNr
            p = page.flush()
            if page.name == INDEX_FILE:
                f = open("index.html", "w")
                f.write(p)
                f.close()
        for name in IMAGENames:
            self.copyImage(name)

    def writeImages(self):
        for key, value in images.items():
            print(key)
            f = open(key, "wb")
            f.write(value)
            f.close()

    def getToken(self):
        token = self.scanner.getToken()
        if (token == "\\begin{") or (token == "\\end{") or \
           (token == "\\bibitem{") or (token[0:5] == "\\cite") or \
           (token == "\\label{") or (token == "\\ref{") or \
           (token == "\\bibliographystyle{"):
            s = ""
            while s != "}":
                s = self.scanner.getToken()
                token = token + s
        return token

    def interpretFontType(self, ltxStr):
        if ltxStr == "em":
            return ["<EM>", "</EM>"]
        elif ltxStr == "bf":
            return ["<B>", "</B>"]
        elif ltxStr == "it":
            return ["<I>", "</I>"]
        elif ltxStr == "tt":
            return ["<TT>", "</TT>"]
        elif ltxStr == "small":
            return ["<SMALL>", "</SMALL>"]
        elif ltxStr == "large":
            return ["<BIG>", "</BIG>"]
        elif ltxStr == "Large":
            return ["<BIG>", "</BIG>"]
        elif ltxStr == "high":
            return["<SUP>", "</SUP>"]
        else:
            return ["", ""]

    def readableBibKey(self, key):
        s = [ch for ch in key]
        s[0] = s[0].upper()
        for i in range(1, len(s)):
            if s[i - 1] == "-" and "".join(s[i:i + 6]).lower() != "et-al:" and \
               "".join(s[i:i + 3]).lower() != "al:":
                s[i - 1] = "/"
            if s[i - 1] == " " or s[i - 1] == "," or s[i - 1] == "/":
                s[i] = s[i].upper()
        return "".join(s)

    def targetFromBibKey(self, key):
        return key.replace(":", "_").replace("/", "_").strip()

    def splitCitation(self, s):
        pages, author = [], []
        i = s.find("[")
        if i >= 0:
            i += 1
            while s[i] != "]":
                pages.append(s[i])
                i += 1
        i = s.find("{") + 1
        while s[i] != "}":
            author.append(s[i])
            i += 1
        return "".join(pages), self.readableBibKey("".join(author))

    def getImgWidth(self, s):
        i = s.find("[") + 1
        k = s.find("]")
        if i > 0 and k > i:
            s = s[i:k]
            i = s.find("width")
            if i >= 0:
                i += 6
                k = s.find("cm", i)
                if k >= 0:
                    w = float(s[i:k])
                    return w
        return -1.0

    def readStr(self):
        st = ""
        self.token = self.getToken()
        while self.token != "}":
            st += self.token
            self.token = self.getToken()
        return st

    def sequenceOfWords(self):
        global PROJECT_TITLE, AUTHOR, REFERENCE, DATE
        stack = []
        sequence = []
        s = ""
        while (not (self.token in TermWSequence)) and \
                (not (self.token[1:8] == "bibitem")):
            if self.token == "\\\\" or self.token == "\\linebreak":
                s = s + "<br />\12"
            elif self.token[0:2] == "{\\":
                ft = self.interpretFontType(self.token[2:])
                s = s + ft[0]
                stack.append(ft[1])
            elif self.token[0:1] == "\\":
                if self.token[1:] == "title{":
                    self.token = self.getToken()
                    PROJECT_TITLE = "".join(
                        self.sequenceOfWords()).strip()  # self.readStr()
                    # TODO: ELIMINATE CR/LF from PROJECT_TITLE string!!!
                elif self.token[1:] == "subtitle{":
                    self.token = self.getToken()
                    PROJECT_TITLE += "\n<br />\n" + \
                        "".join(self.sequenceOfWords())
                    # TODO: ELIMINATE CR/LF from PROJECT_TITLE string!!!
                elif self.token[1:7] == "author":
                    AUTHOR = self.readStr()
                    if REFERENCE == "reference to author ?":
                        REFERENCE = AUTHOR
                elif self.token[1:5] == "date":
                    DATE = self.readStr()
                elif self.token[1:5] == "cite":
                    self.citeFlag = True
                    pages, authors = self.splitCitation(self.token)
                    links = []
                    for author in authors.split(","):
                        links.append('<a class="bibref" href="$bibnode#' +
                                     self.targetFromBibKey(author) + '">' +
                                     author + '</a>')
                    link = ", ".join(links)
                    if pages != "":
                        s = s + "(" + link + ", " + pages + ")"
                    else:
                        s = s + "(" + link + ")"
                elif self.token[1:16] == "includegraphics":
                    w = self.getImgWidth(self.token)
                    name = self.readStr()
                    IMAGENames.append(name)
                    if w > 0.0:
                        SCALEFactors[name] = w / 12.0
                    if CONVERTEPS and name.endswith(".eps"):
                        name = name[:-4] + ".png"
                    s = s + '\n<br /><img src="' + name + \
                        '" alt="[image: ' + name + ']" /><br />\n'
                elif self.token[1:8] == "caption":
                    s = s + ' <div class="caption">'
                    stack.append("</div> ")
                elif self.token[1:6] == "label":
                    name = self.token[7:-1]
                    if self.figureFlag:
                        if LANG == "de":
                            txt = "Abbildung " + str(self.figureNr) + ". "
                        else:
                            txt = "Figure " + str(self.figureNr) + ". "
                        s = s + '<span id="' + name + '">' + txt + '</a>'
                        CROSSReferences[name] = (
                            str(self.figureNr), "node" +
                            str(len(self.pageList) - 1) + ".html#" + name)
                    else:
                        s = s + '<span id="' + name + '"> </a>'
                        CROSSReferences[name] = (
                            self.chapterName, "node" +
                            str(len(self.pageList) - 1) + ".html#" + name)
                elif self.token[1:4] == "ref":
                    name = self.token[5:-1]
                    ref = "TEXREF" + name
                    link = "TEXLINK" + name
                    s = s + ' <a href="' + ref + '">' + link + '</a>'
                elif self.token[1:6] == "begin":
                    ft = self.interpretFontType(self.token[7:-1])
                    s = s + ft[0]
                elif self.token[1:4] == "end":
                    ft = self.interpretFontType(self.token[5:-1])
                    s = s + ft[1]
                elif self.token[1:9] == "fontsize":
                    while self.token != "}":
                        self.token = self.getToken()
                elif self.token[1:7] == "vspace":
                    while self.token != "}":
                        self.token = self.getToken()
                    s = s + "<br />\n"
                elif self.token[-1] == "{":
                    ft = self.interpretFontType(self.token[1:-1])
                    s = s + ft[0]
                    stack.append(ft[1])
                elif len(stack) > 0:
                    ft = self.interpretFontType(self.token[1:])
                    s = s + ft[0]
                    stack[-1] = ft[1] + stack[-1]
            elif self.token[0] == "{":
                while self.token != "}":
                    self.token = self.getToken()
            elif self.token == "}":
                if len(stack) > 0:
                    s = s + stack[-1]
                    stack = stack[:-1]
                else:
                    break
            else:
                if not ((s == "") and (self.leadIn == 0) and
                        (self.token == " ")):
                    s = s + self.token

            self.token = self.getToken()
            if ((len(s) + self.leadIn) >= 66) and (self.token == " "):
                sequence.append(s + " \12")
                s = ""
                self.leadIn = 0

        if s != "":
            sequence.append(s)
        return sequence

    def isP(self, sequence):
        i = len(sequence) - 1
        while i > 0 and sequence[i][0:2] != "<p" and sequence[i][0:2] != "<li":
            i -= 1
        return i > 0 and sequence[i][0:2] == "<p"

    def sequenceOfParagraphs(self, pclass='', palign='', pretext=""):
        sequence = []
        ptag = 1
        while 1:
            if ptag == 1:
                while self.token == "":
                    self.token = self.getToken()
            if (self.token in (TermPSequence + ["}"])):
                break

            if self.token == "\\begin{center}":
                palign = ' align="center"'
                self.token = self.getToken()
            elif self.token == "\\begin{flushleft}":
                palign = ' align="left"'
                self.token = self.getToken()
            elif self.token == "\\begin{flushright}":
                palign = ' align="right"'
                self.token = self.getToken()

            if ptag == 1:
                sequence.append("<p" + pclass + palign + ">\12" + pretext)
                pretext = ""
                self.leadIn = 0
            else:
                ptag = 1

            sequence = sequence + self.sequenceOfWords()
            if self.token == "\\footnote{":
                self.footnoteNr = self.footnoteNr + 1
                fnr = 'FN' + str(self.footnoteNr)
                refnr = 'REF' + str(self.footnoteNr)
                sequence.append('<a id="' + refnr +  # '" name="' + refnr +
                                '" class="internal" href="#' + fnr + '">[' +
                                str(self.footnoteNr) + ']</a> ')
                self.token = self.getToken()
                self.currPage.foot = self.currPage.foot + \
                    self.sequenceOfParagraphs(
                        # '" name="' +
                        ' class="footnote"', "", '<a id="' + fnr +
                        '" class="internal" href="#' + refnr + '">[' +
                        str(self.footnoteNr) + ']</a> ')
                self.currPage.foot.append("\12</p>\12")
                self.leadIn = len(sequence[-2]) + len(sequence[-1])
                self.token = " "
                ptag = 0
            elif self.token in ["\\begin{quote}", "\\begin{quotation}"]:
                sequence.append("<BLOCKQUOTE>\12")
            elif self.token in ["\\end{quote}", "\\end{quotation}"]:
                sequence.append("</BLOCKQUOTE>\12")
            elif self.token == "\\begin{enumerate}":
                if sequence[-1][0:2] == "<p":
                    sequence = sequence[:-1]
                sequence.append("<ol>\12")
                ptag = 0
            elif self.token == "\\end{enumerate}":
                while (sequence[-1][1:4] == "</p") or \
                        (sequence[-1][0:2] == "<p"):
                    sequence = sequence[:-1]
                if self.isP(sequence):
                    sequence.append("</p>")
                sequence.append("</li>\12</ol>\12")
            elif self.token == "\\begin{itemize}":
                if sequence[-1][0:2] == "<p":
                    sequence = sequence[:-1]
                sequence.append("<ul>\12")
                ptag = 0
            elif self.token == "\\end{itemize}":
                while (sequence[-1][1:4] == "</p") or \
                        (sequence[-1][0:2] == "<p"):
                    sequence = sequence[:-1]
                if self.isP(sequence):
                    sequence.append("</p>")
                sequence.append("</li>\12</ul>\12")
            elif self.token == "\\begin{thebibliography}":
                if sequence[-1][0:2] == "<p":
                    sequence = sequence[:-1]
                sequence.append(
                    HeadT[self.mindepth] + BIBLIOGRAPHY_TITLE +
                    HeadTE[self.mindepth] + "\012\012")
                sequence.append('<ol class="bibliography">\12')
                self.bibpageNr = len(self.pageList) - 1
                ptag = 0
            elif self.token == "\\begin{figure}":
                if sequence[-1][0:2] == "<p":
                    sequence = sequence[:-1]
                pclass = ' class="figure"'
                ptag = 1
                self.figureFlag = True
                self.figureNr += 1
            elif self.token == "\\end{figure}":
                while (sequence[-1][1:4] == "</p") or \
                        (sequence[-1][0:2] == "<p"):
                    sequence = sequence[:-1]
                pclass = ''
                sequence.append("\n</p>\n")
                self.figureFlag = False
            elif self.token == "\\begin{verbatim}":
                sequence.append("\n<pre>\n")
                while 1:
                    line = self.scanner.getRawLine()
                    if line.find("\\end{verbatim}") >= 0:
                        break
                    else:
                        sequence.append(line)
                sequence.append("\n</pre>\n")
            elif self.token == "\\begin{abstract}":
                if LANG == "de":
                    sequence.append(
                        "\n<br /><u><b>Zusammenfassung:</b></u><br />\n")
                else:
                    sequence.append("\n<br /><u><b>Abstract:</b></u><br />\n")
            elif self.token == "\\end{thebibliography}":
                while (sequence[-1][1:4] == "</p") or \
                        (sequence[-1][0:2] == "<p"):
                    sequence = sequence[:-1]
                sequence.append("</li>\12</ol>\12")
            elif (self.token == "\\item") or (self.token[1:8] == "bibitem"):
                while (sequence[-1][1:4] == "</p") or \
                        (sequence[-1][0:2] == "<p"):
                    sequence = sequence[:-1]
                if not (sequence[-1] in ["<ol>\12", "<ul>\12"]):
                    sequence.append("<br />&#160;</li>\12\12")
                    # sequence.append("</li>\12\12")
                if self.citeFlag and self.token[1:8] == "bibitem":
                    bibkey = self.readableBibKey(self.token[9:-1])
                    target = self.targetFromBibKey(bibkey)
                    sequence.append('<li id="' + target + '">' +
                                    "<b>(" + bibkey + ")</b> ")
                else:
                    sequence.append("<li>")
                ptag = 0
            elif self.token in ["\\end{center}", "\\end{flushleft}",
                                "\\end{flushright}"]:
                palign = ''
                sequence.append("\12</p>\12")
            elif self.token == "":
                if sequence[-1][0:2] == "<p":
                    sequence = sequence[:-1]
                else:
                    i = len(sequence) - 1
                    while i >= 0 and sequence[i].find("<li") < 0 \
                            and sequence[i].find("<p") < 0:
                        i -= 1
                    if sequence[i].find("<li") < 0:
                        sequence.append("\12</p>\12")
                    else:
                        sequence.append("\12")

            if not (self.token in (TermPSequence + ["}"])):
                self.token = self.getToken()
                while self.token == " ":
                    self.token = self.getToken()

        return sequence

    def mainContent(self):
        sequence = self.sequenceOfParagraphs()
        if len(sequence) > 0 and sequence[-1][0:2] == "<p":
            sequence = sequence[:-1]
        self.currPage.body = self.currPage.body + sequence

    def ParseHeading(self):
        if self.token == "\\chapter{":
            depth = 0
        elif self.token == "\\section{":
            depth = 1
        elif self.token == "\\subsection{":
            depth = 2
        elif self.token == "\\subsubsection{":
            depth = 3
        elif self.token == "\\paragraph{":
            depth = 4
        elif self.token == "\\subparagraph{":
            depth = 5
        else:
            depth = 0  # just for safety

        if ((depth > 0) or (self.token == "\\chapter{")) and \
                (depth < self.mindepth):
            self.mindepth = depth

        self.chapter[depth] = self.chapter[depth] + 1
        self.chapter = self.chapter[0:depth + 1]
        for i in range(depth, 5):
            self.chapter.append(0)
        cn = ""
        if depth <= CHAPTERNUMBERING_DEPTH:
            flag = 0
            for i in range(0, depth + 1):
                if flag or (self.chapter[i] > 0):
                    cn = cn + repr(self.chapter[i]) + "."
                    flag = 1
            if len(cn) > 0:
                cn = cn[:-1]  # chop

        self.chapterName = cn

        self.token = self.getToken()
        if cn != "":
            s = cn + "  "  # + self.token
        else:
            s = ""  # +self.token
        s += "".join(self.sequenceOfWords())

#        self.token = self.getToken()
#        while self.token != "}":
#            s = s + self.token
#            self.token = self.getToken()

        self.depth = depth                      # depth zurückgeben
        return s

    def Parse(self):
        global PROJECT_TITLE, AUTHOR, REFERENCE, DATE
        self.token = self.getToken()
        while self.token != "\\begin{document}":
            self.token = self.getToken()

        while 1:
            if self.token == "\\end{document}":
                break

            elif self.token == "\\begin{titlepage}":
                self.token = self.getToken()
                self.currPage = HTMLPage(DESTINATION_NAME + ENDING,
                                         PROJECT_TITLE, "TitlePage")
                self.mainContent()
                if self.token != "\\end{titlepage}":
                    raise ParserError("\\end{titlepage} expected")
                self.pageList.append(self.currPage)
                self.pageList.append(HTMLPage("toc" + ENDING, TOC_TITLE,
                                              "TableOfContents"))
                self.token = self.getToken()

            elif self.token == "\\maketitle":
                self.currPage = HTMLPage(DESTINATION_NAME + ENDING,
                                         PROJECT_TITLE, "TitlePage")
                self.currPage.body.append('<br /><p align="center"><big>' +
                                          PROJECT_TITLE +
                                          '</big></p><br /><br />')
                self.currPage.body.append(
                    '\n<p>' + AUTHOR_STR + ": " + AUTHOR + '</p>\n')
                self.currPage.body.append(
                    '<p>' + DATE_STR + ": " + DATE + '</p>')
                self.token = self.getToken()
                self.mainContent()
                self.pageList.append(self.currPage)
                self.pageList.append(HTMLPage("toc" + ENDING, TOC_TITLE,
                                              "TableOfContents"))

            elif self.token in SECTIONS:
                s = self.ParseHeading()
                self.nodeCount = self.nodeCount + 1
                self.currPage = HTMLPage("node" + repr(self.nodeCount) +
                                         ENDING, s, "NormalPage",
                                         self.chapter)
                while 1:
                    self.currPage.body.append(
                        HeadT[self.depth] + s + HeadTE[self.depth] + "\12\12")
                    self.token = self.getToken()
                    self.mainContent()

                    if self.token in SECTIONS:
                        t = self.currPage.body[-1]
                        while (len(t) > 0) and (t[-1:] <= " "):
                            t = t[:-1]
                        t = t[-5:]
                        if (t in HeadTE):
                            s = self.ParseHeading()
                        else:
                            break
                    else:
                        break

                self.pageList.append(self.currPage)

            elif self.token == "\\begin{thebibliography}":
                self.nodeCount = self.nodeCount + 1
                self.chapter = [0, 0, 0, 0, 0, 0]
                self.chapter[self.mindepth] = 1
                self.currPage = HTMLPage("node" + repr(self.nodeCount) +
                                         ENDING, BIBLIOGRAPHY_TITLE,
                                         "NormalPage", self.chapter)
                self.mainContent()
                self.pageList.append(self.currPage)

            else:
                if self.token[1:] == "title{":
                    # PROJECT_TITLE = self.readStr()
                    self.token = self.getToken()
                    PROJECT_TITLE = "".join(self.sequenceOfWords())
                elif self.token[1:] == "subtitle{":
                    self.token = self.getToken()
                    PROJECT_TITLE += "\n<br />\n" + \
                        "".join(self.sequenceOfWords())
                elif self.token[1:7] == "author":
                    self.token = self.getToken()
                    AUTHOR = "".join(self.sequenceOfWords())  # self.readStr()
                    if REFERENCE == "reference to author ?":
                        REFERENCE = AUTHOR
                elif self.token[1:5] == "date":
                    DATE = self.readStr()
                self.token = self.getToken()

        while not self.scanner.eof:
            s = self.scanner.getLine()
        self.flushPageList()
        self.writeImages()


texFileName = sys.argv[-1]
basename = texFileName[:-4]

if os.path.exists(basename + ".l2h"):
    with open(basename + ".l2h", "r") as f:
        print("reading metadata from file: " + basename + ".l2h")
        exec(f.read(), globals(), globals())

PDFURL = basename + ".pdf"
DESTINATION_NAME = basename

n = 1
while n < len(sys.argv):
    if sys.argv[n][0:2] == "-t":
        n += 1
        PROJECT_TITLE = sys.argv[n]
    elif sys.argv[n][0:2] == "-a":
        n += 1
        AUTHOR = sys.argv[n]
        if REFERENCE == "reference to author ?":
            REFERENCE = AUTHOR
    elif sys.argv[n][0:2] == "-r":
        n += 1
        REFERENCE = sys.argv[n]
    elif sys.argv[n][0:2] == "-p":
        n += 1
        PDFURL = sys.argv[n]
    elif sys.argv[n][0:2] == "-c":
        n += 1
        TOC_TITLE = sys.argv[n]
    elif sys.argv[n][0:2] == "-b":
        n += 1
        BIBLIOGRAPHY_TITLE = sys.argv[n]
    elif sys.argv[n][0:2] == "-d":
        n += 1
        DESCRIPTION = sys.argv[n]
    elif sys.argv[n][0:2] == "-k":
        n += 1
        KEYWORDS = sys.argv[n]
    elif sys.argv[n][0:2] == "-s":
        n += 1
        DESTINATION_NAME = sys.argv[n]
    elif sys.argv[n][0:2] == "-l":
        n += 1
        LANG = sys.argv[n]
    elif sys.argv[n][0:2] == "-x":
        HTMLPageHead = '<?xml version="1.0" encoding="UTF-8"?>' + \
            HTMLPageHead
        ENDING = ".xhtml"
    elif sys.argv[n][0:2] == "-i":
        INDEX_FILE = "toc.html"
    n += 1

# debugging: texFileName = "Kritik.tex"
if texFileName[-4:].lower() != ".tex":
    print ('''
    Usage:
      latex2html.py [OPTION] texfile

      Options:
          -t name       : project title
          -a name       : author
          -r name       : reference to the author (may include HTML-tags)
          -p url        : valid url of a PDF Version of the document
          -c name       : TOC title (default: "Table of Contents")
          -b name       : bibliography title (default: "Bibliography")
          -d name       : short description
          -k name       : list of keywords
          -s name       : name of destination directory (default: texfile)
          -l name       : language (e.g. "en-US")
          -x            : create xhtml instead of html pages
          -i            : duplicate table of contents as "index.html" file
    ''')
else:
    if LANG == "de":
        TOC_TITLE = "Inhaltsverzeichnis"
        BIBLIOGRAPHY_TITLE = "Literaturverzeichnis"
        AUTHOR_STR = "Autor"
        DATE_STR = "Datum"
    scanner = TexScanner(texFileName)
    parser = TexParser(scanner)
    parser.Parse()
    os.chdir("../")
    if not os.path.exists(basename + ".l2h"):
        with open(basename + ".l2h", "w") as f:
            esc_regex = re.compile("\\n")   # "\\n|(<.*?>)"
            esc = lambda s: esc_regex.sub(" ", s)
            f.write('# fill in the right values and run latex2html.py again!')
            f.write("\n\n")
            f.write("PROJECT_TITLE = '%s'\n" % esc(PROJECT_TITLE))
            f.write("TOC_TITLE = '%s'\n" % esc(TOC_TITLE))
            f.write("BIBLIOGERAPHY_TITLE = '%s'\n" % esc(BIBLIOGRAPHY_TITLE))
            f.write("AUTHOR = '%s'\n" % esc(AUTHOR))
            f.write("AUTHOR_STR = '%s'\n" % esc(AUTHOR_STR))
            f.write("REFERENCE = '%s'\n" % esc(REFERENCE))
            f.write("PDFURL = '%s'\n" % esc(PDFURL))
            f.write("DESCRIPTION = '%s'\n" % esc(DESCRIPTION))
            f.write("KEYWORDS = '%s'\n" % esc(KEYWORDS))
            f.write("LANG = '%s'\n" % esc(LANG))
            f.write("DATE_STR = '%s'\n" % esc(DATE_STR))
