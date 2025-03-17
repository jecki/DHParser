#!/usr/bin/env python3

"""test_log.py - unit tests for the log-module of DHParser

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2023 Bavarian Academy of Sciences and Humanities

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

from DHParser.dsl import create_parser
from DHParser.log import start_logging
from DHParser.trace import set_tracer, trace_history

class TestLookahaeads:
    def test_ignore_regex_lookaheads(self):
        lang = r"doc = ~ /(?![0-9])\w+/"
        parser = create_parser(lang)
        set_tracer(parser, trace_history)
        _ = parser('abc')
        history = '\n'.join(str(entry) for entry in parser.history__)
        assert history.find('!MATCH') < 0


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())