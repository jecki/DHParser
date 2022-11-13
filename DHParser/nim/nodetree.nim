import std/enumerate
import std/sequtils
import std/strformat
import std/strutils
import std/sugar
import std/tables
import std/unicode


type
  Attributes* = OrderedTable[string, string]
  Node* = ref object of RootObj
    name*: string
    children: seq[Node]
    text: string  # must be empty if children is not empty!
    attributes*: Attributes
    sourcePos: int32
  SourcePosUnassignedDefect* = object of Defect
  SourcePosReAssigmentDefect* = object of Defect


proc newNode*(name: string, 
             children: seq[Node], 
             attributes: Attributes = Attributes()): Node =
  Node(name: name, children: children, text: "", attributes: attributes, sourcePos: -1)

proc newNode*(name: string, 
             text: string, 
             attributes: Attributes = Attributes()): Node =
  Node(name: name, children: @[], text: text, attributes: attributes, sourcePos: -1)

func isLeaf*(node: Node): bool = node.children.len == 0

func isEmpty*(node: Node): bool = node.children.len == 0 and node.text.len == 0

func content*(node: Node): string =
  if node.isLeaf:
    result = node.text
  else:
    for child in node.children:
      result &= child.content

func children*(node: Node): seq[Node] =
  node.children

proc `result=`*(node: Node, text: string) =
  node.text = text
  if node.children.len > 0:  node.children = @[]

proc `result=`*(node: Node, children: seq[Node]) =
  node.children = children
  node.text = ""

func runeLen*(node: Node): int =
  if node.isLeaf:
    result = node.text.runeLen
  else:
    for child in node.children:
      result += child.runeLen

func sourcePos*(node: Node): int32 = 
  if node.sourcePos >= 0:
    node.sourcePos
  else:
    raise newException(SourcePosUnassignedDefect, "source position has not yet been assigned")

proc assignSourcePos(node: Node, sourcePos: int32) : int32 =
  if node.sourcePos < 0:
    node.sourcePos = sourcePos
    var pos = sourcePos
    if node.isLeaf:
      pos + int32(node.text.runeLen)
    else:
      for child in node.children:
        pos += child.assignSourcePos(pos)
      pos
  else:
    raise newException(SourcePosReAssigmentDefect, "source position must not be reassigned!")

proc `sourcePos=`*(node: Node, sourcePos: int32) = 
  discard node.assignSourcePos(sourcePos)

proc withSourcePos*(node: Node, sourcePos: int32): Node =
  discard node.assignSourcePos(sourcePos)
  node


const indentation = 2

func serialize(node: Node, 
               opening, closing: proc (nd: Node) : string,
               leafdata: proc(nd: Node): seq[string],
               ind: int = 0): seq[string] =
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
      lines.delete(0)
    for i in countup(0, lines.len - 1):
      lines[i] = indent(lines[i], ind + indentation)      
    result = concat(result, lines)
    if closeLF:
      result.add(close)
    else:
      result[^1] &= close
  
  else:
    var childBlocks = collect(newSeq): 
      for child in node.children: 
        serialize(child, opening, closing, leafdata, ind + indentation)
    if not openLF and child_blocks[0][0].len > 0:
      result[^1] &= child_blocks[0][0]
      child_blocks[0].delete(0)
    result = concat(result, concat(child_blocks))
    if closeLF:
      result.add(close)
    else:
      result[^1] &= close


func asSxpr(node: Node): string =
  func renderAttrs(node: Node): string =
    # if node.attributes.len == 0:  return ""
    var attrStrs = newSeq[string](node.attributes.len)
    for i, attr, value in enumerate(node.attributes):
      attrStrs[i] = fmt"""`({attr} "{value}")"""
    attrStrs.join(" ")

  func opening(node: Node): string =
    if node.attributes.len == 0:
      if node.isLeaf and node.runeLen < 60:
        fmt"({node.name} "
      else:
        fmt"({node.name}{'\n'}"
    else:
      fmt"({node.name} {renderAttrs(node)}{'\n'}"
  
  func closing(node: Node): string = ")"

  func leafdata(node: Node): seq[string] = 
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
      lines
    else:
      @['"' & esc(node.content) & '"']

  serialize(node, opening, closing, leafdata).join("\n")


# Test-code

var n = newNode("root", @[newNode("left", "LEFT", {"id": "007"}.toOrderedTable),
                          newNode("right", "RIGHT")])
echo n.asSxpr
n.`sourcePos=` 0
echo n.children[0].sourcePos
echo n.children[1].sourcePos
