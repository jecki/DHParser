#!/usr/bin/env python3


import sys, os, re

scriptpath = os.path.dirname(__file__) or '.'
abspath = os.path.abspath(scriptpath)
if abspath.find('/DHParser/') >= 0 or abspath.find('\\DHParser\\') >= 0:
    sys.path.append(os.path.abspath(os.path.join(scriptpath, '..', '..')))
scriptpath = abspath


try:
    from DHParser.nodetree import (Node, ContentMapping, parse_xml, find_common_ancestor, TOKEN_PTYPE,
                                   pp_path, PathMatchFunction)
    from DHParser.transform import pull_up, merge_adjacent, reduce_single_child
except ImportError as e:
    raise ImportError("Bitte installiere DHParser mit python3 -m pip install DHParser!")


###### Hier geht's los: ################################################

xml = """
<document>
Klaus Störtebeker gründete <datum>1401</datum> (in <ort>Hamburg</ort>) den HSV!
</document>
"""

klammer_rx = re.compile(r'\([^)]*\)')

such_text_1 = "gründete 1401 (in Hamburg) den HSV"
such_rx_1 = re.compile(re.escape(such_text_1).replace(' ', r's+'))  # s+ und nicht \s+, weil re.escape auch die Leerzeichen "escaped"

such_text_2 = "gründete 1401 den HSV"
such_rx_2 = re.compile(re.escape(such_text_2).replace(' ', r's+'))



def demo_1():
    print("Demo 1: Eingeklammerter Text wird bei der Suche mit angegeben "
          "und bei der Auszeichnung mitberücksichtigt!\n")
    tree = parse_xml(xml)
    cm = ContentMapping(tree)
    for m in such_rx_1.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'wichtig')
    print(tree.as_xml(inline_tags={'document'}), "\n\n\n")  # einschließlich aller in <document> enthaltenen Tags


def demo_2():
    print("Demo 2: Eingeklammerter Text wird bei der Suche ignoriert, "
          "aber bei der Auszeichnung mitberücksichtigt!\n")
    tree = parse_xml(xml)

    print('Schritt 1: Eingeklammerter Text wird zusätzlich durch Tags markiert '
          'und wird dadurch in der XML-Struktur !sichtibar"!')
    cm = ContentMapping(tree)
    for m in klammer_rx.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'klammer')
    print(tree.as_xml(inline_tags={'document'}), '\n')


    print('Schritt 2: Suche "gründete 1401 den HSV" und markiere den gesamten Bereich!')
    print(cm.content)
    print(tree.content)
    for m in such_rx_2.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'wichtig')
    print(tree.as_xml(inline_tags={'document'}), '\n\n\n')  # einschließlich aller in <document> enthaltenen Tags


if __name__ == '__main__':
    # demo_1()
    demo_2()
