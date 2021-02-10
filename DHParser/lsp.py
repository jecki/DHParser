# lsp.py - Language Server Protocol data structures and support functions
#
# Copyright 20w0  by Eckhart Arnold (arnold@badw.de)
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

"""Module lsp.py defines (some of) the constants and data structures from
the Language Server Protocol. See:
<https://microsoft.github.io/language-server-protocol/specifications/specification-current/>

EXPERIMENTAL
"""


import bisect
import enum
from typing import List, Tuple, Any, Iterator, Union, Iterable, Callable

#######################################################################
#
# Language-Server-Protocol data structures
#
#######################################################################
from DHParser.server import RPC_Table


class TextDocumentSyncKind(enum.IntEnum):
    none = 0        # None with a capital "N" is already a Python keyword
    Full = 1
    Incremental = 2


class CompletionTriggerKind(enum.IntEnum):
    Invoked = 1
    TriggerCharacter = 2
    TriggerForIncompleteCompletions = 3


class CompletionItemKind(enum.IntEnum):
    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18
    Folder = 19
    EnumMember = 20
    Constant = 21
    Struct = 22
    Event = 23
    Operator = 24
    TypeParameter = 25

class InsertTextFormat(enum.IntEnum):
    PlainText = 1
    Snippet = 2


#######################################################################
#
# Language-Server-Protocol functions
#
#######################################################################


# general #############################################################

# def get_lsp_methods(cls: Any, prefix: str= 'lsp_') -> List[str]:
#     """Returns the language-server-protocol-method-names from class `cls`.
#     Methods are selected based on the prefix and their name converted in
#     accordance with the LSP-specification."""
#     return [gen_lsp_name(fn, prefix) for fn in lsp_candidates(cls, prefix)]


def lsp_candidates(cls: Any, prefix: str = 'lsp_') -> Iterator[str]:
    """Returns an iterator over all method names from a class that either
    have a certain prefix or, if no prefix was given, all non-special and
    non-private-methods of the class."""
    assert not prefix[:1] == '_'
    if prefix:
        # return [fn for fn in dir(cls) if fn.startswith(prefix) and callable(getattr(cls, fn))]
        for fn in dir(cls):
            if fn[:len(prefix)] == prefix and callable(getattr(cls, fn)):
                yield fn
    else:
        # return [fn for fn in dir(cls) if not fn.startswith('_') and callable(getattr(cls, fn))]
        for fn in dir(cls):
            if not fn[:1] == '_' and callable(getattr(cls, fn)):
                yield fn


def gen_lsp_name(func_name: str, prefix: str = 'lsp_') -> str:
    """Generates the name of an lsp-method from a function name,
    e.g. "lsp_S_cancelRequest" -> "$/cancelRequest" """
    assert func_name[:len(prefix)] == prefix
    return func_name[len(prefix):].replace('_', '/').replace('S/', '$/')


def gen_lsp_table(lsp_funcs_or_instance: Union[Iterable[Callable], Any],
                  prefix: str = 'lsp_') -> RPC_Table:
    """Creates an RPC from a list of functions or from the methods
    of a class that implement the language server protocol.
    The dictionary keys are derived from the function name by replacing an
    underscore _ with a slash / and a single capital S with a $-sign.
    if `prefix` is not the empty string only functions or methods that start
    with `prefix` will be added to the table. The prefix will be removed
    before converting the functions' name to a dictionary key.

    >>> class LSP:
    ...     def lsp_initialize(self, **kw):
    ...         pass
    ...     def lsp_shutdown(self, **kw):
    ...         pass
    >>> lsp = LSP()
    >>> gen_lsp_table(lsp, 'lsp_').keys()
    dict_keys(['initialize', 'shutdown'])
    """
    if isinstance(lsp_funcs_or_instance, Iterable):
        assert all(callable(func) for func in lsp_funcs_or_instance)
        rpc_table = {gen_lsp_name(func.__name__, prefix): func for func in lsp_funcs_or_instance}
    else:
        # assume lsp_funcs_or_instance is the instance of a class
        cls = lsp_funcs_or_instance
        rpc_table = {gen_lsp_name(fn, prefix): getattr(cls, fn)
                     for fn in lsp_candidates(cls, prefix)}
    return rpc_table


# textDocument/completion #############################################

def shortlist(long_list: List[str], typed: str, lo: int = 0, hi: int = -1) -> Tuple[int, int]:
    if not typed:
        return 0, 0
    if hi < 0:
        hi = len(long_list)
    a = bisect.bisect_left(long_list, typed, lo, hi)
    b = bisect.bisect_left(long_list, typed[:-1] + chr(ord(typed[-1]) + 1), lo, hi)
    return a, b
