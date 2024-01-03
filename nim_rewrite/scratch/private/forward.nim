{.experimental: "codeReordering".}

type
  Ref = ref Obj

type
  Obj = object of RootObj
    i: int

