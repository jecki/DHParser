{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}

import std/enumerate
import std/sequtils
import std/strformat
import std/strutils
import std/sugar
import std/tables
import std/unicode

import strslice

type
  Attributes* = OrderedTable[string, string]
  Node* = ref NodeObj not nil
  NodeOrNil* = ref NodeObj
  NodeObj {.acyclic.} = object of RootObj
    name*: string
    children: seq[Node]
    text: StringSlice
    attributes*: Attributes
    sourcePos: int32
  SourcePosUnassignedDefect* = object of Defect
  SourcePosReAssigmentDefect* = object of Defect

proc init*(node: Node, 
          name: string, 
          content: seq[Node] or StringSlice or ref string or string, 
          attributes: Attributes = Attributes()): Node =
  node.name = name
  when content is seq[Node]:
    node.children = content
    node.text = EMPTY_STRSLICE
  else:
    node.children = @[]
    node.text = toStringSlice(content)
  node.attributes = attributes
  node.sourcePos = -1
  return node

template newNode*(args: varargs[untyped]): Node =
  new(Node).init(args)

func isLeaf*(node: Node): bool = node.children.len == 0

proc isEmpty*(node: Node): bool = node.children.len == 0 and node.text.len == 0

func isAnonymous*(node: Node): bool = node.name.len == 0 or node.name[0] == ':'

func content*(node: Node): string =
  if node.isLeaf:
    return node.text.str[]
  else:
    for child in node.children:
      result &= child.content

func children*(node: Node): seq[Node] =
  return node.children

proc `result=`*(node: Node, text: StringSlice or ref string or string) =
  if node.children.len > 0:  
    node.children = @[]
    node.text = toStringSlice(text)
  elif not isNil(node.text):
    when text is StringSlice:
      node.text = text
    elif text is ref string:
      node.text.str = text
    else:
      node.text.str[] = text
  else:  # practically unreachable
    node.text = toStringSlice(text)


proc `result=`*(node: Node, children: seq[Node]) =
  node.children = children
  node.text = EMPTY_STRSLICE

proc runeLen*(node: Node): int32 =
  result = 0
  if node.isLeaf:
    let last = node.text.last
    var i = node.text.first
    while i <= last:
      inc(i, runeLenAt(node.text.str[], Natural(i)))
      inc(result)
  else:
    for child in node.children:
      result += child.runeLen

func sourcePos*(node: Node): int32 =
  if node.sourcePos < 0:
    raise newException(SourcePosUnassignedDefect, "source position has not yet been assigned")
  return node.sourcePos

proc assignSourcePos(node: Node, sourcePos: int32) : int32 =
  if node.sourcePos >= 0:
    raise newException(SourcePosReAssigmentDefect, "source position must not be reassigned!")
  node.sourcePos = sourcePos
  var pos = sourcePos
  if node.isLeaf:
    return pos + int32(node.runeLen)
  else:
    for child in node.children:
      if not child.isNil:
        pos += child.assignSourcePos(pos)
  return pos

proc `sourcePos=`*(node: Node, sourcePos: int32) =
  discard node.assignSourcePos(sourcePos)

proc withSourcePos*(node: Node, sourcePos: int32): Node =
  discard node.assignSourcePos(sourcePos)
  return node


const indentation = 2

proc serialize(node: Node,
               opening, closing: proc(nd: Node) : string,
               leafdata: proc(nd: Node): seq[string],
               ind: int = 0): seq[string] =
  # result = newSeq[string]()
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
    if not openLF and child_blocks[0][0].len > 0:
      result[^1] &= child_blocks[0][0]
      child_blocks[0].delete(0)  # causes SIGSEGV (read from nil) on nim doc?
    result = concat(result, concat(child_blocks))
    if closeLF:
      result.add(close)
    else:
      result[^1] &= close


proc asSxpr*(node: NodeOrNil): string =
  func renderAttrs(node: Node): string =
    # if node.attributes.len == 0:  return ""
    var attrStrs = newSeq[string](node.attributes.len)
    for i, attr, value in enumerate(node.attributes):
      attrStrs[i] = fmt"""`({attr} "{value}")"""
    attrStrs.join(" ")

  proc opening(node: Node): string =
    if node.attributes.len == 0:
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


proc `$`*(node: NodeOrNil): string =
  return node.asSxpr()


# Test-code
when isMainModule:
  var n = newNode("root", @[newNode("left", "LEFT", {"id": "007"}.toOrderedTable),
                            newNode("right", "RIGHT")])
  echo $n
  n.`sourcePos=` 0
  echo n.children[0].sourcePos
  echo n.children[1].sourcePos

