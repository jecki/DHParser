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


import bisect
import functools
import os
from typing import Union, Optional, Callable, Tuple, NamedTuple, List, Any

from DHParser.toolkit import re, dataclasses


__all__ = ('RX_TOKEN_NAME',
           'BEGIN_TOKEN',
           'TOKEN_DELIMITER',
           'END_TOKEN',
           'SourceMap',
           'SourceMapFunc',
           'PreprocessorFunc',
           'Preprocessed',
           'PreprocessorResult',
           'make_token',
           'strip_tokens',
           'nil_preprocessor',
           'chain_preprocessors',
           'prettyprint_tokenized',
           'neutral_mapping',
           'tokenized_to_original_mapping',
           'source_map',
           'with_source_mapping',
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


@dataclasses.dataclass
class SourceMap:
    source_name: str       # nome or path or uri of the original source file
    positions: List[int]   # a list of locations
    offsets: List[int]     # the corresponding offsets to be added from these locations onward


class SourceLocation(NamedTuple):
    source_name: str  # the file name (or path or uri) of the source code
    pos: int   # a position within this file


SourceMapFunc = Union[Callable[[int], SourceLocation],
                      functools.partial]


class Preprocessed(NamedTuple):
    preprocessed_text: str
    back_mapping: SourceMapFunc


@dataclasses.dataclass
class IncludeMap(SourceMap):
    file_names: List[str]  # list of file_names to which the source locations relate

    def has_includes(self) -> bool:
        return any(fname != self.source_name for fname in self.file_names)


class IncludeInfo(NamedTuple):
    begin: int
    length: int
    file_name: str


PreprocessorResult = Union[str, Preprocessed]


FindIncludeFunc = Union[Callable[[str, int], IncludeInfo],   # (document: str,  start: int)
                        functools.partial]
PreprocessorFunc = Union[Callable[[str, str], PreprocessorResult],  # text: str, filename: str
                         functools.partial]


#######################################################################
#
# Chaining of preprocessors
#
#######################################################################


def nil_preprocessor(source_text: str, source_name: str) -> Preprocessed:
    """
    A preprocessor that does nothing, i.e. just returns the input.
    """
    return Preprocessed(source_text, lambda i: SourceLocation(source_name, i))


def _apply_mappings(position: int, mappings: List[SourceMapFunc]) -> SourceLocation:
    """
    Sequentially apply a number of mapping functions to a source position.
    In the context of source mapping, the source position usually is a
    position within a preprocessed source text and mappings should therefore
    be a list of reverse-mappings in reversed order.
    """
    filename = ''
    for mapping in mappings:
        filename, position = mapping(position)
    return SourceLocation(filename, position)


def _apply_preprocessors(source_text: str, source_name: str,
                         preprocessors: Tuple[PreprocessorFunc, ...]) \
        -> Preprocessed:
    """
    Applies several preprocessing functions sequentially to a source text
    and returns the preprocessed text as well as a function that maps text-
    positions in the processed text onto the corresponding position in the
    original source test.
    """
    processed = source_text
    mapping_chain = []
    for prep in preprocessors:
        processed, mapping_func = with_source_mapping(prep(processed, source_name))
        mapping_chain.append(mapping_func)
    mapping_chain.reverse()
    return Preprocessed(processed, functools.partial(_apply_mappings, mappings=mapping_chain))


def chain_preprocessors(*preprocessors) -> PreprocessorFunc:
    """
    Merges a sequence of preprocessor functions in to a single function.
    """
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


def neutral_mapping(pos: int) -> SourceLocation:
    '''Maps source locations on itself and sets the source file name
    to the empty string.'''
    return SourceLocation('', pos)


def tokenized_to_original_mapping(tokenized_text: str, source_name: str='UNKNOWN_FILE') -> SourceMap:
    """
    Generates a source map for mapping positions in a text that has
    been enriched with token markers to their original positions.

    :param tokenized_text:  the source text enriched with token markers.
    :poram source_name:  the name or path or uri of the original source file.
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

    return SourceMap(source_name, positions, offsets)


def source_map(position: int, srcmap: SourceMap) -> SourceLocation:
    """
    Maps a position in a (pre-)processed text to its corresponding
    position in the original document according to the given source map.

    :param  position: the position in the processed text
    :param  srcmap:  the source map, i.e. a mapping of locations to offset values
    :returns:  the mapped position
    """
    i = bisect.bisect_right(srcmap.positions, position)
    if i:
        return SourceLocation(
            srcmap.source_name,
            min(position + srcmap.offsets[i - 1], srcmap.positions[i] + srcmap.offsets[i]))
    raise ValueError


def with_source_mapping(result: PreprocessorResult) -> Preprocessed:
    """
    Normalizes preprocessors results, by adding a mapping if a preprocessor
    only returns the transformed source code and no mapping by itself. It is
    assumed that in this case the preprocessor has just enriched the source
    code with tokens, so that a source mapping can be derived automatically
    with :func:`tokenized_to_original_mapping` (see above).

    :param result:  Either a preprocessed text as atring containing
            preprocessor tokens, or a tuple of a preprocessed text AND a source
            mapping function. In the former case the source mapping will be
            generated, in the latter it will simply be passed through.
    :returns:  A tuple of the preprocessed text and the source-mapping function
            that returns the original text position when called with a position
            in the preprocessed text.
    """
    if isinstance(result, str):
        srcmap = tokenized_to_original_mapping(result)
        token_mapping = functools.partial(source_map, srcmap=srcmap)
        return Preprocessed(result, token_mapping)
    # else: # DOES NOT WORK, because there is no way to reliably find out whether
    #       # token back-mapping has already been done by the provided mapping
    #     text, mapping = cast(Preprocessed, result)
    #     if not (hasattr(mapping, 'func') and mapping.func == source_map):
    #         srcmap = tokenized_to_original_mapping(text)
    #         token_mapping = functools.partial(source_map, srcmap=srcmap)
    #         return Preprocessed(
    #             text, functools.partial(_apply_mappings, mappings=[token_mapping, mapping]))
    return result


#######################################################################
#
# Includes - support for chaining source texts via an in clude command
#
#######################################################################


def gen_find_include_func(rx: Union[str, Any],
                          comment_rx: Optional[Union[str, Any]] = None) -> FindIncludeFunc:
    if isinstance(rx, str):  rx = re.compile(rx)
    if isinstance(comment_rx, str):  comment_rx = re.compile(comment_rx)

    def find_include(text: str, begin: int) -> IncludeInfo:
        nonlocal rx
        m = rx.search(text, begin)
        if m:
            begin = m.start()
            return IncludeInfo(begin, m.end() - begin, m.group('name'))
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


def generate_include_map(source_name: str,
                         source_text: str,
                         find_next_include: FindIncludeFunc) -> Tuple[IncludeMap, str]:
    file_names: set = set()

    def generate_map(source_name, source_text, find_next) -> Tuple[IncludeMap, str]:
        nonlocal file_names
        map = IncludeMap(source_name, [0], [0], [source_name])
        result = []

        if source_name in file_names:
            raise ValueError(f'Circular include of {source_name} detected!')
        file_names.add(source_name)

        dirname = os.path.dirname(source_name)
        source_pointer = 0
        source_offset = 0
        result_pointer = 0
        last_begin = -1
        begin, length, include_name = find_next(source_text, 0)
        include_name = os.path.join(dirname, include_name)
        while begin >= 0:
            assert begin > last_begin
            source_delta = begin - source_pointer
            source_pointer += source_delta
            result_pointer += source_delta
            with open(include_name, 'r', encoding='utf-8') as f:
                included_text = f.read()
            inner_map, inner_text = generate_map(include_name, included_text, find_next)
            inner_map.positions = [pos + result_pointer for pos in inner_map.positions]
            inner_map.offsets = [offset - result_pointer for offset in inner_map.offsets]
            if source_delta == 0:
                map.file_names = map.file_names[:-1] + inner_map.file_names[:-1]
                map.positions = map.positions[:-1] + inner_map.positions[:-1]
                map.offsets = map.offsets[:-1] + inner_map.offsets[:-1]
                result.append(inner_text)
            else:
                result.append(source_text[source_pointer - source_delta: source_pointer])
                map.file_names += inner_map.file_names[:-1]
                map.positions += inner_map.positions[:-1]
                map.offsets += inner_map.offsets[:-1]
                result.append(inner_text)
            inner_length = len(inner_text)
            result_pointer += inner_length
            map.file_names.append(source_name)
            map.positions.append(result_pointer)
            source_pointer += length
            source_offset += length - inner_length
            map.offsets.append(source_offset)
            begin, length, include_name = find_next(source_text, source_pointer)
            include_name = os.path.join(dirname, include_name)
        rest = source_text[source_pointer:]
        if rest:
            result.append(rest)
            map.positions.append(map.positions[-1] + len(rest))
            map.offsets.append(source_offset)
            map.file_names.append(source_name)
        file_names.remove(source_name)
        return map, ''.join(result)

    return generate_map(source_name, source_text, find_next_include)


def srcmap_includes(position: int, inclmap: IncludeMap) -> SourceLocation:
    i = bisect.bisect_right(inclmap.positions, position)
    if i:
        return SourceLocation(
            inclmap.file_names[i - 1],
            position + inclmap.offsets[i - 1])
    raise ValueError


def preprocess_includes(source_text: Optional[str],
                        source_name: str,
                        find_next_include: FindIncludeFunc) -> Preprocessed:
    if not source_text:
        with open(source_name, 'r', encoding='utf-8') as f:
            source_text = f.read()
    include_map, result = generate_include_map(source_name, source_text, find_next_include)
    mapping_func = functools.partial(srcmap_includes, inclmap=include_map)
    return Preprocessed(result, mapping_func)


