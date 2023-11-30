{.experimental: "callOperator".}
{.experimental: "strictNotNil".} 
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}


import std/enumerate
import std/math
import std/options
import std/sets
import std/strformat
import std/strutils
import std/re
import std/sugar
import std/tables

import strslice
import nodetree
import error


## Parser Base and Grammar
## -----------------------
##
## Parser is the base class for all parsers.
##
## Grammar objects contain an ensemble of parsers. A grammar object is
## linked to each contained parser and stores the global variables
## that are shared by all parsers of the ensemble, like memoizing data.

type
  ParsingResult = tuple[node: NodeOrNil, location: int32]
  ParsingException = ref object of CatchableError
    parser: Parser
    node: Node
    node_orig_len: int32
    location: int32
    error: ErrorRef
    first_throw: bool
  ParserFlags = enum isLeaf, noMemoization, isNary, isFlowParser, isLookahead,
   isContextSensitive, isDisposable, dropContent, applyTracker
  ParserFlagSet = set[ParserFlags]
  ParseProc = proc(parser: Parser, location: int32) : ParsingResult {.raises: [ParsingException].}
  Parser* = ref ParserObj not nil
  ParserOrNil = ref ParserObj
  ParserObj = object of RootObj
    name: string
    nodeName: ref string not nil
    ptype: string
    flags: ParserFlagSet
    uniqueID: uint32
    grammarVar: GrammarRef
    symbol: ParserOrNil
    subParsers: seq[Parser]
    call: ParseProc not nil
    visited: Table[int, ParsingResult]

  # the GrammarObj
  ReturnItemProc = proc(parser: Parser, node: NodeOrNil): Node {.raises: [].} not nil
  ReturnSequenceProc = proc(parser: Parser, nodes: sink seq[Node]): Node {.raises: [].} not nil
  RollbackItem = tuple
    location: int32
    rollback: proc() {.closure raises: [].} not nil
  GrammarFlags* = enum postfixNotation, memoize
  GrammarFlagSet = set[GrammarFlags]
  GrammarRef = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    flags: GrammarFlagSet
    returnItem: ReturnItemProc
    returnSequence: ReturnSequenceProc
    document: StringSlice
    errors: seq[ErrorRef]
    rollbackStack: seq[RollbackItem]
    rollbackLocation: int32
    farthestFail: int32
    farthestParser: ParserOrNil


const
  # RecursionLimit = 1536

  # Parser-Names
  ParserName = ":Parser"
  TextName = ":Text"
  RegexName = ":Regex"
  RepeatName = ":Repeat"
  OptionName = ":Option"
  ZeroOrMoreName = ":ZeroOrMore"
  OneOrMoreName = ":OneOrMore"
  AlternativeName = ":Alternative"
  SeriesName = ":Series"
  InterleaveName = ":Interleave"
  LookaheadName = ":Lookahead"
  LookbehindName = ":Lookbehind"
  CaptureName = ":Capture"
  RetrieveName = ":Retrieve"
  PopName = ":Pop"
  SynonymName = ":Synonym"
  ForwardName = ":Forward"
  NaryParsers = [AlternativeName, SeriesName, InterleaveName]
  # Node-Names  
  ZombieName = "__ZOMBIE"
  EmptyName* = ":EMPTY"

let
  EmptyNode* = newNode(EmptyName, "")



## Parser-object infrastructure

proc `$`*(r: ParsingResult): string =
  let tree = $r.node
  if tree.find('\n') < 0:
    return fmt"node: {tree}, location: {r.location}"
  else:
    return fmt"node:\n{tree}\nlocation: {r.location}"


proc parserType*(parser: Parser): string =
  if parser.ptype == ForwardName and parser.subParsers.len > 0:
    parser.subParsers[0].ptype
  else:
    parser.ptype


proc parserName*(parser: Parser): string = 
  if parser.ptype == ForwardName and parser.subParsers.len > 0:
    parser.subParsers[0].name
  else:
    parser.name

proc trackingApply(parser: Parser, visitor: (Parser) -> bool): bool =
  if not (applyTracker in parser.flags):
    parser.flags.incl applyTracker
    if visitor(parser):  return true
    for p in parser.subParsers:
      if p.trackingApply(visitor):  return true
    return false
  return false

proc resetApplyTracker(parser: Parser) =
  if applyTracker in parser.flags:
    parser.flags.excl applyTracker
    for p in parser.subParsers:
      p.resetApplyTracker()

proc apply*(parser: Parser, visitor: (Parser) -> bool): bool =
  result = parser.trackingApply(visitor)
  parser.resetApplyTracker()


## procedures performing early tree-reduction on return values of parsers

proc returnItemAsIs(parser: Parser, node: NodeOrNil): Node =
  if dropContent in parser.flags:
    return EmptyNode
  if isNil(node):
    return newNode(parser.nodeName, "")
  return newNode(parser.nodeName, @[Node(node)])

proc returnSeqAsIs(parser: Parser, nodes: sink seq[Node]): Node =
  if dropContent in parser.flags:
    return EmptyNode
  return newNode(parser.nodeName, nodes)

proc returnItemFlatten(parser: Parser, node: NodeOrNil): Node =
  if not isNil(node):
    if isDisposable in parser.flags:
      if dropContent in parser.flags:
        return EmptyNode
      return node
    if node.isAnonymous:
      return newNode(parser.nodeName, Node(node))
    return newNode(parser.nodeName, node)
  elif isDisposable in parser.flags:
    return EmptyNode
  return newNode(parser.nodeName, "")

proc returnSeqFlatten(parser: Parser, nodes: sink seq[Node]): Node =
  if dropContent in parser.flags:
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
    if res.len > 0 or not (isDisposable in parser.flags):
      return newNode(parser.nodeName, res)
    else:
      return EmptyNode
  elif N == 1:
    return parser.grammarVar.returnItem(parser, nodes[0])
  if isDisposable in parser.flags:
    return EmptyNode
  return newNode(parser.nodeName, "")

proc returnItemPlaceholder(parser: Parser, node: NodeOrNil): Node =
  result = EmptyNode
  raise newException(AssertionDefect, "returnItem called on GrammaPlacholder")

proc returnSeqPlaceholder(parser: Parser, nodes: sink seq[Node]): Node =
  result = EmptyNode
  raise newException(AssertionDefect, "returnItem called on GrammaPlacholder")


proc cleanUp(grammar: GrammarRef) =
  grammar.flags.excl memoize
  grammar.errors = @[]
  grammar.rollbackStack = newSeqOfCap[RollbackItem](20)
  grammar.rollbackLocation = -2
  grammar.farthestFail = -1
  grammar.farthestParser = nil


proc init(grammar: GrammarRef, name: string, 
          flags: GrammarFlagSet = {memoize},
          document: StringSlice = EmptyStringSlice,
          returnItem: ReturnItemProc = returnItemFlatten,
          returnSequence: ReturnSequenceProc = returnSeqFlatten): GrammarRef =
  grammar.name = name
  grammar.flags = flags
  grammar.returnItem = returnItem
  grammar.returnSequence = returnSequence
  grammar.document = document
  grammar.cleanUp()
  return grammar


template Grammar*(args: varargs[untyped]): GrammarRef =
  new(GrammarRef).init(args)


let GrammarPlaceholder = Grammar("__Placeholder__", 
  returnItem = returnItemPlaceholder, 
  returnSequence = returnSeqPlaceholder)


## basic parser-procedures and -methods

method parse*(self: Parser, location: int32): ParsingResult {.base raises: [ParsingException].} =
  echo "Parser.parse"
  result = (nil, 0)


proc grammar(parser: Parser) : GrammarRef {.inline.} =
  return parser.grammarVar


proc `grammar=`*(parser: Parser, grammar: GrammarRef) =
  var uniqueID: uint32 = 0
  proc visitor(parser: Parser): bool =
    assert parser.grammarVar == GrammarPlaceholder
    parser.grammarVar = grammar
    uniqueID += 1
    parser.uniqueID = uniqueID
    # parser.equivID = uniqueID  # TODO: Determine "equivalent" parsers, here
    return false
  discard parser.apply(visitor)


proc handle_parsing_exception(pe: ParsingException): ParsingResult {.raises: [ParsingException].}=
  if isNil(pe):  return (nil, 0)  else:  return (pe.node, pe.location)


proc fatal(parser: Parser, msg: string, location: int32, code: ErrorCode = A_FATALITY): ParsingResult 
  {.raises: [ParsingException].} =
  let 
    node = newNode(ZombieName, msg).withPos(location)
    error: ErrorRef = Error(msg, location, code)
  parser.grammar.errors.add(error)
  result = (node, location)
  raise ParsingException(parser: parser, node: node, node_orig_len: node.runeLen, 
                         location: location, error: error)
 

proc pushRollback(grammar: GrammarRef, item: RollbackItem) =
  grammar.rollbackStack.add(item)
  grammar.rollbackLocation = item.location
  grammar.flags.excl memoize


proc rollback(grammar: GrammarRef, location: int32) {.raises: [].} =
  var rb: RollbackItem
  if grammar.rollbackStack.len > 0 and grammar.rollbackStack[^1].location >= location:
    rb = grammar.rollbackStack.pop()
    rb.rollback()
    if grammar.rollbackStack.len > 0:
      grammar.rollbackLocation = grammar.rollbackStack[^1].location
    else:
      grammar.rollbackLocation = -2


proc memoizationWrapper(parser: Parser, location: int32): ParsingResult {.raises: [ParsingException].} =
  try:
    let grammar: GrammarRef = parser.grammar
    if location < grammar.rollbackLocation:  grammar.rollback(location)
    if location in parser.visited:  return parser.visited[location]

    let memoization = memoize in grammar.flags
    grammar.flags.incl memoize  

    try:
      result = parser.parse(location)
    except ParsingException as pe:
      result = handle_parsing_exception(pe)

    let node = result.node  # isNil(result.node) does not work...
    if isNil(node):
      grammar.farthestFail = location
      grammar.farthestParser = parser
    elif node != EmptyNode:
      node.sourcePos = location

    if memoize in grammar.flags:
      parser.visited[location] = result
      if not memoization:  grammar.flags.excl memoize
      
  except KeyError:
    return fatal(parser, "Totally unexpected KeyError" &  getCurrentExceptionMsg(), location)


method cleanUp(self: Parser) =
  self.visited.clear()


proc init*(parser: Parser, ptype: string = ParserName): Parser =
  assert ptype != "" and ptype[0] == ':'
  parser.name = ""
  new(parser.nodeName)
  parser.nodeName[] = ptype
  parser.ptype = ptype
  parser.flags = {isDisposable}
  parser.uniqueID = 0
  # parser.equivID = 0
  parser.grammarVar = GrammarPlaceholder
  parser.symbol = nil
  parser.subParsers = @[]
  # parser.closure.init()
  parser.call = memoizationWrapper
  parser.visited = initTable[int, ParsingResult]()
  parser.cleanUp()
  return parser


proc assignSymbol(parser: Parser, symbol: Parser) =
  parser.symbol = symbol
  for p in parser.subParsers:
    if isNil(p.symbol):  assignSymbol(p, symbol)

proc assignName(name: string, parser: Parser): Parser =
  assert parser.name == ""
  assert name != ""

  parser.nodeName[] = name
  if name[0] == ':':
    parser.name = name[1 .. ^1]
  else:
    parser.flags.excl isDisposable
    parser.name = name
  assignSymbol(parser, parser)
  return parser

proc assign*[T: Parser](name: string, parser: T): T =
  T(assignName(name, parser))


proc `()`*(parser: Parser, location: int32): ParsingResult {.inline raises: [ParsingException].} =
  parser.call(parser, location)

proc `()`*(parser: Parser, document: string or StringSlice, location: int32 = 0): ParsingResult =
  let doc = when document is string:  document.toStringSlice  else:  document
  if parser.grammar == GrammarPlaceholder:
    parser.grammar = Grammar("adhoc", document=StringSlice(document))
  else:  
    parser.grammar.document = StringSlice(document)
  result = parser.call(parser, location)
  discard parser.apply(
    proc (p: Parser): bool =
      p.cleanUp()
      return false
  )


method `$`*(self: Parser): string {.base.} =
  var args: seq[string] = newSeqOfCap[string](self.subParsers.len)
  for p in self.subParsers:
    if not isNil(p):  args.add($p)
  [self.name, ":", self.parserType, "(", args.join(", "), ")"].join("")
  

proc repr(parser: Parser): string =
  if parser.name != "":  parser.name  else:  $parser


proc getSubParsers*(parser: Parser): seq[Parser] =
  collect(newSeqOfCap(parser.subParsers.len)):
    for p in parser.subParsers:  p
  


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
  assert text.len < 2^32
  discard Parser(textParser).init(TextName)
  textParser.flags.incl isLeaf
  textParser.text = text
  textParser.slice = toStringSlice(text)
  textParser.empty = (text == "")
  return textParser

proc Text*(text: string): TextRef =
  return new(TextRef).init(text)

method parse*(self: TextRef, location: int32): ParsingResult =
  runnableExamples:
    import nodetree
    doAssert Text("A")("A").node.asSxpr() == "(:Text \"A\")"
 
  if self.grammar.document.str[].continuesWith(self.text, location):
    if dropContent in self.flags:
      return (EmptyNode, location + self.text.len.int32)
    elif isDisposable in self.flags and self.empty:
      return (EmptyNode, location)  
    return (newNode(self.nodeName, self.slice), location + self.text.len.int32)
  return (nil, location)

method `$`*(self: TextRef): string =
  ["\"", self.text.replace("\"", "\\\""), "\""].join()


## Regex-Parser
## ^^^^^^^^^^^^
##
## A parser for regular-expressions
##

type
  RegexInfo = tuple[reStr: string, regex: Regex]
  RegexRef = ref RegexObj not nil
  RegexObj = object of ParserObj
    reStr: string  # string-representation of re
    regex: Regex

proc rx*(rx_str: string): RegexInfo = (rx_str, re("(*UTF8)(*UCP)" & rx_str))

proc mrx*(multiline_rx_str: string): RegexInfo = 
  (multiline_rx_str, rex("(*UTF8)(*UCP)" & multiline_rx_str))

proc init*(regexParser: RegexRef, rxInfo: RegexInfo): RegexRef =
  discard Parser(regexParser).init(RegexName)
  regexParser.reStr = rxInfo.reStr
  regexParser.regex = rxInfo.regex
  regexParser.flags.incl isLeaf
  return regexParser

proc Regex*(reInfo: RegexInfo): RegexRef =
  return new(RegexRef).init(reInfo)

proc Regex*(reStr: string): RegexRef =
  let reInfo = if reStr.contains("\n"):  mrx(reStr)  else:  rx(reStr)
  return new(RegexRef).init(reInfo)

method parse*(self: RegexRef, location: int32): ParsingResult =
  runnableExamples:
    import nodetree, regex
    doAssert Regex(re"\w+")("ABC").node.asSxpr() == "(:Regex \"ABC\")"

  var l = matchLen(self.grammar.document.str[], self.regex, location).int32
  if l >= 0:
    let text: StringSlice = self.grammar.document[location..<location+l]
    if dropContent in self.flags:
      return (EmptyNode, location + text.len)
    elif isDisposable in self.flags and text == "":
      return (EmptyNode, location)
    return (newNode(self.nodeName, text), location + text.len)
  return (nil, location)

method `$`*(self: RegexRef): string =
  ["/", self.reStr.replace("/", r"\/"), "/"].join()


## TODO: SmartRE
## ^^^^^^^



## Combined Parsers
## ----------------
##
## Combined "meta"-parsers are parsers that call other parsers
## ("sub-parsers").

proc infiniteLoopWarning(parser: Parser, node: NodeOrNil, location: int32) =
  return


## Repeat-Parsers
## ^^^^^^^^^^^^^^
## 
## A family of combined parsers that apply the sub-parser and
## match if the sub-parser matches at least n-times in sequence
## and at most k-times, where n is the "lower bound" and k the
## upper bound and k >= n.
## 
## Repeat 
##    is the most general repeat-parser, where the lower bound
##    and upper bound are passed as parameters on initialization.
## 
## Option
##    matches always, no matter whether the sub-parser matches
##    or not. If it matches it is applied once before "Option" returns.
## 
## ZeroOrMore
##    matches always. If it matches the sub-parser is applied
##    as often as possible, i.e. until it does not match the beginning
##    of the rest of the document, any more.
## 
## OneOrMore
##    fails if the sub-parser does not match. Otherwise, it returns
##    as many matches of the sub-parser as possible.


type
  Range = tuple[min: uint32, max: uint32]
  RepeatRef = ref RepeatObj not nil
  RepeatObj = object of ParserObj
    repRange: Range

const inf = uint32(2^32 - 1)


proc init*(repeat: RepeatRef, 
           parser: Parser, 
           repRange: Range, 
           name: string = RepeatName): RepeatRef =
  assert repRange[1] > repRange[0]
  discard Parser(repeat).init(name)
  repeat.subParsers = @[parser]
  repeat.repRange = repRange
  return repeat


proc Repeat*(parser: Parser, repRange: Range): RepeatRef =
  return new(RepeatRef).init(parser, repRange)

proc Option*(parser: Parser): RepeatRef =
  return new(RepeatRef).init(parser, (0u32, 1u32), OptionName)

proc ZeroOrMore*(parser: Parser): RepeatRef =
  return new(RepeatRef).init(parser, (0u32, inf), ZeroOrMoreName)

proc OneOrMore*(parser: Parser): RepeatRef =
  return new(RepeatRef).init(parser, (1u32, inf), OneOrMoreName)

method parse*(self: RepeatRef, location: int32): ParsingResult {.raises: [ParsingException].} =
  ## Examples:
  runnableExamples:
    doAssert true
  var
    nodes = newSeqOfCap[Node](max(self.repRange.min, 1))
    loc = location
    lastLoc = location
    node: NodeOrNil = nil
  for i in countup(1u32, self.repRange.min):
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

method `$`*(self: RepeatRef): string =
  let 
    postfix = postfixNotation in self.grammar.flags
    subP = self.subParsers[0]
  var
    subStr: string
  
  if (postfix and subP.parserName == "" and
      subP.parserType in NaryParsers): 
    subStr = ["(", repr(self.subParsers[0]), ")"].join()  
  else:  
    subStr = repr(self.subParsers[0])

  if self.repRange == (0u32, 1u32):
    if postfix:  subStr & "?"  else:  ["[", subStr, "]"].join()   
  elif self.repRange == (0u32, inf):
    if postfix:  subStr & "*"
    else:  ["{", subStr, "}"].join()    
  elif self.repRange == (1u32, inf):
    if postfix:  subStr & "+"
    else:  ["{", subStr, "}+"].join()
  else:
    let (min, max) = self.repRange
    [subStr, "(", $min, ", ", $max, ")"].join()


## Alternative-Parser
## ^^^^^^^^^^^^^^^^^^
## 
## The Alternative-parser matches if the first of series
## of parsers matches that are applied in order. It fails
## if none of theses parsers matches.

type 
  AlternativeRef = ref AlternativeObj not nil
  AlternativeObj = object of ParserObj


proc init*(alternative: AlternativeRef, parsers: openarray[Parser]): AlternativeRef =
  discard Parser(alternative).init(AlternativeName)
  alternative.subParsers = @parsers
  alternative.flags.incl isNary
  return alternative

proc Alternative*(parsers: varargs[Parser]): AlternativeRef =
  new(AlternativeRef).init(parsers)

method parse*(self: AlternativeRef, location: int32): ParsingResult = 
  var
    loc = location 
    node: NodeOrNil
  for parser in self.subParsers:
    (node, loc) = parser(loc)
    if not isNil(node):
      return (self.grammar.returnItem(self, node), loc)
  return (nil, location)

method `$`*(self: AlternativeRef): string =
  let subStrs = collect(newSeqOfCap(self.subParsers.len)):  
    for subP in self.subParsers:  repr(subP)
  subStrs.join("|")

proc `|`*(alternative: AlternativeRef, other: AlternativeRef): AlternativeRef =
  if alternative.name != "": return Alternative(alternative, other)
  if other.name == "":
    alternative.subParsers &= other.subParsers
  else:
    alternative.subParsers.add(other)
  return alternative

proc `|`*(alternative: AlternativeRef, other: Parser): AlternativeRef =
  if alternative.name != "":  return Alternative(alternative, other)
  alternative.subParsers.add(other)
  return alternative

proc `|`*(other: Parser, alternative: AlternativeRef): AlternativeRef =
  if alternative.name != "":  return Alternative(other, alternative)
  alternative.subParsers = @[other] & alternative.subParsers
  return alternative

proc `|`*(parser: Parser, other: Parser): AlternativeRef = Alternative(parser, other)


## Series-Parser
## ^^^^^^^^^^^^^
## 
## The Series-parser calls a series of other parsers ("sub-parsers") in
## sequence. It matches, if the whole series of sub-parsers matches.
## It fails if one of these parsers does not match. In this case the 
## sub-parsers following in the list will not be applied, any more.
## 
## Series parsers can be initialized with a "mandatory"-threshold which
## is an index (counted from zero) to the sequence of sub-parsers. If 
## all sub-parsers up to this index have matched then the following 
## parsers are considered "mandatory" which means that if any of these 
## parsers does not match the Series-parser will not only fail to match, 
## but also report an unexpected continuation error.

type
  SeriesRef = ref SeriesObj not nil
  SeriesObj = object of ParserObj
    mandatory: uint32

proc init*(series: SeriesRef,
           parsers: openarray[Parser],
           mandatory: uint32 = inf): SeriesRef =
  discard Parser(series).init(SeriesName)
  series.flags.incl isNary
  series.subParsers = @parsers
  series.mandatory = mandatory
  return series

proc Series*(parsers: varargs[Parser]): SeriesRef =
  return new(SeriesRef).init(parsers)

proc Series*(parsers: varargs[Parser], mandatory: uint32 = inf): SeriesRef =
  return new(SeriesRef).init(parsers, mandatory)

proc reentry(self: SeriesRef, location: int32): tuple[nd: Node, reloc: int32] =
  return (newNode(ZombieName, ""), -1)  # placeholder

proc violation(self: SeriesRef,
                        location: int32,
                        wasLookAhead: bool,
                        whatExpected: string,
                        reloc: int32,
                        error_node: NodeOrNil): 
                        tuple[err: ErrorRef, location: int32] =
  let error = Error("mandatory violation detected", location)
  self.grammar.errors.add(error)
  return (error, reloc)
  

method parse*(self: SeriesRef, location: int32): ParsingResult {.raises: [ParsingException].} =
  var
    results = newSeqOfCap[Node](self.subParsers.len)
    loc = location
    reloc = 0i32
    error: ErrorOrNil = nil
    node, nd: NodeOrNil
    someNode: Node
  for pos, parser in enumerate(self.subParsers):
    (node, loc) = parser(loc)
    if isNil(node):
      if pos.uint32 < self.mandatory:
        return (nil, location)
      else:
        # TODO: Fill the placeholders: reentry and violation in, above!
        (someNode, reloc) = self.reentry(loc)
        (error, loc) = self.violation(loc, false, parser.name, reloc, node)
        if reloc >= 0:
          (nd, loc) = parser(loc)
          if not isNil(nd):
            results.add(someNode)
            someNode = nd
          if not someNode.isEmpty or not someNode.isAnonymous:
             results.add(someNode)
        else:
          results.add(someNode)
          break
    elif not node.isEmpty or not node.isAnonymous:
      results.add(node)
  someNode = self.grammar.returnSequence(self, results)
  if not isNil(error):
    raise ParsingException(parser: self, node: someNode.withPos(location),
                           node_orig_len: loc - location, location: location,
                           error: error, first_throw: true)
  return (someNode, loc)

method `$`*(self: SeriesRef): string =
  let subStrs = collect(newSeqOfCap(self.subParsers.len)):
    for (i, subP) in enumerate(self.subParsers):
      let 
        subStr = repr(subP)
        marker = if i == self.mandatory.int: "§" else: ""
      if subP.parserType in [AlternativeName, SeriesName] and subP.parserName == "":
        [marker, "(", subStr, ")"].join()
      else: 
        if marker != "": marker & subStr else: subStr
  subStrs.join(" ")


proc `&`*(series: SeriesRef, other: SeriesRef): SeriesRef =
  if series.name != "":  return Series(series, other)
  if other.parserName == "":
    series.subParsers &= other.subParsers
    if series.mandatory == inf and other.mandatory != inf:
      series.mandatory = series.subParsers.len.uint32 + other.mandatory
  else:
    series.subParsers.add(other)
  return series

proc `&`*(series: SeriesRef, other: Parser): SeriesRef =
  if series.name != "":  return Series(series, other)
  series.subParsers.add(other)
  return series

proc `&`*(other: Parser, series: SeriesRef): SeriesRef =
  if series.name != "":  return Series(other, series)
  series.subParsers = @[other] & series.subParsers
  if series.mandatory != inf:
    series.mandatory += 1
  return series

proc `&`*(parser: Parser, other: Parser): SeriesRef = Series(parser, other)


## TODO Intereave-Parser
## ^^^^^^^^^^^^^^^^

## Control-Flow-Parsers
## --------------------
##
## Lookahead
## ^^^^^^^^^

type
  LookaheadRef = ref LookaheadObj not nil
  LookaheadObj = object of ParserObj
    positive: bool


proc init*(lookahead: LookaheadRef,
           parser: Parser,
           positive: bool = true): LookaheadRef =
  discard Parser(lookahead).init(LookAheadName)
  lookahead.subParsers = @[parser]
  lookahead.flags.incl {isFlowParser, isLookahead} 
  lookahead.positive = positive
  return lookahead

proc Lookahead(parser: Parser, positive: bool = true): LookaheadRef =
  return new(LookaheadRef).init(parser, positive)

method parse*(self: LookaheadRef, location: int32): ParsingResult {.raises: [ParsingException].} =
  var 
    loc: int32
    node: NodeOrNil
  
  (node, loc) = self.subParsers[0](location)
  if self.positive xor isNil(node):
    if isDisposable in self.flags:
      node = EmptyNode
    else:
      node = newNode(self.nodeName, "")
    return (node, location)
  else:
    return (nil, location)
  
method `$`*(self: LookaheadRef): string =
  let 
    prefix = if self.positive: "&" else: "<-&"
    subP = self.subParsers[0]
  if subP.parserType in NaryParsers and subP.parserName == "":
    [prefix, "(", repr(subP), ")"].join()
  else:
    prefix & repr(subP)


## TODO: Lookbehind
## ^^^^^^^^^

## Context-Sensitive-Parsers 
## -------------------------

## TODO: CAPTURE
## ^^^^^^^


## TODO: Retrieve
## ^^^^^^^^


## TODO: Pop
## ^^^


## Aliasing-Parsers
## ----------------

## TODO: Synonym
## ^^^^^^^

## Forward
## ^^^^^^^

type
  ForwardRef = ref ForwardObj not nil
  ForwardObj = object of ParserObj
    recursionCounter: Table[int32, int32]  # location -> recursion depth


proc forwardWrapper(parser: Parser, location: int32): ParsingResult {.raises: [ParsingException].} =
  try:
    let grammar: GrammarRef = parser.grammar
    if location <= grammar.rollbackLocation:  grammar.rollback(location)
    if location in parser.visited:  return parser.visited[location]

    var depth: int32
    if location in parser.ForwardRef.recursionCounter:
      depth = parser.ForwardRef.recursionCounter[location]
      if depth == 0:
        grammar.flags.excl memoize
        result = (nil, location)
      else:
        parser.ForwardRef.recursionCounter[location] = depth - 1
        result = parser.subParsers[0](location)
        parser.ForwardRef.recursionCounter[location] = depth
    else:
      parser.ForwardRef.recursionCounter[location] = 0
      let memoization = memoize in grammar.flags
      grammar.flags.incl memoize

      result = parser.subParsers[0](location)

      if not isNil(result.node):
        depth = 1

        while true:
          parser.ForwardRef.recursionCounter[location] = depth
          grammar.flags.incl memoize
          var rb = grammar.rollbackStack.len

          var nextResult = parser.subParsers[0](location)

          if nextResult.location <= result.location:
            while grammar.rollbackStack.len > rb:
              var rbItem = grammar.rollbackStack.pop()
              rbItem.rollback()
              if grammar.rollbackStack.len > 0:
                grammar.rollbackLocation = grammar.rollbackStack[^1].location
              else:
                grammar.rollbackLocation = -2
            break

          result = nextResult
          depth += 1

      if not memoization:  grammar.flags.excl memoize
      if memoize in grammar.flags:  parser.visited[location] = result
  except KeyError:
    return fatal(parser, "Totally unexpected KeyError: " &  getCurrentExceptionMsg(), location)


method cleanUp(self: ForwardRef) =
  self.recursionCounter.clear()
  procCall self.Parser.cleanUp()

proc init*(forward: ForwardRef): ForwardRef =
  discard Parser(forward).init(ForwardName)
  forward.call = forwardWrapper
  forward.recursionCounter = initTable[int32, int32]()
  return forward

proc Forward*(): ForwardRef =
  return new(ForwardRef).init()

proc set*(forward: ForwardRef, parser: Parser) =
  forward.subParsers = @[parser]
  if parser.name == "":
    if forward.name != "":
      parser.name = forward.name
      assignSymbol(parser, parser)
      forward.symbol = parser       # TODO: Could this lead to problems ?
  if isDisposable in forward.flags:  parser.flags.incl isDisposable
  if dropContent in parser.flags:
    forward.flags.incl dropContent
  else:
    if not (isDisposable in forward.flags):  parser.flags.excl isDisposable
    forward.flags.excl dropContent
  forward.name = ""


method parse*(self: ForwardRef, location: int32): ParsingResult {.raises: [ParsingException].} =
  return self.subParsers[0](location)

  
method `$`*(self: ForwardRef): string =
  repr(self.subParsers[0])




## Test-code

when isMainModule:
  let txt = "txt".assignName Text("X")
  let cst = txt("X")
  echo $cst
  echo Text("A")("A").node.asSxpr
  doAssert Text("A")("A").node.asSxpr == "(:Text \"A\")"
  echo Regex(rx"\w+")("ABC").node.asSxpr
  doAssert Regex(rx"\w+")("ABC").node.asSxpr == "(:Regex \"ABC\")"
  echo Repeat(Text("A"), (1u32, 3u32))("AAAA").node.asSxpr
  echo ("r".assignName Repeat(Text("A"), (1u32, 3u32)))("AA").node.asSxpr
  echo Series(Text("A"), Text("B"), Text("C"), mandatory=1u32)("ABC").node.asSxpr
  try:
    echo Series(Text("A"), Text("B"), Text("C"), mandatory=1u32)("ABX").node.asSxpr
  except ParsingException:
    echo "Expected Exception"
  echo Alternative(Text("A"), Text("B"))("B").node.asSxpr
  doAssert Alternative(Text("A"), Text("B"))("B").node.asSxpr == "(:Text \"B\")"
  doAssert $Alternative(Text("A"), Text("B")) == "\"A\"|\"B\""
  doAssert $Series(Text("A"), Text("B"), Text("C"), mandatory=1u32) == "\"A\" §\"B\" \"C\""
  echo $((Text("A")|Text("B"))|(Text("C")|Text("D")|Text("E")))

  let root = "root".assign Forward()
  let t = "t".assign Text("A") & root
  let s = "s".assign root & t & t
  root.set(s)
  echo $root
  echo $t
  echo $root.subParsers[0].subparsers.len
  echo $s
  echo $t.parserType
  echo " "
  root.grammar = Grammar("adhoc1")

  let WS  = "WS".assign                Regex(rx"\s*")
  let NUMBER = "NUMBER".assign         (Regex(rx"(?:0|(?:[1-9]\d*))(?:\.\d+)?") & WS)
  let sign = "sign".assign             ((Text("+") | Text("-")) & WS)
  let expression = "expression".assign Forward()
  let group = "group".assign           (Text("(") & WS & expression & Text(")") & WS)
  let factor = "factor".assign         (Option(sign) & (NUMBER | group))
  let term = "term".assign             (factor & ZeroOrMore((Text("*") | Text("/")) & WS & factor))
  expression.set                       (term & ZeroOrMore((Text("+") | Text("-")) & WS & term))
  expression.grammar = Grammar("Arithmetic")

  let tree = expression("1 + 1").node
  echo tree.asSxpr()

