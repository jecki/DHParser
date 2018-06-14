# dsl.py - Support for domain specific notations for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.


"""
Module ``dsl`` contains various functions to support the
compilation of domain specific languages based on an EBNF-grammar.
"""


import os
import platform
import stat

from DHParser.compile import Compiler, compile_source
from DHParser.ebnf import EBNFCompiler, grammar_changed, \
    get_ebnf_preprocessor, get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler, \
    PreprocessorFactoryFunc, ParserFactoryFunc, TransformerFactoryFunc, CompilerFactoryFunc
from DHParser.error import Error, is_error, has_errors, only_errors
from DHParser.log import logging
from DHParser.parse import Grammar
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc
from DHParser.syntaxtree import Node
from DHParser.transform import TransformationFunc
from DHParser.toolkit import load_if_file, is_python_code, compile_python_object, \
    re, typing
from typing import Any, cast, List, Tuple, Union, Iterator, Iterable


__all__ = ('DHPARSER_IMPORTS',
           'GrammarError',
           'CompilationError',
           'load_compiler_suite',
           'compileDSL',
           'raw_compileEBNF',
           'compileEBNF',
           'grammar_provider',
           'compile_on_disk',
           'recompile_grammar')


SECTION_MARKER = """\n
#######################################################################
#
# {marker}
#
#######################################################################
\n"""

RX_SECTION_MARKER = re.compile(SECTION_MARKER.format(marker=r'.*?SECTION.*?'))
RX_WHITESPACE = re.compile(r'\s*')

SYMBOLS_SECTION = "SYMBOLS SECTION - Can be edited. Changes will be preserved."
PREPROCESSOR_SECTION = "PREPROCESSOR SECTION - Can be edited. Changes will be preserved."
PARSER_SECTION = "PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!"
AST_SECTION = "AST SECTION - Can be edited. Changes will be preserved."
COMPILER_SECTION = "COMPILER SECTION - Can be edited. Changes will be preserved."
END_SECTIONS_MARKER = "END OF DHPARSER-SECTIONS"


dhparserdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


DHPARSER_IMPORTS = '''
import collections
from functools import partial
import os
import sys

sys.path.append(r'{dhparserdir}')

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, \\
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \\
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \\
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \\
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \\
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \\
    Node, TransformationFunc, TransformationDict, transformation_factory, \\
    traverse, remove_children_if, merge_children, is_anonymous, \\
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \\
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \\
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \\
    remove_nodes, remove_content, remove_brackets, replace_parser, remove_anonymous_tokens, \\
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \\
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \\
    replace_content, replace_content_by
'''.format(dhparserdir=dhparserdir)


DHPARSER_MAIN = '''
def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging(log_dir):
        compiler = get_compiler()
        cname = compiler.__class__.__name__
        log_file_name = os.path.basename(os.path.splitext(source)[0]) \\
            if is_filename(source) < 0 else cname[:cname.find('.')] + '_out'
        result = compile_source(source, get_preprocessor(),
                                get_grammar(),
                                get_transformer(), compiler)
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            grammar_file_name = os.path.basename(__file__).replace('Compiler.py', '.ebnf')
            if grammar_changed({NAME}Grammar, grammar_file_name):
                print("Grammar has changed. Please recompile Grammar first.")
                sys.exit(1)
        except FileNotFoundError:
            print('Could not check for changed grammar, because grammar file "%s" was not found!'
                  % grammar_file_name)    
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        result, errors, ast = compile_src(file_name, log_dir)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: {NAME}Compiler.py [FILENAME]")
'''


class DSLException(Exception):
    """
    Base class for DSL-exceptions.
    """
    def __init__(self, errors):
        assert isinstance(errors, Iterator) or isinstance(errors, list) \
               or isinstance(errors, tuple)
        self.errors = errors

    def __str__(self):
        return '\n'.join(str(err) for err in self.errors)


class GrammarError(DSLException):
    """
    Raised when (already) the grammar of a domain specific language (DSL)
    contains errors.
    """
    def __init__(self, errors, grammar_src):
        super().__init__(errors)
        self.grammar_src = grammar_src


class CompilationError(DSLException):
    """
    Raised when a string or file in a domain specific language (DSL)
    contains errors.
    """
    def __init__(self, errors, dsl_text, dsl_grammar, AST, result):
        super().__init__(errors)
        self.dsl_text = dsl_text
        self.dsl_grammar = dsl_grammar
        self.AST = AST
        self.result = result


def error_str(messages: Iterable[Error]) -> str:
    """
    Returns all true errors (i.e. not just warnings) from the
    `messages` as a concatenated multiline string.
    """
    return '\n\n'.join(str(m) for m in messages if is_error(m.code))


def grammar_instance(grammar_representation) -> Tuple[Grammar, str]:
    """
    Returns a grammar object and the source code of the grammar, from
    the given `grammar`-data which can be either a file name, ebnf-code,
    python-code, a Grammar-derived grammar class or an instance of
    such a class (i.e. a grammar object already).
    """
    if isinstance(grammar_representation, str):
        # read grammar
        grammar_src = load_if_file(grammar_representation)
        if is_python_code(grammar_src):
            parser_py, messages = grammar_src, []  # type: str, List[Error]
        else:
            with logging(False):
                parser_py, messages, _ = compile_source(
                    grammar_src, None,
                    get_ebnf_grammar(), get_ebnf_transformer(), get_ebnf_compiler())
        if has_errors(messages):
            raise GrammarError(only_errors(messages), grammar_src)
        parser_root = compile_python_object(DHPARSER_IMPORTS + parser_py, r'\w+Grammar$')()
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
               preprocessor: PreprocessorFunc,
               dsl_grammar: Union[str, Grammar],
               ast_transformation: TransformationFunc,
               compiler: Compiler) -> Any:
    """
    Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Returns the compiled text or raises a
    compilation error.

    Raises:
        CompilationError if any errors occurred during compilation
    """
    assert isinstance(text_or_file, str)
    assert isinstance(compiler, Compiler)

    parser, grammar_src = grammar_instance(dsl_grammar)
    result, messages, AST = compile_source(text_or_file, preprocessor, parser,
                                           ast_transformation, compiler)
    if has_errors(messages):
        src = load_if_file(text_or_file)
        raise CompilationError(only_errors(messages), src, grammar_src, AST, result)
    return result


def raw_compileEBNF(ebnf_src: str, branding="DSL") -> EBNFCompiler:
    """
    Compiles an EBNF grammar file and returns the compiler object
    that was used and which can now be queried for the result as well
    as skeleton code for preprocessor, transformer and compiler objects.

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
    compiler = get_ebnf_compiler(branding, ebnf_src)
    transformer = get_ebnf_transformer()
    compileDSL(ebnf_src, nil_preprocessor, grammar, transformer, compiler)
    return compiler


def compileEBNF(ebnf_src: str, branding="DSL") -> str:
    """
    Compiles an EBNF source file and returns the source code of a
    compiler suite with skeletons for preprocessor, transformer and
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
           SECTION_MARKER.format(marker=PREPROCESSOR_SECTION), compiler.gen_preprocessor_skeleton(),
           SECTION_MARKER.format(marker=PARSER_SECTION), compiler.result,
           SECTION_MARKER.format(marker=AST_SECTION), compiler.gen_transformer_skeleton(),
           SECTION_MARKER.format(marker=COMPILER_SECTION), compiler.gen_compiler_skeleton(),
           SECTION_MARKER.format(marker=SYMBOLS_SECTION), DHPARSER_MAIN.format(NAME=branding)]
    return '\n'.join(src)


def grammar_provider(ebnf_src: str, branding="DSL") -> Grammar:
    """
    Compiles an EBNF grammar and returns a grammar-parser provider
    function for that grammar.

    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF grammar itself as a string.
        branding (str or bool):  Branding name for the compiler
            suite source code.

    Returns:
        A provider function for a grammar object for texts in the
        language defined by ``ebnf_src``.
    """
    grammar_src = compileDSL(ebnf_src, nil_preprocessor, get_ebnf_grammar(),
                             get_ebnf_transformer(), get_ebnf_compiler(branding, ebnf_src))
    grammar_obj = compile_python_object(DHPARSER_IMPORTS + grammar_src, r'get_(?:\w+_)?grammar$')
    grammar_obj.python_src__ = grammar_src
    return grammar_obj


def load_compiler_suite(compiler_suite: str) -> \
        Tuple[PreprocessorFactoryFunc, ParserFactoryFunc,
              TransformerFactoryFunc, CompilerFactoryFunc]:
    """
    Extracts a compiler suite from file or string `compiler_suite`
    and returns it as a tuple (preprocessor, parser, ast, compiler).

    Returns:
        4-tuple (preprocessor function, parser class,
                 ast transformer function, compiler class)
    """
    global RX_SECTION_MARKER
    assert isinstance(compiler_suite, str)
    source = load_if_file(compiler_suite)
    imports = DHPARSER_IMPORTS
    if is_python_code(compiler_suite):
        try:
            _, imports, preprocessor_py, parser_py, ast_py, compiler_py, _ = \
                RX_SECTION_MARKER.split(source)
        except ValueError:
            raise AssertionError('File "' + compiler_suite + '" seems to be corrupted. '
                                 'Please delete or repair file manually.')
        # TODO: Compile in one step and pick parts from namespace later ?
        preprocessor = compile_python_object(imports + preprocessor_py,
                                             r'get_(?:\w+_)?preprocessor$')
        parser = compile_python_object(imports + parser_py, r'get_(?:\w+_)?grammar$')
        ast = compile_python_object(imports + ast_py, r'get_(?:\w+_)?transformer$')
    else:
        # Assume source is an ebnf grammar.
        # Is there really any reasonable application case for this?
        with logging(False):
            compiler_py, messages, n = compile_source(source, None, get_ebnf_grammar(),
                                                      get_ebnf_transformer(),
                                                      get_ebnf_compiler(compiler_suite, source))
        if has_errors(messages):
            raise GrammarError(only_errors(messages), source)
        preprocessor = get_ebnf_preprocessor
        parser = get_ebnf_grammar
        ast = get_ebnf_transformer
    compiler = compile_python_object(imports + compiler_py, r'get_(?:\w+_)?compiler$')

    return preprocessor, parser, ast, compiler


def is_outdated(compiler_suite: str, grammar_source: str) -> bool:
    """
    Returns ``True``  if the ``compile_suite`` needs to be updated.

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
        n1, grammar, n2, n3 = load_compiler_suite(compiler_suite)
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
    preprocessor, parser, ast, compiler = load_compiler_suite(compiler_suite)
    return compileDSL(text_or_file, preprocessor(), parser(), ast(), compiler())


def compile_on_disk(source_file: str, compiler_suite="", extension=".xml") -> Iterable[Error]:
    """
    Compiles the a source file with a given compiler and writes the
    result to a file.

    If no ``compiler_suite`` is given it is assumed that the source
    file is an EBNF grammar. In this case the result will be a Python
    script containing a parser for that grammar as well as the
    skeletons for a preprocessor, AST transformation table, and compiler.
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
        A (potentially empty) list of error or warning messages.
    """
    filepath = os.path.normpath(source_file)
    with open(source_file, encoding="utf-8") as f:
        source = f.read()
    rootname = os.path.splitext(filepath)[0]
    compiler_name = os.path.basename(rootname)
    if compiler_suite:
        sfactory, pfactory, tfactory, cfactory = load_compiler_suite(compiler_suite)
    else:
        sfactory = get_ebnf_preprocessor
        pfactory = get_ebnf_grammar
        tfactory = get_ebnf_transformer
        cfactory = get_ebnf_compiler
    compiler1 = cfactory()
    compiler1.set_grammar_name(compiler_name, source_file)
    result, messages, AST = compile_source(source, sfactory(), pfactory(), tfactory(), compiler1)
    if has_errors(messages):
        return messages

    elif cfactory == get_ebnf_compiler:
        # trans == get_ebnf_transformer or trans == EBNFTransformer:
        # either an EBNF- or no compiler suite given
        ebnf_compiler = cast(EBNFCompiler, compiler1)
        global SECTION_MARKER, RX_SECTION_MARKER, PREPROCESSOR_SECTION, PARSER_SECTION, \
            AST_SECTION, COMPILER_SECTION, END_SECTIONS_MARKER, RX_WHITESPACE, \
            DHPARSER_MAIN, DHPARSER_IMPORTS
        f = None
        try:
            f = open(rootname + 'Compiler.py', 'r', encoding="utf-8")
            source = f.read()
            sections = RX_SECTION_MARKER.split(source)
            intro, imports, preprocessor, parser, ast, compiler, outro = sections
            # TODO: Verify transformation table
            ast_trans_table = compile_python_object(DHPARSER_IMPORTS + ast,
                                                    r'(?:\w+_)?AST_transformation_table$')
            messages.extend(ebnf_compiler.verify_transformation_table(ast_trans_table))
        except (PermissionError, FileNotFoundError, IOError) as error:
            intro, imports, preprocessor, parser, ast, compiler, outro = '', '', '', '', '', '', ''
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
        if RX_WHITESPACE.fullmatch(preprocessor):
            preprocessor = ebnf_compiler.gen_preprocessor_skeleton()
        if RX_WHITESPACE.fullmatch(ast):
            ast = ebnf_compiler.gen_transformer_skeleton()
        if RX_WHITESPACE.fullmatch(compiler):
            compiler = ebnf_compiler.gen_compiler_skeleton()

        compilerscript = rootname + 'Compiler.py'
        try:
            f = open(compilerscript, 'w', encoding="utf-8")
            f.write(intro)
            f.write(SECTION_MARKER.format(marker=SYMBOLS_SECTION))
            f.write(imports)
            f.write(SECTION_MARKER.format(marker=PREPROCESSOR_SECTION))
            f.write(preprocessor)
            f.write(SECTION_MARKER.format(marker=PARSER_SECTION))
            f.write(result)
            f.write(SECTION_MARKER.format(marker=AST_SECTION))
            f.write(ast)
            f.write(SECTION_MARKER.format(marker=COMPILER_SECTION))
            f.write(compiler)
            f.write(SECTION_MARKER.format(marker=END_SECTIONS_MARKER))
            f.write(outro)
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + compilerscript + '" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:
                f.close()

        if platform.system() != "Windows":
            # set file permissions so that the compilerscript can be executed
            st = os.stat(compilerscript)
            os.chmod(compilerscript, st.st_mode | stat.S_IEXEC)

    else:
        f = None
        try:
            f = open(rootname + extension, 'w', encoding="utf-8")
            if isinstance(result, Node):
                if extension.lower() == '.xml':
                    f.write(result.as_xml())
                else:
                    f.write(result.as_sxpr())
            else:
                f.write(result)
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:
                f.close()

    return messages


def recompile_grammar(ebnf_filename, force=False) -> bool:
    """
    Re-compiles an EBNF-grammar if necessary, that is, if either no
    corresponding 'XXXXCompiler.py'-file exists or if that file is
    outdated.

    Parameters:
        ebnf_filename(str):  The filename of the ebnf-source of the
            grammar. In case this is a directory and not a file, all
            files within this directory ending with .ebnf will be
            compiled.
        force(bool):  If False (default), the grammar will only be
            recompiled if it has been changed.
    """
    if os.path.isdir(ebnf_filename):
        success = True
        for entry in os.listdir(ebnf_filename):
            if entry.lower().endswith('.ebnf') and os.path.isfile(entry):
                success = success and recompile_grammar(entry, force)
        return success

    base, ext = os.path.splitext(ebnf_filename)
    compiler_name = base + 'Compiler.py'
    error_file_name = base + '_ebnf_ERRORS.txt'
    messages = []  # type: Iterable[Error]
    if (not os.path.exists(compiler_name) or force or
            grammar_changed(compiler_name, ebnf_filename)):
        # print("recompiling parser for: " + ebnf_filename)
        messages = compile_on_disk(ebnf_filename)
        if messages:
            # print("Errors while compiling: " + ebnf_filename + '!')
            with open(error_file_name, 'w', encoding="utf-8") as f:
                for e in messages:
                    f.write(str(e))
                    f.write('\n')
            if has_errors(messages):
                return False

    if not messages and os.path.exists(error_file_name):
        os.remove(error_file_name)
    return True
