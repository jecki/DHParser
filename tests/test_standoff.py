#!/usr/bin/env python3

"""test_standoff.py - unit-tests for DHParser's standoff-module

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2026 Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import copy
import re

from DHParser import parse_sxpr, split_tree, parse_xml, content_of, ContentMapping, pick_from_path, NO_PATH, Node, \
    TOKEN_PTYPE, flatten_sxpr, DIVISIBLES, sourcemapped_selection, LEAF_PATH, content_regions, ANY_NODE
from DHParser.standoff import gen_chain_ID, deep_split, range_difference


class TestRangeAlgebra:
    def test_superset_subtraction(self):
        include_set = [(3,5), (8,11)]
        superset = [(-10, 100)]
        exclude_set = range_difference(superset, include_set)
        assert exclude_set == [(-10, 3), (5, 8), (11, 100)]
        real_incl_set = range_difference([(2, 14)], exclude_set)
        assert real_incl_set == [(3, 5), (8, 11)]


class TestSplitMethod:
    def test_split(self):
        urtree = parse_sxpr('(A (B (C "123") (M) (D "456")) (E "789") (M) (F "000"))')
        tree = copy.deepcopy(urtree)
        parts = split_tree(tree, "M")
        assert len(parts) == 3
        assert parts[0].as_sxpr() == '(A (B (C "123")))'
        assert parts[1].as_sxpr() == '(A (B (D "456")) (E "789"))'
        assert parts[2].as_sxpr() == '(A (F "000"))'

        tree = copy.deepcopy(urtree)
        parts = split_tree(tree, "M", "B")
        assert len(parts) == 2
        assert parts[0].as_sxpr() == '(A (B (C "123") (M) (D "456")) (E "789"))'
        assert parts[1].as_sxpr() == '(A (F "000"))'

    def test_split_edge_cases(self):
        urtree = parse_sxpr('(A (L) (B (C "123") (M) (M) (D "456")) (E "789") (N))')
        tree = copy.deepcopy(urtree)
        parts = split_tree(tree, 'X')
        assert len(parts) == 1
        assert parts[0] == tree

        tree = copy.deepcopy(urtree)
        parts = split_tree(tree, 'L')
        assert len(parts) == 2
        assert parts[0] == tree
        assert parts[0].as_sxpr() == '(A)'
        assert parts[1].as_sxpr() == '(A (B (C "123") (M) (M) (D "456")) (E "789") (N))'

        tree = copy.deepcopy(urtree)
        parts = split_tree(tree, 'N')
        assert len(parts) == 2
        assert parts[0] == tree
        assert parts[0].as_sxpr() == '(A (L) (B (C "123") (M) (M) (D "456")) (E "789"))'
        assert parts[1].as_sxpr() == '(A)'

        tree = copy.deepcopy(urtree)
        parts = split_tree(tree, 'M')
        assert len(parts) == 3
        assert parts[0] == tree
        assert parts[0].as_sxpr() == '(A (L) (B (C "123")))'
        assert parts[1].as_sxpr() == '(A)'
        assert parts[2].as_sxpr() == '(A (B (D "456")) (E "789") (N))'


class TestMarkupInsertion:
    testdata_1 = '<document>In Charlot<lb/>tenburg steht ein Schloss.</document>'
    testdata_2 = '''<document>
<app n="g">
<lem>silvae</lem>
<rdg wit="A">silvae, </rdg>
</app> glandiferae</document>'''
    testdata_3 = '''<doc>Am <outer><inner>Anfang</inner> war das Wort</outer>.</doc>'''

    def test_content_of(self):
        tree = parse_xml('<p>This is<fn>footnote</fn> a text</p>')
        assert content_of(tree) == 'This isfootnote a text'
        assert content_of(tree, ignore='fn') == 'This is a text'
        assert content_of(tree, select='fn') == 'footnote'

    def test_ContentMapping_constructor(self):
        tree = parse_xml('<doc><p>In München<footnote><em>München</em> is the '
            'German name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>')
        cm = ContentMapping(tree, select='footnote', sourcemap=True)
        cm = ContentMapping(tree, select='footnote', sourcemap=False)
        cm = ContentMapping(tree, select=lambda pth: pick_from_path(pth, 'footnote')
                                                     and not pth[-1].children)

    def test_ContentMapping_rebuild_mapping(self):
        tree = parse_xml('<doc><p>In München<footnote><em>München</em> is the '
            'German name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>')
        fm = ContentMapping(tree, select='footnote', ignore=NO_PATH)
        i = fm.content.find('München')
        path, offset = fm.get_path_and_offset(i)
        path[-1].result = path[-1].result[:offset] + "Stadt " + path[-1].result[offset:]
        assert tree.as_xml(inline_tags={'doc'}) == ('<doc><p>In München<footnote>'
            '<em>Stadt München</em> is the German name of the city of Munich</footnote> '
            'is a Hofbräuhaus</p></doc>')
        k = fm.get_path_index(i)
        fm.rebuild_mapping_slice(k, k)
        assert fm._pos_list == [0, 13]

    def test_chain_id(self):
        s = set()
        for i in range(200_000):
            cid = gen_chain_ID()
            assert cid not in s
            s.add(cid)
            assert len(cid) <= 4
        assert len(s) == 200_000

    def test_chain_attr_1(self):
        tree = parse_xml("<hard>Please mark up Stadt\n<lb/><location><em>München</em> "
                         "in Bavaria</location> in this sentence.</hard>")
        divisability_map = {'foreign': {'location', ':Text'},
                                        '*': {':Text'}}
        mapping = ContentMapping(tree, divisibility=divisability_map,
                                 chain_attr_name = "chain")
        match = re.search(r"Stadt\s+München", mapping.content)
        _ = mapping.add_markup(match.start(), match.end(), "foreign", {'lang': 'de'})
        xml_str = tree.as_xml(empty_tags={'lb'})
        chains = {loc.attr['chain'] for loc in tree.select('location')}
        assert len(chains) == 1

    def test_insert_node(self):
        tree = parse_xml("<document>In Charlottenburg steht ein <i>großes </i> Schloss.</document>")
        cm = ContentMapping(tree, auto_cleanup=True)
        assert cm._pos_list == [0, 28, 35]
        i = cm.content.find('Charlottenburg')
        cm.insert_node(i, Node("b", "der Stadt "))
        assert cm._pos_list == [0, 3, 13, 38, 45]
        assert tree.equals(parse_sxpr("""
            (document
              (:Text "In ")
              (b "der Stadt ")
              (:Text "Charlottenburg steht ein ")
              (i "großes ")
              (:Text " Schloss."))"""))

    def test_insert_milestone_1(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_1, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        i = tree.content.find("Charlottenburg")
        assert i >= 0
        milestone = Node("ref", "").with_attr(type="subj", target="Charlottenburg_S00231")
        empty_tags.add("ref")
        tm = ContentMapping(tree)
        tm.insert_node(i, milestone)
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document>In <ref type="subj" '
                       'target="Charlottenburg_S00231"/>Charlot<lb/>tenburg steht ein '
                       'Schloss.</document>')

    def test_insert_milestone_2(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_2, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = re.search(r'silvae,?\s*glandiferae', tree.content)
        milestone = Node("ref", "").with_attr(type="subj", target="silva_glandifera_S01229")
        empty_tags.add("ref")
        tm = ContentMapping(tree)
        tm.insert_node(m.start(), milestone)
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document><app n="g"><lem>silvae</lem><ref type="subj" '
                       'target="silva_glandifera_S01229"/><rdg wit="A">silvae, </rdg></app> '
                       'glandiferae</document>')

    def test_insert_markup_1(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_1, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        i = tree.content.find("Charlottenburg")
        assert i >= 0
        k = i + len("Charlottenburg")
        tm = ContentMapping(tree)
        tm.add_markup(i, k, "ref", {'type': "subj", 'target': "Charlottenburg_S00231"})
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document>In <ref type="subj" '
                       'target="Charlottenburg_S00231">Charlot<lb/>tenburg</ref> steht ein '
                       'Schloss.</document>')

    def test_insert_markup_2(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_2, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = re.search(r'silvae,?\s*glandiferae', tree.content)
        tm = ContentMapping(tree)
        tm.add_markup(m.start(), m.end(), "ref", {'type': "subj", 'target': "silva_glandifera_S01229"})
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document><app n="g"><lem>silvae</lem><ref type="subj" '
                       'target="silva_glandifera_S01229"><rdg wit="A">silvae, </rdg></ref></app><ref '
                        'type="subj" target="silva_glandifera_S01229"> glandiferae</ref></document>')

    def test_insert_markup_3(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_3, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = re.search(r'Anfang war das Wort', tree.content)
        cm = ContentMapping(tree)
        cm.add_markup(m.start(), m.end(), "a")
        assert tree.as_xml(inline_tags={'doc'}, string_tags={':Text'}) == \
            '<doc>Am <outer><a><inner>Anfang</inner> war das Wort</a></outer>.</doc>'
        empty_tags = set()
        tree = parse_xml(self.testdata_3, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = re.search(r'Am Anfang war', tree.content)
        cm = ContentMapping(tree)
        cm.add_markup(m.start(), m.end(), "a")
        assert tree.as_xml(inline_tags={'doc'}, string_tags={':Text'}) == \
            '<doc><a>Am </a><outer><a><inner>Anfang</inner> war</a> das Wort</outer>.</doc>'

    def test_insert_markup_4(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_3, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = re.search(r'Am Anfang war', tree.content)
        cm = ContentMapping(tree, chain_attr_name='_chain')
        cm.add_markup(m.start(), m.end(), "a")
        I = tree.pick('a').attr['_chain']
        assert tree.as_xml(inline_tags={'doc'}, string_tags={':Text'}) == \
            f'<doc><a _chain="{I}">Am </a><outer><a _chain="{I}"><inner>Anfang</inner> war</a>'\
            f' das Wort</outer>.</doc>'

    def test_insert_markup_5(self):
        tree = parse_xml('<text><hi rend="i">X</hi>34, 53 ... Q. Aelius Tubero tribunus plebis</text>')
        i = tree.content.find('Q.')
        k = tree.content.find('Tubero') + len('Tubero')
        cm = ContentMapping(tree)
        cm.add_markup(i, k, "a")
        assert tree.as_xml(inline_tags={'text'}, string_tags={TOKEN_PTYPE}) == \
            '<text><hi rend="i">X</hi>34, 53 ... <a>Q. Aelius Tubero</a> tribunus plebis</text>'

    def test_insert_markup_6(self):
        tree = parse_xml('<doc>wenn wir bei <hi rend="italic">Cicero</hi><note type="footnote" n="29)">'
            '<pb n="225"/>In Verr. acc. 1. 3, 120. </note> die meist nicht erhebli<lb/>chen Zahlen</doc>')
        m = re.search(r'Cicero', tree.content)
        a, b = m.start(), m.end()
        cm = ContentMapping(tree, auto_cleanup=True)
        cm.add_markup(a, b, 'ref')
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (:Text "wenn wir bei ") '\
            '(hi `(rend "italic") (ref "Cicero")) (note `(type "footnote") `(n "29)") '\
            '(pb `(n "225")) (:Text "In Verr. acc. 1. 3, 120. ")) '\
            '(:Text " die meist nicht erhebli") (lb) (:Text "chen Zahlen"))'

    def test_insert_markup_7(self):
        tree= parse_xml('<doc>Zugleich traf sie für <pb n="219"/>den ager compascuus folgende Bestimmung '
            '(Z. 14, 15 nach <hi rend="italic">Momm</hi><lb/><hi rend="italic">sens</hi>'
            '<note type="comment" n="53"><pb n="219"/>Offenbar</note> nach:</doc>')
        m = re.search(r'Mommsen', tree.content)
        a, b = m.start(), m.end()
        cm = ContentMapping(tree, auto_cleanup=True)
        cm.add_markup(a, b, 'ref')
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (:Text "Zugleich traf sie für ") '\
            '(pb `(n "219")) (:Text "den ager compascuus folgende Bestimmung '\
            '(Z. 14, 15 nach ") (ref (hi `(rend "italic") "Momm") (lb)) (hi `(rend "italic") '\
            '(ref "sen") (:Text "s")) (note `(type "comment") `(n "53") (pb `(n "219")) '\
            '(:Text "Offenbar")) (:Text " nach:"))'

    def test_insert_markup_8(self):
        tree = parse_xml('<item><pb n="283" ed="A"></pb><hi rend="italic">Beaudouin</hi>. Études'
            '<note type="comment" n="10">Im Titel heißt es: Étude. </note> sur le jus Italicum '
            '(Nouvelle revue historique V, 1881, p. 145ff.). </item>')
        m = re.search('Beaudouin. Études', tree.content)
        a, b = m.start(), m.end()
        cm = ContentMapping(tree, auto_cleanup=True)
        cm.add_markup(a, b, 'ref')
        assert tree.as_xml(inline_tags={'item'}) == '<item><pb n="283" ed="A"/>'\
            '<ref><hi rend="italic">Beaudouin</hi>. Études</ref><note type="comment" n="10">'\
            'Im Titel heißt es: Étude. </note> sur le jus Italicum (Nouvelle revue historique '\
            'V, 1881, p. 145ff.). </item>'

    def test_markup_borderline_cases(self):
        ### borderline cases
        tree = parse_xml('<doc>Hello, <em>World</em>!</doc>')
        X = copy.deepcopy(tree)
        t = ContentMapping(X)
        _ = t.add_markup(3, 4, 'b')
        assert X.as_xml(inline_tags={'doc'}) \
            == '<doc>Hel<b>l</b>o, <em>World</em>!</doc>'

        X = copy.deepcopy(tree)
        t = ContentMapping(X)
        _ = t.add_markup(3, 3, 'b')
        assert X.as_xml(inline_tags={'doc'}, empty_tags={'b'}) \
               == '<doc>Hel<b/>lo, <em>World</em>!</doc>'

    def test_markup_new_9(self):
        tree = parse_sxpr('''(p (b "I") (:Text " ") (i "gener.:") (:Text "[MFSP]") (b "A"))''')

        t = copy.deepcopy(tree)
        cm = ContentMapping(t, divisibility=DIVISIBLES | {'i', 'span'})
        cm.greedy = True
        cm.add_markup(2, 8, "Klassifikation")
        assert t.as_sxpr() == \
            '(p (b "I") (:Text " ") (i (Klassifikation "gener.") (:Text ":")) ' \
            '(:Text "[MFSP]") (b "A"))'
        t = copy.deepcopy(tree)
        cm = cm = ContentMapping(t, divisibility=DIVISIBLES)
        cm.add_markup(2, 8, "Klassifikation")
        assert t.as_sxpr() == \
            '(p (b "I") (:Text " ") (i (Klassifikation "gener.") (:Text ":")) ' \
            '(:Text "[MFSP]") (b "A"))'

        t = copy.deepcopy(tree)
        cm = ContentMapping(t, divisibility=DIVISIBLES | {'i', 'span'})
        cm.greedy = False
        cm.add_markup(2, 8, "Klassifikation")
        assert t.as_sxpr() == \
               '(p (b "I") (:Text " ") (Klassifikation (i "gener.")) ' \
               '(i ":") (:Text "[MFSP]") (b "A"))'
        t = copy.deepcopy(tree)
        cm = cm = ContentMapping(t, divisibility=DIVISIBLES)
        cm.add_markup(2, 8, "Klassifikation")
        assert t.as_sxpr() == \
               '(p (b "I") (:Text " ") (i (Klassifikation "gener.") ' \
               '(:Text ":")) (:Text "[MFSP]") (b "A"))'

    def test_markup_rebuild_mapping(self):
        xml = """
        <document>
        Klaus Störtebeker gründete <datum>1401</datum> (in <ort>Hamburg</ort>) den HSV!
        </document>
        """
        klammer_rx = re.compile(r'\([^)]*\)')
        tree = parse_xml(xml)
        cm = ContentMapping(tree)
        assert cm.content == tree.content
        for m in klammer_rx.finditer(cm.content):
            cm.add_markup(m.start(), m.end(), 'klammer')
        assert cm.content == tree.content

    def test_deep_split(self):
        urtree = tree = parse_sxpr(
            '(X (s) (A (u) (C "One, ") (D "two, ")) (B (E "three, ") (F "four!") (t)))')
        tree = copy.deepcopy(urtree)
        path = tree.pick_path('C')
        assert deep_split(path, 0, left_biased=True, greedy=True) == 1
        assert tree.equals(urtree)

        tree = copy.deepcopy(urtree)
        path = tree.pick_path('C')
        assert deep_split(path, 0, left_biased=False, greedy=True) == 2
        assert tree.as_sxpr() == '(X (s) (A (u)) (A (C "One, ") (D "two, ")) (B (E "three, ") (F "four!") (t)))'

        tree = copy.deepcopy(urtree)
        path = tree.pick_path('C')
        assert deep_split(path, 0, left_biased=True, greedy=False) == 2
        assert tree.as_sxpr() == '(X (s) (A (u)) (A (C "One, ") (D "two, ")) (B (E "three, ") (F "four!") (t)))'

        tree = copy.deepcopy(urtree)
        path = tree.pick_path('C')
        assert deep_split(path, 0, left_biased=False, greedy=False) == 2
        assert tree.as_sxpr() == '(X (s) (A (u)) (A (C "One, ") (D "two, ")) (B (E "three, ") (F "four!") (t)))'

        urtree = parse_sxpr('(X (A (B "123") (N) (M) (C "456")) (D "789"))')
        tree = copy.deepcopy(urtree)
        path = tree.pick_path('M')
        assert deep_split(path, i=0, left_biased=True, greedy=True) == 1
        assert tree.as_sxpr() == '(X (A (B "123") (N)) (A (M) (C "456")) (D "789"))'

        tree = copy.deepcopy(urtree)
        path = tree.pick_path('M')
        assert deep_split(path, i=0, left_biased=False, greedy=True) == 1
        assert tree.as_sxpr() == '(X (A (B "123") (N) (M)) (A (C "456")) (D "789"))'

        tree = copy.deepcopy(urtree)
        path = tree.pick_path('M')
        assert deep_split(path, i=0, left_biased=True, greedy=False) == 1
        assert tree.as_sxpr() == '(X (A (B "123") (N)) (A (M) (C "456")) (D "789"))'

        tree = copy.deepcopy(urtree)
        path = tree.pick_path('M')
        assert deep_split(path, i=0, left_biased=False, greedy=False) == 1
        assert tree.as_sxpr() == '(X (A (B "123") (N) (M)) (A (C "456")) (D "789"))'


class TestContentSelectionMapping:
    def test_content_selection(self):
        tree = parse_xml('<doc>Klaus Störtebeker gründete <klammer>(in Hamburg) </klammer>den HSV</doc>')
        full_content = tree.content
        content, pos_list, path_list, sm = sourcemapped_selection(tree, select=LEAF_PATH, ignore="klammer")
        i = content.find('gründete')
        k = sm.map(i).pos # map_source(i, sm).pos
        assert full_content[k:k+len('gründete')] == 'gründete'
        i = content.find('gründete')
        k = sm.map(i + len('gründete')).pos
        assert full_content[k:k+1] == ' '
        i = content.find('HSV')
        k = sm.map(i).pos
        assert full_content[k:k+len('HSV')] == 'HSV'
        i = content.find('den HSV')
        k = sm.map(i).pos
        assert full_content[k:k+len('den HSV')] == 'den HSV'

    def test_markup_with_exclusion(self):
        # HINWEIS: Die Exclude-Bereiche beziehen sich immer auf den vollen
        # Inhalt ("content"), nicht auf den (möglicherweise) reduzierten
        # oder ausgewählten Inhalt eines bestimmten ContentMappings
        # Die Angabe, wo das Tag hinkommt [a, b[ bezieht sich aber wieder
        # auf den möglicherweise reduzierten Inhalt eines konkreten
        # content mappings!
        # Der Grund dafür ist, dass diejenigen Bereich, die bei der Textsuche
        # ausgeschlossen werden sollen sich nicht mit denen decken müssen,
        # die vom Tagging (mittels markup) ausgespart bleiben sollen.

        xml = '<doc>Klaus Störtebeker gründete <klammer>(in Hamburg) </klammer>den HSV</doc>'
        tree = parse_xml(xml)
        cm = ContentMapping(tree, ignore="klammer")
        a = cm.content.find('gründete')
        b = cm.content.find('HSV')

        # Vergleichsfall ohne exclude
        tree = parse_xml(xml)
        cm = ContentMapping(tree, ignore="klammer")
        exclude = []
        cm.markup(a, b, 'X', exclude)
        expected = parse_sxpr('''
            (doc
              (:Text "Klaus Störtebeker ")
              (X
                (:Text "gründete ")
                (klammer "(in Hamburg) ")
                (:Text "den "))
              (:Text "HSV"))''')
        assert tree.equals(expected)

        # Kanonischer Fall
        tree = parse_xml(xml)
        cm = ContentMapping(tree, ignore="klammer")
        exclude = content_regions(tree, 'klammer')
        cm.markup(a, b, 'X', exclude)
        print(tree.as_sxpr())
        expected = parse_sxpr('''
            (doc
              (:Text "Klaus Störtebeker ")
              (X "gründete ")
              (klammer "(in Hamburg) ")
              (X "den ")
              (:Text "HSV"))''')
        assert tree.equals(expected)

        # Unmittelbare Bereichsangabe
        tree = parse_xml(xml)
        full_content = tree.content
        cm = ContentMapping(tree, ignore="klammer")
        exclude = [(full_content.find('('), full_content.find(')') + 1)]
        cm.markup(a, b, 'X', exclude)
        expected = parse_sxpr('''
            (doc
              (:Text "Klaus Störtebeker ")
              (X "gründete ")
              (klammer
                (:Text "(in Hamburg)")
                (X " "))
              (X
                (:Text "den "))
              (:Text "HSV"))''')
        assert tree.equals(expected)

    def test_content_region(self):
        xml = "<doc><f>eins</f><lb/><f>zwei</f></doc>"
        tree = parse_xml(xml)
        ex = content_regions(tree, {'lb', 'f'})
        assert ex == [(0,8)]
        cm = ContentMapping(tree)
        cm.markup(0, 8, "X", ex)
        assert tree.pick('X') is None

        xml = "<doc>eins<lb/><f>zwei</f></doc>"
        tree = parse_xml(xml)
        ex = content_regions(tree, {'lb', 'f'})
        assert ex == [(4,8)]
        cm = ContentMapping(tree)
        cm.markup(0, 8, "X", ex)
        assert tree.equals(parse_sxpr('(doc (X "eins") (lb) (f "zwei"))'))

        xml = "<doc><f>eins</f><lb/>zwei</doc>"
        tree = parse_xml(xml)
        ex = content_regions(tree, {'lb', 'f'})
        assert ex == [(0,4)]
        cm = ContentMapping(tree)
        cm.markup(0, 8, "X", ex)
        assert tree.equals(parse_sxpr('(doc (f "eins") (lb) (X "zwei"))'))

        xml = "<doc><f>eins</f> <lb/> <f>zwei</f></doc>"
        tree = parse_xml(xml)
        ex = content_regions(tree, {'lb', 'f'})
        assert ex == [(0, 4), (5, 5), (6, 10)]
        cm = ContentMapping(tree)
        cm.markup(0, 10, "X", ex)
        assert tree.equals(parse_sxpr('(doc (f "eins") (X " ") (lb) (X " ") (f "zwei"))'))

    def test_markup_with_exclusion_2(self):
        xml = "<doc>Die Stadt<lb/>München liegt in Bayern</doc>"
        tree = parse_xml(xml)
        cm = ContentMapping(tree)
        lb_regions = content_regions(tree, 'lb')
        assert lb_regions == [(9, 9)]
        cm.markup(0, 16, "X", exclude_regions=lb_regions)
        assert tree.as_xml(inline_tags={'doc'}) == \
               "<doc><X>Die Stadt</X><lb/><X>München</X> liegt in Bayern</doc>"

    def test_markup_with_exclusion_3(self):
        xml = ("<doc>Please mark up Stadt\n<lb/>"
               "<em>München</em><footnote>'Stadt <em>München</em>'"
               " is German for 'City of Munich'</footnote> in Bavaria"
               " in this sentence.</doc>")
        tree = parse_xml(xml)
        cm = ContentMapping(tree, ignore='footnote')
        m = re.search(r"München\s+in\s+Bavaria", cm.content)
        exclude = content_regions(tree, 'footnote')
        assert exclude == [(28, 74)]
        cm.markup(m.start(), m.end(), 'location', exclude)
        expected = parse_sxpr('''
            (doc
              (:Text
                "Please mark up Stadt"
                "")
              (lb)
              (em
                (location "München"))
              (footnote
                (:Text "'Stadt ")
                (em "München")
                (:Text "' is German for 'City of Munich'"))
              (location " in Bavaria")
              (:Text " in this sentence."))
            ''')
        assert tree.equals(expected)


class TestSerializationMapping:
    def test_mapping_trivial(self):
        s = '(name "Fritz")'
        tree = parse_sxpr(s)
        mapping = {}
        sxpr = tree.as_sxpr(mapping=mapping)
        assert mapping[tree] == (5, 14, 1)
        mapping = {}
        xml = tree.as_xml(mapping=mapping)
        assert mapping[tree] == (6, 18, 7)


    def test_mapping1(self):
        s = """(BedeutungsPosition `(unterbedeutungstiefe "0")
                 (Bedeutung
                   (Beleg
                     (Quellenangabe (Quelle (Autor "LIUTPR.") (L " ") (Werk "leg.")) (L " ")
                       (BelegStelle (Stellenangabe (Stelle "21")) (L " ")
                         (BelegText (TEXT "...")))))))"""
        tree = parse_sxpr(s)
        mapping = {}
        sxpr = tree.as_sxpr(mapping=mapping)
        assert len(sxpr) == mapping[tree][1]
        for nd in tree.select(ANY_NODE, include_root=True):
            if nd.children:
                inner_size = mapping[nd][1] - mapping[nd][0] - mapping[nd][2]
                overall_size = sum(mapping[child][1] for child in nd.children)
                assert inner_size == overall_size, str(mapping[nd])

        mapping = {}
        sxpr = tree.as_sxpr(flatten_threshold=10_000, mapping=mapping)
        assert len(sxpr) == mapping[tree][1]
        for nd in tree.select(ANY_NODE, include_root=True):
            if nd.children:
                inner_size = mapping[nd][1] - mapping[nd][0] - mapping[nd][2]
                overall_size = sum(mapping[child][1] for child in nd.children)
                assert inner_size == overall_size, nd.as_sxpr()

        mapping = {}
        xml = tree.as_xml(mapping=mapping)
        # print(xml)
        # for k, v in mapping.items():
        #     print(k.name, v)
        # print(len(xml))
        assert len(xml) == mapping[tree][1]
        for nd in tree.select(ANY_NODE, include_root=True):
            if nd.children:
                inner_size = mapping[nd][1] - mapping[nd][0] - mapping[nd][2]
                overall_size = sum(mapping[child][1] for child in nd.children)
                assert inner_size == overall_size, nd.as_xml()

        mapping = {}
        xml = tree.as_xml(inline_tags={'Quelle', 'BelegText'}, mapping=mapping)
        assert len(xml) == mapping[tree][1]
        for nd in tree.select(ANY_NODE, include_root=True):
            if nd.children:
                inner_size = mapping[nd][1] - mapping[nd][0] - mapping[nd][2]
                overall_size = sum(mapping[child][1] for child in nd.children)
                assert inner_size == overall_size, nd.as_xml()

        mapping = {}
        xml = tree.as_xml(inline_tags={'BedeutungsPosition'}, mapping=mapping)
        assert len(xml) == mapping[tree][1]
        for nd in tree.select(ANY_NODE, include_root=True):
            if nd.children:
                inner_size = mapping[nd][1] - mapping[nd][0] - mapping[nd][2]
                overall_size = sum(mapping[child][1] for child in nd.children)
                assert inner_size == overall_size, nd.as_xml()

    def test_xml_mapping(self):
        from DHParser.nodetree import SerializationMapping
        dom = parse_xml('<text>Kommt ein <i><b>Vogel</b></i> geflogen</text>')
        raw_mapping = {}
        ser = dom.as_xml(inline_tags={dom.name}, mapping=raw_mapping)
        sm = SerializationMapping(dom, ser, raw_mapping)
        i = ser.find('</text>')
        path, ser_pos, offset, part = sm.get_path(i, left_biased=True)
        assert (path[-1].name, ser_pos, part) == (TOKEN_PTYPE, 35, 1)
        i = ser.find('</text>')
        path, ser_pos, offset, part = sm.get_path(i, left_biased=False)
        assert (path[-1].name, ser_pos, part) == ('text', 0, 1)
        i = ser.find('<i><b>')
        path, ser_pos, offset, part = sm.get_path(i, left_biased=False)
        assert (path[-1].name, ser_pos, part) == ('i', 16, -1)
        i = ser.find('Vogel')
        path, ser_pos, offset, part = sm.get_path(i, left_biased=False)
        assert (path[-1].name, ser_pos, part) == ('b', 19, 0)
        i = ser.find('ein')
        path, ser_pos, offset, part = sm.get_path(i, left_biased=False)
        assert (path[-1].name, ser_pos, part) == (TOKEN_PTYPE, 6, 0)

        # print(pp_path(path, 1, ', '))
        # print(ser_pos, i - ser_pos)
        # print(part)

        k = sm.content_pos(path[-1], ser_pos, i - ser_pos, part)
        assert k == 6


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())