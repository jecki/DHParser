#!/usr/bin/python3

"""markdown.py - markdown compiler with parser combinators


Copyright 2016  by Eckhart Arnold

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

import os

try:
    import regex as re
except ImportError:
    import re
import sys


sys.path.append(os.path.abspath('../'))
sys.path.append(os.path.abspath('../showcases'))

from ParserCombinators import *



RX_WHITESPACE = re.compile(r' *')

RX_QUOTE = re.compile(r' {0,3}> ?')
RX_VERBATIM = re.compile(r' {4}|(:? *\r?$)')
RX_FENCED = re.compile(r'(?: {0,3}````*)|(?: {0,3}~~~~*)')
RX_PARAGRAPH = re.compile(r' {0,3}(?=[^\s])')
RX_LAZYLINE = re.compile(r' *(?=[^\s])')
RX_BULLET = re.compile(r' {0,3}[-*+](?:(?: (?= {4}))|(?: {1,4}(?=[^ ]|$)))')
RX_NUMBERED = re.compile(r' {0,3}[0-9]{1,9}\.(?:(?: (?= {4}))|(?: {1,4}(?=[^ ]|$)))')

QUOTE = "QUOTE"
VERBATIM = "VERBATIM"
FENCED = "FENCED"
BULLET = "BULLET_ITEM"
NUMBERED = "NUMBERED_ITEM"
PARAGRAPH = "PARAGRAPH"

BEGIN_PREFIX = "BEGIN_"
END_PREFIX = "END_"

CONTINUATION = "CONTINUATION"


# continuation conditions

def continuation(regexp, line, unless):
    m = regexp.match(line)
    if m:
        content = m.group__()
        if content:
            return not unless, make_token(CONTINUATION, content), line[m.end():]
        return not unless, '', line
    return unless, '', line  # return no prefix and unchanged line


continue_if = lambda regexp, line: continuation(regexp, line, False)
continue_unless = lambda regexp, line: continuation(regexp, line, True)

quote_cont = lambda line, blockargs: continue_if(RX_QUOTE, line)
verbatim_cont = lambda line, blockargs: continue_if(RX_VERBATIM, line)
fenced_cont = lambda line, blockargs: continue_unless(re.compile(r' {0,3}%s{%i}' % blockargs), line)
listitem_cont = lambda line, blockargs: continue_if(re.compile(r'(?: {%i})|(?:\s*$)' % blockargs), line)


def paragraph_cont(line, blockargs):
    if RX_QUOTE.match(line) or RX_BULLET.match(line) or RX_NUMBERED.match(line) or RX_FENCED.match(line):
        return False, '', line
    return continue_if(RX_LAZYLINE, line)


# new blocks

def newblock_if(regexp, blocktype, line):
    m = regexp.match(line)
    if m:
        return make_token(BEGIN_PREFIX + blocktype, m.group__()), line[m.end():], m.end()
    return '', line, 0


quote_start = lambda line: newblock_if(RX_QUOTE, QUOTE, line)
verbatim_start = lambda line: newblock_if(RX_VERBATIM, VERBATIM, line)
bullet_start = lambda line: newblock_if(RX_BULLET, BULLET, line)
numbered_start = lambda line: newblock_if(RX_NUMBERED, NUMBERED, line)
paragraph_start = lambda line: newblock_if(RX_PARAGRAPH, PARAGRAPH, line)


def fenced_start(line):
    m = RX_FENCED.match(line)
    if m:
        fence_str = m.group()
        return make_token(BEGIN_PREFIX + FENCED, fence_str), line[m.end():], \
               (fence_str[-1], len(fence_str.strip()))
    else:
        return '', line, 0


BLOCK_RECORDS = (
    (QUOTE, quote_start, quote_cont),
    (BULLET, bullet_start, listitem_cont),
    (NUMBERED, numbered_start, listitem_cont),
    (FENCED, fenced_start, fenced_cont),
    (VERBATIM, verbatim_start, verbatim_cont),
    (PARAGRAPH, paragraph_start, paragraph_cont)
)


def markdown_scanner(text):
    open_blocks = []
    dest_lines = []

    for line in text.split('\n'):
        rest = line.replace('\t', '    ')

        # check for continuation of open blocks

        prefix_list = []
        first_closed = len(open_blocks)
        last_open = -1
        for i, (blocktype, block_cont, blockargs) in enumerate(open_blocks):
            shall_continue, prefix, rest = block_cont(rest, blockargs)
            prefix_list.append(prefix)
            if shall_continue:
                last_open = i
            elif i < first_closed:
                first_closed = i

        last_open_block = open_blocks[last_open][0] if last_open >= 0 else ''

        # check for new block starts

        new_blocks = []
        opener_list = []
        while rest and last_open_block not in {VERBATIM, FENCED, PARAGRAPH}:
            for blocktype, block_start, block_cont in BLOCK_RECORDS:
                opener, rest, blockargs = block_start(rest)
                if opener:
                    opener_list.append(opener)
                    new_blocks.append((blocktype, block_cont, blockargs))
                    last_open_block = blocktype
                    break  # leave for loop and continue with while look
            else:
                break  # leave while loop, if no new block was detected (e.g. empty line or lazy line)

        # if there is a new block start or an empty line, close all uncontinued blocks
        # and their descendants, otherwise assume a lazy line
        if new_blocks or not rest.strip():
            for blocktype in (record[0] for record in reversed(open_blocks[first_closed:])):
                prefix_list.append(make_token(END_PREFIX + blocktype))
            open_blocks = open_blocks[:first_closed] + new_blocks

        dest_lines.append("".join(prefix_list) + "".join(opener_list) + rest)

    loose_ends = [make_token(END_PREFIX + blocktype)
                  for blocktype in (record[0] for record in reversed(open_blocks))]
    dest_lines[-1] += "".join(loose_ends)

    return '\n'.join(dest_lines)



RE_PBREAK = re.compile(r'\s*(?:^|\n)(?:[ \t]*\n)+')
RE_LINEBREAK = re.compile(r'(?:\t ?\n)|(?: [ \t]+)\n(?![ \t]*\n)')


grammar_src = load_if_file('../grammars/Markdown.ebnf')
markdown_text = load_if_file('../testdata/test_md1.md')

parser_py, errors, AST = full_compilation(grammar_src, EBNFGrammar(),
                                          EBNFTransTable, EBNFCompiler())
print(errors)
print(parser_py)
assert parser_py is not None
code = compile(parser_py, '<string>', 'exec')



module_vars = globals()
name_space = {k: module_vars[k] for k in {'RegExp', 'RE', 'Token', 'Required', 'Optional', 'mixin_comment',
                                          'ZeroOrMore', 'OneOrMore', 'Sequence', 'Alternative', 'Forward',
                                          'NegativeLookahead', 'PositiveLookahead', 'ScannerToken', 'GrammarBase'}}
exec(code, name_space)
parser = name_space['Grammar']()

MDTransTable = {
    "*": replace_by_single_child
}

markdown_text = markdown_scanner(markdown_text)
print(markdown_text)
syntax_tree = parser.parse(markdown_text)
ASTTransform(syntax_tree, MDTransTable)

print(syntax_tree.as_sexpr())
print(error_messages(markdown_text, syntax_tree.collect_errors()))
