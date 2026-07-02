import sys, os, json, re

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..', '..')))
scriptpath = os.path.abspath(scriptpath)

from DHParser.nodetree import Node, ContentMapping, parse_xml

EXAMPLES_FILE = "VerlinkungsBeispiele.mwg.xml"

def read_xml_file(filename: str) -> list[dict[str, str]]:
    with open(filename, 'r', encoding='utf-8') as f:
        xml = f.read()
    tree = parse_xml(xml)
    examples = []
    for row in tree.select('row'):
        if len(row.children) == 2 and row[1].children and 'ref' in row[1]:
            before = re.sub(r'\s', row[0].as_xml(inline_tags={'cell'}, empty_tags={'lb'}))
            ref = row[1].pick('ref')
            target = ref.attr['target']
            typ = ref.get_attr('type', '')
            ref_text = ''.join(ref.content for ref in row[1])
            examples.append({'before': row[0].as_xml(inline_tags={'cell'}, empty_tags={'lb'}),
                             'after':row[1].as_xml(inline_tags={'cell'}, empty_tags={'lb'}),
                             'replacements' : [{'ref': ref_text, 'target': target, 'type': typ}]})
    return examples


DIVISIBILITY = {
    'ref': ['hi'],    # ref darf 'hi' zerschneiden
    'note': ['ref'],
    'lem': ['ref'],
}

IGNORE = {'note'}

def markup(before, replacements: list[dict[str, str]]) -> str:
    tree = parse_xml(before)
    for replacement in replacements:
        ref = replacement['ref']
        target = replacement['target']
        typ = replacement.get('type', '')
        cm = ContentMapping(tree, ignore=IGNORE, divisibility=DIVISIBILITY)
        a = cm.content.find(ref)
        assert a >= 0, ref
        b = a + len(ref)
        attrs = {'target': target}
        if typ: attrs['type'] = typ
        cm.markup(a, b, ref, attrs)
    return tree.as_xml(inline_tags={'cell'}, empty_tags={'lb'})


def markup_all_examples(examples):
    i = 1
    for example in examples:
        print(i)
        i += 1
        after = markup(example['before'], example['replacements'])
        assert after == example['after']


def main():
    examples = read_xml_file(EXAMPLES_FILE)
    # markup_all_examples(examples)
    json.dump(examples, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()

