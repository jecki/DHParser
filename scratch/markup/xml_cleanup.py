import re

from DHParser.nodetree import Node, pick_from_path, parse_xml
from DHParser.transform import traverse, apply_if, is_empty, contains_only_whitespace, remove
from DHParser.toolkit import abbreviate_middle


# Leere tags entfernen

# siehe: https://dhparser.readthedocs.io/en/latest/manuals/03_AST-transformation.html

transformationen = {
    "lb": [apply_if(remove, is_empty)],
    "li": [apply_if(remove, contains_only_whitespace)]
    #  "*":  [apply_if(remove, contains_only_whitespace)]  # "*" steht für jedes beliebige Element
}

def entferne_leere_tags(dom: Node):
    traverse(dom, transformationen)



# Absätze ohne xml ID finden:

def fix_XML_IDs(dom: Node, tag="p"):
    last_id = None
    for node in dom.select(tag, include_root=True):
        if node.has_attr('xml:id'):
            last_id = node.attr['xml:id']
        else:
            wrong = node.as_xml(inline_tags={node.name})
            print(f"{node.name} has no xml:id: {abbreviate_middle(wrong, 60)}")
            print(f"last valid id for a {node.name}-tag was: {last_id}")
            print()

            # So kann eine fehlende xml ID hinzugefügt werden,
            # wenn man nur wüsste, welche...?

            last_id = '?' if last_id is None else last_id + '?'
            node.attr["xml:id"] = last_id



# fehlende Seitennummern korrigieren

def fix_missing_page_nr(dom: Node):
    last_page_nr = 0
    for node in dom.select('pb', include_root=True):
        if node.has_attr('n'):
            try:
                page_nr = int(node.attr['n'])
                if page_nr != last_page_nr + 1 and last_page_nr != 0:
                    print(f"Page {page_nr} cannot follow page {last_page_nr}! "
                          # "Either some pages are missing or a wrong page number "
                          # "has been added earlier."
                          )
                last_page_nr = page_nr
            except ValueError:
                print(f"Not a numeric page number '{node.attr['n']}'!")
        else:
            print(f"<pb> without n-Attribute found after page {last_page_nr}!")
            last_page_nr += 1
            node.attr['n'] = str(last_page_nr)
            print(f"Added page-number {last_page_nr}")
            print()



# Leerzeichen und Zeilenumbrüche normalisieren

def normalize(dom: Node, tags = {"p", "title"}) -> str:
    for path in dom.select_path(lambda p: pick_from_path(p, tags) is not None and not p[-1].children,
                                include_root=True):
        node = path[-1]
        node.result = re.sub(r'\s+', ' ', node.content)  # normalisiere Leerraum

    # inline_tags in Verbindung mit reflow_col führt dazu, dass inline-Elemente und ihre
    # Kindelemente nicht (wie ohne reflow_col) in einer Zeile dargestellt werden,
    # sondern, dass sie sauber umgebrochen werden.
    return dom.as_xml(inline_tags=tags, reflow_col=120)


# Test

def test():
    import os

    currdir = os.getcwd()
    if currdir.find('scratch/markup') < 0:
        os.chdir("scratch/markup")

    print("Beginne Test!")
    print("Lese Testdatei ein:")
    with open('Test - b1-02_roemische-agrargeschichte - Input.xml', 'r', encoding='utf-8') as f:
        xml = f.read()
    dom = parse_xml(xml)

    print("Entferne alle <lb/> und aller leeren <li> </li> Elemente")
    entferne_leere_tags(dom)

    print("Prüfe alle <p>-Elemente auf ein xml:id-Attribut")
    fix_XML_IDs(dom)

    print("Prüfe alle <pb>-Elemente auf eine korrekte Sequenz von Seitennummern")
    fix_missing_page_nr(dom)

    print("Normalisiere Leerzeichen und Zeilenumbrüche")
    xml = normalize(dom)

    print("Schreibe Ergebnisdatei: Testergebnis.xml")
    with open('Testergebnix.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    print("Test beendet.")

    os.chdir(currdir)


if __name__ == "__main__":
    test()
