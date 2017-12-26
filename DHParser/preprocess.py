""" preprocess.py - preprocessing of source files for DHParser

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
"""

import bisect
import collections
import functools
from typing import Union, Callable

from DHParser.toolkit import re

__all__ = ('RX_TOKEN_NAME',
           'BEGIN_TOKEN',
           'TOKEN_DELIMITER',
           'END_TOKEN',
           'PreprocessorFunc',
           'make_token',
           'nil_preprocessor',
           'pp_tokenized',
           'tokenized_to_original_mapping',
           'source_map')

BEGIN_TOKEN = '\x1b'
TOKEN_DELIMITER = '\x1c'
END_TOKEN = '\x1d'
RESERVED_TOKEN_CHARS = BEGIN_TOKEN + TOKEN_DELIMITER + END_TOKEN

RX_TOKEN_NAME = re.compile(r'\w+')
RX_TOKEN_ARGUMENT = re.compile(r'[^\x1b\x1c\x1d]*')
RX_TOKEN = re.compile(r'\x1b(?P<name>\w+)\x1c(?P<argument>[^\x1b\x1c\x1d]*)\x1d')

PreprocessorFunc = Union[Callable[[str], str], functools.partial]


def make_token(token: str, argument: str = '') -> str:
    """
    Turns the ``token`` and ``argument`` into a special token that
    will be caught by the `PreprocessorToken`-parser.

    This function is a support function that should be used by
    preprocessors to inject preprocessor tokens into the source text.
    """
    assert RX_TOKEN_NAME.match(token)
    assert RX_TOKEN_ARGUMENT.match(argument)

    return BEGIN_TOKEN + token + TOKEN_DELIMITER + argument + END_TOKEN


def nil_preprocessor(text: str) -> str:
    """A preprocessor that does nothing, i.e. just returns the input."""
    return text


def pp_tokenized(tokenized: str) -> str:
    """Returns a pretty-printable version of a document that contains tokens."""
    return tokenized.replace('\x1b', '<').replace('\x1c', '|').replace('\x1d', '>')


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
    while i >= 0:
        d = tokenized_source.find(TOKEN_DELIMITER, i)
        e = tokenized_source.find(END_TOKEN, i)
        assert 0 <= d < e
        o -= (d - i + 3)
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
    assert all(offsets[i] >= offsets[i + 1] for i in range(len(offsets) - 1))

    return SourceMap(positions, offsets, len(positions))


def source_map(position: int, srcmap: SourceMap) -> int:
    """
    Maps a position in a (pre-)processed text to its corresponding
    position in the original document according to the given source map.

    Args:
        position: the position in the processed text
        srcmap:   the source map, i.e. a mapping of locations to
                  offset values
    Returns:
        the mapped position
    """
    i = bisect.bisect_right(srcmap.positions, position)
    if i:
        return min(position + srcmap.offsets[i - 1], srcmap.positions[i] + srcmap.offsets[i])
    raise ValueError

# TODO: allow preprocessors to return their own source map (really a map or a function (easier)?)
# TODO: apply source maps in sequence.
