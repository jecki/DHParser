def as_ebnf(self) -> str:
    """
    EXPERIMENTAL. Does not yet support serialization of DHParser- directives.

    Serializes the Grammar object as a grammar-description in the
    Extended Backus-Naur-Form.
    """
    ebnf = []

    # gather error, skip, resume and drop information
    resume_rules = self.resume_rules__ if hasattr(self, 'resume_rules__') else dict()
    skip_rules = dict()
    err_msgs = dict()
    drop_set = set()
    for name, attr in self.__class__.__dict__.items():
        if name.endswith('_skip__'):
            skip_rules[name[:-7]] = attr
        elif name.endswith('_err_msg__'):
            err_msgs[name[:-10]] = attr
        elif not name.endswith('__') and isinstance(attr, Parser):
            if cast(Parser, attr).drop_content:
                drop_set.add(name)
    for parser in self.all_parsers__:
        if parser.drop_content:
            if isinstance(parser, Whitespace):
                drop_set.add('whitespace')
            elif not parser.pname:
                if isinstance(parser, RegExp):
                    drop_set.add('regexp')
                elif isinstance(parser, Token):
                    drop_set.add('token')

    # directives
    if hasattr(self, 'WHITESPACE__'):
        ebnf.append('@ whitespace = /%s/' % self.WHITESPACE__)
    if hasattr(self, 'COMMENT__'):
        ebnf.append('@ whitespace = /%s/' % self.COMMENT__)
    if hasattr(self, 'anonymous__'):
        ebnf.append('@ anonymous = /%s/' % self.anonymous__.pattern)

    # TODO: add directives; pay special attention to whitespace!!!

    # definitions
    for entry, parser in self.__dict__.items():
        if isinstance(parser, Parser) and sane_parser_name(entry):
            ebnf.append(str(parser))
    return '\n'.join(ebnf)