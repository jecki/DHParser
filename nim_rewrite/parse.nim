{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/options

import nodetree


type
  ParsingResult = tuple[node: Option[Node], location: int]
  ParseProc = proc(parser: Parser, location: int): ParsingResult
  Parser = ref ParserObj not nil
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


method parse(parser: Parser, location: int): ParsingResult {.base.} =
  result = (none(Node), 0)


proc init(parser: Parser): Parser =
  parser.name = ""
  parser.parserType = "Parser"
  parser.disposable = false
  parser.dropContent = false
  parser.grammar = grammarPlaceholderSingleton
  parser.symbol = ""
  parser.parseProxy = parse
  return parser


proc `()`(parser: Parser, location: int): ParsingResult =
  return parser.parse_proxy(parser, location)


type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
      text: string


method parse(parser: Parser, location: int): ParsinResult =
  result = ()


proc init(textParser: TextRef, text: string): TextRef =
  discard init(Parser(textParser))
  textParser.text = text
  return textParser


## Test-code


let
  p = new(Parser).init()
  t = new(Text).init("A")
#  t = new(Text).initText("A")
let pr = p.parse(p, 32)
echo $pr
t.text = "B"
echo t.text




