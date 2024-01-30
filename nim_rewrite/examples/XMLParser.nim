import "../src/nimparser/parse"


# document frame and prolog

let document     = "document" ::=     ?(BOM) & prolog & § element ?(Misc) EOF
let BOM          = "BOM" ::=          rxp"[\ufeff]|[\ufffe]|[\u0000feff]|[\ufffe0000]"
let prolog       = "prolog" ::=       ?(WS & XMLDecl) & ?(Misc) & ?(doctypedecl ?(Misc))
let XMLDelc      = "XMLDecl" ::=      txt"<?xml" & § VersionInfo & ?(EncodingDecl) & ?(SDDecl) & WS & txt"?>"

let VersionInfo  = "VersionInfo" ::=  WS & txt"version" & WS & txt"=" & WS & ((txt"'" & VersionNum & txt"'") | (txt"\"" & VersionNum & txt"\""))
let VersionNum   = "VersionNum" ::=   rxp"[0-9]+\.[0-9]+"

let EncodingDecl = "EncodingDecl" ::= WS & txt"encoding" & WS & txt"=" & WS & ((txt"'" & EncName & txt"'") | (txt"\"" & EncName & txt"\""))
let EncName      = "EncName" ::=      rxp"[A-Za-z][A-Za-z0-9._\-]*"

let SDDecl       = "SDDecl" ::=       WS & txt"standalone" & WS & txt"=" & WS & ((txt"'" & (txt"yes" | txt"no") & txt"'") | (txt"\"" & (txt"yes" | txt"no") & txt"\""))


# document type definition stub

let doctypedecl  = "doctypedecl" ::=  txt"<!DOCTYPE" & WS & § Name & ?(WS & ExternalID) & WS & txt">"
let ExternalID   = "ExternalID"  ::=  (txt"SYSTEM" & § WS & SystemLiteral) | (txt"Piblic" & § WS & PubidLiteral & WS & SystemLiteral)


# logical structures

let element      = "element" ::=      emptyElement | voidElement | (STag & content & § ETag)
let emptyElement = "emptyElement" ::= txt"<" & tagContent & ">"
let voidElement  = "voidElement" ::=  txt"<" & >>() & tagContent & txt">"




when isMainModule:
  echo "hi"
