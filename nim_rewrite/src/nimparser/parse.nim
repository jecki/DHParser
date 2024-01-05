{.experimental: "callOperator".}
{.experimental: "strictNotNil".} 
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}

import std/[enumerate, math, options, sets, strformat, strutils, sugar, tables]

import strslice
import nodetree
import error


const
  MaxTextLen = 2^30 - 1 + 2^30  # yields 2^31 - 1 without overflow
  SearchWindowDefault = 10_000
  NeverMatchPattern = r"$."
let
  NeverMatchRegex   = re(NeverMatchPattern)


## Parser Base and Grammar
## -----------------------
##
## Parser is the base class for all parsers.
##
## Grammar objects contain an ensemble of parsers. A grammar object is
## linked to each contained parser and stores the global variables
## that are shared by all parsers of the ensemble, like memoizing data.

type
  Parser* = ref ParserObj not nil
  ParserOrNil = ref ParserObj
  ErrorCatchingParserRef* = ref ErrorCatchingParserObj not nil
  ErrorCatchingParserOrNil = ref ErrorCatchingParserObj

  ParsingResult = tuple[node: NodeOrNil, location: int32]
  ParsingException = ref object of CatchableError
    origin: ErrorCatchingParserRef
    node: Node
    node_orig_len: int32
    location: int32
    error: ErrorRef
    first_throw: bool

  # Matchers are needed for error-resumption
  MatcherKind = enum mkRegex, mkString, mkProc, mkParser
  MatcherProc = proc(text: StringSlice, start: int32, stop: int32):
                    tuple[pos, length: int32]
  Matcher = object
    case kind: MatcherKind
    of mkRegex:
      reStr: string
      regex: Regex
    of mkString:
      cmpStr: string
    of mkProc:
      findProc: MatcherProc
    of mkParser:
      consumeParser: Parser
  ErrorMatcher = tuple[matcher: Matcher, msg: string]

  ParserFlags = enum isLeaf, noMemoization, isNary, isFlowParser, isLookahead,
   isContextSensitive, isDisposable, dropContent, traversalTracker
  ParserFlagSet = set[ParserFlags]
  ParseProc = proc(parser: Parser, location: int32) : ParsingResult {.nimcall.}
  ParserObj = object of RootObj
    ptype: string
    pname: string
    nodeName: ref string not nil
    flags: ParserFlagSet
    uniqueID: uint32
    grammarVar: GrammarRef
    symbol: ParserOrNil
    subParsers: seq[Parser]
    call: ParseProc not nil
    visited: Table[int, ParsingResult]  # TODO: use btree or something, here...

  ErrorCatchingParserObj = object of ParserObj
    mandatory: uint32
    skipList: seq[Matcher]
    resumeList: seq[Matcher]
    errorList: seq[ErrorMatcher]
    referredParsers: seq[Parser]

  # the GrammarObj
  ReturnItemProc = proc(parser: Parser, node: NodeOrNil): Node {.nimcall.} not nil
  ReturnSequenceProc = proc(parser: Parser, nodes: sink seq[Node]): Node {.nimcall.} not nil
  RollbackItem = tuple
    location: int32
    rollback: proc() {.closure.} not nil
  GrammarFlags* = enum postfixNotation, memoize
  GrammarFlagSet = set[GrammarFlags]
  GrammarRef = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    flags: GrammarFlagSet
    returnItem: ReturnItemProc
    returnSequence: ReturnSequenceProc
    document: StringSlice
    root: ParserOrNil
    commentRe: Regex
    errors: seq[ErrorRef]
    rollbackStack: seq[RollbackItem]
    rollbackLocation: int32
    farthestFail: int32
    farthestParser: ParserOrNil

when defined(js):
  # nim's javascript-target does not allow closure iterators
  type ParserIterator = proc(parser: Parser): seq[Parser]
else:
  type ParserIterator = iterator(parser: Parser): Parser


const
  # RecursionLimit = 1536

  # Parser-Names
  ParserName = ":Parser"
  TextName = ":Text"
  RegExpName = ":RegExp"
  WhitespaceName = ":Whitespace"
  SmartReName = ":SmartReName"
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
  ErrorCatchers = [SeriesName, InterleaveName]
  # Node-Names  
  ZombieName = "__ZOMBIE"
  EmptyName* = ":EMPTY"

let
  EmptyNode* = newNode(EmptyName, "")

## Grammar class

# Forward declarations
proc returnItemFlatten(parser: Parser, node: NodeOrNil): Node
proc returnSeqFlatten(parser: Parser, nodes: sink seq[Node]): Node
proc returnItemPlaceholder(parser: Parser, node: NodeOrNil): Node
proc returnSeqPlaceholder(parser: Parser, nodes: sink seq[Node]): Node

proc cleanUp(grammar: GrammarRef) =
  grammar.flags.excl memoize
  grammar.errors = @[]
  grammar.rollbackStack = newSeqOfCap[RollbackItem](20)
  grammar.rollbackLocation = -2
  grammar.farthestFail = -1
  grammar.farthestParser = nil
  grammar.root = nil

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
  grammar.commentRe = NeverMatchRegex
  grammar.cleanUp()
  return grammar

template Grammar*(args: varargs[untyped]): GrammarRef =
  new(GrammarRef).init(args)

let GrammarPlaceholder = Grammar("__Placeholder__",
  returnItem = returnItemPlaceholder,
  returnSequence = returnSeqPlaceholder)


## Parser-class

# forward declarations
proc memoizationWrapper(parser: Parser, location: int32): ParsingResult


method cleanUp(self: Parser) {.base.} =
  self.visited.clear()

proc init*(parser: Parser, ptype: string = ParserName): Parser =
  assert ptype != "" and ptype[0] == ':'
  parser.pname = ""
  new(parser.nodeName)
  parser.nodeName[] = ptype
  parser.ptype = ptype
  parser.flags = {isDisposable}
  parser.uniqueID = 0
  # parser.equivID = 0
  parser.grammarVar = GrammarPlaceholder
  parser.symbol = nil
  #parser.subParsers = @[]
  # parser.closure.init()
  parser.call = memoizationWrapper
  parser.visited = initTable[int, ParsingResult]()
  parser.cleanUp()
  return parser


## Parser-object infrastructure

proc type*(parser: Parser): string =
  if parser.ptype == ForwardName and parser.subParsers.len > 0:
    parser.subParsers[0].ptype
  else:
    parser.ptype

proc name*(parser: Parser): string =
  if parser.ptype == ForwardName and parser.subParsers.len > 0:
    parser.subParsers[0].pname
  else:
    parser.pname

proc assignSymbol(parser: Parser, symbol: Parser) =
  parser.symbol = symbol
  for p in parser.subParsers:
    if isNil(p.symbol):  assignSymbol(p, symbol)

proc assignName(name: string, parser: Parser): Parser =
  assert parser.pname == ""
  assert name != ""
  parser.nodeName[] = name
  if name[0] == ':':
    parser.pname = name[1..^1]
  elif name.len >= 5 and name[4] == ':':
    if name[0..3] == "DROP":
      parser.flags.incl dropContent
    else:
      assert name[0..3] == "HIDE"
    parser.pname = name[5..^1]
  else:
    # assert parser.ptype != ":Whitespace",
    #        fmt("Insignificant whitespace requires that assigned names begin " &
    #            "with a colon, e.g. \":{name}\", to mark them as disposable!")
    if parser.ptype != ":Whitespace":  # insignificant whitespace is always disposable
      parser.flags.excl isDisposable
    parser.pname = name
  assignSymbol(parser, parser)
  return parser

template assign*[T: Parser](name: string, parser: T): T =
  T(assignName(name, parser))


## parser serialization

proc `$`*(r: ParsingResult): string =
  let tree = $r.node
  if tree.find('\n') < 0:
    return fmt"node: {tree}, location: {r.location}"
  else:
    return fmt"node:\n{tree}\nlocation: {r.location}"

proc `$`*(pe: ParsingException): string =
  fmt("ParsingException(origin: {pe.name}, node_orign_len: {pe.node_orig_len}" &
      " location: {pe.location}, error: \"{pe.error}\", " &
      "first_throw: {pe.first_throw}")

method `$`*(self: Parser): string {.base.} =
  var args: seq[string] = newSeqOfCap[string](self.subParsers.len)
  for p in self.subParsers:
    if not isNil(p):  args.add($p)
  [self.pname, ":", self.type, "(", args.join(", "), ")"].join("")

template repr(parser: Parser): string =
  if parser.pname != "":  parser.pname  else:  $parser


## parser-graph-traversal

method refdParsers*(self: Parser): lent seq[Parser] {.base.} =
  ## Returns all directly referred parsers. The result is always a superset
  ## of the self.subParsers. An example for a parser that is referred by
  ## self but not a sub-parser, would be a parser that is used for resuming
  ## from a parsing error thrown by self.
  return self.subParsers

proc getSubParsers*(parser: Parser): seq[Parser] =
  collect(newSeqOfCap(parser.subParsers.len)):
    for p in parser.subParsers:  p

when defined(js):
  # nim's javascript-target does not allow closure iterators
  proc subs*(parser: Parser): seq[Parser] = parser.subParsers

  proc refdSubs*(parser: Parser): seq[Parser] = parser.refdParsers

  proc anonSubs*(parser: Parser): seq[Parser] =
    collect(newSeqOfCap(parser.subParsers.len)):
      for p in parser.subParsers:
        if p.name.len == 0:
          p

  proc collect_descendants(parser: Parser, selector: ParserIterator = refdSubs,
                           descs: var seq[Parser]) =
    if traversalTracker notin parser.flags:
      parser.flags.incl traversalTracker
      descs.add(parser)
      let subIter = selector
      for p in subIter(parser):
        p.collect_descendants(selector, descs)

  proc descendants(parser: Parser, selector: ParserIterator = refdSubs): seq[Parser] =
    var descs: seq[Parser] = @[]
    collect_descendants(parser, selector, descs)
    return descs

else:
  iterator subs*(parser: Parser): Parser {.closure.} =
    for p in parser.subParsers:
      yield p

  iterator refdSubs*(parser: Parser): Parser {.closure.} =
    for p in parser.refdParsers:
      yield p

  iterator anonSubs*(parser: Parser): Parser {.closure.} =
    for p in parser.subParsers:
      if p.name.len == 0:
        yield p

  iterator descendants(parser: Parser, selector: ParserIterator = refdSubs): Parser {.closure.} =
    if traversalTracker notin parser.flags:
      parser.flags.incl traversalTracker
      yield parser
      let subIter = selector
      for p in subIter(parser):
        for q in p.descendants(selector):  yield q

proc resetTraversalTracker*(parser: Parser) =
  if traversalTracker in parser.flags:
    parser.flags.excl traversalTracker
    for p in parser.refdParsers:
      p.resetTraversalTracker()

template forEach*(parser: Parser, p: untyped, selector: ParserIterator, body: untyped) =
  ## Apply body to each parser p which is reachable from parser, including
  ## parser itself.
  for p in parser.descendants(selector):
    body
  parser.resetTraversalTracker()

# template forEachReferred*(parser: Parser, p: untyped, body: untyped) =
#   forEach(parser, p, refdSubs, body)

# proc trackingApply(parser: Parser, visitor: (Parser) -> bool): bool =
#   if not (traversalTracker in parser.flags):
#     parser.flags.incl traversalTracker
#     if visitor(parser):  return true
#     for p in parser.refdParsers:
#       if p.trackingApply(visitor):  return true
#     return false
#   return false

# proc apply*(parser: Parser, visitor: (Parser) -> bool): bool =
#   # result = parser.trackingApply(visitor)
#   # parser.resetTraversalTracker()
#   result = false
#   parser.forEach(p, refdSubs):
#     if visitor(p):
#       result = true
#       break
#   parser.resetTraversalTracker()

## grammar-property

template grammar*(parser: Parser) : GrammarRef =
  assert parser.grammarVar != GrammarPlaceholder
  parser.grammarVar

method `grammar=`*(self: Parser, grammar: GrammarRef) {.base.} =
  var uniqueID: uint32 = 0
  self.forEach(p, refdSubs):
    assert p.grammarVar == GrammarPlaceholder
    p.grammarVar = grammar
    uniqueID += 1
    p.uniqueID = uniqueID

  # proc visitor(parser: Parser): bool =
  #   assert parser.grammarVar == GrammarPlaceholder
  #   parser.grammarVar = grammar
  #   uniqueID += 1
  #   parser.uniqueID = uniqueID
  #   # parser.equivID = uniqueID  # TODO: Determine "equivalent" parsers, here
  #   return false
  # discard parser.apply(visitor)


## catching syntax errors and resuming after that

proc reentry_point(document: StringSlice, location: int32, rules: seq[Matcher],
                   commentRe: Regex = NeverMatchRegex,
                   searchWindowSize: int32 = SearchWindowDefault): ParsingResult =
  let upperLimit = document.len + 1
  var
    pos = location
    closestMatch = upperLimit
    searchWindow = if searchWindowSize < 0:  document.len - location
                                      else:  searchWindowSize
    skipNode: NodeOrNil = nil
    commentPointer = if commentRe != NeverMatchRegex:  location
                                                else:  upperLimit

  proc nextComment(): tuple[start, firstAfterMatch: int32] =
    if commentPointer < upperLimit:
      let (a, b) = find(document, commentRe, commentPointer)
      if a >= 0:
        commentPointer = b + 1
        return (a, b + 1)
      else:
        commentPointer = upperLimit
    return (-1, -2)

  proc entry_point(m: Matcher): int32 =
    proc searchFunc(start: int32): tuple[pos, length: int32]  =
      case m.kind:
      of mkRegex:  # rx_search
        let (a, b) = find(document, m.regex, start, searchWindow)
        (a, b - a + 1)
      of mkString:  # str_search
        (find(document.str[], m.cmpStr, start, start + searchWindow).int32,
         m.cmpStr.len.int32)
      of mkProc:  # algorithm_search
        m.findProc(document, start, start + searchWindow)
      else:  # should never be reached!
        (-1, 0)

    var
      (a, b) = nextComment()
      (k, length) = searchfunc(location)

    while a < b and b <= k + length:
      (a, b) = nextComment()
    while (a < k and k < b) or (a < k + length and k + length < b):
      (k, length) = searchFunc(b)
      while a < b and b <= k + length:
        (a, b) = nextComment()
    return if k >= 0:  k + length  else:  upperLimit

  for rule in rules:
    case rule.kind:
    of mkParser:
      let parser = rule.consumeParser
      skipNode = nil
      try:
        (skipNode, pos) = parser.call(parser, location)
      except ParsingException as pe:
        let msg = "Error while searching re-entry point with parser" & $parser & ": " & pe.msg
        let error: ErrorRef = Error(msg, location, ErrorWhileRecovering)
        parser.grammar.errors.add(error)
        # skipNode = nil
        pos = upperLimit
      if not isNil(skipNode):
        if pos < closestMatch:
          closestMatch = pos
    else:
      pos = entry_point(rule)
      if pos < closestMatch:
        skipNode = nil
        closestMatch = pos

  if closestMatch >= upperLimit:  closestMatch = -1
  if isNil(skipNode):
    let skipSlice = document[location ..< max(closestMatch, location)]
    skipNode = newNode(ZombieName, skipSlice)
  return (skip_node, closestMatch)


proc handle_error(parser: Parser, pe: ParsingException, location: int32): ParsingResult =
  assert pe.node_orig_len >= 0, $pe
  assert pe.location >= 0, $pe

  let
    grammar = pe.origin.grammar
    gap = pe.location - location
    cut = grammar.document[location..<location + gap]
    rules = pe.origin.resumeList
  var
    node = EmptyNode
    tail = false
    nextLoc = pe.location + pe.node_orig_len
    (skipNode, i) = reentry_point(grammar.document, nextLoc, rules,
                                   grammar.commentRe, SearchWindowDefault)

  if i >= 0 or parser == grammar.root:
    var zombie: NodeOrNil = nil
    if i < 0:  i = 0
    for child in pe.node.children:
      if child.name == ZombieName:
        zombie = child
        break
    if not isNil(zombie) and zombie.isEmpty:
      zombie.result = grammar.document[location..<location + i]
      tail = false
    nextLoc += i
    if pe.first_throw:
      node = pe.node
      if tail and not isNil(skipNode):  node.children.add(skipNode)
    else:
      if not isNil(skipNode):
        node = newNode(parser.nodeName,
                       @[newNode(ZombieName, cut), pe.node, skipNode])
                       .withPos(location)
      else:
        assert false, "Unrechable, theoretically..."
  elif pe.first_throw:
    pe.first_throw = false
    raise pe
  elif (grammar.errors[^1].code in
        {MandatoryContinuationAtEOF, MandatoryContinuationAtEOFNonRoot}):
    node = newNode(parser.nodeName, @[pe.node]).withPos(location)
  else:
    if gap == 0:
      node = newNode(parser.nodeName, @[pe.node]).withPos(location)
    else:
      node = newNode(parser.nodeName, @[newNode(ZombieName, cut), pe.node]).withPos(location)
    pe.node = node
    pe.node_orig_len = pe.node_orig_len + gap
    pe.location = location
    pe.first_throw = false
    raise pe
  return (node, nextLoc)


## parsing-procedures and -methods

method parse*(self: Parser, location: int32): ParsingResult {.base.} =
  echo "Parser.parse"
  result = (nil, 0)

proc pushRollback(grammar: GrammarRef, item: RollbackItem) =
  grammar.rollbackStack.add(item)
  grammar.rollbackLocation = item.location
  grammar.flags.excl memoize

proc rollback(grammar: GrammarRef, location: int32) =
  var rb: RollbackItem
  if grammar.rollbackStack.len > 0 and grammar.rollbackStack[^1].location >= location:
    rb = grammar.rollbackStack.pop()
    rb.rollback()
    if grammar.rollbackStack.len > 0:
      grammar.rollbackLocation = grammar.rollbackStack[^1].location
    else:
      grammar.rollbackLocation = -2

proc memoizationWrapper(parser: Parser, location: int32): ParsingResult =
  let grammar: GrammarRef = parser.grammar
  if location < grammar.rollbackLocation:  grammar.rollback(location)
  if location in parser.visited:  return parser.visited[location]

  let memoization = memoize in grammar.flags
  grammar.flags.incl memoize

  try:
    result = parser.parse(location)
  except ParsingException as pe:
    result = handle_error(parser, pe, location)

  let node = result.node  # isNil(result.node) does not work...
  if isNil(node):
    grammar.farthestFail = location
    grammar.farthestParser = parser
  elif node != EmptyNode:
    node.sourcePos = location

  if memoize in grammar.flags:
    parser.visited[location] = result
    if not memoization:  grammar.flags.excl memoize

proc `()`*(parser: Parser, location: int32): ParsingResult {.inline.} =
  parser.call(parser, location)

proc `()`*(parser: Parser, document: string or StringSlice, location: int32 = 0): ParsingResult =
  if parser.grammarVar == GrammarPlaceholder:
    parser.grammar = Grammar("adhoc", document=toStringSlice(document))
  else:
    parser.grammar.document = toStringSlice(document)
    parser.grammar.cleanUp()
  parser.grammar.root = parser
  result = parser.call(parser, location)
  parser.forEach(p, refdSubs):
    p.cleanUp()


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
      return node.clone(parser.node_name)
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


## ErrorCatchingParser
## ^^^^^^^^^^^^^^^^^^^
##
## ErrorCatchingParser is a base class for parsers that can catch syntax errors.
## Error-catching-parsers are combined parsers (i.e. parsers that contain other
## which are called during the parsing-process) that can be
## configured to fail with a parsing error instead of returning a non-match,
## if all contained parsers from a specific subset of non-mandatory parsers
## have already matched successfully, so that only "mandatory" parsers are
## left for matching. The idea is that once all non-mandatory parsers have
## been consumed it is clear that this parser is a match so that the failure
## to match any of the following mandatory parsers indicates a syntax
## error in the processed document at the location were a mandatory parser
## fails to match.
##
## For the sake of simplicity, the division between the set of non-mandatory
## parsers and mandatory parsers is realized by an index into the list
## of contained parsers. All parsers from the mandatory-index onward are
## considered mandatory once all parsers up to the index have been consumed.

proc init(errorCatching: ErrorCatchingParserRef,
          ptype: string, mandatory: uint32,
          skipList: sink seq[Matcher] = @[],
          resumeList: sink seq[Matcher] = @[],
          errorList: sink seq[ErrorMatcher] = @[]): ErrorCatchingParserRef =
  discard Parser(errorCatching).init(ptype)
  errorCatching.mandatory = mandatory
  errorCatching.skipList = skipList
  errorCatching.resumeList = resumeList
  errorCatching.errorList = errorList
  return errorCatching

# for "lent" see see: https://nim-lang.org/docs/destructors.html#lent-type
method refdParsers*(self: ErrorCatchingParserRef): lent seq[Parser] =
  if self.referredParsers.len == 0:
    self.referredParsers = self.subParsers
    for matcher in self.skipList:
      case matcher.kind:
      of mkParser:
        self.referredParsers.add(matcher.consumeParser)
      else:  discard
    for matcher in self.resumeList:
      case matcher.kind:
      of mkParser:
        self.referredParsers.add(matcher.consumeParser)
      else:  discard
    for errMatcher in self.errorList:
      case errMatcher.matcher.kind:
      of mkParser:
        self.referredParsers.add(errMatcher.matcher.consumeParser)
      else:  discard
  else:
    assert self.referredParsers.len >= self.subParsers.len
  return self.referredParsers

proc reentry(catcher: ErrorCatchingParserRef, location: int32):
     tuple[nd: Node, reloc: int32] =
  if catcher.skipList.len > 0:
    return reentry_point(catcher.grammar.document, location,
                         catcher.skipList, catcher.grammar.commentRe)
  return (newNode(ZombieName, ""), -1)  # placeholder

proc violation(catcher: ErrorCatchingParserRef,
               location: int32,
               wasLookAhead: bool,
               whatExpected: string,
               reloc: int32,
               errorNode: Node):
               tuple[err: ErrorRef, location: int32] =

  proc match(rule: Matcher, text: StringSlice, location: int32): bool =
    case rule.kind:
    of mkRegex:
      return text.matchLen(rule.regex, location) >= 0
    of mkString:
      return text[location:location + rule.cmpStr.len - 1] == matche.cmpStr
    of mkProc:
      return rule.findProc(text, location, location)
    of mkParser:
      let parser = rule.consumeParser
      try:
        (node, pos) = parser.call(parser, location)
        return not isNil(node)
      except ParsingException as pe:
        let msg = "Error while picking error message with: " & $parser
        let error = Error(msg, location, ErrorWhileRecovering)
        parser.grammer.errors.add(error)

  let
    gr = catcher.grammar
    found = gr.document[location..location+9].replace(re'\n', r'\n')
    sym = if isNil(catcher.symbol):  "?"  else:  catcher.symbol.pname
  var error_code = MandatoryCondinuation
  errorNode.pos = location    # if errorNode.sourcePos < 0:
  for (rule, msg) in catcher.errorList:
    if match(rule, gr.document, location):
      i = msg.find(':') + 1
      let code = if i > 0: ErrorCode(msg[0..<i].parseInt.uint16) else: AnError





## Modifiers
## ---------

proc Drop*(parser: Parser): Parser {.inline.} =
  parser.flags = parser.flags + {dropContent, isDisposable}
  parser


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
  assert text.len <= MaxTextLen
  discard Parser(textParser).init(TextName)
  textParser.flags.incl isLeaf
  textParser.text = text
  textParser.slice = toStringSlice(text)
  textParser.empty = (text == "")
  return textParser

template Text*(text: string): TextRef =
  new(TextRef).init(text)

template txt*(text: string): TextRef = Text(text)

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


## RegExp-Parser
## ^^^^^^^^^^^^^
##
## A parser for regular-expressions
##

type
  RegExpInfo = tuple[reStr: string, regex: Regex]
  RegExpRef = ref RegExpObj not nil
  RegExpObj = object of ParserObj
    reInfo: RegExpInfo

const unicodePrefix = "(*UTF8)(*UCP)"

proc rx*(rx_str: string): RegExpInfo = (rx_str, re(unicodePrefix & rx_str))

proc mrx*(multiline_rx_str: string): RegExpInfo =
  (multiline_rx_str, rex(unicodePrefix & multiline_rx_str))

proc init*(regexParser: RegExpRef, rxInfo: RegExpInfo): RegExpRef =
  discard Parser(regexParser).init(RegExpName)
  regexParser.reInfo = rxInfo
  regexParser.flags.incl isLeaf
  return regexParser

template RegExp*(reInfo: RegExpInfo): RegExpRef =
  new(RegExpRef).init(reInfo)

proc RegExp*(reStr: string): RegExpRef =
  let reInfo = if reStr.contains("\n"):  mrx(reStr)  else:  rx(reStr)
  new(RegExpRef).init(reInfo)

template rxp*(reStr: string): RegExpRef = RegExp(reStr)

method parse*(self: RegExpRef, location: int32): ParsingResult =
  runnableExamples:
    import nodetree, regex
    doAssert RegExp(rx"\w+")("ABC").node.asSxpr() == "(:RegExp \"ABC\")"

  var l = matchLen(self.grammar.document, self.reInfo.regex, location)
  if l >= 0:
    if dropContent in self.flags:
      return (EmptyNode, location + l)
    elif isDisposable in self.flags and l == 0:
      return (EmptyNode, location)
    let text: StringSlice = self.grammar.document[location..<location+l]
    return (newNode(self.nodeName, text), location + l)
  return (nil, location)

method `$`*(self: RegExpRef): string =
  ["/", self.reInfo.reStr.replace("/", r"\/"), "/"].join()



## TODO: SmartRE
## ^^^^^^^^^^^^^



## Whitespace
## ^^^^^^^^^^^^^
##
## A parser for insignificant whitespace and comments. Whitespace's
## parse-method always returns a match, if only an empty match in case
## the defining regular expressions did not match.

let RxNeverMatch*: RegExpInfo = (NeverMatchPattern, NeverMatchRegex)

type
  WhitespaceRef = ref WhitespaceObj not nil
  WhitespaceObj = object of ParserObj
    combined: RegExpInfo
    whitespace: RegExpInfo
    comment: RegExpInfo

proc init*(insignificant: WhitespaceRef,
           whitespace, comment: RegExpInfo): WhitespaceRef =
  discard Parser(insignificant).init(WhitespaceName)
  insignificant.whitespace = whitespace
  insignificant.comment = comment
  assert not whitespace.reStr.startsWith(unicodePrefix)
  assert not comment.reStr.startsWith(unicodePrefix)
  let ws = "(?:" & whitespace.reStr & ")?"
  if comment.reStr.len == 0 or comment.reStr == NeverMatchPattern:
    insignificant.combined = rx(ws)
  else:
    let cmmt = "(?:" & comment.reStr & ")"
    insignificant.combined = rx(fmt"(?:{ws}(?:{cmmt}{ws})*)")
  return insignificant

template Whitespace*(whitespace, comment: RegExpInfo): WhitespaceRef =
  new(WhitespaceRef).init(whitespac, comment)

proc Whitespace*(whitespace, comment: string): WhitespaceRef =
  let wsInfo = if whitespace.contains("\n"):  mrx(whitespace)  else:  rx(whitespace)
  let commentInfo = if comment.contains("\n"):  mrx(comment)  else:  rx(comment)
  new(WhitespaceRef).init(wsInfo, commentInfo)

method parse*(self: WhitespaceRef, location: int32): ParsingResult =
  runnableExamples:
    import nodetree, regex
    doAssert Whitespace(r"\s+", r"#.*")("   # comment").node.asSxpr == "(:Whitespace \"   # comment\")"

  var l = matchLen(self.grammar.document, self.combined.regex, location)
  if l >= 0:
    if l > 0 or isDisposable notin self.flags:
      if dropContent in self.flags:
        return (EmptyNode, location + l)
      let text: StringSlice = self.grammar.document[location..<location+l]
      return (newNode(self.nodeName, text), location + l)
  return (EmptyNode, location)

method `grammar=`*(self: WhitespaceRef, grammar: GrammarRef) =
  assert grammar.commentRe == NeverMatchRegex or grammar.commentRe == self.comment.regex or
         self.comment.regex == NeverMatchRegex or self.comment.reStr.len == 0,
         "Multiple definitions of comments or insignificant whitespace not allowed!"
  procCall `grammar=`(Parser(self), grammar)
  if self.comment.reStr.len > 0 and self.comment.regex != NeverMatchRegex:
    grammar.commentRe = self.comment.regex

method `$`*(self: WhitespaceRef): string = "~"


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

const RepLimit = uint32(2^30)   # 2^31 and higher does not work with js-target, any more


proc init*(repeat: RepeatRef, 
           parser: Parser, 
           repRange: Range, 
           name: string = RepeatName): RepeatRef =
  assert repRange[1] > repRange[0]
  discard Parser(repeat).init(name)
  repeat.subParsers = @[parser]
  repeat.repRange = repRange
  return repeat


template Repeat*(parser: Parser, repRange: Range): RepeatRef =
  new(RepeatRef).init(parser, repRange)

template Option*(parser: Parser): RepeatRef =
  new(RepeatRef).init(parser, (0u32, 1u32), OptionName)

template ZeroOrMore*(parser: Parser): RepeatRef =
  new(RepeatRef).init(parser, (0u32, RepLimit), ZeroOrMoreName)

template OneOrMore*(parser: Parser): RepeatRef =
  new(RepeatRef).init(parser, (1u32, RepLimit), OneOrMoreName)

method parse*(self: RepeatRef, location: int32): ParsingResult =
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
  
  if (postfix and subP.name == "" and
      subP.type in NaryParsers):
    subStr = ["(", repr(self.subParsers[0]), ")"].join()  
  else:  
    subStr = repr(self.subParsers[0])

  if self.repRange == (0u32, 1u32):
    if postfix:  subStr & "?"  else:  ["[", subStr, "]"].join()   
  elif self.repRange[0] == 0u32 and self.repRange[1] >= RepLimit:
    if postfix:  subStr & "*"
    else:  ["{", subStr, "}"].join()    
  elif self.repRange[0] == 1u32 and self.repRange[1] >= RepLimit:
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

template Alternative*(parsers: varargs[Parser]): AlternativeRef =
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
  if alternative.pname != "": return Alternative(alternative, other)
  if other.pname == "":
    alternative.subParsers &= other.subParsers
  else:
    alternative.subParsers.add(other)
  return alternative

proc `|`*(alternative: AlternativeRef, other: Parser): AlternativeRef =
  if alternative.pname != "":  return Alternative(alternative, other)
  alternative.subParsers.add(other)
  return alternative

proc `|`*(other: Parser, alternative: AlternativeRef): AlternativeRef =
  if alternative.pname != "":  return Alternative(other, alternative)
  alternative.subParsers = @[other] & alternative.subParsers
  return alternative

template `|`*(parser: Parser, other: Parser): AlternativeRef = Alternative(parser, other)


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
  SeriesObj = object of ErrorCatchingParserObj

proc init*(series: SeriesRef,
           parsers: openarray[Parser],
           mandatory: uint32): SeriesRef =
  assert parsers.len >= 1
  discard ErrorCatchingParserRef(series).init(SeriesName, mandatory)
  series.flags.incl isNary
  series.subParsers = @parsers
  return series

template Series*(parsers: varargs[Parser]): SeriesRef =
  new(SeriesRef).init(parsers, RepLimit)

template Series*(parsers: varargs[Parser], mandatory: uint32): SeriesRef =
  new(SeriesRef).init(parsers, mandatory)

# proc Required*(parsers: varargs[Parser]): SeriesRef =
#   return new(SeriesRef).init(parsers, 0)

proc Required*(series: SeriesRef): SeriesRef {.inline.} =
  series.mandatory = 0
  series


method parse*(self: SeriesRef, location: int32): ParsingResult =
  var
    results = newSeqOfCap[Node](self.subParsers.len)
    loc = location
    reloc = 0'i32
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
        (error, loc) = self.violation(loc, false, parser.pname, reloc, node)
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
    raise ParsingException(origin: self, node: someNode.withPos(location),
                           node_orig_len: loc - location, location: location,
                           error: error, first_throw: true)
  return (someNode, loc)

method `$`*(self: SeriesRef): string =
  let subStrs = collect(newSeqOfCap(self.subParsers.len)):
    for (i, subP) in enumerate(self.subParsers):
      let 
        subStr = repr(subP)
        marker = if i == self.mandatory.int: "§" else: ""
      if subP.type in [AlternativeName, SeriesName] and subP.name == "":
        [marker, "(", subStr, ")"].join()
      else: 
        if marker != "": marker & subStr else: subStr
  subStrs.join(" ")


proc `&`*(series: SeriesRef, other: SeriesRef): SeriesRef =
  if series.pname != "":  return Series(series, other)
  if other.name == "":
    series.subParsers &= other.subParsers
    if series.mandatory >= RepLimit and other.mandatory < RepLimit:
      series.mandatory = min(series.subParsers.len.uint32 + other.mandatory, RepLimit)
  else:
    series.subParsers.add(other)
  return series

proc `&`*(series: SeriesRef, other: Parser): SeriesRef =
  if series.pname != "":  return Series(series, other)
  series.subParsers.add(other)
  return series

proc `&`*(other: Parser, series: SeriesRef): SeriesRef =
  if series.pname != "":  return Series(other, series)
  series.subParsers = @[other] & series.subParsers
  if series.mandatory < RepLimit:
    series.mandatory += 1
  return series

proc `&`*(parser: Parser, other: Parser): SeriesRef = Series(parser, other)


## TODO Intereave-Parser
## ^^^^^^^^^^^^^^^^^^^^^

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
  new(LookaheadRef).init(parser, positive)

method parse*(self: LookaheadRef, location: int32): ParsingResult =
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
  if subP.type in NaryParsers and subP.name == "":
    [prefix, "(", repr(subP), ")"].join()
  else:
    prefix & repr(subP)


## TODO: Lookbehind
## ^^^^^^^^^^^^^^^^

## Context-Sensitive-Parsers 
## -------------------------

## TODO: CAPTURE
## ^^^^^^^^^^^^^


## TODO: Retrieve
## ^^^^^^^^^^^^^^


## TODO: Pop
## ^^^^^^^^^


## Aliasing-Parsers
## ----------------

## TODO: Synonym
## ^^^^^^^^^^^^^

## Forward
## ^^^^^^^

type
  ForwardRef = ref ForwardObj not nil
  ForwardObj = object of ParserObj
    recursionCounter: Table[int32, int32]  # location -> recursion depth


proc forwardWrapper(parser: Parser, location: int32): ParsingResult =
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


method cleanUp(self: ForwardRef) =
  self.recursionCounter.clear()
  procCall self.Parser.cleanUp()

proc init*(forward: ForwardRef): ForwardRef =
  discard Parser(forward).init(ForwardName)
  forward.call = forwardWrapper
  forward.recursionCounter = initTable[int32, int32]()
  return forward

template Forward*(): ForwardRef =
  new(ForwardRef).init()

proc set*(forward: ForwardRef, parser: Parser) =
  forward.subParsers = @[parser]
  if parser.pname == "":
    if forward.pname != "":
      discard assignName(forward.pname, parser)
      forward.symbol = parser       # TODO: Could this lead to problems ?
  if isDisposable in forward.flags:  parser.flags.incl isDisposable
  if dropContent in parser.flags:
    forward.flags.incl dropContent
  else:
    if not (isDisposable in forward.flags):  parser.flags.excl isDisposable
    forward.flags.excl dropContent
  forward.pname = ""


method parse*(self: ForwardRef, location: int32): ParsingResult =
  return self.subParsers[0](location)

  
method `$`*(self: ForwardRef): string =
  repr(self.subParsers[0])


## Test-code

when isMainModule:
  let doc = "text".assignName Text("X")
  let cst = doc("X")
  echo $cst
  echo Text("A")("A").node.asSxpr
  doAssert Text("A")("A").node.asSxpr == "(:Text \"A\")"
  echo RegExp(rx"\w+")("ABC").node.asSxpr
  doAssert RegExp(rx"\w+")("ABC").node.asSxpr == "(:RegExp \"ABC\")"
  echo Whitespace(r"\s+", r"#.*")("   # comment").node.asSxpr
  doAssert Whitespace(r"\s+", r"#.*")("   # comment").node.asSxpr == "(:Whitespace \"   # comment\")"
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
  echo $t.type
  echo " "
  root.grammar = Grammar("adhoc1")

  let WS  = "WS".assign                DROP(rxp"\s*")
  let NUMBER = ":NUMBER".assign         (rxp"(?:0|(?:[1-9]\d*))(?:\.\d+)?" & WS)
  let sign = "sign".assign             ((txt"+" | txt"-") & WS)
  let expression = "expression".assign Forward()
  let group = "group".assign           (txt"(" & WS & expression & txt")" & WS)
  let factor = "factor".assign         (Option(sign) & (NUMBER | group))
  let term = "term".assign             (factor & ZeroOrMore((txt"*" | txt"/") & WS & factor))
  expression.set                       (term & ZeroOrMore((txt"+" | txt"-") & WS & term))
  expression.grammar = Grammar("Arithmetic")
  echo $expression

  let tree = expression("1 + 1").node
  echo tree.asSxpr()

  echo "descendants-iterator"
  for p in descendants(expression):
    echo if p.name.len > 0:  $p.name & " := " & $p  else:  $p
  expression.resetTraversalTracker()

  # echo "apply-callback"
  # proc visitor(p: Parser): bool =
  #   echo if p.name.len > 0:  $p.name & " := " & $p  else:  $p
  #   return false
  #
  # discard expression.apply(visitor)

  echo "---"
  expression.subParsers[0].forEach(p, anonSubs):
    echo $p