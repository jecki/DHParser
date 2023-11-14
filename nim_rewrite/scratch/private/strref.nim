const
  S = "Hallo"

type
  SObj = object
    s: string

proc test(r: string) =
  var o: SObj
  o.s = r


when isMainModule:
  test(S)
