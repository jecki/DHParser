import sys, os, json, re

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..', '..')))
scriptpath = os.path.abspath(scriptpath)

from DHParser.nodetree import Node, ContentMapping, parse_xml, find_common_ancestor, TOKEN_PTYPE, pp_path
from DHParser.transform import pull_up, merge_adjacent, reduce_single_child

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

IGNORE = {}  # {'note'}


def pull_out(path):
    """A variant of DHParser.transform.pull_up that does not keep the
    surrounding markup intact."""
    node = path[-1]
    if len(path) <= 2:
        return
    parent = path[-2]
    ur_parent = path[-3]
    i = parent.index(node)
    i2 = ur_parent.index(parent)
    children = ur_parent._children
    inlay = []
    if i > 0:
        inlay.append(Node(parent.name, parent[:i]).with_pos(parent._pos).with_attr(parent.attr))
    inlay.append(node)
    if i < len(parent.children) - 1:
        inlay.append(Node(parent.name, parent[i + 1:]).with_pos(parent[i + 1]._pos).with_attr(parent.attr))
    ur_parent._set_result(children[:i2] + tuple(inlay) + children[i2 + 1:])


def select_note_inside_app(path) -> bool:
    if len(path) < 3:
        return False
    if (path[-1].name == 'note' and
        path[-2].name == 'ref'
            and any(nd.name == 'app' for nd in path)):
        return True
    return False


def markup(before: str, replacements: list[dict[str, str]], exclude=select_note_inside_app) -> str:
    """Fügt <ref> tags in einen XML-Schnipsel ein. "replacements" ist eine Liste
    von Verzeichnissen der Gestalt:
    [ {
        "ref": "Handelsgesellschaften", # Der Text (ohne Tags), der mit einer Referenz versehen werden soll
        "target": "Weber_Handelsgesellschaften_MWG_I_1_L0336",  # Das Ziel der Referenz
        "type": "bibl"  # Der Typ der Referenz
      }
      {...}
    ]
    """
    tree = parse_xml(before)
    for replacement in replacements:
        ref = replacement['ref']
        target = replacement['target']
        typ = replacement.get('type', '')
        ignore = set(replacement.get('ignore', "").split(','))
        cm = ContentMapping(tree, ignore=ignore, divisibility=DIVISIBILITY)
        a = cm.content.find(ref)
        assert a >= 0, f'{ref}\n{cm.content}'
        b = a + len(ref)
        attrs = dict()
        if typ: attrs['type'] = typ
        attrs['target'] = target

        cm.markup(a, b, 'ref', attrs)   # <=== the most important part!

        smallest_subtree, _ = find_common_ancestor(cm.path(cm.get_path_index(a)),
                                                   cm.path(cm.get_path_index(b)))

        for note_path in smallest_subtree.select_path(exclude):
            pull_out(note_path)

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

