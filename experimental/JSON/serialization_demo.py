import sys, os

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'../..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

import JSONParser

if __name__ == "__main__":
    syntax_tree = JSONParser.parse_JSON('{ "one": 1, "two": 2 }')
    JSONParser.transform_JSON(syntax_tree)
    print(syntax_tree.as_sxpr())
    print(syntax_tree.as_json(indent=None))
    print(syntax_tree.as_xml())
    print(syntax_tree.as_tree())

