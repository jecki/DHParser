import sys
sys.path.append('../')


from DHParser.nodetree import parse_xml


def main():
    with open('archiv.xml') as f:
        xml = f.read()
    data = parse_xml(xml, strict_mode=False)
    print(data.as_sxpr())


if __name__ == '__main__':
    main()
