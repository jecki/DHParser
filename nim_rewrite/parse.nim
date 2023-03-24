{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/math
import std/options
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
  ParserOrNil = ref ParserObj
  ParserObj = object of RootObj
    name: string
    nodeName: string
    parserType: string
    disposable: bool
    dropContent: bool
    eqClass: uint
    grammar: GrammarRef
    symbol: ParserOrNil
    subParsers: seq[Parser]
    parseProxy: ParseProc not nil

  # the GrammarObj
  ReturnItemProc = proc(parser: Parser, node: NodeOrNil): Node
  ReturnSequenceProc = proc(parser: Parser, nodes: seq[Node]): Node
  GrammarRef* = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    document: string
    roots: seq[Parser]
    returnItem: ReturnItemProc
    returnSequence: ReturnSequenceProc


## Special Node-Singletons

let
   EmptyPType* = ":EMPTY"
   EmptyNode* = newNode(EmptyPType, "")


proc `$`*(r: ParsingResult): string =
  let tree = $r.node
  if tree.find('\n') < 0:
    return fmt"node: {tree}, location: {r.location}"
  else:
    return fmt"node:\n{tree}\nlocation: {r.location}"


## procedures performing early tree-reduction on return values of parsers

proc returnItemAsIs(parser: Parser, node: NodeOrNil): Node =
  if parser.dropContent:
    return EmptyNode
  if isNil(node):
    return newNode(parser.nodeName, "")
  return newNode(parser.nodeName, @[Node(node)])

proc returnSeqAsIs(parser: Parser, nodes: seq[Node]): Node =
  if parser.dropContent:
    return EmptyNode
  return newNode(parser.nodeName, nodes)

proc returnItemFlatten(parser: Parser, node: NodeOrNil): Node =
  if not isNil(node):
    if parser.disposable:
      if parser.dropContent:
        return EmptyNode
      return node
    if node.isAnonymous:
      return newNode(parser.nodeName, @[Node(node)])
  elif parser.disposable:
    return EmptyNode
  return newNode(parser.nodeName, "")

proc returnSeqFlatten(parser: Parser, nodes: seq[Node]): Node =
  if parser.dropContent:
    return EmptyNode
  let N = nodes.len
  if N > 1:
    var res = newSeqOfCap[Node](N * 2)
    for child in nodes:
      let anonymous = child.isAnonymous
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
    return parser.grammar.returnItem(parser, nodes[0])
  if parser.disposable:
    return EmptyNode
  return newNode(parser.nodeName, "")



let GrammarPlaceholder = GrammarRef(name: "__Placeholder__")


## basic parser-procedures and -methods

method parse*(self: Parser, location: int): ParsingResult {.base.} =
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
  parser.grammar = GrammarPlaceholder
  parser.symbol = nil
  parser.subParsers = @[]
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
  parser.symbol = parser
  return parser
  # TODO: assign name as symbol to sub-parsers


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


method is_optional(self: Parser): Option[bool] =
  ## Returns some(true), if the parser can never fail, i.e. never yields nil
  ## instead of a node.
  ## Returns some(false), if the parser can fail.
  ## Returns none(bool), if it is not known whether the parser can fail
  return  none(bool)


## Leaf Parsers
## ------------
##
## Leaf parsers are "object"-parsers that capture text directly without
## calling other parsers


type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
    text: string

proc init*(textParser: TextRef, text: string): TextRef =
  discard Parser(textParser).init(":Text")
  textParser.text = text
  return textParser

proc Text*(text: string): TextRef =
  return new(TextRef).init(text)

method parse(self: TextRef, location: int): ParsingResult =
  runnableExamples:
    doAssert Text("A")("A").node.asSxpr == "(:Text \"A\")"

  if self.grammar.document.continuesWith(self.text, location):
    if self.dropContent:
      return (EMPTY_NODE, location + self.text.len)
    elif self.text != "" or not self.disposable:
      return (newNode(self.nodeName, self.text), location + self.text.len)
    return (EMPTY_NODE, location)
  return (nil, location)


## Combined Parsers
## ----------------
##
## Combined "meta"-parsers are parsers that call other parsers.

proc infiniteLoopWarning(parser: Parser, node: NodeOrNil, location: int) =
  return

# type
#   OptionRef = ref OptionObj not nil
#   OptionObj = object of ParserObj
#
# proc init*(option: OptionRef, parser: Parser): OptionRef =
#   discard Parser(option).init(":Option")
#   option.subParsers = @[parser]
#   return option
#
# proc Option*(parser: Parser): OptionRef =
#   return new(OptionRef).init(parser)
#
# method parse(self: OptionRef, location: int): ParsingResult =
#   let pr = self.subParsers[0](location)
#   return (self.grammar.returnItem(self, pr.node), pr.location)


type
  Range = tuple[min: uint32, max: uint32]
  RepeatRef = ref RepeatObj not nil
  RepeatObj = object of ParserObj
    repRange: Range

const inf = 2^32 - 1

proc init*(repeat: RepeatRef, parser: Parser, repRange: Range): RepeatRef =
  discard Parser(repeat).init(":Repeat")
  repeat.subParsers = @[parser]
  repeat.repRange = repRange

proc Repeat*(parser: Parser, repRange: Range): RepeatRef =
  return new(RepeatRef).init(parser, repRange)

method parse(self: RepeatRef, location: int): ParsingResult =
  ## Examples:
  runnableExamples:
    doAssert True
  var
    nodes = newSeqOfCap[Node](max(self.repRange.min, 1))
    loc = location
    lastLoc = location
    node: NodeOrNil = nil
  for i in countup(uint32(1), self.repRange.min):
    (node, loc) = self.subParsers[0](loc)
    if isNil(node):
      return (nil, lastLoc)
    else:
      nodes.add(node)
    if lastLoc >= loc:
      self.infiniteLoopWarning(node, loc)
      break  # avoid infinite loops
    lastLoc = loc
  for i in countup(self.repRange.min +  1, self.repRange.max):
    (node, loc) = self.subParsers[0](loc)
    if isNil(node):
      break
    else:
      nodes.add(node)
    if lastLoc >= loc:
      self.infiniteLoopWarning(node, loc)
      break
    lastLoc = loc
  return (self.grammar.returnSequence(self, nodes), loc)


method is_optional(self: RepeatRef): Option[bool] =
  if self.repRange.min == 0:
    return some(true)
  else:
    return none(bool)


## Test-code

when isMainModule:
#   let
#     t = "t".assignName Text("A")
#   #  t = new(Text).initText("A")
#   let cst = t("A")
#   echo $cst
  echo Text("A")("A").node.asSxpr
  doAssert Text("A")("A").node.asSxpr == "(:Text \"A\")"





