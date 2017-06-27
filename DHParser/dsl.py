"""dsl.py - Support for domain specific notations for DHParser

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

import os
try:
    import regex as re
except ImportError:
    import re
from .typing import Any, cast, Tuple, Union

from DHParser.ebnf import EBNFTransformer, EBNFCompiler, grammar_changed, \
    get_ebnf_scanner, get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler, \
    ScannerFactoryFunc, ParserFactoryFunc, TransformerFactoryFunc, CompilerFactoryFunc
from DHParser.toolkit import logging, load_if_file, is_python_code, compile_python_object
from DHParser.parsers import Grammar, Compiler, compile_source, nil_scanner, ScannerFunc
from DHParser.syntaxtree import Node, TransformationFunc


__all__ = ['GrammarError',
           'CompilationError',
           'load_compiler_suite',
           'compileDSL',
           'raw_compileEBNF',
           'compileEBNF',
           'parser_factory',
           'compile_on_disk']


SECTION_MARKER = """\n
#######################################################################
#
# {marker}
#
#######################################################################
\n"""

RX_SECTION_MARKER = re.compile(SECTION_MARKER.format(marker=r'.*?SECTION.*?'))
RX_WHITESPACE = re.compile('\s*')

SYMBOLS_SECTION = "SYMBOLS SECTION - Can be edited. Changes will be preserved."
SCANNER_SECTION = "SCANNER SECTION - Can be edited. Changes will be preserved."
PARSER_SECTION = "PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!"
AST_SECTION = "AST SECTION - Can be edited. Changes will be preserved."
COMPILER_SECTION = "COMPILER SECTION - Can be edited. Changes will be preserved."
END_SECTIONS_MARKER = "END OF DHPARSER-SECTIONS"


DHPARSER_IMPORTS = '''
from functools import partial
import os
import sys
try:
    import regex as re
except ImportError:
    import re
from DHParser.toolkit import logging, is_filename, load_if_file    
from DHParser.parsers import Grammar, Compiler, nil_scanner, \\
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, Synonym, \\
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Sequence, RE, Capture, \\
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \\
    nop_filter, counterpart_filter, accumulating_filter, ScannerFunc
from DHParser.syntaxtree import Node, traverse, remove_enclosing_delimiters, \\
    remove_children_if, reduce_single_child, replace_by_single_child, remove_whitespace, \\
    no_transformation, remove_expendables, remove_tokens, flatten, is_whitespace, is_expendable, \\
    collapse, map_content, WHITESPACE_PTYPE, TOKEN_PTYPE, TransformationFunc
'''


DHPARSER_MAIN = '''
def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging("LOGS"):
        compiler = get_compiler()
        cname = compiler.__class__.__name__
        log_file_name = os.path.basename(os.path.splitext(source)[0]) \\
            if is_filename(source) < 0 else cname[:cname.find('.')] + '_out'    
        result = compile_source(source, get_scanner(), 
                                get_grammar(),
                                get_transformer(), compiler)
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result, errors, ast = compile_src(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
            sys.exit(1)
        else:
            print(result)
    else:
        print("Usage: {NAME}Compiler.py [FILENAME]")
'''


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
    def __init__(self, error_messages, dsl_text, dsl_grammar, AST, result):
        self.error_messages = error_messages
        self.dsl_text = dsl_text
        self.dsl_grammar = dsl_grammar
        self.AST = AST
        self.result = result

    def __str__(self):
        return '\n'.join(self.error_messages)


def grammar_instance(grammar_representation) -> Tuple[Grammar, str]:
    """Returns a grammar object and the source code of the grammar, from
    the given `grammar`-data which can be either a file name, ebnf-code,
    python-code, a Grammar-derived grammar class or an instance of
    such a class (i.e. a grammar object already).
    """
    if isinstance(grammar_representation, str):
        # read grammar
        grammar_src = load_if_file(grammar_representation)
        if is_python_code(grammar_src):
            parser_py, errors, AST = grammar_src, '', None
        else:
            with logging(False):
                parser_py, errors, AST = compile_source(grammar_src, None,
                    get_ebnf_grammar(), get_ebnf_transformer(), get_ebnf_compiler())
        if errors:
            raise GrammarError('\n\n'.join(errors), grammar_src)
        parser_root = compile_python_object(DHPARSER_IMPORTS + parser_py, '\w+Grammar$')()
    else:
        # assume that dsl_grammar is a ParserHQ-object or Grammar class
        grammar_src = ''
        if isinstance(grammar_representation, Grammar):
            parser_root = grammar_representation
        else:
            # assume ``grammar_representation`` is a grammar class and get the root object
            parser_root = grammar_representation()
    return parser_root, grammar_src


def compileDSL(text_or_file: str,
               scanner: ScannerFunc,
               dsl_grammar: Union[str, Grammar],
               ast_transformation: TransformationFunc,
               compiler: Compiler) -> Any:
    """Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Returns the compiled text or raises a
    compilation error.
    
    Raises:
        CompilationError if any errors occurred during compilation
    """
    assert isinstance(text_or_file, str)
    assert isinstance(compiler, Compiler)

    parser, grammar_src = grammar_instance(dsl_grammar)
    result, errors, AST = compile_source(text_or_file, scanner, parser,
                                         ast_transformation, compiler)
    if errors:
        src = load_if_file(text_or_file)
        raise CompilationError(errors, src, grammar_src, AST, result)
    return result


def raw_compileEBNF(ebnf_src: str, branding="DSL") -> EBNFCompiler:
    """Compiles an EBNF grammar file and returns the compiler object
    that was used and which can now be queried for the result as well
    as skeleton code for scanner, transformer and compiler objects.
    
    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF grammar itself as a string.
        branding (str):  Branding name for the compiler suite source
            code. 
    Returns:
        An instance of class ``ebnf.EBNFCompiler``
    Raises:
        CompilationError if any errors occurred during compilation      
    """
    grammar = get_ebnf_grammar()
    compiler = get_ebnf_compiler(branding , ebnf_src)
    compileDSL(ebnf_src, nil_scanner, grammar, EBNFTransformer, compiler)
    return compiler


def compileEBNF(ebnf_src: str, branding="DSL") -> str:
    """Compiles an EBNF source file and returns the source code of a
    compiler suite with skeletons for scanner, transformer and 
    compiler.

    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF grammar itself as a string.
        branding (str):  Branding name for the compiler suite source
            code. 
    Returns:
        The complete compiler suite skeleton as Python source code.
    Raises:
        CompilationError if any errors occurred during compilation        
    """
    compiler = raw_compileEBNF(ebnf_src, branding)
    src = ["#/usr/bin/python\n",
           SECTION_MARKER.format(marker=SYMBOLS_SECTION), DHPARSER_IMPORTS,
           SECTION_MARKER.format(marker=SCANNER_SECTION), compiler.gen_scanner_skeleton(),
           SECTION_MARKER.format(marker=PARSER_SECTION), compiler.result,
           SECTION_MARKER.format(marker=AST_SECTION), compiler.gen_transformer_skeleton(),
           SECTION_MARKER.format(marker=COMPILER_SECTION), compiler.gen_compiler_skeleton(),
           SECTION_MARKER.format(marker=SYMBOLS_SECTION), DHPARSER_MAIN.format(NAME=branding)]
    return '\n'.join(src)


def parser_factory(ebnf_src: str, branding="DSL") -> Grammar:
    """Compiles an EBNF grammar and returns a grammar-parser factory
    function for that grammar.

    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF grammar itself as a string.
        branding (str or bool):  Branding name for the compiler
            suite source code. 
    
    Returns:
        A factory function for a grammar-parser for texts in the
        language defined by ``ebnf_src``.
    """
    grammar_src = compileDSL(ebnf_src, nil_scanner, get_ebnf_grammar(),
                             get_ebnf_transformer(), get_ebnf_compiler(branding))
    return compile_python_object(DHPARSER_IMPORTS + grammar_src, 'get_(?:\w+_)?grammar$')


def load_compiler_suite(compiler_suite: str) -> \
        Tuple[ScannerFactoryFunc, ParserFactoryFunc, TransformerFactoryFunc, CompilerFactoryFunc]:
    """Extracts a compiler suite from file or string ``compiler suite``
    and returns it as a tuple (scanner, parser, ast, compiler).
    
    Returns:
        4-tuple (scanner function, parser class, ast transformer function, compiler class)
    """
    global RX_SECTION_MARKER
    assert isinstance(compiler_suite, str)
    source = load_if_file(compiler_suite)
    if is_python_code(compiler_suite):
        try:
            intro, imports, scanner_py, parser_py, ast_py, compiler_py, outro = \
                RX_SECTION_MARKER.split(source)
        except ValueError as error:
            raise AssertionError('File "' + compiler_suite + '" seems to be corrupted. '
                                 'Please delete or repair file manually.')
        # TODO: Compile in one step and pick parts from namespace later ?
        scanner = compile_python_object(imports + scanner_py, 'get_(?:\w+_)?scanner$')
        parser = compile_python_object(imports + parser_py, 'get_(?:\w+_)?grammar$')
        ast = compile_python_object(imports + ast_py, 'get_(?:\w+_)?transformer$')
    else:
        # assume source is an ebnf grammar. Is there really any reasonable application case for this?
        with logging(False):
            compile_py, errors, AST = compile_source(source, None,
                get_ebnf_grammar(), get_ebnf_transformer(), get_ebnf_compiler())
        if errors:
            raise GrammarError('\n\n'.join(errors), source)
        scanner = get_ebnf_scanner
        parser = get_ebnf_grammar
        ast = get_ebnf_transformer
    compiler = compile_python_object(imports + compiler_py, 'get_(?:\w+_)?compiler$')

    return scanner, parser, ast, compiler


def is_outdated(compiler_suite: str, grammar_source: str) -> bool:
    """Returns ``True``  if the ``compile_suite`` needs to be updated.
     
    An update is needed, if either the grammar in the compieler suite 
    does not reflect the latest changes of ``grammar_source`` or if 
    sections from the compiler suite have diligently been overwritten
    with whitespace order to trigger their recreation. Note: Do not
    delete or overwrite the section marker itself. 

    Args:
        compiler_suite:  the parser class representing the grammar
            or the file name of a compiler suite containing the grammar
        grammar_source:  File name or string representation of the
            EBNF code of the grammar

    Returns (bool):
        True, if ``compiler_suite`` seems to be out of date.
    """
    try:
        scanner, grammar, ast, compiler = load_compiler_suite(compiler_suite)
        return grammar_changed(grammar(), grammar_source)
    except ValueError:
        return True


def run_compiler(text_or_file: str, compiler_suite: str) -> Any:
    """Compiles a source with a given compiler suite.

    Args:
        text_or_file (str):  Either the file name of the source code or
            the source code directly. (Which is determined by 
            heuristics. If ``text_or_file`` contains at least on
            linefeed then it is always assumed to be a source text and
            not a file name.)
        compiler_suite(str):  File name of the compiler suite to be
            used.
        
    Returns:
        The result of the compilation, the form and type of which 
        depends entirely on the compiler.
        
    Raises:
        CompilerError
    """
    scanner, parser, ast, compiler = load_compiler_suite(compiler_suite)
    return compileDSL(text_or_file, scanner(), parser(), ast(), compiler())


def compile_on_disk(source_file: str, compiler_suite="", extension=".xml"):
    """Compiles the a source file with a given compiler and writes the
    result to a file.

    If no ``compiler_suite`` is given it is assumed that the source
    file is an EBNF grammar. In this case the result will be a Python
    script containing a parser for that grammar as well as the
    skeletons for a scanner, AST transformation table, and compiler.
    If the Python script already exists only the parser name in the
    script will be updated. (For this to work, the different names
    need to be delimited section marker blocks.). `compile_on_disk()`
    returns a list of error messages or an empty list if no errors
    occurred.
    
    Parameters:
        source_file(str):  The file name of the source text to be
            compiled.
        compiler_suite(str):  The file name of the compiler suite
            (usually ending with 'Compiler.py'), with which the source
            file shall be compiled. If this is left empty, the source
            file is assumed to be an EBNF-Grammar that will be compiled
            with the internal EBNF-Compiler.
        extension(str):  The result of the compilation (if successful)
            is written to a file with the same name but a different
            extension than the source file. This parameter sets the
            extension.
            
    Returns:
        A list of error messages or an empty list if there were no 
        errors. 
    """
    filepath = os.path.normpath(source_file)
    # with open(source_file, encoding="utf-8") as f:
    #     source = f.read()
    rootname = os.path.splitext(filepath)[0]
    compiler_name = os.path.basename(rootname)
    if compiler_suite:
        sfactory, pfactory, tfactory, cfactory = load_compiler_suite(compiler_suite)
    else:
        sfactory = get_ebnf_scanner
        pfactory = get_ebnf_grammar
        tfactory = get_ebnf_transformer
        cfactory = get_ebnf_compiler
    compiler1 = cfactory()
    compiler1.set_grammar_name(compiler_name, source_file)
    result, errors, ast = compile_source(source_file, sfactory(), pfactory(), tfactory(), compiler1)
    if errors:
        return errors

    elif cfactory == get_ebnf_compiler:  # trans == get_ebnf_transformer or trans == EBNFTransformer:  # either an EBNF- or no compiler suite given
        ebnf_compiler = cast(EBNFCompiler, compiler1)
        global SECTION_MARKER, RX_SECTION_MARKER, SCANNER_SECTION, PARSER_SECTION, \
            AST_SECTION, COMPILER_SECTION, END_SECTIONS_MARKER, RX_WHITESPACE, \
            DHPARSER_MAIN, DHPARSER_IMPORTS
        f = None
        try:
            f = open(rootname + 'Compiler.py', 'r', encoding="utf-8")
            source = f.read()
            sections = RX_SECTION_MARKER.split(source)
            intro, imports, scanner, parser, ast, compiler, outro = sections
        except (PermissionError, FileNotFoundError, IOError) as error:
            intro, imports, scanner, parser, ast, compiler, outro = '', '', '', '', '', '', ''
        except ValueError as error:
            name = '"' + rootname + 'Compiler.py"'
            raise ValueError('Could not identify all required sections in ' + name +
                             '. Please delete or repair ' + name + ' manually!')
        finally:
            if f:
                f.close()
                f = None

        if RX_WHITESPACE.fullmatch(intro):
            intro = '#!/usr/bin/python'
        if RX_WHITESPACE.fullmatch(outro):
            outro = DHPARSER_MAIN.format(NAME=compiler_name)
        if RX_WHITESPACE.fullmatch(imports):
            imports = DHPARSER_IMPORTS
        if RX_WHITESPACE.fullmatch(scanner):
            scanner = ebnf_compiler.gen_scanner_skeleton()
        if RX_WHITESPACE.fullmatch(ast):
            ast = ebnf_compiler.gen_transformer_skeleton()
        if RX_WHITESPACE.fullmatch(compiler):
            compiler = ebnf_compiler.gen_compiler_skeleton()

        try:
            f = open(rootname + 'Compiler.py', 'w', encoding="utf-8")
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
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + 'Compiler.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:  f.close()

    else:
        f = None
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

    return []
