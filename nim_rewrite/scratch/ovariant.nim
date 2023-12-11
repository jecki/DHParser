{.experimental: "strictCaseObjects".}

import std/re

type
  Parser = ref object
    id: int
  MatcherKind = enum mkRegex, mkString, mkProc, mkParser
  MatcherProc = proc(text: string, start: int32, stop: int32): tuple[pos, length: int32]
  Matcher = object
    case kind: MatcherKind
    of mkRegex:
      reStr: string
      regex: Regex
    of mkString:
      cmpStr: string
    of mkProc:
      findProc: MatcherProc
    of mkParser:
      consumeParser: Parser

method check(p: Parser, s: seq[Matcher]) =
  for m in s:
    if m.kind == mkString:
      echo m.cmpStr

when isMainModule:
  let p = Parser(id: 10)
  let a: seq[Matcher] = @[Matcher(kind: mkString, cmpStr: "***")]
  p.check(a)

