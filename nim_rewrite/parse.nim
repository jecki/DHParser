{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/strformat
import std/strutils

import nodetree


## Parser Base and Grammar
## -----------------------
##
## Parser is the base class for all parsers.
##
## Grammar objects contain an ensemble of parsers. A grammar object is
## linked to each contained parser and stores the global variables
## that are shared by all parsers of the ensemble, like memoizing data.

type
  ParsingResult = tuple[node: NodeOrNil, location: int]
  ParseProc = proc(parser: Parser, location: int): ParsingResult
  Parser* = ref ParserObj not nil
  ParserObj = object of RootObj
    name: string
    nodeName: string
    parserType: string
    disposable: bool
    dropContent: bool
    eqClass: int
    grammar: GrammarRef
    symbol: string
    parseProxy: ParseProc not nil

  # the GrammarObj
  ReturnItemFunc = proc(parser: Parser, node: NodeOrNil): Node
  ReturnSequenceFunc = proc(parser: Parser, nodes: seq[Node]): Node
  GrammarRef* = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    document: string
    parsers: seq[Parser]
    returnItem: ReturnItemFunc
    returnSequence: ReturnSequenceFunc


proc `$`*(r: ParsingResult): string =
  let tree = $r.node
  if tree.find('\n') < 0:
    return fmt"node: {tree}, location: {r.location}"
  else:
    return fmt"node:\n{tree}\nlocation: {r.location}"


func returnItemAsIs(parser: Parser, node: NodeOrNil): Node =
  if parser.dropContent:
    return EmptyNode
  if isNil(node):
    return newNode(parser.nodeName, "")
  return newNode(parser.nodeName, @[node])

func returnSeqAsIs(parser: Parser, nodes: seq[Node]): Node =
  if parser.dropContent:
    return EmptyNode
  return newNode(parser.nodeName, nodes)

func returnItemFlatten(parser: Parser, node: NodeOrNil): Node =
  if not isNil(node):
    if parser.disposable:
      if parser.dropContent:
        return EmptyNode
      return node
    if node.isAnonymous:
      return newNode(parser.nodeName, node)
  elif parser.disposable:
    return EmptyNode
  return newNodw(parser.nodeName, "")

func returnSeqFlatten(parser: Parser, nodes: seq[Node]): Node =
  if parser.dropContent:
    return EmptyNode
  N = seq.len
  if N > 1:
    let res = newSeq[Node](seq.len * 2)
    for child in nodes:
      let anonymous = child.anonymous
      if not child.isLeaf and anonymous:
        for item in child.children:
          res.add(item)
      elif not child.isEmpty or not anonymous:
        res.add(child)
    if res.len > 0 or not parser.disposable:
      return newNode(parser.nodeName, res)
    else:
      return EmptyNode
  elif N == 1:
    return parser.grammer.returnItem(nodes[0])
  if self.disposable:
    return EmptyNode
  return newNode(parser.nodeName, "")

proc init*(grammar: GrammarRef,
           name: string="",
           returnItem: ReturnItemProc): GrammarRef =



let grammarPlaceholderSingleton = GrammarRef(name: "Placeholder")


method parse*(parser: Parser, location: int): ParsingResult {.base.} =
  echo "Parser.parse"
  result = (nil, 0)


proc callParseMethod(parser: Parser, location: int): ParsingResult =
  return parser.parse(location)


proc init*(parser: Parser, ptype: string = ":Parser"): Parser =
  assert ptype != "" and ptype[0] == ':'

  parser.name = ""
  parser.nodeName = ptype
  parser.parserType = ptype
  parser.disposable = true
  parser.dropContent = false
  parser.grammar = grammarPlaceholderSingleton
  parser.symbol = ""
  parser.parseProxy = callParseMethod
  return parser

proc assignName*(name: string, parser: Parser): Parser =
  assert parser.name == ""
  assert name != ""

  parser.nodeName = name
  if name[0] == ':':
    parser.name = name[1 .. ^1]
  else:
    parser.disposable = false
    parser.name = name
  return parser

proc `()`*(parser: Parser, location: int): ParsingResult =
  # is this faster than simply calling parser.parseProxy?
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


proc `()`*(parser: Parser, document: string, location: int = 0): ParsingResult =
  parser.grammar = GrammarRef(name: "adhoc", document: document)  # TODO: do some thing propper here
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


## Leaf Parsers
## ------------
##
## Leaf parsers are "object"-parsers that capture text directly without
## calling other parsers


type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
      text: string
      length: int

proc init*(textParser: TextRef, text: string): TextRef =
  discard Parser(textParser).init(":Text")
  textParser.text = text
  textParser.length = text.len
  return textParser

proc Text*(text: string): TextRef =
  return new(TextRef).init(text)

method parse(parser: TextRef, location: int): ParsingResult =
  if parser.grammar.document.continuesWith(parser.text, location):
    if parser.dropContent:
      return (EMPTY_NODE, location + parser.length)
    elif parser.text != "" or not parser.disposable:
      return (newNode(parser.nodeName, parser.text), location + parser.length)
    return (EMPTY_NODE, location)
  return (nil, location)


## Combined Parsers
## ----------------
##
## Combined "meta"-parsers are parsers that call other parsers.


type
  ReturnValueProc = proc(parser: Parser, node: NodeOrNil): Node
  ReturnValuesProc = proc(parser: Parser, nodes: seq[Node]): Node
  CombinedParser ref CombinedParserObj not nil
  CombinedParserObj = object of ParserObj
    returnValue: ReturnValueProc
    returnValues: ReturnValuesProc



## Test-code


let
  t = "A".assignName Text("A")
#  t = new(Text).initText("A")
let cst = t("A")
echo $cst






