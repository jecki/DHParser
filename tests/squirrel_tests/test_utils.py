# test_utils.py - a DHParser-surrogate for the test_utils.py from SquirrelParser
# https://github.com/lukehutch/squirrelparser/blob/main/python/tests/test_utils.py

from dataclasses import dataclass
import os
import sys


scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
LOG_DIR = os.path.abspath(os.path.join(scriptpath, "LOGS"))


from DHParser.dsl import create_parser
from DHParser.error import FATAL
from DHParser.nodetree import WHITESPACE_PTYPE


@dataclass
class ParseTestResult:
    ok: bool
    error_count: int
    skipped_strings: list[str]


def run_test_parse(grammar: str, input_string: str) -> ParseTestResult:
    grammar = "@flavor=heuristic\n" + grammar
    grammar = create_parser(grammar)
    root_node = grammar(input_string)
    ok = not any(e.code >= FATAL for e in root_node.errors)
    error_count = len(root_node.errors)
    skipped_strings = [nd.content for nd in root_node.walk_tree(include_root=True)
                       if nd.name == WHITESPACE_PTYPE]
    return ParseTestResult(ok, error_count, skipped_strings)
