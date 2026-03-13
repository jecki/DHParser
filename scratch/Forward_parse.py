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
        origin = grammar.ref_origin__

        # rollback variable changing operation if the parser backtracks
        # to a position before the variable-changing operation occurred
        if location <= grammar.last_rb__loc__:
            grammar.rollback_to__(location)

        print(self.parser.pname + ': ', location)

        # if the location has already been visited by the current parser, return the saved result
        visited = self.visited  # using local variable for better performance
        if location in visited:
            # Sorry, no history recording in case of memoized results!
            return visited[location]

        if (origin, location) in self.recursion_counter:
            depth = self.recursion_counter[(origin, location)]
            if depth == 0:
                grammar.suspend_memoization__ = id(self)
                result = None, location
            else:
                self.recursion_counter[(origin, location)] = depth - 1
                result = self.parser(location)
                self.recursion_counter[(origin, location)] = depth  # allow moving back and forth
        else:
            self.recursion_counter[(origin, location)] = 0  # fail on the first recursion
            save_suspend_memoization = grammar.suspend_memoization__
            grammar.suspend_memoization__ = False
            history_pointer = len(grammar.history__)

            result = self.parser(location)

            if result[0] is not None:
                # keep calling the (potentially left-)recursive parser and increase
                # the recursion depth by 1 for each call as long as the length of
                # the match increases.
                last_history_state = grammar.history__[history_pointer:len(grammar.history__)]
                farthest = grammar.ff_pos__
                depth = 1
                while True:
                    self.recursion_counter[(origin, location)] = depth
                    grammar.suspend_memoization__ = False
                    rb_stack_size = len(grammar.rollback__)
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
                    #
                    if (next_result[0] is None or (next_result[1] <= farthest)
                        # or (next_result[1] < result[1] and result[1] >= grammar.ff_pos__)
                    ):
                    # if next_result[1] <= result[1]:  # also true, if no match
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
                        grammar.history__ = grammar.history__[:history_pointer] + last_history_state
                        # record = grammar.history__[-1]
                        # if record.call_stack[-1] == (self.parser.pname, location):
                        #     record.text = result[1]
                        #     delta = len(text) - len(result[1])
                        #     assert record.node.name != ':None'
                        #     record.node.result = text[:delta]
                        print(grammar.ff_pos__, result[1], next_result[1])
                        break

                    last_history_state = grammar.history__[history_pointer:len(grammar.history__)]
                    print(grammar.ff_pos__, result[1], next_result[1])
                    result = next_result
                    farthest = grammar.ff_pos__
                    depth += 1
            # grammar.suspend_memoization__ = save_suspend_memoization \
            #     or location <= (grammar.last_rb__loc__ + int(text._len == result[1]._len))
            # both checks in the following are necessary:
            # 1. id(self)-check in order not to interfere with interwoven recursive parser calls
            # 2. isinstance check for referenced parsers that are not in fact recursive
            if grammar.suspend_memoization__ == id(self) or isinstance(grammar.suspend_memoization__, bool):
                grammar.suspend_memoization__ = save_suspend_memoization  #  = is_context_sensitive(self.parser)
        if location in visited and result[1] < visited[location][1]:
            # assert False
            result = visited[location]
        elif not grammar.suspend_memoization__:
            visited[location] = result
        print(self.parser.pname + ': ', '*' if result[0] is None else result[0].content)
        return result