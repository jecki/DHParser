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

    # roll back variable-changing operation if the parser backtracks
    # to a position before the variable-changing operation occurred
    if location <= grammar.last_rb__loc__:
        grammar.rollback_to__(location)

    # if the location has already been visited by the current parser, return the saved result
    visited = self.visited  # using local variable for better performance
    if location in visited:
        # Sorry, no history recording in case of memoized results!
        if self.recursion_counter[location]:
            grammar.suspend_memoization__ = id(self)
        return visited[location]

    if location in self.recursion_counter:
        grammar.suspend_memoization__ = id(self)
        return None, location

    self.recursion_counter[location] = True  # fail on the first recursion
    save_suspend_memoization = grammar.suspend_memoization__
    grammar.suspend_memoization__ = False
    history_tracking = grammar.history_tracking__
    history_pointer = len(grammar.history__) if history_tracking else 0
    rb_stack_size = len(grammar.rollback__)
    last_history_state = []

    result = None, location
    next_result = self.parser(location)

    while next_result[1] > result[1]:
        result = next_result
        grammar.suspend_memoization__ = False
        rb_stack_size = len(grammar.rollback__)
        if history_tracking:
            last_history_state.extend(grammar.history__[history_pointer:len(grammar.history__)])
            grammar.history__ = grammar.history__[:history_pointer]
        visited[location] = result
        next_result = self.parser(location)

    if history_tracking and result[0] is not None:
        grammar.history__ = grammar.history__[:history_pointer] + last_history_state

    self.recursion_counter[location] = False
    # Since the result of the last parser call ("next_result") is discarded,
    # any variables captured by this call should be "rolled back", too.
    while len(grammar.rollback__) > rb_stack_size:
        _, rb_func = grammar.rollback__.pop()
        rb_func()
        grammar.last_rb__loc__ = grammar.rollback__[-1][0] \
            if grammar.rollback__ else -2

    # both checks in the following are necessary:
    # 1. id(self)-check in order not to interfere with interwoven recursive parser calls
    # 2. isinstance check for referenced parsers that are not in fact recursive
    if grammar.suspend_memoization__ == id(self) or isinstance(grammar.suspend_memoization__, bool):
        grammar.suspend_memoization__ = save_suspend_memoization  # = is_context_sensitive(self.parser)
    if not grammar.suspend_memoization__:
        visited[location] = result
    return result