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

from functools import partial
import os
try:
    import regex as re
except ImportError:
    import re

from EBNFcompiler import *
from toolkit import *
from parsercombinators import *
from syntaxtree import *
from version import __version__


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
END_SECTIONS_MARKER = "END OF PYDSL-SECTIONS"


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


def compile_python_object(python_src, obj_name_ending="Grammar"):
    """Compiles the python source code and returns the object the name of which
    ends with `obj_name_ending`.
     """
    code = compile(python_src, '<string>', 'exec')
    module_vars = globals()
    allowed_symbols = PARSER_SYMBOLS | AST_SYMBOLS | COMPILER_SYMBOLS
    namespace = {k: module_vars[k] for k in allowed_symbols}
    exec(code, namespace)  # safety risk?
    for key in namespace.keys():
        if key.endswith(obj_name_ending):
            obj = namespace[key]
            break
    else:
        obj = None
    return obj


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
                                                      EBNFGrammar(), EBNFTransTable, EBNFCompiler())
        if errors:
            raise GrammarError(errors, grammar_src)
        parser_root = compile_python_object(parser_py, 'Grammar')()
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
            intro, syms, scanner_py, parser_py, ast_py, compiler_py, outro = \
                RX_SECTION_MARKER.split(source)
        except ValueError as error:
            raise ValueError('File "' + compiler_suite + '" seems to be corrupted. '
                                                         'Please delete or repair file manually.')
        scanner = compile_python_object(scanner_py, 'Scanner')
        ast = compile_python_object(ast_py, 'TransTable')
        compiler = compile_python_object(compiler_py, 'Compiler')
    else:
        # assume source is an ebnf grammar
        parser_py, errors, AST = full_compilation(
            source, EBNFGrammar(), EBNFTransTable, EBNFCompiler())
        if errors:
            raise GrammarError(errors, source)
        scanner = nil_scanner
        ast = EBNFTransTable
        compiler = EBNFCompiler()
    parser = compile_python_object(parser_py, 'Grammar')()

    return scanner, parser, ast, compiler


def compileDSL(text_or_file, dsl_grammar, trans_table, compiler,
               scanner=nil_scanner):
    """Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Returns the compiled text.
    """
    assert isinstance(text_or_file, str)
    assert isinstance(compiler, CompilerBase)
    assert isinstance(trans_table, dict)
    parser_root, grammar_src = get_grammar_instance(dsl_grammar)
    src = scanner(load_if_file(text_or_file))
    result, errors, AST = full_compilation(src, parser_root, trans_table,
                                           compiler)
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
    grammar_src = compileDSL(ebnf_src, grammar, EBNFTransTable, EBNFCompiler())
    return compile_python_object(grammar_src)


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

    def import_block(python_module, symbols):
        """Generates an Python-``import`` statement that imports all
        alls symbols in ``symbols`` (set or other container) from
        python_module ``python_module``."""
        symlist = list(symbols)
        grouped = [symlist[i:i + 3] for i in range(0, len(symlist), 3)]
        return ("\nfrom " + python_module + " import "
                + ', \\\n    '.join(', '.join(g) for g in grouped))

    filepath = os.path.normpath(source_file)
    with open(source_file, encoding="utf-8") as f:
        source = f.read()
    rootname = os.path.splitext(filepath)[0]
    if compiler_suite:
        scanner, parser, trans, cclass = load_compiler_suite(compiler_suite)
        compiler = cclass()
    else:
        scanner = nil_scanner
        parser = EBNFGrammar()
        trans = EBNFTransTable
        compiler = EBNFCompiler(os.path.basename(rootname), source)
    result, errors, ast = full_compilation(scanner(source), parser,
                                           trans, compiler)
    if errors:
        return errors

    elif trans == EBNFTransTable:  # either an EBNF- or no compiler suite given
        f = None

        global SECTION_MARKER, RX_SECTION_MARKER, SCANNER_SECTION, PARSER_SECTION, \
            AST_SECTION, COMPILER_SECTION, END_SECTIONS_MARKER
        try:
            f = open(rootname + '_compiler.py', 'r', encoding="utf-8")
            source = f.read()
            intro, syms, scanner, parser, ast, compiler, outro = RX_SECTION_MARKER.split(source)
        except (PermissionError, FileNotFoundError, IOError) as error:
            intro, outro = '', ''
            syms = 'import re\n' + import_block("DHParser.syntaxtree", AST_SYMBOLS)
            syms += import_block("DHParser.parser", PARSER_SYMBOLS | {'CompilerBase'}) + '\n\n'
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
            f.write(intro)
            f.write(SECTION_MARKER.format(marker=SYMBOLS_SECTION))
            f.write(syms)
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
