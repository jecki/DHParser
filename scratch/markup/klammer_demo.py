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
    from DHParser.transform import (pull_up, merge_adjacent, reduce_single_child, replace_by_children,
                                    merge_leaves, pull_out)
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
    print("Demo 1: Eingeklammerter Text wird bei der Suche und "
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
          'und wird dadurch in der XML-Struktur "sichtibar"!')
    cm = ContentMapping(tree)
    for m in klammer_rx.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'klammer')
    print(tree.as_xml(inline_tags={'document'}), '\n')

    print('Schritt 2: Suche "gründete 1401 den HSV" und markiere den gesamten Bereich '
          'einschließlich der beim suchen ignorierten eingeklammerten Textteile!')
    # Erst mal ContentMapping neu bauen. Diesmal soll der eingeklammerte Text nicht
    # im content des ContentMappings auftauchen
    cm = ContentMapping(tree, ignore={'klammer'})
    for m in such_rx_2.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'wichtig')
    print(tree.as_xml(inline_tags={'document'}), '\n')  # einschließlich aller in <document> enthaltenen Tags

    print('Schritt 3: Entfernung der nicht mehr benötigten <klammer>-tags!')
    for p in tree.select_path('klammer'):
        assert len(p) > 1, '<klammer> sollte nicht das toplevel-tag sein!'
        replace_by_children(p)
        merge_leaves(p[-2])
    print(tree.as_xml(inline_tags={'document'}), '\n\n\n')


def demo_3():
    print("Demo 3: Eingeklammerter Text wird bei der Suche berücksichtigt, "
          "aber bei der Auszeichnung ausgespart!\n")
    tree = parse_xml(xml)

    print('Schritt 1: Eingeklammerter Text wird zusätzlich durch Tags markiert '
          'und wird dadurch in der XML-Struktur "sichtibar"!')
    cm = ContentMapping(tree)
    for m in klammer_rx.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'klammer')
    print(tree.as_xml(inline_tags={'document'}), '\n')

    print('Schritt 2: Suche "gründete 1401 (in Hamburg) den HSV" und markiere den gesamten Bereich '
          'einschließlich der beim suchen ignorierten eingeklammerten Textteile!')
    # Erst mal ContentMapping neu bauen. Diesmal soll der eingeklammerte Text nicht
    # im content des ContentMappings auftauchen
    cm = ContentMapping(tree, ignore={'klammer'})
    for m in such_rx_2.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'wichtig')
    print(tree.as_xml(inline_tags={'document'}), '\n')  # einschließlich aller in <document> enthaltenen Tags

    print('Schritt 3: Nimm die eingeklammerten Bereiche von der <wichtig>-Markierung aus. ')
    # Dieser Not-Algorithmus funktionier nur, wenn zwischen dem <wichtig>-Tag und dem '
    # '<klammer>-Tag keine weiteren Schichten im XML liegen!'
    for p in tree.select_path('klammer'):
        pull_out(p)
    print(tree.as_xml(inline_tags={'document'}), '\n')

    print('Schritt 4: Entfernung der nicht mehr benötigten <klammer>-tags!')
    for p in tree.select_path('klammer'):
        assert len(p) > 1, '<klammer> sollte nicht das toplevel-tag sein!'
        replace_by_children(p)
        merge_leaves(p[-2])
    print(tree.as_xml(inline_tags={'document'}), '\n\n\n')


def demo_4():
    print("Demo 4: Eingeklammerter Text wird bei der Suche ignoriert "
          "und bei der Auszeichnung ausgespart!\n")
    tree = parse_xml(xml)

    print('Schritt 1: Eingeklammerter Text wird zusätzlich durch Tags markiert '
          'und wird dadurch in der XML-Struktur "sichtibar"!')
    cm = ContentMapping(tree)
    for m in klammer_rx.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'klammer')
    print(tree.as_xml(inline_tags={'document'}), '\n')

    print('Schritt 2: Suche "gründete 1401 (in Hamburg) den HSV" und markiere den gesamten Bereich '
          'einschließlich der beim suchen ignorierten eingeklammerten Textteile!')
    # kein Neubau des ContentMappings erforderlich!
    for m in such_rx_1.finditer(cm.content):
        cm.markup(m.start(), m.end(), 'wichtig')
    print(tree.as_xml(inline_tags={'document'}), '\n')  # einschließlich aller in <document> enthaltenen Tags

    print('Schritt 3: Nimm die eingeklammerten Bereiche von der <wichtig>-Markierung aus. ')
    # Dieser Not-Algorithmus funktionier nur, wenn zwischen dem <wichtig>-Tag und dem '
    # '<klammer>-Tag keine weiteren Schichten im XML liegen!'
    for p in tree.select_path('klammer'):
        pull_out(p)
    print(tree.as_xml(inline_tags={'document'}), '\n')

    print('Schritt 4: Entfernung der nicht mehr benötigten <klammer>-tags!')
    for p in tree.select_path('klammer'):
        assert len(p) > 1, '<klammer> sollte nicht das toplevel-tag sein!'
        replace_by_children(p)
        merge_leaves(p[-2])
    print(tree.as_xml(inline_tags={'document'}), '\n\n\n')


if __name__ == '__main__':
    demo_1()
    demo_2()
    demo_3()
    demo_4()