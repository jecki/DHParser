# Transformation factory that can also dispatch on Union typs

def transformation_factory(t=None):
    """Creates factory functions from transformation-functions that
    dispatch on the first parameter after the context parameter.

    Decorating a transformation-function that has more than merely the
    ``node``-parameter with ``transformation_factory`` creates a
    function with the same name, which returns a partial-function that
    takes just the context-parameter.

    Additionally, there is some some syntactic sugar for
    transformation-functions that receive a collection as their second
    parameter and do not have any further parameters. In this case a
    list of parameters passed to the factory function will be converted
    into a collection.

    Main benefit is readability of processing tables.

    Usage:
        @transformation_factory(AbstractSet[str])
        def remove_tokens(context, tokens):
            ...
      or, alternatively:
        @transformation_factory
        def remove_tokens(context, tokens: AbstractSet[str]):
            ...

    Example:
        trans_table = { 'expression': remove_tokens('+', '-') }
      instead of:
        trans_table = { 'expression': partial(remove_tokens, tokens={'+', '-'}) }

    Parameters:
        t:  type of the second argument of the transformation function,
            only necessary if the transformation functions' parameter list
            does not have type annotations.
    """

    def decorator(f):
        sig = inspect.signature(f)
        params = list(sig.parameters.values())[1:]
        if len(params) == 0:
            return f  # '@transformer' not needed w/o free parameters
        assert t or params[0].annotation != params[0].empty, \
            "No type information on second parameter found! Please, use type " \
            "annotation or provide the type information via transfomer-decorator."
        p1type = t or params[0].annotation
        p_types = (p1type,)
        if hasattr(p1type, '_subs_tree'):
            subs_tree = p1type._subs_tree()
            if isinstance(subs_tree, Container) and subs_tree[0] is Union:
                p_types = subs_tree[1:]
        f = singledispatch(f)
        for p1type in p_types:
            if len(params) == 1 and issubclass(p1type, Container) \
                    and not issubclass(p1type, Text) and not issubclass(p1type, ByteString):
                def gen_special(*args):
                    c = set(args) if issubclass(p1type, AbstractSet) else \
                        list(args) if issubclass(p1type, Sequence) else args
                    d = {params[0].name: c}
                    return partial(f, **d)

                f.register(p1type.__args__[0], gen_special)

            def gen_partial(*args, **kwargs):
                print(f.__name__)
                d = {p.name: arg for p, arg in zip(params, args)}
                d.update(kwargs)
                return partial(f, **d)

            f.register(p1type, gen_partial)
        return f

    if isinstance(t, type(lambda: 1)):
        # Provide for the case that transformation_factory has been
        # written as plain decorator and not as a function call that
        # returns the decorator proper.
        func = t
        t = None
        return decorator(func)
    else:
        return decorator