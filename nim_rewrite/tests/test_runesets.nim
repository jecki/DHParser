# unit-tests for the runesets.nim module
# To run these tests, simply execute `nimble test`.

import std/[unittest, strutils, unicode, algorithm, strformat]

import nimparser/runesets

test "String code for Rune-Ranges (rr and sr)":
  # assert (rr"Ä-Ö").toRange() == (196'u32, 214'u32)
  # assert (rr"\xC4-\xD6").toRange() == (196'u32, 214'u32)
  assert rs0"a-z0-9\xc4-\xd6".ranges == @[rr"0-9", rr"a-z", rr"Ä-Ö"]
  assert rs0"abc0-9äöü".ranges == @[rr"0-9", rr"a-c", rr"ä", rr"ö", rr"ü"]


test "inRuneRanges":
  var rr: seq[RuneRange] = @[rr"2-4", rr"B-D", rr"b-d"]
  assert contains(rr, "1".runeAt(0)) == false
  assert contains(rr, "2".runeAt(0)) == true
  assert contains(rr, "3".runeAt(0)) == true
  assert contains(rr, "4".runeAt(0)) == true
  assert contains(rr, "5".runeAt(0)) == false

  assert contains(rr, "A".runeAt(0)) == false
  assert contains(rr, "B".runeAt(0)) == true
  assert contains(rr, "C".runeAt(0)) == true
  assert contains(rr, "D".runeAt(0)) == true
  assert contains(rr, "E".runeAt(0)) == false

  assert contains(rr, "a".runeAt(0)) == false
  assert contains(rr, "b".runeAt(0)) == true
  assert contains(rr, "c".runeAt(0)) == true
  assert contains(rr, "d".runeAt(0)) == true
  assert contains(rr, "e".runeAt(0)) == false

  rr = @[rr"2-4", rr"B-D", rr"U-W", rr"b-d"]
  assert contains(rr, "1".runeAt(0)) == false
  assert contains(rr, "2".runeAt(0)) == true
  assert contains(rr, "3".runeAt(0)) == true
  assert contains(rr, "4".runeAt(0)) == true
  assert contains(rr, "5".runeAt(0)) == false

  assert contains(rr, "A".runeAt(0)) == false
  assert contains(rr, "B".runeAt(0)) == true
  assert contains(rr, "C".runeAt(0)) == true
  assert contains(rr, "D".runeAt(0)) == true
  assert contains(rr, "E".runeAt(0)) == false

  assert contains(rr, "T".runeAt(0)) == false
  assert contains(rr, "U".runeAt(0)) == true
  assert contains(rr, "V".runeAt(0)) == true
  assert contains(rr, "W".runeAt(0)) == true
  assert contains(rr, "X".runeAt(0)) == false

  assert contains(rr, "a".runeAt(0)) == false
  assert contains(rr, "b".runeAt(0)) == true
  assert contains(rr, "c".runeAt(0)) == true
  assert contains(rr, "d".runeAt(0)) == true
  assert contains(rr, "e".runeAt(0)) == false

test "sortAndMerge":
  var rr: seq[RuneRange] = @[rr"2-5", rr"B-E", rr"H-K", rr"b-e", rr"h-p"]
  sortAndMerge(rr)
  assert rr == @[rr"2-5", rr"B-E", rr"H-K", rr"b-e", rr"h-p"]
  rr = @[rr"b-e", rr"2-5", rr"B-E", rr"C-K", rr"f-p"]
  sortAndMerge(rr)
  assert rr == @[rr"2-5", rr"B-K", rr"b-p", ]

test "Joining and Subtracting or Rune-Ranges":
  var m: seq[RuneRange] = @[rr"2-5", rr"B-E", rr"H-K", rr"b-e", rr"h-p"]
  assert ((m + @[rr"6-8", rr"A-C", rr"I-K", rr"c-d", rr"h-i", rr"j", rr"l-n"]) ==
          @[rr"2-8", rr"A-E", rr"H-K", rr"b-e", rr"h-p"])
  assert ((m - @[rr"6-8", rr"A-C", rr"I-K", rr"c-d", rr"h-i", rr"j", rr"l-n"]) ==
          @[rr"2-5", rr"D-E", rr"H", rr"b", rr"e", rr"k", rr"o-p"])
 #         "@[(low: 2, high: 5), (low: D, high: E), (low: H, high: H), (low: b, high: b), (low: e, high: e), (low: k, high: k), (low: o, high: p)]")
  assert (rs0"0-4F-Ha-c".ranges * rs0"2-7B-Gb".ranges) == rs0"2-4F-Gb".ranges

test "RuneSet":
  assert (rs0"A-C" + rs0"X-Z") == rs0"A-CX-Z"
  assert (rs0"^A-Z" + rs0"B-E") == rs0"^AF-Z"
  assert (rs0"A-C" + rs0"^X-Z") == rs0"^X-Z"
  assert (rs0"A-D" + rs0"^C-Z") == rs0"^E-Z"
  assert (rs0"^A-D" + rs0"^C-Z") == rs0"^C-D"
  assert rs0"A-C" != rs0"A-Z"
  # assert (rs"^A-D" + rs"^X-Z") == rs"^C-D" -> Empty or All not allowed

  assert (rs0"A-Z" - rs0"D-E") == rs0"A-CF-Z"
  assert (rs0"^A-Z" - rs0"B-E") == rs0"^A-Z"
  assert (rs0"^A-G" - rs0"F-K") == rs0"^A-K"
  assert (rs0"^A-G" - rs0"^F-K") == rs0"H-K"
  assert (rs0"A-G" - rs0"^F-K") == rs0"F-G"

  var r = rs0(r"\s")
  assert r.ranges.len == 3  # 9-10, 12-13, 20
  r = rs0(r"\n")
  assert r.ranges.len == 1


test "RuneRanges parser":
  assert $rs"\xC4-\xD6" == r"[\xC4-\xD6]" 
  assert $rs"\xC4|\xD6" == r"[\xC4\xD6]"
  assert $rs"\xC4-\xD6|\u00E4" ==  r"[\xC4-\xD6\xE4]"
  assert $rs"[\x61-\x7A]|\xDF-\xF6|\xF8-\xFF|\u0101" == r"[a-z\xDF-\xF6\xF8-\xFF\u0101]"
  assert $rs("""[\x61-\x7A]
               |\xDF-\xF6|
                \xF8-\xFF
               |\u0101""") == r"[a-z\xDF-\xF6\xF8-\xFF\u0101]"
  var latin = rs("""[\x61-\x7A]|[\xDF-\xF6]|[\xF8-\xFF]|\u0101|\u0103|\u0105|\u0107|\u0109|\u010B|\u010D
            |\u010F|\u0111|\u0113|\u0115|\u0117|\u0119|\u011B|\u011D|\u011F|\u0121|\u0123|\u0125
            |\u0127|\u0129|\u012B|\u012D|\u012F|\u0131|\u0133|\u0135|[\u0137-\u0138]|\u013A|\u013C
            |\u013E|\u0140|\u0142|\u0144|\u0146|[\u0148-\u0149]|\u014B|\u014D|\u014F|\u0151|\u0153
            |\u0155|\u0157|\u0159|\u015B|\u015D|\u015F|\u0161|\u0163|\u0165|\u0167|\u0169|\u016B
            |\u016D|\u016F|\u0171|\u0173|\u0175|\u0177|\u017A|\u017C|[\u017E-\u0180]|\u0183|\u0185
            |\u0188|[\u018C-\u018D]|\u0192|\u0195|[\u0199-\u019B]|\u019E|\u01A1|\u01A3|\u01A5
            |\u01A8|\u01AB|\u01AD|\u01B0|\u01B4|\u01B6|[\u01B9-\u01BA]|\u01BD|[\u01C5-\u01C6]
            |[\u01C8-\u01C9]|[\u01CB-\u01CC]|\u01CE|\u01D0|\u01D2|\u01D4|\u01D6|\u01D8|\u01DA
            |[\u01DC-\u01DD]|\u01DF|\u01E1|\u01E3|\u01E5|\u01E7|\u01E9|\u01EB|\u01ED
            |[\u01EF-\u01F0]|[\u01F2-\u01F3]|\u01F5|\u01F9|\u01FB|\u01FD|\u01FF|\u0201|\u0203
            |\u0205|\u0207|\u0209|\u020B|\u020D|\u020F|\u0211|\u0213|\u0215|\u0217|\u0219|\u021B
            |\u021D|\u021F|\u0221|\u0223|\u0225|\u0227|\u0229|\u022B|\u022D|\u022F|\u0231
            |[\u0233-\u0239]|\u023C|[\u023F-\u0240]|\u0242|\u0247|[\u0249-\u024B]|\u024D
            |[\u024F-\u0293]|[\u0299-\u02A0]|[\u02A3-\u02AB]|[\u02AE-\u02AF]|[\u0363-\u036F]
            |[\u1D00-\u1D23]|[\u1D62-\u1D65]|[\u1D6B-\u1D77]|[\u1D79-\u1D9A]|\u1DCA
            |[\u1DD3-\u1DF4]|\u1E01|\u1E03|\u1E05|\u1E07|\u1E09|\u1E0B|\u1E0D|\u1E0F|\u1E11|\u1E13
            |\u1E15|\u1E17|\u1E19|\u1E1B|\u1E1D|\u1E1F|\u1E21|\u1E23|\u1E25|\u1E27|\u1E29|\u1E2B
            |\u1E2D|\u1E2F|\u1E31|\u1E33|\u1E35|\u1E37|\u1E39|\u1E3B|\u1E3D|\u1E3F|\u1E41|\u1E43
            |\u1E45|\u1E47|\u1E49|\u1E4B|\u1E4D|\u1E4F|\u1E51|\u1E53|\u1E55|\u1E57|\u1E59|\u1E5B
            |\u1E5D|\u1E5F|\u1E61|\u1E63|\u1E65|\u1E67|\u1E69|\u1E6B|\u1E6D|\u1E6F|\u1E71|\u1E73
            |\u1E75|\u1E77|\u1E79|\u1E7B|\u1E7D|\u1E7F|\u1E81|\u1E83|\u1E85|\u1E87|\u1E89|\u1E8B
            |\u1E8D|\u1E8F|\u1E91|\u1E93|[\u1E95-\u1E9D]|\u1E9F|\u1EA1|\u1EA3|\u1EA5|\u1EA7|\u1EA9
            |\u1EAB|\u1EAD|\u1EAF|\u1EB1|\u1EB3|\u1EB5|\u1EB7|\u1EB9|\u1EBB|\u1EBD|\u1EBF|\u1EC1
            |\u1EC3|\u1EC5|\u1EC7|\u1EC9|\u1ECB|\u1ECD|\u1ECF|\u1ED1|\u1ED3|\u1ED5|\u1ED7|\u1ED9
            |\u1EDB|\u1EDD|\u1EDF|\u1EE1|\u1EE3|\u1EE5|\u1EE7|\u1EE9|\u1EEB|\u1EED|\u1EEF|\u1EF1
            |\u1EF3|\u1EF5|\u1EF7|\u1EF9|\u1EFB|\u1EFD|\u1EFF|\u2071|\u207F|[\u2090-\u209C]|\u2184
            |[\u249C-\u24B5]|[\u24D0-\u24E9]|\u2C5E|\u2C61|[\u2C65-\u2C66]|\u2C68|\u2C6A|\u2C6C
            |\u2C71|[\u2C73-\u2C74]|[\u2C76-\u2C7C]|\uA723|\uA725|\uA727|\uA729|\uA72B|\uA72D
            |[\uA72F-\uA731]|\uA733|\uA735|\uA737|\uA739|\uA73B|\uA73D|\uA73F|\uA741|\uA743|\uA745
            |\uA747|\uA749|\uA74B|\uA74D|\uA74F|\uA751|\uA753|\uA755|\uA757|\uA759|\uA75B|\uA75D
            |\uA75F|\uA761|\uA763|\uA765|\uA767|\uA769|\uA76B|\uA76D|\uA76F|[\uA771-\uA778]|\uA77A
            |\uA77C|\uA77F|\uA781|\uA783|\uA785|\uA787|\uA78C|\uA78E|\uA791|[\uA793-\uA795]|\uA797
            |\uA799|\uA79B|\uA79D|\uA79F|\uA7A1|\uA7A3|\uA7A5|\uA7A7|\uA7A9|[\uA7AE-\uA7AF]|\uA7B5
            |\uA7B7|\uA7B9|\uA7BB|\uA7BD|\uA7BF|\uA7C3|\uA7FA|[\uAB30-\uAB5A]|[\uAB60-\uAB64]
            |[\uAB66-\uAB67]|[\uFB00-\uFB06]|[\uFF41-\uFF5A]|\U0001F1A5|\U0001F521
            |[\U000E0061-\U000E007A]""")
  assert latin.ranges.len == 369 
  assert latin.contains(latin, Rune('a'))
  assert not latin.contains(latin, Rune('0'))
  


test "Serialization":
  let rs1 = rs"""[_]|[:]|[A-Z]|[a-z]
                |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                |[\U00010000-\U000EFFFF]"""
  let rs2 = rs"[ace\sD-G]"
  let rs3 = rs"[a-f]|[^c-z0-9]|[24]"
  assert rs1 == rs($rs1)
  assert rs2 == rs($rs2)
  assert rs3 == rs($rs3)  
  assert $rs1 == $rs($rs1)
  assert $rs2 == $rs($rs2)
  assert $rs3 == $rs($rs3)  
  assert $rs1 == $rs(rs1 $ true)
  assert $rs2 == $rs(rs2 $ true)
  assert $rs3 == $rs(rs3 $ true)
