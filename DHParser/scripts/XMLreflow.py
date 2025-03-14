#!/usr/bin/env python3

"""XMLreflow.py - reformat XML, HTML and XML file for better readability

Copyright 2025  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences and Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import argparse
import os.path
import sys
from typing import cast

scriptdir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
dhparserdir = os.path.abspath(os.path.join(scriptdir, os.pardir, os.pardir))
if dhparserdir not in sys.path:
    sys.path.append(dhparserdir)

from DHParser.nodetree import parse_sxpr, RootNode
from DHParser.parsers import parse_XML, parse_HTML
from DHParser.toolkit import AbstractSet


def process_file(filename: str, tags: AbstractSet, column: int,
                 output: str, verbose: bool):
    with open(filename, 'r', encoding='utf-8') as f:
        xml = f.read()
    rump, ext = os.path.splitext(filename)
    extension = ext.lower()
    if extension in ('.sxml', '.sxpr'):
        tree = parse_sxpr(xml)
        if extension == '.sxml':
            xml = tree.as_sxml(flatten_threshold=0, reflow_col=column)
        else:
            xml = tree.as_sxpr(flatten_threshold=0, reflow_col=column)
    elif extension == '.xml':
        # from DHParser import parse_xml as parse_XML
        tree = parse_XML(xml)
        for e in cast(RootNode, tree.errors_sorted):  print(e)
        xml = tree.as_xml(inline_tags=set(tags), strict_mode=False, reflow_col=column)
    else:
        a = xml.find('<head>')
        if a < 0:  a = xml.find('<HEAD>')
        b = xml.find('</head>')
        if b < 0:  b = xml.find('</HEAD>')
        head = xml[a:b+7] if a >= 0 and b >= 0 else ''
        lang = "en"
        a = xml.find('<html')
        if a < 0:  a = xml.find('<HTML')
        if a >= 0:
            b = xml.find('>', a)
            l = xml.find('lang=', a, b)
            if l >= 0:
                l = xml.find('"', l, b)
                r = xml.find('"', l+1, b)
                lang = xml[l+1:r]
        tree = parse_HTML(xml)
        xml = tree.as_html(head=head, lang=lang, inline_tags=set(tags),
                           reflow_col=column)
    if output is None:
        output = rump + '_reflow' + ext
    with open(output, 'w', encoding='utf-8') as f:
        f.write(xml)
    if verbose:
        print(f"Output written to: {output}")


def main():
    parser = argparse.ArgumentParser(description="Reformat HTML, XML or SXML"
                                                 " files.")
    parser.add_argument('filenames', nargs='+',
                        help='One or more file- or directory-names to process')
    parser.add_argument('--tags', '-t', nargs='+', default=['p'],
                        help='The outermost tags the content of which '
                             'shall be rewrapped')
    parser.add_argument('--column', '-c', type=int, default=100,
                        help='The column at which to wrap text (default:100)')
    parser.add_argument('--output', '-o', type=str,
                        help='The output filename')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    filenames = args.filenames
    tags = args.tags if args.tags else []
    if not isinstance(tags, list):  tags = [tags]
    column = args.column
    output = args.output
    verbose = args.verbose

    if column is not None and column < 0:
        parser.error("The --column/-c option must be zero or a positive integer.")

    for name in filenames:
        if not os.path.exists(name):
            parser.error(f"The file or directory '{name}' does not exist.")
        if not os.access(name, os.R_OK):
            parser.error(f"Cannot read file '{name}'.")

    if output is not None:
        if len(filenames) > 1:
            parser.error("The --output/-o option can only be used with a "
                         "single input file.")
        if not os.path.isfile(filenames[0]):
            parser.error(f"The file '{filenames[0]}' does not exist.")

    for name in filenames:
        if os.path.isdir(name):
            for root, dirs, files in os.walk(name):
                outdir = os.path.join(root, 'XMLreflow')
                if not os.path.exists(outdir):
                    if not os.access(root, os.W_OK):
                        parser.error(f"Cannot create directory '{outdir}'.")
                    os.mkdir(os.path.join(root, 'XMLreflow'))
                elif not os.path.isdir(outdir):
                    parser.error(f"Cannot create directory '{outdir}', because "
                                 "a file with the same name already exists.")
                elif not os.access(name, os.R_OK):
                    parser.error(f"Cannot write to directory '{outdir}'.")
                for file in files:
                    lfn = file.lower()
                    if (lfn[-4:] in ('.xml', '.htm')
                            or lfn[-5:] in ('.sxml', '.sxpr', '.html')):
                        name = os.path.join(root, file)
                        outfile = os.path.join(outdir, name)
                        process_file(name, tags, column, outfile, verbose)
        else:
            extension = os.path.splitext(name)[1].lower()
            if extension not in ('.xml', '.htm', '.sxml', '.sxpr', '.html'):
                parser.error(f"The file '{name}' is not an XML or SXML file.")
            process_file(name, tags, column, output, verbose)


if __name__ == "__main__":
    main()
