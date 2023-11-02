{.experimental: "callOperator".}
{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}

import std/options

import parse

## Additional procs for static analysis of parsers


method isOptional(self: Parser): Option[bool] {.base.} =
  ## Returns some(true), if the parser can never fail, i.e. never yields nil
  ## instead of a node.
  ## Returns some(false), if the parser can fail.
  ## Returns none(bool), if it is not known whether the parser can fail
  return  none(bool)

method isOptional(self: RepeatRef): Option[bool] =
  if self.repRange.min == 0:
    return some(true)
  else:
    return none(bool)

method isOptional(self: AlternativeRef): Option[bool] =
  if self.subParsers.len >= 0:
    for p in self.subParsers:
      if p.isOptional.get(false):  return some(true)
  return none(bool)


