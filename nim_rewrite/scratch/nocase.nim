import std/unicode

proc compare(s: string, pos: int, c: string): bool =
  var
    i = pos
    sr: Rune

  for r in c.runes:
    s.fastRuneAt(i, sr)
    if not (r == sr.toLower):
      return false
  return true

when isMainModule:
  let cmpRaw = "ÄBCDÖÜß"
  let cmp = toLower(cmpRaw)

  echo $cmp
  echo $compare("123ÄBCDÖÜß456", 3, cmp)
  echo $compare("123ÄBCDÖß456", 3, cmp)
