import os
import sys

sys.path.append(os.path.abspath('../'))

from ParserCombinators import *

mlregex = r"""
regex = /\w+    # one or more alphabetical characters including the underscore
         [+]    # followed by a plus sign
         \w*    # possibly followed by more alpha chracters/ ;
"""
result, messages, syntax_tree = full_compilation(mlregex, EBNFGrammar.root__, EBNFTransTable,
                                                 EBNFCompiler('MultilineRegexTest'))
parser = compile_python_parser(result)
node, rest = parser.regex('abc+def')
assert rest == ''
assert node.result == 'abc+def'
print(node.as_sexpr())


