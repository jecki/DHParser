proc recursive(c: int) =
  echo c
  # if c > 100: return
  # const size=16384
  # var d:array[size, int]
  # d[0] = 1
  # d[size-1] = 2
  recursive(c + 1)

when isMainModule:
  recursive(1)

