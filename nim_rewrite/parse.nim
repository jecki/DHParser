{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/options

import nodetree


type
  ParsingResult = tuple[node: Option[Node], location: int32]
  ParseProc = proc(parser: Parser, location: int32): ParsingResult
  Parser = ref ParserObj not nil
  ParserObj = object of RootObj
    name: string
    parserType: string
    disposable: bool
    dropContent: bool
    eqClass: int32
    grammar: Grammar
    symbol: string
    parse: ParseProc not nil

  GrammarObj = object of RootObj
    name: string
  Grammar = ref GrammarObj not nil


let GrammarPlaceholderSingleton: Grammar = Grammar(name: "Placeholder")


proc parsePlaceHolder(parser:Parser, location: int32): ParsingResult =
  result = (none(Node), int32(0))


proc init(parser: Parser): Parser =
  parser.name = ""
  parser.parserType = "Parser"
  parser.disposable = false
  parser.dropContent = false
  parser.grammar = GrammarPlaceholderSingleton
  parser.symbol = ""
  parser.parse = parsePlaceHolder
  parser


# func `()`(parser: Parser, location: int32): ParsingResult =

type
  Text = ref TextObj not nil
  TextObj = object of ParserObj
      text: string


proc init(parser: Text, text: string): Text =
  discard init(Parser(parser))
  parser.text = text
  parser


## Test-code


let
  p = new(Parser).init()
  t = new(Text).init("A")
#  t = new(Text).initText("A")
let pr = p.parse(p, 32)
echo $pr
t.text = "B"
echo t.text




