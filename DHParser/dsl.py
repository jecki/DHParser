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
Module ``dsl`` contains high-level functions for the compilation
of domain specific languages based on an EBNF-grammar.
"""

from __future__ import annotations

import functools
import inspect
import os
import platform
import stat
from typing import Any, cast, List, Tuple, Union, Iterator, Iterable, Optional, \
    Callable, Sequence

import DHParser.ebnf
from DHParser.compile import Compiler, compile_source
from DHParser.configuration import get_config_value
from DHParser.ebnf import EBNFCompiler, grammar_changed, DHPARSER_IMPORTS, \
    get_ebnf_preprocessor, get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler, \
    PreprocessorFactoryFunc, ParserFactoryFunc, TransformerFactoryFunc, CompilerFactoryFunc
from DHParser.error import Error, is_error, has_errors, only_errors, \
    CANNOT_VERIFY_TRANSTABLE_WARNING, ErrorCode, ERROR
from DHParser.log import suspend_logging, resume_logging, is_logging, log_dir, append_log
from DHParser.parse import Grammar
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc
from DHParser.nodetree import Node
from DHParser.transform import TransformerCallable, TransformationDict
from DHParser.toolkit import DHPARSER_DIR, load_if_file, is_python_code, \
    compile_python_object, re, as_identifier


__all__ = ('DefinitionError',
           'CompilationError',
           'read_template',
           'load_compiler_suite',
           'compileDSL',
           'raw_compileEBNF',
           'compileEBNF',
           'grammar_provider',
           'create_parser',
           'compile_on_disk',
           'recompile_grammar',
           'restore_server_script')


@functools.lru_cache()
def read_template(template_name: str) -> str:
    """
    Reads a script-template from a template file named ``template_name``
    in the template-directory and returns it as a string.
    """
    with open(os.path.join(DHPARSER_DIR, 'templates', template_name), 'r', encoding='utf-8') as f:
        return f.read()


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


class DSLException(Exception):
    """
    Base class for DSL-exceptions.
    """
    def __init__(self, errors: Union[Sequence[Error], Iterator[Error]]):
        Exception.__init__(self)
        assert isinstance(errors, Iterator) or isinstance(errors, list) \
            or isinstance(errors, tuple)
        self.errors = list(errors)

    def __str__(self):
        if len(self.errors) == 1:
            return str(self.errors[0])
        return '\n' + '\n'.join(("%i. " % (i + 1) + str(err))
                                for i, err in enumerate(self.errors))
        # return '\n'.join(str(err) for err in self.errors)


class DefinitionError(DSLException):
    """
    Raised when (already) the grammar of a domain specific language (DSL)
    contains errors. Usually, these are repackaged parse.GrammarError(s).
    """
    def __init__(self, errors, grammar_src):
        super().__init__(errors)
        self.grammar_src = grammar_src


class CompilationError(DSLException):
    """
    Raised when a string or file in a domain specific language (DSL)
    contains errors. These can also contain definition errors that
    have been caught early.
    """
    def __init__(self, errors, dsl_text, dsl_grammar, AST, result):
        super().__init__(errors)
        self.dsl_text = dsl_text
        self.dsl_grammar = dsl_grammar
        self.AST = AST
        self.result = result

    def __str__(self):
        return '\n'.join(str(error) for error in self.errors)


def error_str(messages: Iterable[Error]) -> str:
    """
    Returns all true errors (i.e. not just warnings) from the
    ``messages`` as a concatenated multiline string.
    """
    return '\n\n'.join(str(m) for m in messages if is_error(m.code))


def grammar_instance(grammar_representation) -> Tuple[Grammar, str]:
    """
    Returns a grammar object and the source code of the grammar, from
    the given ``grammar``-data which can be either a file name, ebnf-code,
    python-code, a Grammar-derived grammar class or an instance of
    such a class (i.e. a grammar object already).
    """
    if isinstance(grammar_representation, str):
        # read grammar
        grammar_src = load_if_file(grammar_representation)
        if is_python_code(grammar_src):
            parser_py = grammar_src  # type: str
            messages = []            # type: List[Error]
        else:
            lg_dir = suspend_logging()
            result, messages, _ = compile_source(
                grammar_src, None,
                get_ebnf_grammar(), get_ebnf_transformer(), get_ebnf_compiler())
            parser_py = cast(str, result)
            resume_logging(lg_dir)
        if has_errors(messages):
            raise DefinitionError(only_errors(messages), grammar_src)
        imports = DHPARSER_IMPORTS  
        grammar_class = compile_python_object(imports + parser_py, r'\w+Grammar$')
        if inspect.isclass(grammar_class) and issubclass(grammar_class, Grammar):
            parser_root = grammar_class()
        else:
            raise ValueError('Could not compile or Grammar class!')
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
               preprocessor: Optional[PreprocessorFunc],
               dsl_grammar: Union[str, Grammar],
               ast_transformation: TransformerCallable,
               compiler: Compiler,
               fail_when: ErrorCode = ERROR) -> Any:
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
    if has_errors(messages, fail_when):
        src = load_if_file(text_or_file)
        raise CompilationError(only_errors(messages, fail_when), src, grammar_src, AST, result)
    return result


def raw_compileEBNF(ebnf_src: str, branding="DSL", fail_when: ErrorCode = ERROR) -> EBNFCompiler:
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
    compileDSL(ebnf_src, nil_preprocessor, grammar, transformer, compiler, fail_when)
    return compiler


def compileEBNF(ebnf_src: str, branding="DSL") -> str:
    """
    Compiles an EBNF source file and returns the source code of a
    compiler suite with skeletons for preprocessor, transformer and
    compiler.

    Args:
        ebnf_src(str):  Either the file name of an EBNF-grammar or
            the EBNF-grammar itself as a string.
        branding (str):  Branding name for the compiler suite source
            code.
    Returns:
        The complete compiler suite skeleton as Python source code.
    Raises:
        CompilationError if any errors occurred during compilation
    """
    compiler = raw_compileEBNF(ebnf_src, branding)
    src = ["#/usr/bin/python\n",
           SECTION_MARKER.format(marker=SYMBOLS_SECTION),
           DHPARSER_IMPORTS,
           SECTION_MARKER.format(marker=PREPROCESSOR_SECTION), compiler.gen_preprocessor_skeleton(),
           SECTION_MARKER.format(marker=PARSER_SECTION), compiler.result,
           SECTION_MARKER.format(marker=AST_SECTION), compiler.gen_transformer_skeleton(),
           SECTION_MARKER.format(marker=COMPILER_SECTION), compiler.gen_compiler_skeleton(),
           SECTION_MARKER.format(marker=END_SECTIONS_MARKER),
           read_template('DSLParser.pyi').format(NAME=branding)]
    return '\n'.join(src)


@functools.lru_cache()
def grammar_provider(ebnf_src: str,
                     branding="DSL",
                     additional_code: str = '',
                     fail_when: ErrorCode = ERROR) -> ParserFactoryFunc:
    """
    Compiles an EBNF-grammar and returns a grammar-parser provider
    function for that grammar.

    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF-grammar itself as a string.
        branding (str or bool):  Branding name for the compiler
            suite source code.
        additional_code: Python code added to the generated source. This typically
            contains the source code of semantic actions referred to in the
            generated source, e.g. filter-functions, resume-point-search-functions

    Returns:
        A provider function for a grammar object for texts in the
        language defined by ``ebnf_src``.
    """
    grammar_src = compileDSL(
        ebnf_src, get_ebnf_preprocessor(), get_ebnf_grammar(), get_ebnf_transformer(),
        get_ebnf_compiler(branding, ebnf_src), fail_when)
    log_name = get_config_value('compiled_EBNF_log')
    if log_name and is_logging():  append_log(log_name, grammar_src)
    imports = DHPARSER_IMPORTS  
    grammar_factory = compile_python_object('\n'.join([imports, additional_code, grammar_src]),
                                            r'get_grammar$')  # r'get_(?:\w+_)?grammar$'
    if callable(grammar_factory):
        grammar_factory.python_src__ = grammar_src
        return grammar_factory
    raise ValueError('Could not compile grammar provider!')


def create_parser(ebnf_src: str, branding="DSL", additional_code: str = '') -> Grammar:
    """Compiles the ebnf source into a callable Grammar-object. This is
    essentially syntactic sugar for ``grammar_provider(ebnf)()``.
    """
    grammar_factory = grammar_provider(ebnf_src, branding, additional_code)
    grammar = grammar_factory()
    grammar.python_src__ = grammar_factory.python_src__
    return grammar


def split_source(file_name: str, file_content: str) -> List[str]:
    """Splits the ``file_content`` into the seven sections: intro, imports,
    preprocessor_py, parser_py, ast_py, compiler_py, outro.
    Raises a value error, if the number of sections if not equal to 7.
    """
    sections = RX_SECTION_MARKER.split(file_content)
    ls = len(sections)
    if ls != 7:
        raise ValueError('File "%s" contains %i instead of 7 sections. Please '
                         'delete or repair file manually.' % (file_name, ls))
    return sections


def load_compiler_suite(compiler_suite: str) -> \
        Tuple[PreprocessorFactoryFunc, ParserFactoryFunc,
              TransformerFactoryFunc, CompilerFactoryFunc]:
    """
    Extracts a compiler suite from file or string ``compiler_suite``
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
        sections = split_source(compiler_suite, source)
        _, imports, preprocessor_py, parser_py, ast_py, compiler_py, _ = sections
        # TODO: Compile in one step and pick parts from namespace later ?
        preprocessor = compile_python_object(imports + preprocessor_py,
                                             r'get_(?:\w+_)?preprocessor$')
        parser = compile_python_object(imports + parser_py, r'get_(?:\w+_)?grammar$')
        ast = compile_python_object(imports + ast_py, r'get_(?:\w+_)?transformer$')
    else:
        # Assume source is an ebnf grammar.
        # Is there really any reasonable application case for this?
        lg_dir = suspend_logging()
        compiler_py, messages, _ = compile_source(source, None, get_ebnf_grammar(),
                                                  get_ebnf_transformer(),
                                                  get_ebnf_compiler(compiler_suite, source))
        resume_logging(lg_dir)
        if has_errors(messages):
            raise DefinitionError(only_errors(messages), source)
        preprocessor = get_ebnf_preprocessor
        parser = get_ebnf_grammar
        ast = get_ebnf_transformer
    compiler = compile_python_object(imports + compiler_py, r'get_(?:\w+_)?compiler$')
    if callable(preprocessor) and callable(parser) and callable(Callable) and callable(compiler):
        return preprocessor, parser, ast, compiler
    raise ValueError('Could not generate compiler suite from source code!')


def is_outdated(compiler_suite: str, grammar_source: str) -> bool:
    """
    Returns ``True``  if the ``compile_suite`` needs to be updated.

    An update is needed, if either the grammar in the compiler suite
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
        _, grammar, _, _ = load_compiler_suite(compiler_suite)
        return grammar_changed(grammar(), grammar_source)
    except ValueError:
        return True


def run_compiler(text_or_file: str, compiler_suite: str, fail_when: ErrorCode = ERROR) -> Any:
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
    return compileDSL(text_or_file, preprocessor(), parser(), ast(), compiler(), fail_when)


def compile_on_disk(source_file: str,
                    parser_name: str = '',
                    compiler_suite: str = "",
                    extension: str = ".xml") -> Iterable[Error]:
    """
    Compiles the a source file with a given compiler and writes the
    result to a file.

    If no ``compiler_suite`` is given it is assumed that the source
    file is an EBNF grammar. In this case the result will be a Python
    script containing a parser for that grammar as well as the
    skeletons for a preprocessor, AST transformation table, and compiler.
    If the Python script already exists only the parser name in the
    script will be updated. (For this to work, the different names
    need to be delimited section marker blocks.). :py:func:`compile_on_disk`
    returns a list of error messages or an empty list if no errors
    occurred.

    :param source_file:  The file name of the source text to be compiled.
    :param parser_name:  The name of the generated parser. If the empty
        string is passed, the default name "...Parser.py" will be used.
    :param compiler_suite:  The file name of the parser/compiler-suite
        (usually ending with 'Parser.py'), with which the source file
        shall be compiled. If this is left empty, the source file is
        assumed to be an EBNF-Grammar that will be compiled with the
        internal EBNF-Compiler.
    :param extension:  The result of the compilation (if successful)
        is written to a file with the same name but a different extension
        than the source file. This parameter sets the extension.
    :returns:  A (potentially empty) list of error or warning messages.
    """
    filepath = os.path.normpath(source_file)
    rootname = os.path.splitext(filepath)[0]
    if not parser_name:  parser_name = rootname + 'Parser.py'
    f = None  # Optional[TextIO]
    with open(source_file, encoding="utf-8") as f:
        source = f.read()
    # dhpath = relative_path(os.path.dirname(rootname), DHPARSER_PARENTDIR)
    compiler_name = as_identifier(os.path.basename(rootname))
    if compiler_suite:
        sfactory, pfactory, tfactory, cfactory = load_compiler_suite(compiler_suite)
        compiler1 = cfactory()
    else:
        sfactory = get_ebnf_preprocessor  # PreprocessorFactoryFunc
        pfactory = get_ebnf_grammar       # ParserFactoryFunc
        tfactory = get_ebnf_transformer   # TransformerFactoryFunc
        cfactory = get_ebnf_compiler      # CompilerFactoryFunc
        compiler1 = cfactory()            # Compiler

    is_ebnf_compiler = False  # type: bool
    if isinstance(compiler1, EBNFCompiler):
        is_ebnf_compiler = True
        compiler1.set_grammar_name(compiler_name, source_file)

    result, messages, _ = compile_source(source, sfactory(), pfactory(), tfactory(), compiler1)

    if has_errors(messages):
        return messages

    elif is_ebnf_compiler:
        # trans == get_ebnf_transformer or trans == EBNFTransformer:
        # either an EBNF- or no compiler suite given
        ebnf_compiler = cast(EBNFCompiler, compiler1)  # type: EBNFCompiler
        global SECTION_MARKER, RX_SECTION_MARKER, PREPROCESSOR_SECTION, PARSER_SECTION, \
            AST_SECTION, COMPILER_SECTION, END_SECTIONS_MARKER, RX_WHITESPACE
        f = None
        try:
            f = open(parser_name, 'r', encoding="utf-8")
            source = f.read()
            sections = split_source(parser_name, source)
            intro, imports, preprocessor, _, ast, compiler, outro = sections
            ast_trans_python_src = imports + ast
            ast_trans_table = dict()  # type: TransformationDict
            try:
                ast_trans_table = compile_python_object(ast_trans_python_src,
                                                        r'(?:\w+_)?AST_transformation_table$')
            except Exception as e:
                if isinstance(e, NameError):
                    err_str = 'NameError "{}" while compiling AST-Transformation. ' \
                              'Possibly due to a forgotten import at the beginning ' \
                              'of the AST-Block (!)'.format(str(e))
                else:
                    err_str = 'Exception {} while compiling AST-Transformation: {}' \
                              .format(str(type(e)), str(e))
                messages.append(Error(err_str, 0, CANNOT_VERIFY_TRANSTABLE_WARNING))
                if is_logging():
                    with open(os.path.join(log_dir(), rootname + '_AST_src.py'), 'w',
                              encoding='utf-8') as f:
                        f.write(ast_trans_python_src)
            messages.extend(ebnf_compiler.verify_transformation_table(ast_trans_table))
            # TODO: Verify compiler
        except (PermissionError, FileNotFoundError, IOError):
            intro, imports, preprocessor, _, ast, compiler, outro = '', '', '', '', '', '', ''
        finally:
            if f:
                f.close()
                f = None

        if RX_WHITESPACE.fullmatch(intro):
            intro = '#!/usr/bin/env python3'
        if RX_WHITESPACE.fullmatch(outro):
            outro = read_template('DSLParser.pyi').format(NAME=compiler_name)
        if RX_WHITESPACE.fullmatch(imports):
            imports = DHParser.ebnf.DHPARSER_IMPORTS
        if RX_WHITESPACE.fullmatch(preprocessor):
            preprocessor = ebnf_compiler.gen_preprocessor_skeleton()
        if RX_WHITESPACE.fullmatch(ast):
            ast = ebnf_compiler.gen_transformer_skeleton()
        if RX_WHITESPACE.fullmatch(compiler):
            compiler = ebnf_compiler.gen_compiler_skeleton()

        try:
            f = open(parser_name, 'w', encoding="utf-8")
            f.write(intro)
            f.write(SECTION_MARKER.format(marker=SYMBOLS_SECTION))
            f.write(imports)
            f.write(SECTION_MARKER.format(marker=PREPROCESSOR_SECTION))
            f.write(preprocessor)
            f.write(SECTION_MARKER.format(marker=PARSER_SECTION))
            f.write(cast(str, result))
            f.write(SECTION_MARKER.format(marker=AST_SECTION))
            f.write(ast)
            f.write(SECTION_MARKER.format(marker=COMPILER_SECTION))
            f.write(compiler)
            f.write(SECTION_MARKER.format(marker=END_SECTIONS_MARKER))
            f.write(outro)
        except (PermissionError, FileNotFoundError, IOError) as error:
            print(f'# Could not write file "{parser_name}" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:
                f.close()

        if platform.system() != "Windows":
            # set file permissions so that the parser_name can be executed
            st = os.stat(parser_name)
            os.chmod(parser_name, st.st_mode | stat.S_IEXEC)

    else:
        f = None
        try:
            f = open(rootname + extension, 'w', encoding="utf-8")
            if isinstance(result, Node):
                if extension.lower() == '.xml':
                    f.write(result.as_xml())
                else:
                    f.write(result.as_sxpr())
            elif isinstance(result, str):
                f.write(result)
            else:
                raise AssertionError('Illegal result type: ' + str(type(result)))
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:
                f.close()

    return messages


def recompile_grammar(ebnf_filename: str,
                      parser_name: str = '',
                      force: bool = False,
                      notify: Callable = lambda: None) -> bool:
    """
    Re-compiles an EBNF-grammar if necessary, that is, if either no
    corresponding 'XXXXParser.py'-file exists or if that file is
    outdated.

    :param ebnf_filename:  The filename of the ebnf-source of the grammar.
            In case this is a directory and not a file, all files within
            this directory ending with .ebnf will be compiled.
    :param parser_name:  The name of the compiler script. If not given
            the ebnf-filename without extension and with the the addition
            of "Parser.py" will be used.
    :param force:  If False (default), the grammar will only be
            recompiled if it has been changed.
    :param notify:  'notify' is a function without parameters that
            is called when recompilation actually takes place. This can
            be used to inform the user.
    :returns: True, if recompilation of grammar has been successful or did
            not take place, because the Grammar hasn't changed since the last
            compilation. False, if the recompilation of the grammar has been
            attempted but failed.
    """
    if os.path.isdir(ebnf_filename):
        success = True
        for entry in os.listdir(ebnf_filename):
            if entry.lower().endswith('.ebnf') and os.path.isfile(entry):
                success = success and recompile_grammar(entry, parser_name, force)
        return success

    base, _ = os.path.splitext(ebnf_filename)
    if not parser_name:
        parser_name = base + 'Parser.py'
    error_file_name = base + '_ebnf_MESSAGES.txt'
    messages = []  # type: Iterable[Error]
    if (not os.path.exists(parser_name) or force
            or grammar_changed(parser_name, ebnf_filename)):
        notify()
        messages = compile_on_disk(ebnf_filename, parser_name)
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


def restore_server_script(ebnf_filename: str,
                          parser_name: str = '',
                          server_name: str = '',
                          overwrite: bool = False):
    """Creates a script for compiling texts adhering to the given grammar
    with a server. Because the server script relies on a parser script,
    a parser scripte will be created, too, if it does not yet exist.

    :param ebnf_filename: The filename of the grammar, from which the servfer
        script's filename is derived.
    :param parser_name: The filename of the parser script or the empty string
        if the default filename shall be used.
    :param server_name: The filename of the server script of the empty string
        if the default filename shall be used.
    :param overwrite: If True an existing server script will be overwritten.
    """
    if os.path.isdir(ebnf_filename):
        for entry in os.listdir(ebnf_filename):
            if entry.lower().endswith('.ebnf') and os.path.isfile(entry):
                restore_server_script(entry)
        return

    base, _ = os.path.splitext(ebnf_filename)
    name = os.path.basename(base)
    if not server_name:
        server_name = base + 'Server.py'
    if not parser_name:
        parser_name = base + 'Parser.py'
    if not os.path.exists(server_name) or overwrite:
        template = read_template('DSLServer.pyi')
        # reldhparserdir = os.path.relpath(os.path.dirname(DHPARSER_DIR), os.path.abspath('.'))
        # rel_dhpath_expr = ', '.join(f"'{p}'" for p in split_path(reldhparserdir))
        serverscript = base + 'Server.py'
        with open(serverscript, 'w', encoding='utf-8') as f:  
            f.write(template.replace('DSL', name))
        if platform.system() != "Windows":
            # set file permissions so that the server-script can be executed
            st = os.stat(serverscript)
            os.chmod(serverscript, st.st_mode | stat.S_IEXEC)
    if not os.path.exists(parser_name):  recompile_grammar(ebnf_filename, parser_name)


