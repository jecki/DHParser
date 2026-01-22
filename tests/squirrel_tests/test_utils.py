# test_utils.py - a DHParser-surrogate for the test_utils.py from SquirrelParser
# https://github.com/lukehutch/squirrelparser/blob/main/python/tests/test_utils.py


from __future__ import annotations


from dataclasses import dataclass
import os
import sys


scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
LOG_DIR = os.path.abspath(os.path.join(scriptpath, "LOGS"))


from DHParser.dsl import create_parser
from DHParser.error import FATAL
from DHParser.nodetree import WHITESPACE_PTYPE, ZOMBIE_TAG, LEAF_PATH, RootNode


@dataclass
class ParseTestResult:
    ok: bool
    error_count: int
    skipped_strings: list[str]
    root_node: RootNode


class MatchResult:
    root_node: RootNode



def run_test_parse(grammar_spec: str, input_str: str) -> ParseTestResult:
    grammar_spec = "@flavor=heuristic\n" + grammar_spec
    grammar = create_parser(grammar_spec)
    root_node = grammar(input_str)
    ok = not any(e.code >= FATAL for e in root_node.errors)
    error_count = len(root_node.errors)
    skipped_strings = [nd.content for nd in root_node.walk_tree(include_root=True)
                       if nd.name == WHITESPACE_PTYPE]
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
    for e in root_node.errors_sorted:  print(e)
    return result if result.root_node.name != ZOMBIE_TAG else None


def count_rule_depth(result: MatchResult | None, rule_name: str) -> int:
    counts = [0]
    for path in result.root_node.select_path(LEAF_PATH):
        counter = 0
        for nd in path:
            if nd.name == rule_name:
                counter += 1
        counts.append(counter)
    return max(counts)


def is_left_associative(result: MatchResult | None, rule_name: str) -> bool:
    if result is None or result.root_node.errors:
        return False

    for nd in result.root_node.select(rule_name, include_root=True):
        if len(nd.children) >= 2:
            if nd[1].name == rule_name and not nd[0].children:
                return False
    return True
