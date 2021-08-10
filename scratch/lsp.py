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

EXPERIMENTAL!!!
"""


import bisect
from collections import ChainMap
from enum import Enum, IntEnum
import functools
from typing import  Union, List, Tuple, Optional, Dict, Any, Generic, TypeVar, \
    Iterator, Iterable, Callable

from DHParser.server import RPC_Table
from DHParser.toolkit import dataclasses, JSON_Type, JSON_Dict
from dataclasses import dataclass, asdict



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


# decorator for typed lsp-functions ###################################

DefValType = Dict[str, Dict[str, Any]]
RefObjType = Dict[str, Dict[str, List[Union[str, Any]]]]


def fromdict(D: JSON_Dict, DataClass: Any, keep_dict=True):
    name = DataClass.__name__
    if hasattr(DataClass, 'references__') and name in DataClass.references__:
        references = DataClass.references__
    else:
        try:
            references = DataClass.references__
        except AttributeError:
            DataClass.references__ = {}
            references = DataClass.references
        for key, value in D.items():
            if isinstance(value, Dict):
                typ = DataClass.__annotations__[key]
                if isinstance(typ, str):
                    typ = eval(typ)
                references[key] = typ
        DataClass.references__[name] = references
    if references:
        if keep_dict:  D = D.copy()
        for field, types in references.items():
            for i in range(len(types)):
                typ = types[i]
                if isinstance(typ, str):
                    typ = eval(typ)
                    references[field][i] = typ
                try:
                    D[field] = fromdict(D[field], typ)
                    break
                except TypeError:
                    pass
    default_values = DataClass.defaults__ if hasattr(DataClass, 'defaults__') else {}
    return DataClass(**ChainMap(D, default_values.get(name, {})))


def typed_lsp(lsp_function):
    params = lsp_function.__annotations__
    if len(params) != 2 or 'return' not in params:
        raise ValueError(f'Decorator "typed_lsp" does not work with function '
            f'"{lsp_function.__name__}" annotated with "{params}"! '
            f'LSP functions can have at most one argument. Both the type of the '
            f' argument and the return type must be specified with annotations.')
    return_type = params['return']
    for k in params.items():
        if k != 'return':
            call_type = params[k]
            break
    ct_is_str = isinstance(call_type, str)
    call_type_name = call_type if ct_is_str else call_type.__name__
    rt_is_str = isinstance(return_type, str)
    return_type_name = return_type if rt_is_str else return_type.__name__
    resolve_types = ct_is_str or rt_is_str

    @functools.wraps(lsp_function)
    def type_guard(*args, **kwargs):
        global default_values, referred_objects
        nonlocal resolve_types, return_type, call_type, call_type_name, return_type_name
        if resolve_types:
            if isinstance(call_type, str):  call_type = eval(call_type)
            if isinstance(return_type, str):  return_type = eval(return_type)
            resolve_types = False
        dict_obj = args[0] if args else kwargs
        call_obj = fromdict(call_type, dict_obj, default_values, referred_objects)
        dict_val = lsp_function(call_type(**dict_obj))
        return asdict(dict_val)

    return type_guard


#######################################################################
#
# Language-Server-Protocol data structures
#
#######################################################################

