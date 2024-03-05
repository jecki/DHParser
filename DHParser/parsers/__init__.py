"""__init__.py - package definition module for DHParser/parsers

Copyright 2024  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

from __future__ import annotations

from typing import Callable, Tuple, List, Any, Dict

from DHParser.nodetree import Node
from DHParser.error import Error, has_errors


__all__ = ("parse_HTML",
           "parse_XML")

def parse_template(src: str,
                   parse_func: Callable[[str, Dict], Tuple[Any, List[Error]]],
                   src_format: str="unknown",
                   cfg: Dict={}) -> Node:
    result, errors = parse_func(src, cfg)
    if has_errors(errors):
        err_str = "\n".join(str(e) for e in errors)
        raise ValueError(
            f"Malformed input for format: {src_format}. Parsing Errors:\n"
            + err_str
        )
    return result


def parse_HTML(html: str, preserve_whitespace: bool=False) -> Node:
    from DHParser.parsers import HTMLParser
    return parse_template(html, HTMLParser.compile_src, "HTML",
                          {"HTML.preserve_whitespace": preserve_whitespace})


def parse_XML(xml: str, preserve_whitespace: bool=False) -> Node:
    from DHParser.parsers import XMLParser
    return parse_template(xml, XMLParser.compile_src, "XML",
                          {"XML.preserve_whitespace": preserve_whitespace})


