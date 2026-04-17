########################################################################
#
# Aliasing parser classes
#
########################################################################


class Synonym(UnaryParser):
    r"""
    Simply calls another parser and encapsulates the result in
    another node if that parser matches.

    This parser is needed to support synonyms in EBNF, e.g.::

        jahr       = JAHRESZAHL
        JAHRESZAHL = /\d\d\d\d/

    Otherwise, the first line could not be represented by any parser
    class, in which case it would be unclear whether the parser
    RegExp('\d\d\d\d') carries the name 'JAHRESZAHL' or 'jahr'.
    """
    def __init__(self, parser: Parser) -> None:
        super().__init__(parser)

    def _parse(self, location: cython.int) -> ParsingResult:
        node, location = self.parser(location)
        if node is not None:
            if self.drop_content:
                return EMPTY_NODE, location
            if not self.disposable:
                if node is EMPTY_NODE:
                    return Node(self.node_name, '', True), location
                if node.name[0] == ':':  # node.anonymous:
                    # eliminate anonymous child-node on the fly
                    # node.name = self.node_name   # Big mistake: this can spoil the memo-cache
                    return Node(self.node_name, node._result), location
                else:
                    return Node(self.node_name, (node,)), location
        return node, location

    def __str__(self):
        return self.pname + (' = ' if self.pname else '') + self.parser.repr

    def __repr__(self):
        return self.pname or self.parser.repr


class Forward(UnaryParser):
    r"""
    Forward allows to declare a parser before it is actually defined.
    Forward declarations are needed for parsers that are recursively
    nested, e.g.::

        >>> class Arithmetic(Grammar):
        ...     r'''
        ...     expression =  term  { ("+" | "-") term }
        ...     term       =  factor  { ("*" | "/") factor }
        ...     factor     =  INTEGER | "("  expression  ")"
        ...     INTEGER    =  /\d+/~
        ...     '''
        ...     expression = Forward()
        ...     INTEGER    = RE('\\d+')
        ...     factor     = INTEGER | TKN("(") + expression + TKN(")")
        ...     term       = factor + ZeroOrMore((TKN("*") | TKN("/")) + factor)
        ...     expression.set(term + ZeroOrMore((TKN("+") | TKN("-")) + term))
        ...     root__     = expression

    :ivar recursion_counter:  Mapping of places to how often the parser
            has already been called recursively at this place. This
            is needed to implement left recursion. The number of
            calls becomes irrelevant once a result has been memoized.

    The Forward parser class contains an algorithm to handle left-recursivef
    grammars. See it's __call__()-method. The algorithm handles direct and indirect
    left-recursion, but not interwoven left-recursion!
    """

    def __init__(self):
        super().__init__(get_parser_placeholder())
        # self.parser = get_parser_placeholder  # type: Parser
        self.cycle_reached: bool = False
        self.sub_parsers = frozenset()

    def reset(self):
        super(Forward, self).reset()
        self.recursion_counter: Dict[int, int] = dict()
        assert not self.pname, "Forward-Parsers mustn't have a name!"

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        memo[id(self)] = duplicate  # prevent infinite recursion during next deepcopy() call
        copy_parser_base_attrs(self, duplicate, memo)
        parser = copy.deepcopy(self.parser, memo)
        duplicate.parser = parser
        duplicate.sub_parsers = frozenset({parser})
        return duplicate

    @cython.locals(ldepth=cython.int, rb_stack_size=cython.int)
    def __call__(self, location: cython.int) -> ParsingResult:
        """
        Overrides :py:meth:`Parser.__call__`, because Forward is not an independent parser
        but merely redirects the call to another parser. Other than parser
        :py:class:`Synonym`, which might be a meaningful marker for the syntax tree,
        parser Forward should never appear in the syntax tree.

        :py:meth:`Forward.__call__` also takes care of (most of) the left recursion
        handling. In order to do so it (unfortunately) has to duplicate some code
        from :py:meth:`Parser.__call__`.

        The algorithm for avoiding infinite loops in left-recursive grammars roughly follows:
        https://medium.com/@gvanrossum_83706/left-recursive-peg-grammars-65dab3c580e1
        See also:
        https://tinlizzie.org/VPRIPapers/tr2007002_packrat.pdf
        """
        grammar = self._grammar

        # rollback variable-changing operation if the parser backtracks
        # to a position before the variable-changing operation occurred
        if location <= grammar.last_rb__loc__:
            grammar.rollback_to__(location)

        # if the location has already been visited by the current parser, return the saved result
        visited = self.visited  # using local variable for better performance
        if location in visited:
            # Sorry, no history recording in case of memoized results!
            return visited[location]

        if location in self.recursion_counter:
            depth = self.recursion_counter[location]
            if depth == 0:
                grammar.suspend_memoization__ = id(self)
                result = None, location
            else:
                self.recursion_counter[location] = depth - 1
                result = self.parser(location)
                self.recursion_counter[location] = depth  # allow moving back and forth
        else:
            self.recursion_counter[location] = 0  # fail on the first recursion
            save_suspend_memoization = grammar.suspend_memoization__
            grammar.suspend_memoization__ = False
            history_tracking = grammar.history_tracking__
            history_pointer = len(grammar.history__) if history_tracking else 0

            result = self.parser(location)

            if result[0] is not None:
                # keep calling the (potentially left-)recursive parser and increase
                # the recursion depth by 1 for each call as long as the length of
                # the match increases.
                last_history_state = grammar.history__[history_pointer:len(grammar.history__)] \
                    if history_tracking else []
                depth = 1
                while True:
                    self.recursion_counter[location] = depth
                    grammar.suspend_memoization__ = False
                    rb_stack_size = len(grammar.rollback__)
                    if history_tracking:
                        grammar.history__ = grammar.history__[:history_pointer]
                    # reduplication of error messages will be caught by nodetree.RootNode.add_error()
                    # saving and restoring the errors-messages state on each iteration presupposes
                    # that error messages will be recreated every time, which, however, does not
                    # happen because of memoization. (This is a downside of global error-reporting
                    # in contrast to attaching error-messages locally to the node where they
                    # occurred. Big topic...)
                    # don't carry error/resumption-messages over to the next iteration
                    # grammar.most_recent_error__ = None
                    next_result = self.parser(location)

                    # discard next_result if it is not the longest match and return
                    if next_result[1] <= result[1]:  # also true, if no match
                        # Since the result of the last parser call (``next_result``) is discarded,
                        # any variables captured by this call should be "rolled back", too.
                        while len(grammar.rollback__) > rb_stack_size:
                            _, rb_func = grammar.rollback__.pop()
                            rb_func()
                            grammar.last_rb__loc__ = grammar.rollback__[-1][0] \
                                if grammar.rollback__ else -2
                        # Finally, overwrite the discarded result in the last history record with
                        # the accepted result, i.e. the longest match.
                        # TODO: Move this to trace.py, somehow... and make it less confusing
                        #       that the result is not the last but the longest match...
                        if history_tracking:
                            grammar.history__ = grammar.history__[:history_pointer] + last_history_state
                        # record = grammar.history__[-1]
                        # if record.call_stack[-1] == (self.parser.pname, location):
                        #     record.text = result[1]
                        #     delta = len(text) - len(result[1])
                        #     assert record.node.name != ':None'
                        #     record.node.result = text[:delta]
                        break

                    if history_tracking:
                        last_history_state = grammar.history__[history_pointer:len(grammar.history__)]
                    result = next_result
                    depth += 1
            # grammar.suspend_memoization__ = save_suspend_memoization \
            #     or location <= (grammar.last_rb__loc__ + int(text._len == result[1]._len))
            # both checks in the following are necessary:
            # 1. id(self)-check in order not to interfere with interwoven recursive parser calls
            # 2. isinstance check for referenced parsers that are not in fact recursive
            if grammar.suspend_memoization__ == id(self) or isinstance(grammar.suspend_memoization__, bool):
                grammar.suspend_memoization__ = save_suspend_memoization  #  = is_context_sensitive(self.parser)
        if not grammar.suspend_memoization__:
            visited[location] = result
        return result

    def set_proxy(self, proxy: Optional[ParseFunc]):
        """``set_proxy`` has no effects on Forward-objects!"""
        return

    def __cycle_guard(self, func, alt_return):
        """
        Returns the value of ``func()`` or ``alt_return`` if a cycle has
        been reached (which can happen if ``func`` calls methods of
        child parsers).
        """
        if self.cycle_reached:
            return alt_return
        else:
            self.cycle_reached = True
            ret = func()
            self.cycle_reached = False
            return ret

    def effective_pname(self) -> str:
        """Returns the parser's pname. In the case of a Forward-
        or Ref-parser, returns parser.parser.pname."""
        return self.parser.pname

    def __repr__(self):
        return self.__cycle_guard(lambda: repr(self.parser), '...')

    def __str__(self):
        return self.__cycle_guard(lambda: str(self.parser), '...')

    @property
    def repr(self) -> str:
        """Returns the parser's name if it has a name or ``repr(self)`` if not."""
        return self.parser.pname if self.parser.pname else self.__repr__()

    def set(self, parser: Parser):
        """Sets the parser to which the calls to this Forward-object
        shall be delegated.
        """
        assert not isinstance(parser, Forward)
        self.parser = parser
        self.sub_parsers = frozenset({parser})
        if self.pname and not parser.pname:  parser.name(self.pname, self.disposable)
        if not parser.drop_content:  parser.disposable = self.disposable
        self.drop_content = parser.drop_content
        self.pname = ""


class Ref(LateBindingUnary):
    """A late binding passive reference to another parser. In contrast to
    Synonym, Refs do not alter the node name."""

    def reset(self):
        super(Ref, self).reset()
        assert not self.pname, "Ref-Parsers mustn't have a name!"

    @cython.locals(ldepth=cython.int, rb_stack_size=cython.int)
    def __call__(self, location: cython.int) -> ParsingResult:
        result = self.parser(location)
        if self.drop_content:
            return EMPTY_NODE, result[1]
        return result

    def set_proxy(self, proxy: Optional[ParseFunc]):
        """``set_proxy`` has no effects on Ref-objects!"""
        return

    def name(self, pname: str = "", disposable: Optional[bool] = None) -> Parser:
        assert not pname or pname[0:1] == ":" or pname[0:5] in ('DROP:', 'HIDE:')
        assert disposable is not False
        return super().name(pname, True)

    def __repr__(self):
        return self.parser_name

    def __str__(self):
        return self.parser_name
