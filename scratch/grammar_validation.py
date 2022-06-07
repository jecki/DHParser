from typing import Optional, Union

from DHParser import *


class Validator(Parser):
    @property
    def grammar(self) -> 'Grammar':
        try:
            return self._grammar
        except (AttributeError, NameError):
            raise AttributeError('Validator has not yet been assigned to a schema!')

    @grammar.setter
    def grammar(self, grammar: 'Grammar'):
        if not isinstance(grammar, Schema):
            raise TypeError('Validators can only be assigned to Schemas, '
                            'not to Grammars.')
        assert isinstance(grammar, Schema)
        try:
            if is_grammar_placeholder(self._grammar):
                self._grammar = grammar
            elif self._grammar != grammar:
                raise AssertionError("Validator has already been assigned"
                                     "to a different Schema-object!")
        # except AttributeError:
        #     pass  # ignore setting of grammar attribute for placeholder parser
        except NameError:  # Cython: No access to _GRAMMAR_PLACEHOLDER, yet :-(
            self._grammar = grammar

    # TODO: Override call method


class Leaf(Validator):
    def __init__(self, name: str, content_regexp=''):
        super().__init__()
        if content_regexp and isinstance(content_regexp, str):
            self.content_regexp = re.compile(content_regexp)
        else:
            self.content_regexp = content_regexp
        self.name = name

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.name, self.content_regexp)
        copy_parser_base_attrs(self, duplicate)
        return duplicate

    def _parse(self, location: int) -> ParsingResult:
        pass


def reset_parser(ctx):
    return ctx[-1].reset()


class Schema(Grammar):
    def __init__(self, root: Parser = None, static_analysis: Optional[bool] = None) -> None:
        super().__init__(root, static_analysis)
        self.data_tree: Optional[Node] = None

    def __call__(self,
                 data_tree: Node,
                 start_parser: Union[str, Parser] = "root_parser__",
                 source_mapping: Optional[SourceMapFunc] = None,
                 *, complete_match: bool = True) -> RootNode:

        parser = self[start_parser] if isinstance(start_parser, str) else start_parser
        assert parser.grammar == self, "Cannot run parsers from a different grammar object!" \
                                       " %s vs. %s" % (str(self), str(parser.grammar))

        if self._dirty_flag__:
            self._reset__()
            parser.apply(reset_parser)
            for p in self.resume_parsers__:  p.apply(reset_parser)
        else:
            self._dirty_flag__ = True

        self.start_parser__ = parser
        assert isinstance(data_tree, Node)
        self.data_tree = data_tree
        # done by reset: self.last_rb__loc__ = -1  # rollback location
        result, _ = parser(0)

        self.tree__.swallow(result, '', None)
        self.start_parser__ = None
        return self.tree__


if __name__ == "__main__":
    v = Validator()
    v.grammar = Schema()
