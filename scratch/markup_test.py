#!/usr/bin/env python3

import re
import sys
import DHParser.versionnumber

assert sys.version_info >= (3, 6), "Python Version 3.6 oder höher erforder"
assert DHParser.versionnumber.__version_info__ >= (1,1,1), "DHParser Verion 1.1.1 oder höher erfordert"

from DHParser.nodetree import Node, parse_xml, TOKEN_PTYPE, \
    generate_content_mapping, insert_node, markup

testdata_1 = '<document>In Charlot<lb/>tenburg steht ein Schloss.</document>'

testdata_2 = '''<document>
<app n="g">
<lem>silvae</lem>
<rdg wit="A">silvae, </rdg>
</app> glandiferae</document>'''


# füge ref-element als XML-milestone ein (Beispiel 2):

empty_tags = set()
tree = parse_xml(testdata_1, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
position = tree.content.find("Charlottenburg")
assert position >= 0
milestone = Node("ref", "").with_attr(type="subj",
                                      target="Charlottenburg_S00231",
                                      phrase="Charlottenburg")
empty_tags.add("ref")
mapping = generate_content_mapping(tree)
insert_node(mapping, position, milestone)
xml = tree.as_xml(inline_tags={"document"},
                  string_tags={TOKEN_PTYPE},
                  empty_tags=empty_tags)
print('\n1. Refernz als milestone eingefügt (Beispiel 1):\n')
print(xml)


# füge ref-element als markup ein (Beispiel 1)

empty_tags = set()
tree = parse_xml(testdata_1, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
start = tree.content.find("Charlottenburg")
assert start >= 0
end = start + len("Charlottenburg")
mapping = generate_content_mapping(tree)
markup(mapping, start, end, "ref", type="subj", target="Charlottenburg_S00231", phrase="Charlottenburg")
xml = tree.as_xml(inline_tags={"document"},
                  string_tags={TOKEN_PTYPE},
                  empty_tags=empty_tags)
print('\n\nReferenz als markup eingefügt (Beispiel 1):')
print(xml)


# füge ref-element als XML-milestone ein (Beispiel 2):

empty_tags = set()
tree = parse_xml(testdata_2, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
m = next(re.finditer(r'silvae,?\s*glandiferae', tree.content))
milestone = Node("ref", "").with_attr(type="subj",
                                      target="silva_glandifera_S01229",
                                      phrase=m.group(0))
empty_tags.add("ref")
mapping = generate_content_mapping(tree)
insert_node(mapping, m.start(), milestone)
xml = tree.as_xml(# inline_tags={"document"},
                  string_tags={TOKEN_PTYPE},
                  empty_tags=empty_tags)
print('\n\nReferenz als mildestone eingefügt (Beispiel 2):')
print(xml)


# füge Refernz als markup ein (Beispiel 2):
empty_tags = set()
tree = parse_xml(testdata_2, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
m = next(re.finditer(r'silvae,?\s*glandiferae', tree.content))
mapping = generate_content_mapping(tree)
markup(mapping, m.start(), m.end(), "ref", type="subj",
       target="silva_glandifera_S01229", phrase=m.group(0))
xml = tree.as_xml(string_tags={TOKEN_PTYPE},
                  empty_tags=empty_tags)
print('\n\nReferenz als markup eingefügt (Beispiel 2)')
print(xml)

