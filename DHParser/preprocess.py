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
for some domain specific languages, most notable those that
cannot completely be described with context-free grammars.
"""


import bisect
import collections
import functools

from DHParser.toolkit import re, typing
from typing import Union, Callable, Tuple, List


__all__ = ('RX_TOKEN_NAME',
           'BEGIN_TOKEN',
           'TOKEN_DELIMITER',
           'END_TOKEN',
           'SourceMapFunc',
           'PreprocessorFunc',
           'PreprocessorResult',
           'make_token',
           'strip_tokens',
           'nil_preprocessor',
           'chain_preprocessors',
           'prettyprint_tokenized',
           'SourceMap',
           'tokenized_to_original_mapping',
           'source_map',
           'with_source_mapping')

BEGIN_TOKEN = '\x1b'
TOKEN_DELIMITER = '\x1c'
END_TOKEN = '\x1d'
RESERVED_TOKEN_CHARS = BEGIN_TOKEN + TOKEN_DELIMITER + END_TOKEN

RX_TOKEN_NAME = re.compile(r'\w+')
RX_TOKEN_ARGUMENT = re.compile(r'[^\x1b\x1c\x1d]*')
RX_TOKEN = re.compile(r'\x1b(?P<name>\w+)\x1c(?P<argument>[^\x1b\x1c\x1d]*)\x1d')

SourceMapFunc = Union[Callable[[int], int], functools.partial]
PreprocessorResult = Union[str, Tuple[str, SourceMapFunc]]
PreprocessorFunc = Union[Callable[[str], PreprocessorResult], functools.partial]


def nil_preprocessor(text: str) -> Tuple[str, SourceMapFunc]:
    """
    A preprocessor that does nothing, i.e. just returns the input.
    """
    return text, lambda i: i


def _apply_mappings(position: int, mappings: List[SourceMapFunc]) -> int:
    """
    Sequentially apply a number of mapping functions to a source position.
    In the context of source mapping, the source position usually is a
    position within a preprocessed source text and mappings should therefore
    be a list of reverse-mappings in reversed order.
    """
    for mapping in mappings:
        position = mapping(position)
    return position


def _apply_preprocessors(text: str, preprocessors: Tuple[PreprocessorFunc, ...]) \
        -> Tuple[str, SourceMapFunc]:
    """
    Applies several preprocessing functions sequentially to a source text
    and returns the preprocessed text as well as a function that maps text-
    positions in the processed text onto the corresponding position in the
    original source test.
    """
    processed = text
    mapping_chain = []
    for prep in preprocessors:
        processed, mapping_func = with_source_mapping(prep(processed))
        mapping_chain.append(mapping_func)
    mapping_chain.reverse()
    return processed, functools.partial(_apply_mappings, mappings=mapping_chain)


def chain_preprocessors(*preprocessors) -> PreprocessorFunc:
    """
    Merges a seuqence of preprocessor functions in to a single function.
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


SourceMap = collections.namedtuple('SourceMap', ['positions', 'offsets'])


def tokenized_to_original_mapping(tokenized_source: str) -> SourceMap:
    """
    Generates a source map for mapping positions in a text that has
    been enriched with token markers to their original positions.

    Args:
        tokenized_source: the source text enriched with token markers
    Returns:
        a source map, i.e. a list of positions and a list of corresponding
        offsets. The list of positions is ordered from smallest to highest.
        An offset is valid for its associated position and all following
        positions until (and excluding) the next position in the list of
        positions.
    """
    positions, offsets = [0], [0]
    o = 0
    i = tokenized_source.find(BEGIN_TOKEN)
    e = -1
    while i >= 0:
        d = tokenized_source.find(TOKEN_DELIMITER, i)
        e = tokenized_source.find(END_TOKEN, i)
        assert 0 <= d < e
        o -= (d - i + 2)
        positions.extend([d + 1, e + 1])
        offsets.extend([o + 1, o])
        i = tokenized_source.find(BEGIN_TOKEN, e + 1)
    if e + 1 < len(tokenized_source):
        positions.append(len(tokenized_source))
        offsets.append(offsets[-1])

    # post conditions
    assert len(positions) == len(offsets), '\n' + str(positions) + '\n' + str(offsets)
    assert positions[0] == 0
    assert all(positions[i] < positions[i + 1] for i in range(len(positions) - 1))
    assert all(offsets[i] > offsets[i + 1] for i in range(len(offsets) - 2))

    return SourceMap(positions, offsets)


def source_map(position: int, srcmap: SourceMap) -> int:
    """
    Maps a position in a (pre-)processed text to its corresponding
    position in the original document according to the given source map.

    Args:
        position: the position in the processed text
        srcmap:   the source map, i.e. a mapping of locations to offset values
    Returns:
        the mapped position
    """
    i = bisect.bisect_right(srcmap.positions, position)
    if i:
        return min(position + srcmap.offsets[i - 1], srcmap.positions[i] + srcmap.offsets[i])
    raise ValueError


def with_source_mapping(result: PreprocessorResult) -> Tuple[str, SourceMapFunc]:
    """
    Normalizes preprocessors results, by adding a mapping if a preprocessor
    only returns the transformed source code and no mapping by itself. It is
    assumed that in this case the preprocessor has just enriched the source
    code with tokens, so that a source mapping can be derived automatically
    with :func:`tokenized_to_original_mapping` (see above).
    """
    if isinstance(result, str):
        srcmap = tokenized_to_original_mapping(result)
        mapping_func = functools.partial(source_map, srcmap=srcmap)
        return result, mapping_func
    return result
