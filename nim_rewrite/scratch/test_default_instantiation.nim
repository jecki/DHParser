# {.experimental: "notnil".}
{.experimental: "strictNotNil".}

type
  Foo = object
    a: int = 2
    b = 3.0
  Bar = ref Foo not nil


block: # created with an object construction expression
  let x = Foo()
  assert x.a == 2 and x.b == 3.0
  
  let y = Bar()
  assert y.a == 2 and y.b == 3.0

block: # created with an object construction expression
  let x = default(Foo)
  assert x.a == 2 and x.b == 3.0
  
  let y = default(array[1, Foo])
  assert y[0].a == 2 and y[0].b == 3.0
  
  let z = default(tuple[x: Foo])
  assert z.x.a == 2 and z.x.b == 3.0

  var u: seq[Foo] = default(seq[Foo])
  u.setLen(1)
  assert u[0].a == 2 and u[0].b == 3.0


block: # created with the procedure `new`
  let y = new Bar
  assert y.a == 2 and y.b == 3.0

  var u: seq[Bar] = default(seq[Bar])
  u.setLen(1)
  assert u[0].a == 2 and u[0].b == 3.0


