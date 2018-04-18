#!/usr/bin/python3

"""test_compile.py - unit tests for the compile-module of DHParser

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2017 Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


from DHParser import parse_sxpr, Compiler


# class TestCompilerClass:
#     def test_error_propagations(self):
#         tree = parse_sxpr('(A (B 1) (C (D (E 2) (F 3))))')
#         A = tree
#         B = next(tree.select(lambda node: str(node) == "1"))
#         D = next(tree.select(lambda node: node.parser.name == "D"))
#         F = next(tree.select(lambda node: str(node) == "3"))
#         B.new_error("Error in child node")
#         F.new_error("Error in child's child node")
#         Compiler.propagate_error_flags(tree, lazy=True)
#         assert A.error_flag
#         assert not D.error_flag
#         Compiler.propagate_error_flags(tree, lazy=False)
#         assert D.error_flag


if __name__ == "__main__":
    from DHParser.testing import runner
    from DHParser.log import logging
    with logging(False):
        runner("", globals())