"""__init__.py - package definition module for DHParser/parsers

Copyright 2024  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

from __future__ import annotations

from typing import Callable, Tuple, List, Any, Dict, Optional

from DHParser.nodetree import RootNode
from DHParser.error import Error, has_errors


__all__ = ("parse_HTML",
           "parse_XML")

def parse_template(src: str,
                   parse_func: Callable[[str, Dict], Tuple[Any, List[Error]]],
                   src_format: str="unknown",
                   cfg: Dict={}) -> RootNode:
    result, errors = parse_func(src, cfg)
    if has_errors(errors):
        err_str = "\n".join(str(e) for e in errors)
        raise ValueError(
            f"Malformed input for format: {src_format}. Parsing Errors:\n"
            + err_str
        )
    return result


def parse_HTML(html: str, preserve_whitespace: Optional[bool]=None) -> RootNode:
    """Parses an HTML document and returns the root node of the resulting
    DOM-tree.

    :param html: The HTML document to be parsed.
    :param preserve_whitespace: If True, whitespace between tags is preserved
        faithfully in the resulting DOM-tree. If False, it is removed, unless
        an xml:space-attribute with the value "preserve" explicitly requests
        its preservation.
        If None, whitespace is presvered unless the HTML-document contains
        an xml:space-attribute somewhere,
        Default is None.
    :retuns: The root node of the resulting DOM-tree.
    """
    from DHParser.parsers import HTMLParser
    if preserve_whitespace is None:
        preserve_whitespace = html.find('xml:space') < 0
    return parse_template(html, HTMLParser.compile_src, "HTML",
                          {"HTML.preserve_whitespace": preserve_whitespace})


def parse_XML(xml: str, preserve_whitespace: Optional[bool]=None) -> RootNode:
    """Parses an XML document and returns the root node of the resulting
    DOM-tree. This parser is more exact, but slower than
    :py:func:`~nodetree.parse_xml`. The differences are: Inclusion of
    processing instructions and comments in the DOM-tree and better
    conformance to the `XML standard <https://www.w3.org/TR/xml/>`_.
    The parser is also more robust if the source-data contains structural
    errors.

    :param xml: The XML document to be parsed.
    :param preserve_whitespace: If True, whitespace between tags is preserved
        faithfully in the resulting DOM-tree. If False, it is removed, unless
        an xml:space-attribute with the value "preserve" explicitly requests
        its preservation.
        If None, whitespace is presvered unless the HTML-document contains
        an xml:space-attribute somewhere,
        Default is None.
    :retuns: The root node of the resulting DOM-tree.
    """
    from DHParser.parsers import XMLParser
    if preserve_whitespace is None:
        preserve_whitespace = xml.find('xml:space') < 0
    return parse_template(xml, XMLParser.compile_src, "XML",
                          {"XML.preserve_whitespace": preserve_whitespace})
