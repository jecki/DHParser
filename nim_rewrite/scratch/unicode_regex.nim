import "../src/nimparser/strslice"

let rs = """_|:|[A-Z]|[a-z]
             |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
             |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
             |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
             |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
             |[\U00010000-\U000EFFFF]"""



when not defined(js):
  import std/re
  let prs = "(*UTF8)(*UCP)" & replacef(rs, re"\\[uU]([0-9a-fA-F]+)", r"\x{$1}")

  let r = ure("""(*UTF8)(*UCP)_|:|[A-Z]|[a-z]|\x09
              |[\x{00C0}-\x{00D6}]|[\x{00D8}-\x{00F6}]|[\x{00F8}-\x{02FF}]
              |[\x{0370}-\x{037D}]|[\x{037F}-\x{1FFF}]|[\x{200C}-\x{200D}]
              |[\x{2070}-\x{218F}]|[\x{2C00}-\x{2FEF}]|[\x{3001}-\x{D7FF}]
              |[\x{F900}-\x{FDCF}]|[\x{FDF0}-\x{FFFD}]
              |[\x{00010000}-\x{000EFFFF}]""")

else:
  import std/jsre
  let prs = replace(rs, ure"\\U([0-9a-fA-F]+)", r"\u{$1}")
  let r = ure("""_|:|[A-Z]|[a-z]|\x09
             |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
             |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
             |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
             |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
             |[\u{00010000}-\u{000EFFFF}]""")
  let rs2 = """(?:(?!-)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+"""
  let prs2 = replace(rs2, ure"\\U([0-9a-fA-F]+)", r"\u{$1}")
  echo prs2
  let rr = ure(prs2)


echo $prs
let rx = urex(prs)
echo toStringSlice(" ").find(ure"(?:(?!\]\]>)[^<&])+")
echo toStringSlice(" ").matchLen(ure"(?:(?!\]\]>)[^<&])+", 0)
echo " ".len

echo toStringSlice("ä").find(ure"(?:(?!\]\]>)[^<&])+")
echo toStringSlice("ä").matchLen(ure"(?:(?!\]\]>)[^<&])+", 0)
echo "ä".len
