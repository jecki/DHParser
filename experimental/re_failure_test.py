#!/usr/bin/python
"""A regular expression that apparently never terminates!?"""

import re

s = '                                                # whitespace of a regular expression will be ignored tacitly.'

rx = re.compile("(?:\\s*(?:'#.*\\\\\\\\n'/ # /#.*\\n)?\\s*)*(\\w+)(?:\\s*(?:'#.*\\\\\\\\n'/ # /#.*\\n)?\\s*)*")

rx.match(s)   # never terminates?
