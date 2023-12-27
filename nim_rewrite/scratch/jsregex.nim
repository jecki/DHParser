import std/jsre

type Regex = RegExp
func re(pattern: cstring): Regex = newRegexp(pattern)
func search(pattern: cstring; self: RegExp): int {.importjs: "(#.search(#) || [])".}


when isMainModule:
  let rx: Regex = re"[0-9]+"
  var result: seq[cstring]
  var index: int

  result = rx.exec("abc 123 def 456 gh 78 ijk")
  echo $result
  result = "abc 123 def 456 gh 78 ijk".match(rx)
  echo $result
  index = "abc 123 def 456 gh 78 ijk".search(rx)
  echo $index
