type Obj = object
  i: int

proc consume(x: sink Obj) = discard "no implementation"

proc main =
  var tup = (Obj(i: 0), Obj(i: 2))
  # consume tup[0]
  # ok, only tup[0] was consumed, tup[1] is still alive:
  echo tup[1]
  echo tup[0]
  tup[0].i = 2
