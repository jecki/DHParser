class TSICheckLevel(IntEnum):
    NO_CHECK = 0        # No checks when instantiating a Type Script Interface
    ARG_CHECK = 1       # Check whether the named arguments match the given arguments
    TYPE_CHECK = 2      # In addition, check the types of the given arguments as well


TSI_DYNAMIC_CHECK = TSICheckLevel.TYPE_CHECK


def derive_types(annotation) -> Tuple:
    types = []
    if isinstance(annotation, ForwardRef):
        annotation = eval(annotation.__forward_arg__)
    elif isinstance(annotation, str):  # really needed?
        annotation = eval(annotation)
    try:
        origin = annotation.__origin__
        if origin is Union:
            for t_anno in annotation.__args__:
                types.extend(derive_types(t_anno))
        else:
            _ = annotation.__args__
            types.append(annotation.__origin__)
    except AttributeError:
        if annotation is Any:
            types.append(object)
        else:
            types.append(annotation)
    return tuple(types)


def chain_from_bases(cls, chain: str, field: str) -> Dict:
    try:
        return cls.__dict__[chain]
    except KeyError:
        chained = {}
        chained.update(getattr(cls, field, {}))
        for base in cls.__bases__:
            chained.update(getattr(base, field, {}))
        setattr(cls, chain, chained)
        return chained


class TSInterface:
    def derive_arg_types__(self, fields):
        cls = self.__class__
        assert not hasattr(cls, 'arg_types__')
        cls.arg_types__ = {param: derive_types(param_type)
                           for param, param_type in fields.items()}

    def typecheck__(self, level: TSICheckLevel):
        if level <= TSICheckLevel.NO_CHECK:  return
        # level is at least TSIContract.ARG_CHECK
        cls = self.__class__
        fields = cls.fields__
        if fields.keys() != self.__dict__.keys():
            missing = fields.keys() - self.__dict__.keys()
            wrong = self.__dict__.keys() - fields.keys()
            msgs = [f'{cls.__name__} ']
            if missing:
                msgs.append(f'missing required arguments: {", ".join(missing)}!')
            if wrong:
                msgs.append(f'got unexpected parameters: {", ".join(wrong)}!')
            raise TypeError(' '.join(msgs) + f' Received: {self.__dict__}')
        if level >= TSICheckLevel.TYPE_CHECK:
            if not hasattr(cls, 'arg_types__'):
                self.derive_arg_types__(fields)
            type_errors = [f'{arg} is not a {typ}' for arg, typ in self.arg_types__.items()
                           if (not isinstance(self.__dict__[arg], typ)
                               or (typ == [object] and self.__dict__[arg] is None))]
            if type_errors:
                raise TypeError(f'{cls.__name__} got wrong types: ' + ', '.join(type_errors))

    def __init__(self, *args, **kwargs):
        cls = self.__class__
        fields = chain_from_bases(cls, 'fields__', '__annotations__')
        args_dict = {kw: arg for kw, arg in zip(fields.keys(), args)}
        optional_fields = chain_from_bases(cls, 'optional_fields__', 'optional__')
        parameters = {**optional_fields, **kwargs, **args_dict}
        references = chain_from_bases(cls, 'all_refs__', 'references__')
        for ref, types in references.items():
            d = parameters[ref]
            if isinstance(d, (dict, tuple)):
                parameters[ref] = fromjson_obj(d, types)
        self.__dict__.update(parameters)
        self.typecheck__(TSI_DYNAMIC_CHECK)

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise ValueError(f'No field named "{key}" in {self.__class__.__name__}')

    def __eq__(self, other):
        return self.__dict__.keys() == other.__dict__.keys() \
            and all(v1 == v2 for v1, v2 in zip(self.__dict__.values(), other.__dict__.values()))

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(f'{k}={repr(v)}' for k, v in self.__dict__.items())})"

def asjson_obj(data: Union[TSInterface, JSON_Type], deepcopy: bool = False) -> JSON_Type:
    if data is None:  return None
    if isinstance(data, TSInterface):
        cls = data.__class__
        references = chain_from_bases(cls, 'all_refs__', 'references__')
        optionals = chain_from_bases(cls, 'optional_fields__', 'optional__')
        if references:
            d = {field: (asjson_obj(value, True) if field in references
                         else (copy.deepcopy(value) if deepcopy else value))
                 for field, value in data.__dict__.items()
                 if value is not None or field not in optionals}
            return d
        return copy.deepcopy(data.__dict__) if deepcopy else data.__dict__
    elif isinstance(data, (list, tuple)):
        if deepcopy or (data and isinstance(data[0], TSInterface)):  # assumes uniform list
            return [asjson_obj(item) for item in data]
        else:
            return data
    elif isinstance(data, dict):
        return {key: asjson_obj(value) for key, value in data}
    else:
        assert isinstance(data, (str, int, float, bool, None))
        return data


def asdict(data: TSInterface, deepcopy: bool = False) -> Dict:
    assert isinstance(data, TSInterface)
    result = asjson_obj(data, deepcopy)
    assert isinstance(result, Dict)
    return cast(Dict, result)


def fromjson_obj(d: JSON_Type, initial_type: List[type]) -> Union[TSInterface, JSON_Type]:
    if isinstance(d, (str, int, float, type(None))):  return d
    assert isinstance(initial_type, Iterable)
    type_errors = []
    for itype in initial_type:
        try:
            origin = getattr(itype, '__origin__', None)
            if origin is list or origin is List:
                try:
                    typ = itype.__args__[0]
                    return [fromjson_obj(item, [typ]) for item in d]
                except AttributeError:
                    return d
            if origin is dict or origin is Dict:
                try:
                    typ = initial_type.__args__[1]
                    return {key: fromjson_obj(value, [typ]) for key, value in d}
                except AttributeError:
                    return d
            assert issubclass(itype, TSInterface), str(itype)
            if isinstance(d, tuple):
                fields = chain_from_bases(itype, 'fields__', '__annotations__')
                d = {kw: arg for kw, arg in zip(fields.keys(), d)}
            references = chain_from_bases(itype, 'all_refs__', 'references__')
            refs = {field: fromjson_obj(d[field], typ)
                    for field, typ in references.items() if field in d}
            merged = {**d, **refs}
            return itype(**merged)
        except TypeError as e:
            type_errors.append(str(e))
    raise TypeError(f"No matching types for {d} among {initial_type}:\n" + '\n'.join(type_errors))


def fromdict(d: Dict, initial_type: Union[type, List[type]]) -> TSInterface:
    assert isinstance(d, Dict)
    if not isinstance(initial_type, Iterable):
        initial_type = [initial_type]
    result = fromjson_obj(d, initial_type)
    assert isinstance(result, TSInterface)
    return result


def json_adaptor(func):
    params = func.__annotations__
    if len(params) != 2 or 'return' not in params:
        raise ValueError(f'Decorator "json_adaptor" does not work with function '
            f'"{func.__name__}" annotated with "{params}"! '
            f'LSP functions can have at most one argument. Both the type of the '
            f' argument and the return type must be specified with annotations.')
    return_type = params['return']
    for k in params:
        if k != 'return':
            call_type = params[k]
            break
    ct_forward = isinstance(call_type, ForwardRef) or isinstance(call_type, str)
    rt_forward = isinstance(return_type, ForwardRef) or isinstance(return_type, str)
    resolve_types = ct_forward or rt_forward

    @functools.wraps(func)
    def adaptor(*args, **kwargs):
        nonlocal resolve_types, return_type, call_type
        if resolve_types:
            if isinstance(call_type, ForwardRef):  call_type = call_type.__forward_arg__
            elif isinstance(call_type, str):  call_type = eval(call_type)
            if isinstance(return_type, ForwardRef):  return_type = return_type.__forward_arg__
            elif isinstance(return_type, str):  return_type = eval(return_type)
            resolve_types = False
        dict_obj = args[0] if args else kwargs
        call_params = fromjson_obj(dict_obj, [call_type])
        return_val = func(call_params)
        return asjson_obj(return_val) if return_val is not None else None

    return adaptor