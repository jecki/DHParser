#!/usr/bin/python3

"""DSLsupport.py - Support for domain specific notations for DHParser

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.

Module ``DSLsupport`` contains various functions to support the
compilation of domain specific languages based on an EBNF-grammar.
"""

import collections
import os
try:
    import regex as re
except ImportError:
    import re

from .__init__ import __version__
from .EBNFcompiler import EBNFGrammar, EBNF_ASTPipeline, EBNFCompiler
from .toolkit import IS_LOGGING, load_if_file, is_python_code, md5, compile_python_object
from .parsercombinators import GrammarBase, CompilerBase, full_compilation, nil_scanner
from .syntaxtree import Node


__all__ = ['GrammarError',
           'CompilationError',
           'load_compiler_suite',
           'compileDSL',
           'run_compiler',
           'source_changed']


SECTION_MARKER = """\n
#######################################################################
#
# {marker}
#
#######################################################################
\n"""

RX_SECTION_MARKER = re.compile(SECTION_MARKER.format(marker=r'.*?SECTION.*?'))

SYMBOLS_SECTION = "SYMBOLS SECTION - Can be edited. Changes will be preserved."
SCANNER_SECTION = "SCANNER SECTION - Can be edited. Changes will be preserved."
PARSER_SECTION = "PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!"
AST_SECTION = "AST SECTION - Can be edited. Changes will be preserved."
COMPILER_SECTION = "COMPILER SECTION - Can be edited. Changes will be preserved."
END_SECTIONS_MARKER = "END OF DHPARSER-SECTIONS"


class GrammarError(Exception):
    """Raised when (already) the grammar of a domain specific language (DSL)
    contains errors.
    """

    def __init__(self, error_messages, grammar_src):
        self.error_messages = error_messages
        self.grammar_src = grammar_src


class CompilationError(Exception):
    """Raised when a string or file in a domain specific language (DSL)
    contains errors.
    """

    def __init__(self, error_messages, dsl_text, dsl_grammar, AST):
        self.error_messages = error_messages
        self.dsl_text = dsl_text
        self.dsl_grammar = dsl_grammar
        self.AST = AST

    def __str__(self):
        return self.error_messages


DHPARSER_IMPORTS = """
from functools import partial
import sys
try:
    import regex as re
except ImportError:
    import re
from DHParser.toolkit import load_if_file    
from DHParser.parsercombinators import GrammarBase, CompilerBase, nil_scanner, \\
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, \\
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Sequence, RE, Capture, \\
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, full_compilation
from DHParser.syntaxtree import Node, remove_enclosing_delimiters, remove_children_if, \\
    reduce_single_child, replace_by_single_child, remove_whitespace, TOKEN_KEYWORD, \\
    no_operation, remove_expendables, remove_tokens, flatten, WHITESPACE_KEYWORD, \\
    is_whitespace, is_expendable
"""


DHPARSER_COMPILER = '''
def compile_{NAME}(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    source_text = load_if_file(source)
    return full_compilation({NAME}Scanner(source_text),
        {NAME}Grammar(), {NAME}_ASTPipeline, {NAME}Compiler())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result, errors, ast = compile_{NAME}(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
                sys.exit(1)
        else:
            print(result)
    else:
        print("Usage: {NAME}_compiler.py [FILENAME]")
'''


def get_grammar_instance(grammar):
    """Returns a grammar object and the source code of the grammar, from
    the given `grammar`-data which can be either a file name, ebnf-code,
    python-code, a GrammarBase-derived grammar class or an instance of
    such a class (i.e. a grammar object already).
    """
    if isinstance(grammar, str):
        # read grammar
        grammar_src = load_if_file(grammar)
        if is_python_code(grammar):
            parser_py, errors, AST = grammar_src, '', None
        else:
            parser_py, errors, AST = full_compilation(grammar_src,
                    EBNFGrammar(), EBNF_ASTPipeline, EBNFCompiler())
        if errors:
            raise GrammarError(errors, grammar_src)
        parser_root = compile_python_object(DHPARSER_IMPORTS + parser_py, '\w*Grammar$')()
    else:
        # assume that dsl_grammar is a ParserHQ-object or Grammar class
        grammar_src = ''
        if isinstance(grammar, GrammarBase):
            parser_root = grammar
        else:
            # assume `grammar` is a grammar class and get the root object
            parser_root = grammar()
    return parser_root, grammar_src


def load_compiler_suite(compiler_suite):
    """Extracts a compiler suite from file or string ``compiler suite``
    and returns it as a tuple (scanner, parser, ast, compiler).
    """
    global RX_SECTION_MARKER
    assert isinstance(compiler_suite, str)
    source = load_if_file(compiler_suite)
    if is_python_code(compiler_suite):
        try:
            intro, imports, scanner_py, parser_py, ast_py, compiler_py, outro = \
                RX_SECTION_MARKER.split(source)
        except ValueError as error:
            raise ValueError('File "' + compiler_suite + '" seems to be corrupted. '
                                                         'Please delete or repair file manually.')
        scanner = compile_python_object(imports + scanner_py, '\w*Scanner$')
        ast = compile_python_object(imports + ast_py, '\w*Pipeline$')
        compiler = compile_python_object(imports + compiler_py, '\w*Compiler$')
    else:
        # assume source is an ebnf grammar
        parser_py, errors, AST = full_compilation(
            source, EBNFGrammar(), EBNF_ASTPipeline, EBNFCompiler())
        if errors:
            raise GrammarError(errors, source)
        scanner = nil_scanner
        ast = EBNF_ASTPipeline
        compiler = EBNFCompiler()
    parser = compile_python_object(DHPARSER_IMPORTS + parser_py, '\w*Grammar$')()

    return scanner, parser, ast, compiler


def compileDSL(text_or_file, dsl_grammar, ast_pipeline, compiler,
               scanner=nil_scanner):
    """Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Returns the compiled text.
    """
    assert isinstance(text_or_file, str)
    assert isinstance(compiler, CompilerBase)
    assert isinstance(ast_pipeline, collections.abc.Sequence) or isinstance(ast_pipeline, dict)
    parser_root, grammar_src = get_grammar_instance(dsl_grammar)
    src = scanner(load_if_file(text_or_file))
    result, errors, AST = full_compilation(src, parser_root, ast_pipeline, compiler)
    if errors:  raise CompilationError(errors, src, grammar_src, AST)
    return result


def compileEBNF(ebnf_src, ebnf_grammar_obj=None):
    """Compiles an EBNF source file into a Grammar class

    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF grammar itself as a string.
        ebnf_grammar_obj:  An existing instance of the 
            DHParser.EBNFcompiler.EBNFGrammar object. This can speed
            up compilation, because no new EBNFGrammar object needs to
            be instantiated.
    Returns:
        A Grammar class that can be instantiated for parsing a text
        which conforms to the language defined by ``ebnf_src``
    """
    grammar = ebnf_grammar_obj or EBNFGrammar()
    grammar_src = compileDSL(ebnf_src, grammar, EBNF_ASTPipeline, EBNFCompiler())
    return compile_python_object(DHPARSER_IMPORTS + grammar_src, '\w*Grammar$')


def run_compiler(source_file, compiler_suite="", extension=".xml"):
    """Compiles the a source file with a given compiler and writes the
    result to a file.

    If no ``compiler_suite`` is given it is assumed that the source
    file is an EBNF grammar. In this case the result will be a Python
    script containing a parser for that grammar as well as the
    skeletons for a scanner, AST transformation table, and compiler.
    If the Python script already exists only the parser name in the
    script will be updated. (For this to work, the different names
    need to be delimited section marker blocks.). `run_compiler()`
    returns a list of error messages or an empty list if no errors
    occurred.
    """
    filepath = os.path.normpath(source_file)
    with open(source_file, encoding="utf-8") as f:
        source = f.read()
    rootname = os.path.splitext(filepath)[0]
    compiler_name = os.path.basename(rootname)
    if compiler_suite:
        scanner, parser, trans, cclass = load_compiler_suite(compiler_suite)
        compiler = cclass()
    else:
        scanner = nil_scanner
        parser = EBNFGrammar()
        trans = EBNF_ASTPipeline
        compiler = EBNFCompiler(compiler_name, source)
    result, errors, ast = full_compilation(scanner(source), parser,
                                           trans, compiler)
    if errors:
        return errors

    elif trans == EBNF_ASTPipeline:  # either an EBNF- or no compiler suite given
        f = None

        global SECTION_MARKER, RX_SECTION_MARKER, SCANNER_SECTION, PARSER_SECTION, \
            AST_SECTION, COMPILER_SECTION, END_SECTIONS_MARKER
        try:
            f = open(rootname + '_compiler.py', 'r', encoding="utf-8")
            source = f.read()
            intro, imports, scanner, parser, ast, compiler, outro = RX_SECTION_MARKER.split(source)
        except (PermissionError, FileNotFoundError, IOError) as error:
            intro, outro = '', ''
            imports = DHPARSER_IMPORTS
            scanner = compiler.gen_scanner_skeleton()
            ast = compiler.gen_AST_skeleton()
            compiler = compiler.gen_compiler_skeleton()
        except ValueError as error:
            raise ValueError('File "' + rootname + '_compiler.py" seems to be corrupted. '
                                                   'Please delete or repair file manually!')
        finally:
            if f:  f.close()

        try:
            f = open(rootname + '_compiler.py', 'w', encoding="utf-8")
            f.write("#!/usr/bin/python")
            f.write(intro)
            f.write(SECTION_MARKER.format(marker=SYMBOLS_SECTION))
            f.write(imports)
            f.write(SECTION_MARKER.format(marker=SCANNER_SECTION))
            f.write(scanner)
            f.write(SECTION_MARKER.format(marker=PARSER_SECTION))
            f.write(result)
            f.write(SECTION_MARKER.format(marker=AST_SECTION))
            f.write(ast)
            f.write(SECTION_MARKER.format(marker=COMPILER_SECTION))
            f.write(compiler)
            f.write(SECTION_MARKER.format(marker=END_SECTIONS_MARKER))
            f.write(outro)
            f.write(DHPARSER_COMPILER.format(NAME=compiler_name))
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '_compiler.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:  f.close()

    else:
        try:
            f = open(rootname + extension, 'w', encoding="utf-8")
            if isinstance(result, Node):
                f.write(result.as_xml())
            else:
                f.write(result)
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:  f.close()
        if IS_LOGGING():
            print(ast)

    return []


def source_changed(grammar_source, grammar_class):
    """Returns `True` if `grammar_class` does not reflect the latest
    changes of `grammar_source`

    Parameters:
        grammar_source:  File name or string representation of the
            grammar source
        grammar_class:  the parser class representing the grammar
            or the file name of a compiler suite containing the grammar

    Returns (bool):
        True, if the source text of the grammar is different from the
        source from which the grammar class was generated
    """
    grammar = load_if_file(grammar_source)
    chksum = md5(grammar, __version__)
    if isinstance(grammar_class, str):
        # grammar_class = load_compiler_suite(grammar_class)[1]
        with open(grammar_class, 'r', encoding='utf8') as f:
            pycode = f.read()
        m = re.search('class \w*\(GrammarBase\)', pycode)
        if m:
            m = re.search('    source_hash__ *= *"([a-z0-9]*)"',
                          pycode[m.span()[1]:])
            return not (m and m.groups() and m.groups()[-1] == chksum)
        else:
            return True
    else:
        return chksum != grammar_class.source_hash__
