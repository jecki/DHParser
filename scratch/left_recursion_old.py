@cython.locals(location=cython.int, gap=cython.int, i=cython.int)
def __call__(self: 'Parser', text: StringView) -> Tuple[Optional[Node], StringView]:
    """Applies the parser to the given text. This is a wrapper method that adds
    the business intelligence that is common to all parsers. The actual parsing is
    done in the overridden method `_parse()`. This wrapper-method can be thought of
    as a "parser guard", because it guards the parsing process.
    """
    # def get_error_node_id(error_node: Node, tree: RootNode) -> int:
    #     if error_node:
    #         error_node_id = id(error_node)
    #         while error_node_id not in grammar.tree__.error_nodes and error_node.children:
    #             error_node = error_node.result[-1]
    #             error_node_id = id(error_node)
    #     else:
    #         error_node_id = 0

    grammar = self._grammar
    location = grammar.document_length__ - text._len  # faster then len(text)?

    try:
        # rollback variable changing operation if parser backtracks
        # to a position before the variable changing operation occurred
        if grammar.last_rb__loc__ > location:
            grammar.rollback_to__(location)

        # if location has already been visited by the current parser, return saved result
        visited = self.visited  # using local variable for better performance
        if location in visited:
            # no history recording in case of memoized results!
            return visited[location]

        # TODO: Move Left recursion logic to Alternative or Forward-Parser
        # break left recursion at the maximum allowed depth
        left_recursion_depth__ = grammar.left_recursion_depth__
        if left_recursion_depth__:
            if self.recursion_counter[location] > left_recursion_depth__:
                grammar.recursion_locations__.add(location)
                return None, text
            self.recursion_counter[location] += 1

        # finally, the actual parser call!
        try:
            node, rest = self._parse_proxy(text)
        except ParserError as pe:
            # catching up with parsing after an error occurred
            gap = len(text) - len(pe.rest)
            rules = grammar.resume_rules__.get(self.pname, [])
            rest = pe.rest[len(pe.node):]
            i = reentry_point(rest, rules, grammar.comment_rx__,
                              grammar.reentry_search_window__)
            if i >= 0 or self == grammar.start_parser__:
                assert pe.node.children or (not pe.node.result)
                # apply reentry-rule or catch error at root-parser
                if i < 0:  i = 0
                try:
                    zombie = pe.node.pick_child(ZOMBIE_TAG)  # type: Optional[Node]
                except (KeyError, ValueError):
                    zombie = None
                if zombie and not zombie.result:
                    zombie.result = rest[:i]
                    tail = tuple()  # type: ChildrenType
                else:
                    nd = Node(ZOMBIE_TAG, rest[:i]).with_pos(location)
                    # nd.attr['err'] = pe.error.message
                    tail = (nd,)
                rest = rest[i:]
                if pe.first_throw:
                    node = pe.node
                    node.result = node.children + tail
                else:
                    node = Node(
                        self.name,
                        (Node(ZOMBIE_TAG, text[:gap]).with_pos(location), pe.node) + tail) \
                        .with_pos(location)
            elif pe.first_throw:
                # TODO: Is this case still needed with module "trace"?
                raise ParserError(pe.node, pe.rest, pe.error, first_throw=False)
            elif grammar.tree__.errors[-1].code == MANDATORY_CONTINUATION_AT_EOF:
                # try to create tree as faithful as possible
                node = Node(self.name, pe.node).with_pos(location)
            else:
                result = (Node(ZOMBIE_TAG, text[:gap]).with_pos(location), pe.node) if gap \
                    else pe.node  # type: ResultType
                raise ParserError(Node(self.name, result).with_pos(location),
                                  text, pe.error, first_throw=False)

        if left_recursion_depth__:
            self.recursion_counter[location] -= 1
            # don't clear recursion_locations__ !!!

        if node is None:
            # retrieve an earlier match result (from left recursion) if it exists
            if location in grammar.recursion_locations__:
                if location in visited:
                    node, rest = visited[location]
                    if location != grammar.last_recursion_location__:
                        grammar.tree__.add_error(
                            node, Error("Left recursion encountered. "
                                        "Refactor grammar to avoid slow parsing.",
                                        node.pos if node else location,
                                        LEFT_RECURSION_WARNING))
                        # error_id = id(node)
                        grammar.last_recursion_location__ = location
                # don't overwrite any positive match (i.e. node not None) in the cache
                # and don't add empty entries for parsers returning from left recursive calls!
            elif grammar.memoization__:
                # otherwise also cache None-results
                visited[location] = (None, rest)
        else:
            # assert node._pos < 0 or node is EMPTY_NODE
            node._pos = location
            # assert node._pos >= 0 or node is EMPTY_NODE, \
            #     str("%i < %i" % (grammar.document_length__, location))
            if (grammar.last_rb__loc__ < location
                    and (grammar.memoization__ or location in grammar.recursion_locations__)):
                # - variable manipulating parsers will not be entered into the cache,
                #   because caching would interfere with changes of variable state
                # - in case of left recursion, the first recursive step that
                #   matches will store its result in the cache
                # TODO: need a unit-test concerning interference of variable manipulation
                #       and left recursion algorithm?
                visited[location] = (node, rest)

    except RecursionError:
        node = Node(ZOMBIE_TAG, str(text[:min(10, max(1, text.find("\n")))]) + " ...")
        node._pos = location
        grammar.tree__.new_error(node, "maximum recursion depth of parser reached; "
                                       "potentially due to too many errors!")
        rest = EMPTY_STRING_VIEW

    return node, rest