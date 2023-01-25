{.experimental: "strictNotNil".} 


type
  NodeObj = object of RootObj
    children: seq[Node]
    data: int
  Node = ref NodeObj not nil


func sumFunc(node: Node): int =
  if node.children.len == 0:
    result = node.data
  else:
    var sum: int = 0
    for child in node.children:
        sum += child.sumFunc()
    
proc sumProc(node: Node): int =
  if node.children.len == 0:
    result = node.data
  else:
    var sum: int = 0
    for child in node.children:
      sum += child.sumProc()


proc init(node: Node): Node =
  echo "init Node"
  node.children = @[]
  node.data = 0
  result = node


type
  LinkedNodeObj = object of NodeObj
    parent: Node
  LinkedNode = ref LinkedNodeObj not nil

proc init(node: LinkedNode, parent: Node): LinkedNode =
  echo "init LinkedNode"
  discard Node(node).init()
  node.parent = parent
  result = node


type
  SpecialNodeObj = object of NodeObj
  SpecialNode = ref SpecialNodeObj not nil

proc show(n: Node) =
  echo $n.data

var
  root = new(Node).init() 
  ln = new(LinkedNode).init(root)
  sn = new(SpecialNode).init()

  n = NodeObj(children: @[], data:0)
  np = addr n



