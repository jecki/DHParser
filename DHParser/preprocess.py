# preprocess.py - preprocessing of source files for DHParser
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
Module ``preprocess`` contains functions for preprocessing source
code before the parsing stage as well as source mapping facilities
to map the locations of parser and compiler errors to the
non-preprocessed source text.

Preprocessing (and source mapping of errors) will only be needed
for some domain specific languages, most notably those that
cannot completely be described entirely with context-free grammars.
"""

from __future__ import annotations

import bisect
from collections import namedtuple
import functools
import os
from typing import Union, Optional, Callable, Tuple, List, Any

from DHParser.error import Error, SourceMap, SourceLocation, SourceMapFunc, \
    add_source_locations
from DHParser.stringview import StringView
from DHParser.toolkit import re, TypeAlias


__all__ = ('RX_TOKEN_NAME',
           'BEGIN_TOKEN',
           'TOKEN_DELIMITER',
           'END_TOKEN',
           'IncludeInfo',
           'FindIncludeFunc',
           'PreprocessorFunc',
           'PreprocessorResult',
           'Tokenizer',
           'make_token',
           'strip_tokens',
           'nil_preprocessor',
           'chain_preprocessors',
           'prettyprint_tokenized',
           'gen_neutral_srcmap_func',
           'tokenized_to_original_mapping',
           'make_preprocessor',
           'gen_find_include_func',
           'preprocess_includes')


#######################################################################
#
# Types and constants
#
#######################################################################

BEGIN_TOKEN = '\x1b'
TOKEN_DELIMITER = '\x1c'
END_TOKEN = '\x1d'
RESERVED_TOKEN_CHARS = BEGIN_TOKEN + TOKEN_DELIMITER + END_TOKEN

RX_TOKEN_NAME = re.compile(r'\w+')
RX_TOKEN_ARGUMENT = re.compile(r'[^\x1b\x1c\x1d]*')
RX_TOKEN = re.compile(r'\x1b(?P<name>\w+)\x1c(?P<argument>[^\x1b\x1c\x1d]*)\x1d')


# class IncludeInfo(NamedTuple):
#     begin: int
#     length: int
#     file_name: str

# collections.namedtuple needed for Cython compatbility
IncludeInfo = namedtuple('IncludeInfo',
    ['begin',       ## type: int
     'length',      ## type: int
     'file_name'],  ## type: str
    module=__name__)


def has_includes(sm: SourceMap) -> bool:
    return any(fname != sm.original_name for fname in sm.file_names)


# class PreprocessorResult(NamedTuple):
#     original_text: Union[str, StringView]
#     preprocessed_text: Union[str, StringView]
#     back_mapping: SourceMapFunc
#     errors: List[Error]

# collections.namedtuple needed for Cython compatbility
PreprocessorResult = namedtuple('PreprocessorResult',
    ['original_text',      ## type: Union[str, StringView]
     'preprocessed_text',  ## type: Union[str, StringView]
     'back_mapping',       ## type: SourceMapFunc
     'errors'],            ## type: List[Error]
    module=__name__)


FindIncludeFunc: TypeAlias = Union[Callable[[str, int], IncludeInfo],   # (document: str,  start: int)
                                   functools.partial]
DeriveFileNameFunc: TypeAlias = Union[Callable[[str], str], functools.partial]  # include name -> file name
PreprocessorFunc: TypeAlias = Union[Callable[[str, str], PreprocessorResult],  # text: str, filename: str
                                    functools.partial]
Tokenizer: TypeAlias = Union[Callable[[str], Tuple[str, List[Error]]],
                             functools.partial]

# a functions that merely adds preprocessor tokens to a source text


#######################################################################
#
# Chaining of preprocessors
#
#######################################################################


def nil_preprocessor(original_text: str, original_name: str) -> PreprocessorResult:
    """
    A preprocessor that does nothing, i.e. just returns the input.
    """
    return PreprocessorResult(original_text,
                              original_text,
                              lambda i: SourceLocation(original_name, original_text, i),
                              [])


def _apply_mappings(position: int, mappings: List[SourceMapFunc]) -> SourceLocation:
    """
    Sequentially apply a number of mapping functions to a source position.
    In the context of source mapping, the source position usually is a
    position within a preprocessed source text and mappings should therefore
    be a list of reverse-mappings in reversed order.
    """
    assert mappings
    filename, text = '', ''
    for mapping in mappings:
        filename, text, position = mapping(position)
    return SourceLocation(filename, text, position)


def _apply_preprocessors(original_text: str, original_name: str,
                         preprocessors: Tuple[PreprocessorFunc, ...]) \
        -> PreprocessorResult:
    """
    Applies several preprocessing functions sequentially to a source text
    and returns the preprocessed text as well as a function that maps text-
    positions in the processed text onto the corresponding position in the
    original source test.
    """
    processed = original_text
    mapping_chain = []
    error_list = []
    for prep in preprocessors:
        _, processed, mapping_func, errors = prep(processed, original_name)
        if errors:
            if mapping_chain:
                chain = mapping_chain.copy()
                chain.reverse()
            else:
                chain = [gen_neutral_srcmap_func(original_text, original_name)]
            add_source_locations(errors, functools.partial(_apply_mappings, mappings=chain))
        mapping_chain.append(mapping_func)
        error_list.extend(errors)
    mapping_chain.reverse()
    return PreprocessorResult(
        original_text, processed,
        functools.partial(_apply_mappings, mappings=mapping_chain),
        error_list)


def chain_preprocessors(*preprocessors) -> PreprocessorFunc:
    """
    Merges a sequence of preprocessor functions in to a single function.
    """
    if any(prep is preprocess_includes for prep in preprocessors[1:]):
        raise ValueError("The preprocessor for include files must be applied first, "
                         "and there can be no more than one preprocessor for includes.")
    return functools.partial(_apply_preprocessors, preprocessors=preprocessors)


#######################################################################
#
# Tokenization support
#
# In DHParser the source text is usually not tokenized, but,
# optionally, it can be enriched by tokens (or parts of it replaced
# by tokens) to, say indicate beginnings and endings of indented
# or quoted blocks that are difficult to capture with an EBNF-parser.
#
######################################################################


def make_token(token: str, argument: str = '') -> str:
    """
    Turns the ``token`` and ``argument`` into a special token that
    will be caught by the ``PreprocessorToken``-parser.

    This function is a support function that should be used by
    preprocessors to inject preprocessor tokens into the source text.
    """
    assert RX_TOKEN_NAME.match(token)
    assert RX_TOKEN_ARGUMENT.match(argument)

    return BEGIN_TOKEN + token + TOKEN_DELIMITER + argument + END_TOKEN


def prettyprint_tokenized(tokenized: str) -> str:
    """Returns a pretty-printable version of a document that contains tokens."""
    return tokenized.replace('\x1b', '<').replace('\x1c', '|').replace('\x1d', '>')


def strip_tokens(tokenized: str) -> str:
    """Replaces all tokens with the token's arguments."""
    result = []
    pos = 0
    match = RX_TOKEN.search(tokenized, pos)
    while match:
        start, end = match.span()
        result.append(tokenized[pos:start])
        result.append(match.groupdict()['argument'])
        pos = end
        match = RX_TOKEN.search(tokenized, pos)
    result.append(tokenized[pos:])
    return ''.join(result)


#######################################################################
#
# Source Maps - mapping source code positions between different
#               transformations of the source text
#
#######################################################################


def gen_neutral_srcmap_func(original_text: Union[StringView, str], original_name: str = '') -> SourceMapFunc:
    """Generates a source map function that maps positions to itself."""
    if not original_name:  original_name = 'UNKNOWN_FILE'
    return lambda pos: SourceLocation(original_name, original_text, pos)


def tokenized_to_original_mapping(tokenized_text: str,
                                  original_text: str,
                                  original_name: str = 'UNKNOWN_FILE') -> SourceMap:
    """
    Generates a source map for mapping positions in a text that has
    been enriched with token markers to their original positions.

    :param tokenized_text:  the source text enriched with token markers
    :param original_text: the original source text
    :param original_name:  the name or path or uri of the original source file
    :returns:  a source map, i.e. a list of positions and a list of corresponding
        offsets. The list of positions is ordered from smallest to highest.
        An offset is valid for its associated position and all following
        positions until (and excluding) the next position in the list of
        positions.
    """
    positions, offsets = [0], [0]
    o = 0
    i = tokenized_text.find(BEGIN_TOKEN)
    e = -2
    while i >= 0:
        d = tokenized_text.find(TOKEN_DELIMITER, i)
        e = tokenized_text.find(END_TOKEN, i)
        assert 0 <= d < e
        o -= (d - i + 2)
        positions.extend([d + 1, e + 1])
        offsets.extend([o + 1, o])
        i = tokenized_text.find(BEGIN_TOKEN, e + 1)
    if e + 1 < len(tokenized_text):
        positions.append(len(tokenized_text) + 1)
        offsets.append(offsets[-1])

    # post conditions
    assert len(positions) == len(offsets), '\n' + str(positions) + '\n' + str(offsets)
    assert positions[0] == 0
    assert all(positions[i] < positions[i + 1] for i in range(len(positions) - 1))

    # specific condition for preprocessor tokens
    assert all(offsets[i] > offsets[i + 1] for i in range(len(offsets) - 2))

    L = len(positions)
    return SourceMap(
        original_name, positions, offsets, [original_name] * L, {original_name: original_text})


def source_map(position: int, srcmap: SourceMap) -> SourceLocation:
    """
    Maps a position in a (pre-)processed text to its corresponding
    position in the original document according to the given source map.

    :param  position: the position in the processed text
    :param  srcmap:  the source map, i.e. a mapping of locations to offset values
        and source texts.
    :returns:  the mapped position
    """
    i = bisect.bisect_right(srcmap.positions, position)
    if i:
        original_name = srcmap.file_names[i - 1]
        return SourceLocation(
            original_name,
            srcmap.originals_dict[original_name],
            min(position + srcmap.offsets[i - 1], srcmap.positions[i] + srcmap.offsets[i]))
    raise ValueError


def make_preprocessor(tokenizer: Tokenizer) -> PreprocessorFunc:
    """Generates a preprocessor function from a "naive" tokenizer, i.e.
    a function that merely adds preprocessor tokens to a source text and
    returns the modified source.
    """
    def preprocessor(original_text: str, original_name: str, *args) \
            -> PreprocessorResult:
        tokenized_text, errors = tokenizer(original_text)
        srcmap = tokenized_to_original_mapping(tokenized_text, original_text, original_name)
        mapping = functools.partial(source_map, srcmap=srcmap)
        return PreprocessorResult(original_text, tokenized_text, mapping, errors)
    return preprocessor


#######################################################################
#
# Includes - support for chaining source texts via an in clude command
#
#######################################################################


def gen_find_include_func(rx: Union[str, Any],
                          comment_rx: Optional[Union[str, Any]] = None,
                          derive_file_name: DeriveFileNameFunc = lambda name: name) \
                          -> FindIncludeFunc:
    """Generates a function to find include-statements in a file.

    :param rx: A regular expression (either as string or compiled
        regular expression) to catch the names of the includes in
        a document. The expression should catch
    """
    if isinstance(rx, str):  rx = re.compile(rx)
    if isinstance(comment_rx, str):  comment_rx = re.compile(comment_rx)

    def find_include(text: str, begin: int) -> IncludeInfo:
        nonlocal rx
        m = rx.search(text, begin)
        if m:
            begin = m.start()
            file_name = derive_file_name(m.group('name'))
            return IncludeInfo(begin, m.end() - begin, file_name)
        else:
            return IncludeInfo(-1, 0, '')

    def find_comment(text: str, begin: int) -> Tuple[int, int]:
        m = comment_rx.search(text, begin)
        return m.span() if m else (-1, -2)

    def meta_find_include(text: str, begin: int) -> IncludeInfo:
        a, b = find_comment(text, begin)
        info = find_include(text, begin)
        k, length, name = info
        while a < b <= k:
            a, b = find_comment(text, b)
        while (a < k < b) or (a < k + length < b):
            info = find_include(text, b)
            k, length, name = info
            while a < b <= k:
                a, b = find_comment(text, b)
        return info

    return find_include if comment_rx is None else meta_find_include


def generate_include_map(original_name: str,
                         original_text: str,
                         find_next_include: FindIncludeFunc) -> Tuple[SourceMap, str]:
    file_names: set = set()

    def generate_map(source_name, source_text, find_next) -> Tuple[SourceMap, str]:
        nonlocal file_names
        map = SourceMap(source_name, [0], [0], [source_name], {source_name: source_text})
        result = []

        if source_name in file_names:
            raise ValueError(f'Circular include of {source_name} detected!')
        file_names.add(source_name)

        dirname = os.path.dirname(source_name)
        original_pointer = 0
        original_offset = 0
        result_pointer = 0
        last_begin = -1
        begin, length, include_name = find_next(source_text, 0)
        include_name = os.path.join(dirname, include_name)
        while begin >= 0:
            assert begin > last_begin
            source_delta = begin - original_pointer
            original_pointer += source_delta
            result_pointer += source_delta
            with open(include_name, 'r', encoding='utf-8') as f:
                included_text = f.read()
            inner_map, inner_text = generate_map(include_name, included_text, find_next)
            assert len(inner_map.positions) == len(inner_map.offsets) == len(inner_map.file_names)
            for i in range(len(inner_map.positions)):
                inner_map.positions[i] += result_pointer
                inner_map.offsets[i] -= result_pointer
            if source_delta == 0:
                map.file_names.pop()
                map.positions.pop()
                map.offsets.pop()
            else:
                result.append(source_text[original_pointer - source_delta: original_pointer])
            map.file_names.extend(inner_map.file_names[:-1])
            map.positions.extend(inner_map.positions[:-1])
            map.offsets.extend(inner_map.offsets[:-1])
            map.originals_dict.update(inner_map.originals_dict)
            result.append(inner_text)
            inner_length = len(inner_text)
            result_pointer += inner_length
            map.file_names.append(source_name)
            map.positions.append(result_pointer)
            original_pointer += length
            original_offset += length - inner_length
            map.offsets.append(original_offset)
            begin, length, include_name = find_next(source_text, original_pointer)
            include_name = os.path.join(dirname, include_name)
        rest = source_text[original_pointer:]
        if rest:
            result.append(rest)
            map.positions.append(map.positions[-1] + len(rest))
            map.offsets.append(original_offset)
            map.file_names.append(source_name)
        file_names.remove(source_name)
        # map.file_offsets = [-offset for offset in map.offsets]  # only for debugging!
        return map, ''.join(result)

    return generate_map(original_name, original_text, find_next_include)


def srcmap_includes(position: int, inclmap: SourceMap) -> SourceLocation:
    i = bisect.bisect_right(inclmap.positions, position)
    if i:
        source_name = inclmap.file_names[i - 1]
        return SourceLocation(
            source_name,
            inclmap.originals_dict[source_name],
            position + inclmap.offsets[i - 1])
    raise ValueError


def preprocess_includes(original_text: Optional[str],
                        original_name: str,
                        find_next_include: FindIncludeFunc) -> PreprocessorResult:
    if not original_text:
        with open(original_name, 'r', encoding='utf-8') as f:
            original_text = f.read()
    include_map, result = generate_include_map(original_name, original_text, find_next_include)
    mapping_func = functools.partial(srcmap_includes, inclmap=include_map)
    return PreprocessorResult(original_text, result, mapping_func, [])

