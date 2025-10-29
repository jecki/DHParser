#!/usr/bin/env python3

"""test_pipeline.py - tests of DHParser's pipeline-module


Author: Eckhart Arnold <arnold@badw.de>

Copyright 2024 Bavarian Academy of Sciences and Humanities

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

import sys
import os
from functools import partial

from DHParser import PickMultiCoreExecutor

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.compile import Compiler
from DHParser.configuration import CONFIG_PRESET
from DHParser.error import Error, FATAL, CANCELED
from DHParser.nodetree import Node, RootNode
from DHParser.parse import Grammar, Forward, CombinedParser, mixin_comment, Whitespace, Drop, \
    NegativeLookahead, RegExp, Synonym, Series, Alternative, Option, ZeroOrMore, Lookahead, \
    Lookbehind, Text, RX_NEVER_MATCH
from DHParser.pipeline import create_parser_junction, create_junction, end_points, full_pipeline, \
    create_preprocess_junction, PseudoJunction, Junction
from DHParser.toolkit import ThreadLocalSingletonFactory, expand_table, Any, Tuple, List, \
    NEVER_MATCH_PATTERN, re, MultiCoreManager
from DHParser.transform import merge_adjacent, is_one_of, apply_if, replace_by_single_child, \
    replace_content_with, replace_by_children, reduce_single_child, change_name, transformer, \
    TransformerFunc


RE_INCLUDE = NEVER_MATCH_PATTERN
RE_COMMENT = NEVER_MATCH_PATTERN  # THIS MUST ALWAYS BE THE SAME AS outlineGrammar.COMMENT__ !!!


def outlineTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []

preprocessing: PseudoJunction = create_preprocess_junction(
    outlineTokenizer, RE_INCLUDE, RE_COMMENT)


class outlineGrammar(Grammar):
    r"""Parser for an outline source file.
    """
    emphasis = Forward()
    s5section = Forward()
    section = Forward()
    subsection = Forward()
    subsubsection = Forward()
    source_hash__ = "1733f231ee889a6a76d4f45d0eb7bfd6"
    early_tree_reduction__ = CombinedParser.MERGE_LEAVES
    disposable__ = re.compile('(?:LLF$|WS$|GAP$|inner_emph$|LINE$|ESCAPED$|L$|EOF$|inner_bold$|CHARS$|TEXT$|blocks$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'[ \t]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp('.')))
    GAP = Drop(RegExp('(?:[ \\t]*\\n)+'))
    WS = Drop(Synonym(GAP))
    PARSEP = Series(dwsp__, RegExp('\\n'), dwsp__, RegExp('\\n'))
    LF = RegExp('[ \\t]*\\n[ \\t]*(?!\\n)')
    L = Series(RegExp('[ \\t]'), dwsp__)
    LLF = Alternative(L, LF)
    ESCAPED = Series(Drop(Text("\\")), RegExp('.'))
    CHARS = RegExp('[^\\s\\\\_*]+')
    TEXT = Series(CHARS, ZeroOrMore(Series(LLF, CHARS)))
    LINE = RegExp('[^\\n]+')
    text = Series(Alternative(TEXT, ESCAPED), ZeroOrMore(Series(Option(LLF), Alternative(TEXT, ESCAPED))))
    inner_bold = Series(Option(Series(dwsp__, Lookahead(RegExp('[*_]')))), Alternative(text, emphasis),
                        ZeroOrMore(Series(Option(LLF), Alternative(text, emphasis))),
                        Option(Series(Lookbehind(RegExp('[*_]')), dwsp__)))
    bold = Alternative(Series(Drop(Text("**")), inner_bold, Drop(Text("**")), mandatory=1),
                       Series(Drop(Text("__")), inner_bold, Drop(Text("__")), mandatory=1))
    is_heading = RegExp('##?#?#?#?#?(?!#)')
    heading = Synonym(LINE)
    inner_emph = Series(Option(Series(dwsp__, Lookahead(RegExp('[*_]')))), Alternative(text, bold),
                        ZeroOrMore(Series(Option(LLF), Alternative(text, bold))),
                        Option(Series(Lookbehind(RegExp('[*_]')), dwsp__)))
    indent = RegExp('[ \\t]+(?=[^\\s])')
    markup = Series(Option(indent), Alternative(text, bold, emphasis),
                    ZeroOrMore(Series(Option(LLF), Alternative(text, bold, emphasis))))
    blocks = Series(NegativeLookahead(is_heading), markup,
                    ZeroOrMore(Series(GAP, NegativeLookahead(is_heading), markup)))
    s6section = Series(Drop(Text("######")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading,
                       Option(Series(WS, blocks)))
    s5section_expect = Alternative(section, subsection, subsubsection, s5section, s6section, EOF)
    subsubsection_expect = Alternative(section, subsection, subsubsection, s5section, EOF)
    subsection_expect = Alternative(section, subsection, subsubsection, EOF)
    section_expect = Alternative(section, subsection, EOF)
    main_expect = Alternative(section, EOF)
    main = Series(Option(WS), Drop(Text("#")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading,
                  Option(Series(WS, blocks)),
                  ZeroOrMore(Series(WS, Series(Lookahead(main_expect), mandatory=0), section)))
    emphasis.set(Alternative(
        Series(Drop(Text("*")), NegativeLookahead(Drop(Text("*"))), inner_emph, Drop(Text("*")), mandatory=2),
        Series(Drop(Text("_")), NegativeLookahead(Drop(Text("_"))), inner_emph, Drop(Text("_")), mandatory=2)))
    s5section.set(
        Series(Drop(Text("#####")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)),
               ZeroOrMore(Series(WS, Series(Lookahead(s5section_expect), mandatory=0), s6section))))
    subsubsection.set(
        Series(Drop(Text("####")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)),
               ZeroOrMore(Series(WS, Series(Lookahead(subsubsection_expect), mandatory=0), s5section))))
    subsection.set(
        Series(Drop(Text("###")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)),
               ZeroOrMore(Series(WS, Series(Lookahead(subsection_expect), mandatory=0), subsubsection))))
    section.set(
        Series(Drop(Text("##")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)),
               ZeroOrMore(Series(WS, Series(Lookahead(section_expect), mandatory=0), subsection))))
    document = Series(main, Option(WS), EOF, mandatory=2)
    root__ = document


parsing: PseudoJunction = create_parser_junction(outlineGrammar)


outline_AST_transformation_table = {
    # AST Transformations for the outline-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],   # called for each node after calling its specific rules
    "markup, bold, emphasis, text":
          [merge_adjacent(is_one_of('text', ':Text', ':L', ':RegExp', ':CHARS'), 'text'),
           apply_if(replace_by_single_child, is_one_of({'text'}))],
          # apply_if(reduce_single_child, has_child({'text'}))],
    "LF": [replace_content_with(' '), change_name(':L')],
    ":GAP": [change_name('GAP')]
}


def outlineTransformer() -> TransformerFunc:
    return partial(transformer, transformation_table=outline_AST_transformation_table.copy(),
                   src_stage='CST', dst_stage='AST')


ASTTransformation: Junction = Junction(
    'CST', ThreadLocalSingletonFactory(outlineTransformer), 'AST')


class DOMCompiler(Compiler):
    """Transforms the abstract-syntax-tree to a DOM-tree
    with HTML-based node-names.
    """

    def __init__(self):
        super(DOMCompiler, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "AST", f"Source stage `AST` expected, `but `{root.stage}` found."
        root.stage = "DOM"

    def finalize(self, result: Any) -> Any:
        if result.name in ('main', 'section', 'subsection', 'subsubsection',
                           's5section', 's6section', 'blocks', ':blocks'):
            result.name = 'div'
        return result

    def on_document(self, node):
        node = self.fallback_compiler(node)
        node.name = "body"
        return node

    def compile_structure(self, node, heading_name):
        node = self.fallback_compiler(node)
        node['heading'].name = heading_name
        replace_by_children(self.path)
        return node

    def on_main(self, node):
        return self.compile_structure(node, "h1")

    def on_section(self, node):
        return self.compile_structure(node, "h2")

    def on_subsection(self, node):
        return self.compile_structure(node, "h3")

    def on_subsubsection(self, node):
        return self.compile_structure(node, "h4")

    def on_s5section(self, node):
        return self.compile_structure(node, "h5")

    def on_s6section(self, node):
        return self.compile_structure(node, "h6")

    def on_markup(self, node):
        node = self.fallback_compiler(node)
        if node[0].name == 'indent':
            node.attr['style'] = "text-indent: 2em;"
            del node[0]
        if len(node.children) == 1 and node[0].name == 'text':
            reduce_single_child(self.path)
        node.name = "p"
        return node

    def on_bold(self, node):
        node = self.fallback_compiler(node)
        if len(node.children) == 1 and node[0].name == 'text':
            reduce_single_child(self.path)
        node.name = "b"
        return node

    def on_emphasis(self, node):
        node = self.fallback_compiler(node)
        if len(node.children) == 1 and node[0].name == 'text':
            reduce_single_child(self.path)
        node.name = "i"
        return node

compiling: Junction = create_junction(
    DOMCompiler, "AST", "DOM")

HTML_TMPL = """<!DOCTYPE html>
<html lang="en-GB">
<head>
    <title>{title}</title>
    <meta charset="utf8"/>
</head>
{body}
</html>
"""


class HTMLSerializer(Compiler):
    def prepare(self, root: RootNode) -> None:
        assert root.stage == "DOM", f"Source stage `DOM` expected, `but `{root.stage}` found."
        root.stage = "html"
        h1 = root.pick('h1')
        self.title = h1.content if h1 else ''

    def on_body(self, node: Node) -> str:
        body = node.as_xml(string_tags={'text'})
        return HTML_TMPL.format(title=self.title, body=body)

    def wildcard(self, node: Node) -> str:
        return node.as_xml(string_tags={'text'})

serializing: Junction = create_junction(HTMLSerializer, "DOM", "html")

junctions = {ASTTransformation, compiling, serializing}
targets = end_points(junctions)
test_targets = {j.dst for j in junctions}

# add one or more serializations for those targets that are node-trees
serializations = expand_table({'DOM': ['sxpr'], '*': ['sxpr']})


def compile_src(source: str, target: str = "html", cancel_query=None) -> Tuple[Any, List[Error]]:
    full_compilation_result = full_pipeline(
        source, preprocessing.factory, parsing.factory, junctions, {target},
        cancel_query=cancel_query)
    return full_compilation_result.get(target, list(full_compilation_result.values())[-1])


BAD_NESTING_EXAMPLE = """# Main Heading
## Section 1
#### BADLY NESTED SubSubSection 1.1.1
## Section 2"""


class TestErrorPassing:
    def test_pass_errors_through_pipeline(self):
        html, errors = compile_src(BAD_NESTING_EXAMPLE)
        assert len(errors) == 3, '\n'.join(str(e) for e in errors)
        assert {e.code for e in errors} == {1010, 1040, 10100}
        # check if Python-Error has been passed through correctly
        assert any(e.code >= FATAL for e in errors)
        assert any(str(e).find('test_pipeline.py') >= 0 for e in errors)


EXAMPLE_OUTLINE = """# Main Heading

Some introductory Text

## Section 1
One paragraph of text

Another paragraph of text. This
time stretching over several lines.

## Section 2

### Section 2.1

### Section 2.2

The previous sections is (still) empty.
This one is not.
"""


def never():
    return False

class MyError:
    def __init__(self, s, c):
        self.s = s
        self.c = c

def dummy(a: str):
    me = MyError("Error", CANCELED)
    return (None, [1, me])


class TestCancellation:
    def setup_method(self):
        self.mc_pool = CONFIG_PRESET['multicore_pool']

    def teardown_method(self):
        CONFIG_PRESET['multicore_pool'] = self.mc_pool

    def test_cancellation(self):
        import multiprocessing
        import threading
        from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
        # ProcessPool
        with multiprocessing.Manager() as manager:
            event = manager.Event()
            assert not event.is_set()
            event.set() # cancel right away
            with ProcessPoolExecutor() as ex:
                f = ex.submit(compile_src, EXAMPLE_OUTLINE, "html", event.is_set)
                result = f.result()
        assert result[0] is None
        assert result[1][0].code == CANCELED
        # ThreadPool
        with multiprocessing.Manager() as manager:
            event = manager.Event()
            assert not event.is_set()
            event.set() # cancel right away
            with ThreadPoolExecutor() as ex:
                f = ex.submit(compile_src, EXAMPLE_OUTLINE, "html", event.is_set)
                result = f.result()
        assert result[0] is None
        assert result[1][0].code == CANCELED

    def test_cancellation_interpreter_pool(self):
        import DHParser.stringview
        if sys.version_info >= (3, 14) \
                and not getattr(DHParser.stringview, 'cython_optimized', False):
            CONFIG_PRESET['multicore_pool'] = 'InterpreterPool'
            from concurrent.futures import InterpreterPoolExecutor
            if __name__ != '__main__':
                os.chdir('..')
                import tests.test_pipeline as test_pipeline
            else:
                import test_pipeline
            with MultiCoreManager() as manager:
                event = manager.Event()
                assert not event.is_set()
                event.set()  # cancel right away
                with InterpreterPoolExecutor() as ex:
                    f = ex.submit(test_pipeline.compile_src, EXAMPLE_OUTLINE, "html", event.is_set)
                    # f = ex.submit(dummy, "abc")
                    result = f.result()
            assert result[0] is None
            assert result[1][0].code == CANCELED

    def test_cancellation_pick_pool(self):
        import DHParser.stringview
        if sys.version_info < (3, 14) \
                or not getattr(DHParser.stringview, 'cython_optimized', False):
            CONFIG_PRESET['multicore_pool'] = 'InterpreterPool'
        else:
            CONFIG_PRESET['multicore_pool'] = 'ProcessPool'
        if __name__ != '__main__':
            os.chdir('..')
            import tests.test_pipeline as test_pipeline
        else:
            import test_pipeline
        with MultiCoreManager() as manager:
            event = manager.Event()
            assert not event.is_set()
            event.set()  # cancel right away
            with PickMultiCoreExecutor() as ex:
                f = ex.submit(test_pipeline.compile_src, EXAMPLE_OUTLINE, "html", event.is_set)
                # f = ex.submit(dummy, "abc")
                result = f.result()
        assert result[0] is None
        assert result[1][0].code == CANCELED

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
