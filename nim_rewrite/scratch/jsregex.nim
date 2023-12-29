import std/jsre

type Regex = RegExp
func re(pattern: cstring): Regex = newRegexp(pattern)
func search(pattern: cstring; self: RegExp): int {.importjs: "(#.search(#) || [])".}


func matchLen(str: string, pattern: RegExp, start: int32): int32 =
  if startsWith(str[start..<str.len], pattern):
    let m: seq[cstring] = match(str, pattern)
    return m[0].len
  return -1

func findBounds(str: string, pattern: RegExp, start: int32, last: int32 = -1): tuple[a, b: int32] =
  let strend: int32 = if last < 0: str.len else: last
  let a: int32 = search(str[start ..< strend], pattern)
  let m: seq[cstring] = match(str, pattern)
  let b: int32 = a + m[0].len
  return (a, b)

when isMainModule:
  let rx: Regex = re"[0-9]+"
  var result: seq[cstring]
  var index, size: int
  const teststr = "abc 123 def 456 gh 78 ijk"

  result = rx.exec(teststr)
  echo $result
  result = teststr.match(rx)
  echo $result
  index = teststr.search(rx)
  echo $index

  echo "---"
  size = teststr.matchLen(rx, 0)
  echo $size
  size = teststr.matchLen(rx, 4)
  echo $size
  let (a, b) = teststr.findBounds(rx, 0)
  echo $a
  echo $b

