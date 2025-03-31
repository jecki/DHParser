{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}

import std/[enumerate, sequtils, strformat, strutils, sugar, tables, unicode, options]

import strslice

type
  Attributes* = OrderedTable[string, string]
  Node {.acyclic.} = object of RootObj
    name*: Option[string]
    childrenSeq: seq[Node]
    textSlice: StringSlice
    attributes: Option[Attributes]
    sourcePos*: int32
  SourcePosUnassignedDefect* = object of Defect
  SourcePosReAssigmentDefect* = object of Defect

proc init*(node: Node, 
           name: ref string or string, 
           data: sink seq[Node] or Option[Node] or sink StringSlice or ref string or string,
           attributes: ref Attributes = nil): Node =
  when name is ref string:
    node.name = name
  else:
    new(node.name)
    node.name[] = name
  when data is seq[Node]:
    node.childrenSeq = data
    node.textSlice = EmptyStringSlice
  elif data is Option[Node]:
    if not isNil(data):
      let nonNilData: Node = data
      node.childrenSeq = @[nonNilData]
    # else:  node.childrenSeq = @[]
    node.textSlice = EmptyStringSlice
  else:
    # node.childrenSeq = @[]
    node.textSlice = toStringSlice(data)
  node.attributes = attributes
  node.sourcePos = -1
  return node

proc init*(node: Node, 
           name: ref string or string, 
           data: sink seq[Node] or Option[Node] or sink StringSlice or ref string or string,
           attributes: Attributes): Node =
  var attrRef: ref Attributes
  new(attrRef)
  attrRef[] = attributes
  return init(node, name, data, attrRef)

template Node.new*(args: varargs[untyped]): Node =
  new(Node).init(args)


template `name=`*(node: Node, name: ref string or string) =
  when name is ref string:
    node.name = name
  else:
    node.name[] = name

template name*(node: Node): string = node.name[]

template isLeaf*(node: Node): bool = node.childrenSeq.len == 0

template hasChildren*(node: Node): bool = node.childrenSeq.len > 0

template isEmpty*(node: Node): bool = node.childrenSeq.len == 0 and node.textSlice.len == 0

template isAnonymous*(node: Node): bool = node.name.len == 0 or node.name[0] == ':'

func content*(node: Node): string =
  if node.isLeaf:
    return $node.textSlice
  else:
    result = ""
    for child in node.childrenSeq:
      result &= child.content

# func children*(node: Node): seq[Node] =
#   return node.children

proc `text=`(node: Node, text: StringSlice or ref string or string) =
  if node.childrenSeq.len > 0:  
    node.childrenSeq = @[]
  if node.textSlice == EmptyStringSlice:
    node.textSlice = toStringSlice(text)
  else:
    when text is StringSlice:
      node.textSlice = text
    elif text is ref string:
      node.textSlice.str = text
    else:
      node.textSlice.str[] = text    

template text*(node: Node): StringSlice = node.textSlice

# see: https://nim-lang.org/docs/destructors.html

proc `children=`(node: Node, children: sink seq[Node]) =
  node.childrenSeq = children
  node.textSlice = EmptyStringSlice

template children*(node: Node): lent seq[Node] = node.childrenSeq

template `result=`*(node: Node, text: StringSlice or ref string or string) =
  node.`text=` text

template `result=`*(node: Node, children: sink seq[Node]) =
  node.`children=` children

template `attr=`*(node: Node, attributes: ref Attributes = nil) =
  node.attributes = attributes

proc `attr=`*(node: Node, attributes: sink Attributes) =
  if isNil(node.attributes):
    new(node.attributes)
  node.attributes[] = attributes

proc attr*(node: Node): lent Attributes =
  if isNil(node.attributes):
    new(node.attributes)
  return node.attributes[]

proc hasAttr*(node: Node, attr: string = ""): bool =
  if isNil(node.attributes):
    return false
  if attr == "":
    return true
  return attr in node.attributes[]

proc runeLen*(node: Node): int32 =
  result = 0
  if node.isLeaf and node.textSlice.len > 0:
    let last = node.textSlice.last
    var i = node.textSlice.first
    while i <= last:
      inc(i, runeLenAt(node.textSlice.str[], Natural(i)))
      inc(result)
  else:
    for child in node.childrenSeq:
      result += child.runeLen

proc asSxpr*(node: Option[Node]): string

func pos*(node: Node): int32 =
  if node.sourcePos < 0:
    raise newException(SourcePosUnassignedDefect, "source position has not yet been assigned")
  return node.sourcePos

proc assignSourcePos(node: Node, sourcePos: int32) : int32 =
  assert sourcePos >= 0
  if node.sourcePos >= 0 and node.sourcePos != sourcePos:
    raise newException(SourcePosReAssigmentDefect, "source position must not be reassigned!")
  node.sourcePos = sourcePos
  var pos = sourcePos
  if node.isLeaf:
    return pos + node.runeLen.int32
  else:
    for child in node.childrenSeq:
      if not child.isNil:
        if child.sourcePos < 0:
          pos += child.assignSourcePos(pos)
        else:
          pos += child.runeLen.int32
  return pos

template `pos=`*(node: Node, sourcePos: int32) =
  discard node.assignSourcePos(sourcePos)

template withPos*(node: Node, sourcePos: int32): Node =
  discard node.assignSourcePos(sourcePos)
  node

proc copy*(node: Node): Node =
  ## Yields a shallow copy of a node
  if node.isLeaf:
    if isNil(node.attributes):
      Node.new(node.name, node.textSlice)
    else:
      Node.new(node.name, node.textSlice, node.attr)
  else:
    if isNil(node.attributes):
      Node.new(node.name, node.childrenSeq)
    else:
      Node.new(node.name, node.childrenSeq, node.attr)

proc clone*(node: Node, newName: ref string not nil): Node =
  ## Creates a new node, keeping merely the result of the old node
  if node.isLeaf:  Node.new(newName, node.textSlice)  else:  Node.new(newName, node.childrenSeq)


const indentation = 2

proc serialize(node: Node,
               opening, closing: proc(nd: Node) : string,
               leafdata: proc(nd: Node): seq[string],
               ind: int = 0): seq[string] =
  result = newSeq[string]()
  var open = opening(node)
  var close = closing(node)
  let openLF = open.endsWith("\n")
  let closeLF = close.startsWith("\n")
  if ind > 0:
    open = if openLF: indent(open[0 ..< ^1], ind) else: indent(open, ind)
    if closeLF: close = indent(close[1 .. ^1], ind)
  else:
    if openLF: open = open[0 ..< ^1]
    if closeLF: close = close[1 .. ^1]
  result.add(open)

  if node.isLeaf:
    var lines = leafdata(node)
    if not openLF and lines.len > 0:
      result[^1] &= lines[0]
      lines.delete(0)  # causes a SEGSIGV Illegal storage access attempt to read from nil? with "nim doc"
    for i in countup(0, lines.len - 1):
      lines[i] = indent(lines[i], ind + indentation)
    result = concat(result, lines)
    if closeLF:
      result.add(close)
    else:
      result[^1] &= close

  else:
    var childBlocks = collect(newSeqofCap(node.children.len)):
      for child in node.children:
        serialize(child, opening, closing, leafdata, ind + indentation)
    if not openLF and childBlocks[0][0].len > 0:
      result[^1] &= childBlocks[0][0]
      childBlocks[0].delete(0)  # causes SIGSEGV (read from nil) on nim doc?
    result = concat(result, concat(childBlocks))
    if closeLF:
      result.add(close)
    else:
      result[^1] &= close


proc asSxpr*(node: Option[Node]): string =
  proc renderAttrs(node: Node): string =
    # if node.attr.len == 0:  return ""
    var attrStrs = newSeq[string](node.attr.len)
    for i, attr, value in enumerate(node.attr):
      attrStrs[i] = fmt"""`({attr} "{value}")"""
    attrStrs.join(" ")

  proc opening(node: Node): string =
    if node.attr.len == 0:
      if node.isLeaf and node.runeLen < 60:
        fmt"({node.name} "
      else:
        fmt"({node.name}{'\n'}"
    else:
      fmt"({node.name} {renderAttrs(node)}{'\n'}"

  func closing(node: Node): string = ")"

  proc leafdata(node: Node): seq[string] =
    func esc(s: string): string =
      s.replace("\\", "\\\\").replace(""""""", """\"""")

    assert node.isLeaf
    var L = node.runeLen
    if L >= 60:
      let s = node.content
      var
        lines: seq[string] = @[]
        i = 0
        k = 0
      while L > 0:
        k = s.runeOffset(i + (if L < 60: L else: 60), i)
        if k <= i:  break
        lines.add('"' & esc(s[i..<k]) & '"')
        i = k
        L -= 60
      return lines
    else:
      return @['"' & esc(node.content) & '"']

  if isNil(node):
    return "nil"
  else:
    return serialize(node, opening, closing, leafdata).join("\n")


proc `$`*(node: Option[Node]): string =
  return node.asSxpr()


# Test-code
when isMainModule:
  var n = Node.new("root", @[Node.new("left", "LEFT", {"id": "007"}.toOrderedTable),
                            Node.new("right", "RIGHT")])
  echo $n
  n.pos = 0
  echo n.children[0].sourcePos
  echo n.children[1].sourcePos

  echo Node.new("ZOMBIE__", "").asSxpr
  n.sourcePos = 3

  var
    s: seq[Node] = @[] 
    m = Node.new("", s)
  echo $m.isLeaf()

  n = Node.new("root", Node.new("element", "Inhalt"))
  echo $n
