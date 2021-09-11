"""validation.py - contains an alternative implementation of TypedDict
    that allows to specify individual fields as optional - and
    validation functions and decorators that put these to use.

STL's TypeDict merely supports classifying all fields of a TypedDict
class as either required or optional. This TypedDict implementation
classifies fields as optional if their type is annotated as
"Optional[...]" or "Union[..., None]".

Copyright 2021  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.
"""


import functools
import sys
from typing import Any, Union, Dict, Tuple, Iterable, Callable, get_type_hints
try:
    from typing import ForwardRef, _GenericAlias, _SpecialForm
except ImportError:
    from typing import _ForwardRef, GenericMeta  # Python 3.6 compatibility
    ForwardRef = _ForwardRef
    _GenericAlias = GenericMeta
    _SpecialForm = GenericMeta
from typing_extensions import Generic, ClassVar, Final, Protocol, NoReturn, \
    TypeVar, TypedDict, PEP_560
try:
   from typing_extensions import get_origin
except ImportError:
    def get_origin(typ):
        return typ.__origin__


# The following functions have been copied from the Python
# standard libraries typing-module. They have been adapted
# to support a more flexible version of TypedDict
# see also: <https://www.python.org/dev/peps/pep-0655/>

def _type_convert(arg, module=None):
    """For converting None to type(None), and strings to ForwardRef."""
    if arg is None:
        return type(None)
    if isinstance(arg, str):
        fwref = ForwardRef(arg)
        if hasattr(fwref, '__forward_module__'):
            fwref.__forward_module__ = module
        return fwref
    return arg


def _type_check(arg, msg, is_argument=True, module=None):
    """Check that the argument is a type, and return it (internal helper).
    As a special case, accept None and return type(None) instead. Also wrap strings
    into ForwardRef instances. Consider several corner cases, for example plain
    special forms like Union are not valid, while Union[int, str] is OK, etc.
    The msg argument is a human-readable error message, e.g::
        "Union[arg, ...]: arg should be a type."
    We append the repr() of the actual value (truncated to 100 chars).
    """
    invalid_generic_forms = (Generic, Protocol)
    if is_argument:
        invalid_generic_forms = invalid_generic_forms + (ClassVar, Final)

    arg = _type_convert(arg, module=module)
    if (isinstance(arg, _GenericAlias) and
            arg.__origin__ in invalid_generic_forms):
        raise TypeError(f"{arg} is not valid as type argument")
    if arg in (Any, NoReturn):
        return arg
    if isinstance(arg, _SpecialForm) or arg in (Generic, Protocol):
        raise TypeError(f"Plain {arg} is not valid as type argument")
    if isinstance(arg, (type, TypeVar, ForwardRef)):
        return arg
    if not callable(arg):
        raise TypeError(f"{msg} Got {arg!r:.100}.")
    return arg


def _caller(depth=1, default='__main__'):
    try:
        return sys._getframe(depth + 1).f_globals.get('__name__', default)
    except (AttributeError, ValueError):  # For platforms without _getframe()
        return None


class _TypedDictMeta(type):
    def __new__(cls, name, bases, ns, total=True):
        """Create new typed dict class object.
        This method is called when TypedDict is subclassed,
        or when TypedDict is instantiated. This way
        TypedDict supports all three syntax forms described in its docstring.
        Subclasses and instances of TypedDict return actual dictionaries.
        """
        for base in bases:
            if type(base) is not _TypedDictMeta and get_origin(base) is not Generic:
                raise TypeError('cannot inherit from both a TypedDict type '
                                'and a non-TypedDict base class')
        tp_dict = type.__new__(_TypedDictMeta, name, (dict,), ns)

        annotations = {}
        own_annotations = ns.get('__annotations__', {})
        # own_annotation_keys = set(own_annotations.keys())
        msg = "TypedDict('Name', {f0: t0, f1: t1, ...}); each t must be a type"
        own_annotations = {
            n: _type_check(tp, msg, module=tp_dict.__module__)
            for n, tp in own_annotations.items()
        }
        required_keys = set()
        optional_keys = set()

        for base in bases:
            annotations.update(base.__dict__.get('__annotations__', {}))
            required_keys.update(base.__dict__.get('__required_keys__', ()))
            optional_keys.update(base.__dict__.get('__optional_keys__', ()))

        annotations.update(own_annotations)

        total = True
        for field, field_type in own_annotations.items():
            if get_origin(field_type) is Union \
                    and type(None) in field_type.__args__:
                optional_keys.add(field)
                total = False
            else:
                required_keys.add(field)

        tp_dict.__annotations__ = annotations
        tp_dict.__required_keys__ = frozenset(required_keys)
        tp_dict.__optional_keys__ = frozenset(optional_keys)
        if not hasattr(tp_dict, '__total__'):
            tp_dict.__total__ = total
        return tp_dict

    __call__ = dict  # static method

    def __subclasscheck__(cls, other):
        # Typed dicts are only for static structural subtyping.
        raise TypeError('TypedDict does not support instance and class checks')

    __instancecheck__ = __subclasscheck__


def TypedDict(typename, fields=None, *, total=True, **kwargs):
    """A simple typed namespace. At runtime it is equivalent to a plain dict.
    TypedDict creates a dictionary type that expects all of its
    instances to have a certain set of keys, where each key is
    associated with a value of a consistent type. This expectation
    is not checked at runtime but is only enforced by type checkers.
    Usage::
        class Point2D(TypedDict):
            x: int
            y: int
            label: str
        a: Point2D = {'x': 1, 'y': 2, 'label': 'good'}  # OK
        b: Point2D = {'z': 3, 'label': 'bad'}           # Fails type check
        assert Point2D(x=1, y=2, label='first') == dict(x=1, y=2, label='first')
    The type info can be accessed via the Point2D.__annotations__ dict, and
    the Point2D.__required_keys__ and Point2D.__optional_keys__ frozensets.
    TypedDict supports two additional equivalent forms::
        Point2D = TypedDict('Point2D', x=int, y=int, label=str)
        Point2D = TypedDict('Point2D', {'x': int, 'y': int, 'label': str})
    By default, all keys must be present in a TypedDict. It is possible
    to override this by specifying totality.
    Usage::
        class point2D(TypedDict, total=False):
            x: int
            y: int
    This means that a point2D TypedDict can have any of the keys omitted.A type
    checker is only expected to support a literal False or True as the value of
    the total argument. True is the default, and makes all items defined in the
    class body be required.
    The class syntax is only supported in Python 3.6+, while two other
    syntax forms work for Python 2.7 and 3.2+
    """
    if fields is None:
        fields = kwargs
    elif kwargs:
        raise TypeError("TypedDict takes either a dict or keyword arguments,"
                        " but not both")

    ns = {'__annotations__': dict(fields)}
    module = _caller()
    if module is not None:
        # Setting correct module is necessary to make typed dict classes pickleable.
        ns['__module__'] = module

    return _TypedDictMeta(typename, (), ns)


_TypedDict = type.__new__(_TypedDictMeta, 'TypedDict', (), {})
TypedDict.__mro_entries__ = lambda bases: (_TypedDict,)

# up to this point all functions have been copied and adapted from
# the typing.py module of the Pyhton-STL

def validate_type(val: Any, typ):
    if isinstance(typ, _TypedDictMeta):
        if not isinstance(val, Dict):
            raise TypeError(f"{val} is not even a dictionary")
        validate_TypedDict(val, typ)
    elif hasattr(typ, '__args__'):
        validate_compound_type(val, typ)
    else:
        if not isinstance(val, typ):
            raise TypeError(f"{val} is not of type {typ}")


def validate_uniform_sequence(sequence: Iterable, typ):
    if isinstance(typ, _TypedDictMeta):
        for val in sequence:
            if not isinstance(val, Dict):
                raise TypeError(f"{val} is not of type {typ}")
            validate_TypedDict(val, typ)
    elif hasattr(typ, '__args__'):
        for val in sequence:
            validate_compound_type(val, typ)
    else:
        for val in sequence:
            if not isinstance(val, typ):
                raise TypeError(f"{val} is not of type {typ}")


def validate_compound_type(value: Any, T):
    assert hasattr(T, '__args__')
    if isinstance(value, get_origin(T)):
        if isinstance(value, Dict):
            assert len(T.__args__) == 2, str(T)
            key_type, value_type = T.__args__
            validate_uniform_sequence(value.keys(), key_type)
            validate_uniform_sequence(value.values(), value_type)
        elif isinstance(value, Tuple):
            if len(T.__args__) == 2 and T.__args__[-1] is Ellipsis:
                validate_uniform_sequence(value, T.__args__[0])
            else:
                if len(T.__args__) != len(value):
                    raise TypeError(f"{value} is not of type {T}")
                for item, typ in zip(value, T.__args__):
                    validate_type(item, typ)
        else:  # assume that value is of type List
            if len(T.__args__) != 1:
                raise ValueError(f"Unknown compound type {T}")
            validate_uniform_sequence(value, T)
    else:
        raise TypeError(f"{value} is not of type {get_origin(T)}")


def validate_TypedDict(D: Dict, T: _TypedDictMeta):
    assert isinstance(D, Dict), str(D)
    assert isinstance(T, _TypedDictMeta), str(T)
    type_errors = []
    missing = T.__required_keys__ - D.keys()
    if missing:
        type_errors.append(f"Missing required keys: {missing}")
    unexpected = D.keys() - (T.__required_keys__ | T.__optional_keys__)
    if unexpected:
        type_errors.append(f"Unexpected keys: {unexpected}")
    for field, field_type in get_type_hints(T).items():
        if field not in D:
            continue
        if isinstance(field_type, _TypedDictMeta):
            value = D[field]
            if isinstance(value, Dict):
                validate_TypedDict(value, field_type)
            else:
                type_errors.append(f"Field {field} is not a {field_type}")
        elif get_origin(field_type) is Union:
            value = D[field]
            for union_typ in field_type.__args__:
                if isinstance(union_typ, _TypedDictMeta):
                    if isinstance(value, Dict):
                        try:
                            validate_TypedDict(value, union_typ)
                            break
                        except TypeError:
                            pass
                elif hasattr(union_typ, '__args__'):
                    try:
                        validate_compound_type(value, union_typ)
                        break
                    except TypeError:
                        pass
                elif isinstance(value, union_typ):
                    break
            else:
                type_errors.append(f"Field {field} is not of {field_type}")
        elif hasattr(field_type, '__args__'):
            validate_compound_type(D[field], field_type)
        elif isinstance(field_type, TypeVar):
            pass  # for now
        elif not isinstance(D[field], field_type):
            type_errors.append(f"Field {field} is not a {field_type}")
    if type_errors:
        if len(type_errors) == 1:
            raise TypeError(f"Type error in dictionary of type {T}: "
                            + type_errors[0])
        else:
            raise TypeError(f"Type errors in dictionary of type {T}:\n"
                            + '\n'.join(type_errors))


def type_check(func: Callable) -> Callable:
    arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
    arg_types = get_type_hints(func)
    return_type = arg_types.get('return', None)
    if return_type is not None:  del arg_types['return']
    assert arg_types or return_type, \
        f'type_check-decorated "{func}" has no type annotations'

    @functools.wraps(func)
    def guard(*args, **kwargs):
        nonlocal arg_names, arg_types, return_type
        arg_dict = {**dict(zip(arg_names, args)), **kwargs}
        for name, typ in arg_types.items():
            try:
                validate_type(arg_dict[name], typ)
            except TypeError as e:
                raise TypeError(
                    f'Parameter "{name}" of function "{func.__name__}" failed '
                    f'the type-check, because: {str(e)}')
            except KeyError as e:
                raise TypeError(f'Missing parameter {str(e)} in call of '
                                f'"{func.__name__}"')
        ret = func(*args, **kwargs)
        if return_type:
            try:
                validate_type(ret, return_type)
            except TypeError as e:
                raise TypeError(
                    f'Value returned by function "{func.__name__}" failed '
                    f'the type-check, because: {str(e)}')
        return ret

    return guard
