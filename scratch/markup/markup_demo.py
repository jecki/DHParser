import sys, os, json, re

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..', '..')))
scriptpath = os.path.abspath(scriptpath)

from DHParser.nodetree import Node, ContentMapping, parse_xml, find_common_ancestor
from DHParser.transform import pull_up

EXAMPLES_FILE = "VerlinkungsBeispiele.mwg.xml"


def clean_snippet(cell: Node) -> str:
    return re.sub(r'\s+', ' ', cell.as_xml(inline_tags={'cell'}, empty_tags={'lb'}))


def read_xml_file(filename: str) -> list[dict[str, str]]:
    with open(filename, 'r', encoding='utf-8') as f:
        xml = f.read()
    tree = parse_xml(xml)
    examples = []
    for row in tree.select('row'):
        if len(row.children) == 2 and row[1].children and 'ref' in row[1]:
            ref = row[1].pick('ref')
            target = ref.attr['target']
            typ = ref.get_attr('type', '')
            ref_text = re.sub(r'\s+', ' ', ''.join(ref.content for ref in row[1].select('ref')))
            examples.append({'before': clean_snippet(row[0]),
                             'after': clean_snippet(row[1]),
                             'replacements' : [{'ref': ref_text, 'target': target, 'type': typ}]})
    return examples


DIVISIBILITY = {
    'ref': ['hi'],    # ref darf 'hi' zerschneiden (ref ist "härter" als "hi")
    'note': ['ref'],  # note ist "härter" als "ref"
    'lem': ['ref'],   # lem ist "härter" als "ref"
    'app': ['ref']    # app ist "härter" als "ref"
}

IGNORE = {'note'}


def note_selector(path) -> bool:
    if len(path) < 3:
        return False
    if (path[-1].name == 'note' and
        path[-2].name == 'ref'
            and any(nd.name == 'app' for nd in path)):
        return True
    return False


def markup(before: str, replacements: list[dict[str, str]]) -> str:
    tree = parse_xml(before)
    for replacement in replacements:
        ref = replacement['ref']
        target = replacement['target']
        typ = replacement.get('type', '')
        cm = ContentMapping(tree, ignore=IGNORE, divisibility=DIVISIBILITY)
        a = cm.content.find(ref)
        assert a >= 0, f'{ref}\n{cm.content}'
        b = a + len(ref)
        attrs = dict()
        if typ: attrs['type'] = typ
        attrs['target'] = target
        cm.markup(a, b, 'ref', attrs)
        smallest_subtree, _ = find_common_ancestor(cm.path(cm.get_path_index(a)),
                                                   cm.path(cm.get_path_index(b)))
        for note_path in smallest_subtree.select_path(note_selector):
            pull_up(note_path)
        # cm.rebuild_mapping(a, b)  # content mapping is build a new with the next iteration, anyway
    return tree.as_xml(inline_tags={'cell'}, empty_tags={'lb'})


def markup_all_examples(examples):
    i = 1
    for example in examples:
        print(i)
        i += 1
        after = markup(example['before'], example['replacements'])
        assert after == example['after'], f'\n{after}\n{example["after"]}'


def read_json(filename) -> dict:
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # examples = read_xml_file(EXAMPLES_FILE)
    examples = read_json('prepared.json')['examples']
    markup_all_examples(examples)
    json.dump(examples, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()

