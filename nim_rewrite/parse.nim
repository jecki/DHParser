{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/options

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
    grammar: Grammar
    symbol: string
    parseProxy: ParseProc not nil

  GrammarObj = object of RootObj
    name: string
    document: string
  Grammar = ref GrammarObj not nil


let grammarPlaceholderSingleton: Grammar = Grammar(name: "Placeholder")


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


proc `()`(parser: Parser, location: int): ParsingResult {.inline.} =
  # is this faster than simply calling parser.parseProxy?
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
      text: string


method parse(parser: TextRef, location: int): ParsingResult =
  echo "Test.parse"
  result = (none(Node), 0)


proc init(textParser: TextRef, text: string): TextRef =
  discard Parser(textParser).init()
  textParser.text = text
  return textParser


## Test-code


let
  p = new(Parser).init()
  t = new(TextRef).init("A")
#  t = new(Text).initText("A")
let pr = p(32)
let pr2 = t(32)
echo $pr





