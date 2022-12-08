import std/options
import nodetree


type
  ParsingResult = tuple[node: Option[Node], location: int32]
  ParseProc = proc(parser: Parser, location: int32): ParsingResult
  Parser = ref object of RootObj
    name: string
    parserType: string
    disposable: bool
    dropContent: bool
    eqClass: int32
    grammar: Grammar
    symbol: string
    parse: ParseProc

  Grammar = ref object of RootObj
    name: string
    

  Text = ref object of Parser
      text: string


proc parsePlaceHolder(parser:Parser, location: int32): ParsingResult =
  result = (none(Node), int32(0))


proc initParser(parser: Parser) =
  parser.name = ""
  parser.parserType = "Parser"
  parser.disposable = false
  parser.dropContent = false
  parser.grammar = GrammarPlaceholderSingleton
  parser.symbol = 


# func `()`(parser: Parser, location: int32): ParsingResult =



## Test-code

let 
  p = Parser(name: "")
  t = Text(name: "", text: "abc")

echo r.node.get().name

