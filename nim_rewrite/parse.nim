import nodetree


type
  ParsingResult = tuple[node: Node, location: int32]
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




## Test-code

let 
  p = Parser(name: "")
  t = Text(name: "", text: "abc")

echo t is Parser


