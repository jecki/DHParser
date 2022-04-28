import sys
sys.path.append('../')


from DHParser.nodetree import parse_xml, parse_sxpr
from DHParser.toolkit import normalize_docstring


def json_beispiel():
    """Dient nur dazu zu zeigen, wie DHParser.nodetree (XML-)Datenbäume nach
    JSON überträgt, denn es sind ja durchaus unterschiedliche Arten denkbar,
    um XML eineindeutig zu JSON zu transformieren.
    """
    # data = parse_sxpr('''
    #     (xml
    #         (leer "")
    #         (leer_mit_Attributen `(name "wert") "")
    #         (nur_Text "text")
    #         (Text_mit_Attributen `(name "wert") "text")
    #         (knoten_mit_Kindern (kind "1") (kind "2"))
    #         (knoten_mit_Kindern_und_Attributen `(name "wert") (kind "1") (kind "2"))
    #     )''')
    xml = '''
        <xml>
          <leer/>
          <leer_mit_Attributen name="wert"/>
          <nur_Text>text</nur_Text>
          <Text_mit_Attributen name="wert">text</Text_mit_Attributen>
          <knoten_mit_Kindern>
            <kind>1</kind>
            <kind>2</kind>
          </knoten_mit_Kindern>
          <knoten_mit_Kindern_und_Attributen name="wert">
            <kind>1</kind>
            <kind>2</kind>
          </knoten_mit_Kindern_und_Attributen>
          <Gemischtes_Element>anfang <kind>1</kind> ende</Gemischtes_Element>
        </xml>    
    '''
    data = parse_xml(xml)
    with open('beispiel_xml_nach_json.txt', 'w', encoding='utf-8') as f:
        f.write(normalize_docstring(json_beispiel.__doc__))
        f.write('\n\nXML-Urquelle:\n')
        f.write(xml)
        f.write('\n\nDHParser-XML:\n\n')
        f.write(data.as_xml(empty_tags={'leer', 'leer_mit_Attributen'}))
        f.write('\n\nJSON-Ausgabe:\n\n')
        f.write(data.as_json())


def cpu_profile(func, repetitions=1):
    """Profile the function `func`.
    """
    import cProfile
    import pstats
    profile = cProfile.Profile()
    profile.enable()
    success = True
    for _ in range(repetitions):
        success = func()
        if not success:
            break
    profile.disable()
    # after your program ends
    stats = pstats.Stats(profile)
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(80)
    return success


def profile():
    print('Lese archiv.xml')
    with open('archiv.xml', 'r', encoding='utf-8') as f:
        xml = f.read()
    print('Parse archiv.xml mit DHParser.nodetree.parse_xml - Bitte etwas Geduld')
    cpu_profile(lambda :parse_xml(xml, strict_mode=False))


def main():
    print('Lese archiv.xml')
    with open('archiv.xml', 'r', encoding='utf-8') as f:
        xml = f.read()
    print('Parse archiv.xml - Bitte etwas Geduld')
    data = parse_xml(xml, strict_mode=False)
    print('Schreibe archiv.json')
    with open('archiv.json', 'w', encoding='utf-8') as f:
        f.write(data.as_json())
    print('Schreibe archiv.tree.txt')
    with open('archiv.tree.txt', 'w', encoding='utf-8') as f:
        f.write(data.as_tree())
    print('Schreibe archiv.lsp')
    with open('archiv.lsp', 'w', encoding='utf-8') as f:
        f.write(data.as_sxpr())


if __name__ == '__main__':
    # json_beispiel()
    # main()
    profile()