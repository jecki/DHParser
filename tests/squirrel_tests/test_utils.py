# test_utils.py - a DHParser-surrogate for the test_utils.py from SquirrelParser
# https://github.com/lukehutch/squirrelparser/blob/main/python/tests/test_utils.py


from __future__ import annotations


from dataclasses import dataclass
import os
import sys


scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
LOG_DIR = os.path.abspath(os.path.join(scriptpath, "LOGS"))


from DHParser.dsl import create_parser, CompilationError
from DHParser.error import FATAL, Error
from DHParser.nodetree import WHITESPACE_PTYPE, ZOMBIE_TAG, LEAF_PATH, RootNode


@dataclass
class ParseTestResult:
    ok: bool
    error_count: int
    skipped_strings: list[str]
    root_node: RootNode


class MatchResult:
    root_node: RootNode
    root: RootNode
    is_mismatch: bool
    len: int


def run_test_parse(grammar_spec: str, input_str: str, start_parser: str = '') -> ParseTestResult:
    grammar_spec = "@flavor=heuristic\n" + grammar_spec
    try:
        grammar = create_parser(grammar_spec)
        if start_parser:
            root_node = grammar(input_str, start_parser=start_parser)
        else:
            root_node = grammar(input_str)
        ok = not any(e.code >= FATAL for e in root_node.errors)
        error_count = len(root_node.errors)
        skipped_strings = [nd.content for nd in root_node.walk_tree(include_root=True)
                           if nd.name == WHITESPACE_PTYPE]
    except CompilationError as e:
        print(e)
        root_node = RootNode().with_pos(0)
        root_node.errors.append(Error(str(e), 0))
        ok = False
        error_count = 1
        skipped_strings = []
    return ParseTestResult(ok, error_count, skipped_strings, root_node)


# Export for use in other test files
test_parse = run_test_parse
test_parse.__test__ = False  # Prevent pytest from collecting this as a test


def parse_for_tree(grammar_spec: str, input_str: str, top_rule = 'S') -> MatchResult | None:
    grammar_spec = "@flavor=heuristic\n" + grammar_spec
    grammar = create_parser(grammar_spec)
    root_node = grammar(input_str, start_parser=top_rule)
    result = MatchResult()
    result.root_node = root_node
    result.len = root_node.strlen()
    for e in root_node.errors_sorted:  print(e)
    return result if result.root_node.name != ZOMBIE_TAG else None

def squirrel_parse_pt(grammar_spec, top_rule_name, input) -> MatchResult:
    result = parse_for_tree(grammar_spec, input, top_rule_name)
    if result is None:
        result = MatchResult()
        result.is_mismatch = True
    else:
        result.is_mismatch = False
        result.root = result.root_node
    return result


def count_rule_depth(result: MatchResult | None, rule_name: str) -> int:
    counts = [0]
    for path in result.root_node.select_path(LEAF_PATH):
        counter = 0
        for nd in path:
            if nd.name == rule_name:
                counter += 1
        counts.append(counter)
    return max(counts)


def verify_operator_count(result: MatchResult | None, operator: str, n: int) -> bool:
    if result is None:
        return n <= 0
    else:
        cnt = len(list(result.root_node.select(lambda nd: not nd.children and nd.content == operator,
                                               include_root=True)))
        return cnt == n

def is_left_associative(result: MatchResult | None, rule_name: str) -> bool:
    if result is None or result.root_node.errors:
        return False

    for nd in result.root_node.select(rule_name, include_root=True):
        if len(nd.children) >= 2:
            if nd[0].name != rule_name or any(nd[x].name == rule_name for x in nd[1:]):
                return False
    return True
