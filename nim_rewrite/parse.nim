{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/options
import std/strutils

import nodetree


type
  ParsingResult = tuple[node: Option[Node], location: int]
  ParseProc = proc(parser: Parser, location: int): ParsingResult
  Parser* = ref ParserObj not nil
  ParserObj = object of RootObj
    name: string
    parserType: string
    disposable: bool
    dropContent: bool
    eqClass: int
    grammar: GrammarRef
    symbol: string
    parseProxy: ParseProc not nil

  # the GrammarObj
  GrammarRef = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    document: string


let grammarPlaceholderSingleton = GrammarRef(name: "Placeholder")


method parse*(parser: Parser, location: int): ParsingResult {.base.} =
  echo "Parser.parse"
  result = (none(Node), 0)


proc callParseMethod(parser: Parser, location: int): ParsingResult =
  return parser.parse(location)


proc init*(parser: Parser): Parser =
  parser.name = ""
  parser.parserType = "Parser"
  parser.disposable = false
  parser.dropContent = false
  parser.grammar = grammarPlaceholderSingleton
  parser.symbol = ""
  parser.parseProxy = callParseMethod
  return parser


proc `()`*(parser: Parser, location: int): ParsingResult =
  # is this faster than simply calling parser.parseProxy?
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


proc `()`*(parser: Parser, document: string, location: int = 0): ParsingResult =
  parser.grammar = GrammarRef(name: "adhoc", document: document)
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
      text: string

method parse(parser: TextRef, location: int): ParsingResult =
  if substrEq(parser.grammmar.document, location, parser.text):



proc init*(textParser: TextRef, text: string): TextRef =
  discard Parser(textParser).init()
  textParser.text = text
  return textParser

proc Text*(text: string): TextRef =
  return new(TextRef).init(text)



## Test-code


let
  t = Text("A")
#  t = new(Text).initText("A")
let pr2 = t(32)
echo $pr2





