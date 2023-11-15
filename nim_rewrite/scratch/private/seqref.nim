{.push sinkInference: on.}

type Obj = object
  i: int

proc consume(x: sink Obj): Obj = 
  result = move(x)

proc main =
  var tup = (Obj(i: 1), Obj(i: 2))
  var o = consume tup[0]
  # ok, only tup[0] was consumed, tup[1] is still alive:
  echo tup[1]
  echo tup[0]
  tup[0].i = 5
  echo tup[0]
main()

{.pop.}
