#!/usr/bin/python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, DropWhitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, DropToken, Synonym, AllOf, SomeOf, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, PreprocessorFunc, is_empty, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, left_associative, lean_left, \
    set_config_value, get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def jsonPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return jsonPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class jsonGrammar(Grammar):
    r"""Parser for a json source file.
    """
    element = Forward()
    value = Forward()
    source_hash__ = "ef3108350d5f28b0f32716ad3952316d"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'(?:\/\/|#).*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('.'))
    EXP = Option(Series(Alternative(DropToken("E"), DropToken("e")), Option(Alternative(DropToken("+"), DropToken("-"))), RegExp('[0-9]+')))
    FRAC = Option(Series(DropToken("."), RegExp('[0-9]+')))
    INT = Alternative(Series(Option(DropToken("-")), RegExp('[0-9]')), RegExp('[1-9][0-9]+'))
    HEX = RegExp('[0-9a-fA-F]')
    ESCAPE = Alternative(RegExp('\\\\[/bnrt\\\\]'), Series(RegExp('\\\\u'), HEX, HEX, HEX, HEX))
    CHARACTERS = ZeroOrMore(Alternative(RegExp('[^"\\\\]+'), ESCAPE))
    null = Series(Token("null"), dwsp__)
    bool = Alternative(Series(RegExp('true'), dwsp__), Series(RegExp('false'), dwsp__))
    number = Series(INT, FRAC, EXP, dwsp__)
    string = Series(DropToken('"'), CHARACTERS, DropToken('"'), dwsp__)
    array = Series(Series(DropToken("["), dwsp__), Option(Series(value, ZeroOrMore(Series(Series(DropToken(","), dwsp__), value)))), Series(DropToken("]"), dwsp__))
    member = Series(string, Series(DropToken(":"), dwsp__), element)
    object = Series(Series(DropToken("{"), dwsp__), Option(Series(member, ZeroOrMore(Series(Series(DropToken(","), dwsp__), member)))), Series(DropToken("}"), dwsp__))
    value.set(Alternative(object, array, string, number, bool, null))
    element.set(Synonym(value))
    json = Series(dwsp__, element, EOF)
    root__ = json
    
def get_grammar() -> jsonGrammar:
    """Returns a thread/process-exclusive jsonGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()    
    try:
        grammar = THREAD_LOCALS.json_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.json_00000001_grammar_singleton = jsonGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.json_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.json_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

json_AST_transformation_table = {
    # AST Transformations for the json-grammar
    "<": flatten,
    "json": [remove_nodes('EOF'), replace_by_single_child],
    "element": [replace_by_single_child],
    "value": [replace_by_single_child],
    "object": [],
    "member": [],
    "array": [],
    "string": [collapse],
    "number": [collapse],
    "bool": [],
    "null": [],
    "CHARACTERS": [],
    "ESCAPE": [],
    "HEX": [],
    "INT": [],
    "FRAC": [],
    "EXP": [],
    "EOF": [],
    "*": replace_by_single_child
}


def CreatejsonTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=json_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.json_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.json_00000001_transformer_singleton = CreatejsonTransformer()
        transformer = THREAD_LOCALS.json_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class jsonCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a json source file.
    """

    def __init__(self):
        super(jsonCompiler, self).__init__()

    def reset(self):
        super().reset()
        self._None_check = False

    def on_object(self, node):
        return dict(self.compile(child) for child in node.children)

    def on_member(self, node) -> tuple:
        return (self.compile(node.children[0]), self.compile(node.children[1]))

    def on_array(self, node) -> list:
        return [self.compile(child) for child in node.children]

    def on_string(self, node) -> str:
        return node.content

    def on_number(self, node) -> float:
        return float(node.content)

    def on_bool(self, node) -> bool:
        return True if node.content == "true" else False

    def on_null(self, node) -> None:
        return None


def get_compiler() -> jsonCompiler:
    """Returns a thread/process-exclusive jsonCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.json_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.json_00000001_compiler_singleton = jsonCompiler()
        compiler = THREAD_LOCALS.json_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    start_logging(log_dir)
    compiler = get_compiler()
    result_tuple = compile_source(source, get_preprocessor(),
                                  get_grammar(),
                                  get_transformer(), compiler)
    return result_tuple


# class JsonLSP(LanguageServerProtocol):
#     def __init__(self):
#         super().__init__(capabilities={
#               "capabilities": {
#                 "textDocumentSync": 1,
#                 "completionProvider": {
#                   "resolveProvider": False,
#                   "triggerCharacters": [
#                     "/"
#                   ]
#                 },
#                 "hoverProvider": True,
#                 "documentSymbolProvider": True,
#                 "referencesProvider": True,
#                 "definitionProvider": True,
#                 "documentHighlightProvider": True,
#                 "codeActionProvider": True,
#                 "renameProvider": True,
#                 "colorProvider": {},
#                 "foldingRangeProvider": True
#               }
#             },  additional_rpcs={'default': compile_src})
#         return
#         # super().__init__(capabilities={
#         #     "testDocumentSync": {
#         #         'openClode': False,
#         #         'change': 0,  # 0 = no sync, 1 = full sync, 2 = incremental sync
#         #         'willSave': True,
#         #         'willSaveWaitUntil': False,
#         #         'save': {
#         #             "includeText": False
#         #         }
#         #     },
#         #     "hoverProvider": True,
#         #     # "completionProvier": {
#         #     #     'resolveProvider': False,
#         #     #     # 'triggerCharacters': ''
#         #     # },
#         #     # "signatureHelpProvider": {
#         #     #     # 'triggerCharacters': ''
#         #     # },
#         #     "definitionProvider": True,
#         #     "typeDefinitionProvider": False,
#         #     # "typeDefinitionProvider": {
#         #     #     # 'id': ''
#         #     #     'documentSelector': [
#         #     #         {
#         #     #             "language": '',
#         #     #             "scheme": '',
#         #     #             "pattern": ''
#         #     #         }
#         #     #     ]
#         #     # },
#         #     "implementationDefinitionProvider": False,
#         #     "referencesProvider": True,
#         #     "documentHighlightProvider": False,
#         #     "documentSymbolProvider": True,
#         #     "workspaceSymbolProvider": True,
#         #     "codeActionProvider": False,
#         #     # "codeActionProvider": {
#         #     #   'codeActionKinds': ['']
#         #     # },
#         #     # "codeLensProvider": {
#         #     #     'resolveProvider': False,
#         #     # },
#         #     "documentFormattingProvider": False,
#         #     "documentRangeFormattingProvider": False,
#         #     # "documentOnTypeFormattingProvider": {
#         #     #     'firstTriggerCharacter': '',
#         #     #     # 'moreTriggerCharacter': ''
#         #     # },
#         #     "renameProvider": False,
#         #     # "renameProvider": {
#         #     #     'prepareProvider': False
#         #     # },
#         #     # "documentLinkProvider": {
#         #     #     'resolveProvider': False
#         #     # },
#         #     "colorProvider": False,
#         #     "foldingRangeProvider": False,
#         #     "declarationProvider": False,
#         #     # "executeCommandProvider": {
#         #     #     'commands': ['']
#         #     # },
#         #     # "workspace": {
#         #     #     'workspaceFolders': {
#         #     #         'supported': False,
#         #     #         'changeNotifications': '' # string id or bool
#         #     #     }
#         #     # }
#         # },  additional_rpcs={'default': compile_src})
#
#     @lsp_rpc
#     def rpc_textDocument_hover(self, **kwargs):
#         print(kwargs)
#
#     @lsp_rpc
#     def rpc_textDocument_definition(self, **kwargs):
#         print(kwargs)
#
#     @lsp_rpc
#     def rpc_textDocument_references(self, **kwargs):
#         print(kwargs)
#
#     @lsp_rpc
#     def rpc_textDocument_documentSymbol(self, **kwargs):
#         print(kwargs)
#
#     @lsp_rpc
#     def rpc_workspace_symbol(self, **kwargs):
#         print(kwargs)
#
#     @lsp_rpc
#     def rpc_S_cancelRequest(self, **kwargs):
#         print(kwargs)


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Compiler.py', '.ebnf')
    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False,
                                  notify=lambda:print('recompiling ' + grammar_path)):
            error_file = os.path.basename(__file__).replace('Compiler.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        result, errors, _ = compile_src(file_name, log_dir)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_sxpr() if isinstance(result, Node) else result)
    else:
        print("Usage: jsonCompiler.py [FILENAME]")
