#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree


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


XPATH_LIBRARY = {
    '//text[@type="main-text"]/body': lambda p: len(p) >= 2 \
        and p[-1].name == 'body'
        and p[-2].name == 'text' \
        and p[-2].get_attribute('type', '') == 'main-text',

    './/app/rdg|.//app/note|.//note': lambda p: len(p) >= 1 and p[-1].name == 'node' \
        or (len(p) >= 0 and p[-1].name == 'rdg' and p[-2].name == 'app')
}


def XPath(xpath) -> PathMatchFunction:
    """XPath-Match-Funktion für DHParser-Elemente. Bisher nur ein Stummel, der
    bereits in Python-codierte Funktionen für fest vorgegebene XPath-Ausdrücke zurückliefert.

    Args:
        xpath: XPath-Ausdruck, der die zu suchenden Elemente definiert.
    Returns:
        Eine Funktion, die ein DHParser-Element überprüft und entscheidet, ob es dem XPath-Ausdruck entspricht.
    """
    try:
        return XPATH_LIBRARY[xpath]
    except KeyError as e:
        raise KeyError(f"Bitte für den Schlüssel '{xpath}' noch eine passende Python-Funktion"
            f"in der XPATH_LIBRARY im script hinterlegen: {scriptpath}")



def mark_text(root: etree._Element,
              elements: str,
              pattern: str,
              exclude: str,
              lock_out: list,
              split: list,
              tag: str,
              attributes: dict) -> etree._Element:
    """Markiert Text strukturübergreifend.

    Args:
        root: Wurzelelement des zu bearbeitenden XML-Baums.
        elements: XPath der Elemente, innerhalb derer Text ausgezeichnet werden soll.
        pattern: Regulärer Ausdruck für den Text, der ausgezeichnet werden soll.
        exclude: XPath der Unterelemente, deren Inhalt bei der Suche ignoriert werden soll
        lock_out: Liste von Elementen, die bei der Einfügung ausgespart bleiben sollen.
        split: Liste von Elementen, die nötigenfalls zerteilt werden können.
        tag: Name des einzufügenden Elements.
        attributes: Attribute des einzufügenden Elements.

    """
    if lock_out:
        print("Warnung: Der Algorithmus zum Aussparen von Elementen is noch provisorisch und "
              "wirkt sich bisher nur auf unmittelbare Kind-Elemente des einzufügenden Tags aus!")
    root_node = Node.from_etree(root)
    for element in root_node.select-path(XPath(elements)):
        cm = ContentMapping(element, ignore=XPath(exclude), divisibility=split)
        for m in re.finditer(pattern, cm.content):
            a, b = m.span()
            attrs = dict()
            if typ: attrs['type'] = typ
            attrs['target'] = target
            cm.markup(a, b, 'ref', attrs)

            if lock_out:
                smallest_subtree, _ = find_common_ancestor(cm.path(cm.get_path_index(a)),
                                                           cm.path(cm.get_path_index(b)))
                for note_path in smallest_subtree.select_path(lock_out):
                    pull_out(note_path)
                cm.rebuild_mapping(smallest_subtree.pos,
                                   smallest_subtree.pos + len(smallest_subtree.content) - 1)
    return root_node.as_etree(empty_tag={'lb'})


def process_example():

    input_path = 'example.mwg.tei.xml'
    output_path = 'example.output.mwg.tei.xml'
    tree = etree.parse(input_path, parser=etree.XMLParser())
    root = tree.getroot()
    mark_text(root,
              elements='//text[@type="main-text"]/body',
              pattern=r'scamn\w+ et strig\w+',
              exclude='.//app/rdg|.//app/note|.//note',
              # split=['hi'],
              tag='ref',
              attributes={
                  'type': 'subj',
                  'target': 'scamna_et_strigae_S01193',
              }
    )
    with open(output_path, "wb") as output_file:
        output_file.write(
            etree.tostring(tree,
                           encoding="utf-8",
                           xml_declaration=True,
                           pretty_print=True)
        )



if __name__ == '__main__':
    process_example()


