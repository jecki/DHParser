{.experimental: "callOperator".}
{.experimental: "strictNotNil".} 
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}


import std/math
import std/options
import std/sets
import std/strformat
import std/strutils
import std/re

import strslice
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
    grammarVar: GrammarRef
    symbol: ParserOrNil
    subParsers: seq[Parser]
    cycleReached: bool
    # closure: HashSet[Parser]
    parseProxy: ParseProc not nil

  # the GrammarObj
  ReturnItemProc = proc(parser: Parser, node: NodeOrNil): Node
  ReturnSequenceProc = proc(parser: Parser, nodes: seq[Node]): Node
  GrammarRef* = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    document: StringSlice
    root: seq[Parser]
    returnItem: ReturnItemProc not nil
    returnSequence: ReturnSequenceProc not nil


## Special Node-Singletons

let
   EmptyPType* = ":EMPTY"
   EmptyNode* = newNode(EmptyPType, "")

## Parser-object infrastructure

proc `$`*(r: ParsingResult): string =
  let tree = $r.node
  if tree.find('\n') < 0:
    return fmt"node: {tree}, location: {r.location}"
  else:
    return fmt"node:\n{tree}\nlocation: {r.location}"


proc cycleGuard[T](self: Parser, f: proc(): T, alt: T): T =
  if self.cycleReached:
    return alt
  else:
    self.cycleReached = true
    result = f()
    self.cycleReached = false

proc cycleGuard(self: Parser, f: proc()) =
  if not self.cycleReached:
    self.cycleReached = true
    f()
    self.cycleReached = false

# proc `grammar=`*(self: Parser, grammar: GrammarRef) =
#   echo ">>>" & self.nodeName
#   self.grammarVar = grammar
#   for p in self.subParsers:
#     var p_borrowed = p
#     self.cycleGuard(proc() = p_borrowed.grammar = grammar)

proc `grammar=`*(self: Parser, grammar: GrammarRef) =
  self.cycleGuard(proc() = 
    self.grammarVar = grammar
    for p in self.subParsers:
      p.grammar = grammar)

proc grammar(self: Parser) : GrammarRef {.inline.} =
  return self.grammarVar


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

proc returnItemPlaceholder(parser: Parser, node: NodeOrNil): Node =
  result = EmptyNode
  raise newException(AssertionDefect, "returnItem called on GrammaPlacholder")

proc returnSeqPlaceholder(parser: Parser, nodes: seq[Node]): Node =
  result = EmptyNode
  raise newException(AssertionDefect, "returnItem called on GrammaPlacholder")


proc init(grammar: GrammarRef, name: string, document: StringSlice,
          returnItem: ReturnItemProc = returnItemFlatten,
          returnSequence: ReturnSequenceProc = returnSeqFlatten): GrammarRef =
  grammar.name = name
  grammar.document = document
  grammar.root = @[]
  grammar.returnItem = returnItemFlatten
  grammar.returnSequence = returnSeqFlatten
  return grammar

template Grammar(args: varargs[untyped]): GrammarRef =
  new(GrammarRef).init(args)

let GrammarPlaceholder = Grammar("__Placeholder__", EmptyStrSlice, returnItemPlaceholder, returnSeqPlaceholder)


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
  parser.grammarVar = GrammarPlaceholder
  parser.symbol = nil
  parser.subParsers = @[]
  parser.cycleReached = false
  # parser.closure.init()
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
  parser.grammar = Grammar("adhoc", StringSlice(document))  # TODO: do some thing propper here
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


method is_optional(self: Parser): Option[bool] {.base.} =
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
##


## Text-Parser
## ^^^^^^^^^^^
##
## A plain-text-parser
##

type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
    text: string
    slice: StringSlice
    empty: bool

proc init*(textParser: TextRef, text: string): TextRef =
  discard Parser(textParser).init(":Text")
  textParser.text = text
  textParser.slice = toStringSlice(text)
  textParser.empty = (text.len == 0)
  return textParser

proc Text*(text: string): TextRef =
  return new(TextRef).init(text)

method parse*(self: TextRef, location: int): ParsingResult =
  runnableExamples:
    import nodetree
    doAssert Text("A")("A").node.asSxpr() == "(:Text \"A\")"
 
  if self.grammar.document.str[].continuesWith(self.text, location):
    if self.dropContent:
      return (EmptyNode, location + self.text.len)
    elif self.disposable and self.empty:
      return (EmptyNode, location)  
    return (newNode(self.nodeName, self.slice), location + self.text.len)
  return (nil, location)


## Regex-Parser
## ^^^^^^^^^^^^
##
## A parser for regular-expressions
##

type
  RegexRef = ref RegexObj not nil
  RegexObj = object of ParserObj
    regex: Regex

proc rx(rx_str: string): Regex = re("(*UTF8)(*UCP)" & rx_str)

proc init*(regexParser: RegexRef, regex: Regex): RegexRef =
  discard Parser(regexParser).init(":Regex")
  regexParser.regex = regex
  return regexParser

proc Regex*(regex: Regex): RegexRef =
  return new(RegexRef).init(regex)

method parse*(self: RegexRef, location: int): ParsingResult =
  runnableExamples:
    import nodetree, regex
    doAssert Regex(re"\w+")("ABC").node.asSxpr() == "(:Regex \"ABC\")"

  var l = matchLen(self.grammar.document.str[], self.regex, location)
  if l >= 0:
    let text: StringSlice = self.grammar.document[location..<location+l]
    if self.dropContent:
      return (EmptyNode, location + text.len)
    elif self.disposable and text == "":
      return (EmptyNode, location)
    return (newNode(self.nodeName, text), location + text.len)
  return (nil, location)


## Combined Parsers
## ----------------
##
## Combined "meta"-parsers are parsers that call other parsers.

proc infiniteLoopWarning(parser: Parser, node: NodeOrNil, location: int) =
  return

# use Repeat as generalized parser instead!
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
  return repeat

proc Repeat*(parser: Parser, repRange: Range): RepeatRef =
  return new(RepeatRef).init(parser, repRange)

method parse*(self: RepeatRef, location: int): ParsingResult =
  ## Examples:
  runnableExamples:
    doAssert true
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
  let  t = "t".assignName Text("X")
  let cst = t("Y")
  echo $cst
  echo Text("A")("A").node.asSxpr
  doAssert Text("A")("A").node.asSxpr == "(:Text \"A\")"
  echo Regex(rx"\w+")("ABC").node.asSxpr
  doAssert Regex(rx"\w+")("ABC").node.asSxpr == "(:Regex \"ABC\")"
  echo Repeat(Text("A"), (1u32, 3u32))("AA").node.asSxpr





