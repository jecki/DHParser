#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'../..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, AnyChar, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, Counted, Interleave, INFINITE, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, \
    merge_adjacent, collapse, collapse_children_if, transform_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    transform_content, replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, node_maker, any_of, \
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_tag_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def MLWPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return MLWPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class MLWGrammar(Grammar):
    r"""Parser for a MLW source file.
    """
    AUSGEWICHEN = Forward()
    BINDESTRICH = Forward()
    BelegKern = Forward()
    BelegLemma = Forward()
    BelegText = Forward()
    Belege = Forward()
    Beschreibung = Forward()
    DEU_GEMISCHT = Forward()
    DEU_GWORT = Forward()
    DEU_WORT = Forward()
    DeutscheBedeutung = Forward()
    ECKIGE_AUF = Forward()
    ECKIGE_ZU = Forward()
    Einschub = Forward()
    FREITEXT = Forward()
    GRI_WORT = Forward()
    GROSSSCHRIFT = Forward()
    GRÖßER_ZEICHEN = Forward()
    HOCHGESTELLT = Forward()
    Junktur = Forward()
    KLAMMER_AUF = Forward()
    KLAMMER_ZU = Forward()
    KLEINER_ZEICHEN = Forward()
    Kursiv = Forward()
    LAT_GWORT = Forward()
    LZ = Forward()
    LateinischeBedeutung = Forward()
    LemmaWort = Forward()
    ROEMISCHE_ZAHL = Forward()
    SATZZEICHEN = Forward()
    SCHLUESSELWORT = Forward()
    SEITENZAHL = Forward()
    Sperrung = Forward()
    Stelle = Forward()
    TEIL_SATZZEICHEN = Forward()
    TEXTELEMENT = Forward()
    VARIANTE = Forward()
    Werk = Forward()
    ZITAT_SATZZEICHEN = Forward()
    Zusatz = Forward()
    casus = Forward()
    flexion = Forward()
    genus = Forward()
    numerus = Forward()
    opus = Forward()
    unberechtigt = Forward()
    wortart = Forward()
    wortarten = Forward()
    source_hash__ = "8178a608ef87f3a8b0c2e7f6c6925dd2"
    anonymous__ = re.compile('_\\w+$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'Artikel': [(re.compile(r'(?=:)'), 'Hier darf kein (weiterer) Doppelpunkt stehen "{1}", ggf. sollte er in einen (verschachtelten) Kommentar verschoben werden.'),
                                    (re.compile(r'\s*ETYMOLOGIE'), 'Die Etymologie-Position muss unmittelbar auf die Grammatik-Position folgen.'),
                                    (re.compile(r'\s*[A-Z][A-Z][A-Z]+'), 'An dieser Stelle sollte {0} folgen, nicht "{1}"')],
                        'VerweisBlock': [(re.compile(r'\['), 'Die "unberechtigt"-Markierung [] muss immer am Anfang, ggf. noch vor der Lemma-Nr. stehen!')],
                        'LemmaPosition': [(re.compile(r'(?=)'), 'Artikelkopf, Etymologie- oder Bedeutungsposition erwaretet, aber nicht "{1}" !')],
                        'LemmaBlock': [(re.compile(r'(?=)'), '"{1}" ist kein gültiges Lemma!')],
                        'Grammatik': [(re.compile(r'(?=nomen)'), '"nomen" ist als wortangabe nicht erlaubt, verwende bitte "substantiv"!')],
                        'GrammatikVariante': [(re.compile(r'(?=)'), "Fehlerhafte Angabe bei Grammatik-Variante oder fehlende Belege!")],
                        'Position': [(re.compile(r'(?!\s*\n)'), "Zeilenwechsel nach Schlüsselwort vor »{1}« erforderlich!")],
                        'Besonderheit': [(re.compile(r'\n* +\w'), "Einrückung scheint nicht zu stimmen. Zu viele oder zu wenig Leerzeichen!"),
                                         ('', "Hier sollten Verweise {{=> ...}}, Belege oder Unterkategorien folgen, nicht »{1}«. Möglicherweise wurde die maximale Gliederungstiefe von vier Ebenen überschritten.")],
                        'Bedeutungsangabe': [(re.compile(r'(?=\()'), "\'{1}\' kann nicht verarbeitet werden, möglicherweise wurde die Markierung eines Zusatzes mit geschweiften Klammern {{ }} versäumt?")],
                        'FreierZusatz': [(re.compile(r'(?=\{)'), "\'{1}\' kann nicht verarbeitet werden. Zusätze können nicht geschachtelt werden, dürfen aber Verweise \'{{=> ...}}\' enthalten."),
                                         (re.compile(r'[\\]'), "Hier darf kein rückwärtsgerichteter Schrägstrich »{1}« stehen. Vielleicht wurde er mit einem vorwärts gerichteten Schrägstrich »/« verwechselt."),
                                         (re.compile(r'--'), 'Unerwarter Doppelstrich: "--" Bedeutungsangaben sollten als Nebenbedeutungen notiert und nicht in Zusätze verpackt werden.')],
                        'Beleg': [(re.compile(r'\.( *\n| *\*)'), "Belege dürfen nicht mit einem Punkt \'.\' abgeschlossen werden!"),
                                  (re.compile(r';\s*\*'), "Nach einem Semikolon werden weitere Belegstellen desselben Autors UND Werks erwartet, nicht: »{1}«"),
                                  (re.compile(r'(?<=")[.]'), 'Trennpunkte nach Zitaten müssen innerhalb der Anführungsstriche stehen, z.B. "punctum.", nicht "punctum". !'),
                                  (re.compile(r'"(?!$)'), 'An der Stelle:  »"{1}« ist kein weiteres Zitat erlaubt. Wurde zuvor evtl. eine doppelte runde Klammer »((« vergessen?'),
                                  (re.compile(r'\s*$'), "Unerwartetes Ende des Textes erreicht!"),
                                  (re.compile(r'\^ '), 'Das Hochstellungszeichen "^" muss dem Buchstaben (unmittelbar) vorangestellt werden.'),
                                  (re.compile(r'[()][^()]'), '»{1}« passt hier nicht. Einschübe, opera minora etc. sollten in doppelte runde Klammern "(( ... ))" gesetzt werden'),
                                  (re.compile(r'(?=)'), "Hier darf es nicht weitergehen mit: »{1}« (Möglicherweise ein Folgefehler eines vorhergehen Fehlers.)")],
                        'BelegText': [(re.compile(r'(?=\|)'), 'Das Zeichen "|" darf nur in einem mit "#" gekennzeichneten Lemmawort vorkommen!'),
                                      (re.compile(r'(?=\*)'), 'Quellen- und Literaturangaben sind innerhalb von Zitaten nur in Einschüben "((...))" erlaubt!'),
                                      (re.compile(r'(?=@)'), 'Anker müssen in geschweifte Klammern eingeschlossen werden, z.B. "{{@ invado_3a}}".')],
                        'AutorWerk': [('', 'Unerwartete Zeichenfolge »{1}« im Autor- oder Werknamen. Wurde ein Semikolon vor der Stellenangabe ";" vergessen?')],
                        'VerweisKern': [(re.compile(r'[\w:\/\/=?.%&\[\] ]*,[^|]*}'), 'Komma als Trenner zwischen Verweisen nicht erlaubt. Verwende Semikolon ";".'),
                                        (re.compile(r'[^|]*}'), 'Kein gültiges Verweisziel: "{1}" oder Platzhalter "|-" fehlt nach Alias!'),
                                        (re.compile(r'=>'), 'Kein gültiger Verweis "{1}". Mglw. ein Verweiszeichen "=>" zuviel.'),
                                        (re.compile(r'(?=)'), 'Kein gültiger Verweis: "{1}"')],
                        'Anker': [(re.compile(r'(?=)'), "Ungültiger Ankername (erlaubte Zeichen: A-Z, a-z, 0-9 und _) oder keine schließende geschweifte Klammer.")],
                        'Verweis': [('', 'Hier muß eine gültige Zielangabe (z.B. "domus/domus_22") oder NUR ein Platzhalter "-" stehen, aber kein weiterer Text es sei denn innerhalb von Kommentarzeichen /* ... */')]}
    skip_rules__ = {'Artikel': [re.compile(r'(?:\n\s*[A-Z][A-Z][A-Z]+)(?:.|\n)*?(?=\n\s*BEDEUTUNG|VERWEISE|AUTOR|STELLENVERZEICHNIS)'),
                                re.compile(r'$')],
                    'VerweisArtikel': [re.compile(r'(?=$)')],
                    '_VerweisBlöcke': [re.compile(r'(?=LEMMA)')],
                    'VerweisBlock': [re.compile(r'(?=\w)')],
                    'Vide': [re.compile(r'(?=ET)')],
                    'Grammatik': [re.compile(r'[^\w.-] *')],
                    'AutorWerk': [re.compile(r'(?=\)\)|;|\s\*)|\s*\n(?:\s*\n)+.')]}
    resume_rules__ = {'_VerweisBlöcke': [re.compile(r'(?=\nAUTOR|$)')],
                      'Vide': [re.compile(r'(?=\nAUTOR|[A-Z][A-Z][A-Z]|$)')],
                      'SubLemmaPosition': [re.compile(r'(?=\nETYMOLOGIE|\nSCHREIBWEISE|\nSTRUKTUR|\nGEBRAUCH|\nMETRIK|\nVERWECHSELBAR|\nBEDEUTUNG)')],
                      'NachtragsPosition': [re.compile(r'(?=\nLEMMA)')],
                      'LemmaPosition': [re.compile(r'(?=\nETYMOLOGIE|\nSCHREIBWEISE|\nSTRUKTUR|\nGEBRAUCH|\nMETRIK|\nVERWECHSELBAR|\nBEDEUTUNG)')],
                      'wortart': [re.compile(r'(?=(?:[-:;\n{]|vel|raro|semel))')],
                      'GrammatikVariante': [re.compile(r'(?=\n(?=(?:[^\n]*:)|(?:\s*\n)))')],
                      'Position': [re.compile(r'(?=\n[A-Z][A-Z][A-Z])')],
                      'Beschreibung': [re.compile(r'(?=:)')],
                      'Bedeutung': [re.compile(r'(?=\nBEDEUTUNG|\nUNTER|\nU_|\nUU|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR)')],
                      'U1Bedeutung': [re.compile(r'(?=\nBEDEUTUNG|\nUNTER|\nU_|\nUU|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR)')],
                      'U2Bedeutung': [re.compile(r'(?=\nBEDEUTUNG|\nUNTER|\nU_|\nUU|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR)')],
                      'U3Bedeutung': [re.compile(r'(?=\nBEDEUTUNG|\nUNTER|\nU_|\nUU|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR)')],
                      'U4Bedeutung': [re.compile(r'(?=\nBEDEUTUNG|\nUNTER|\nU_|\nUU|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR)')],
                      'U5Bedeutung': [re.compile(r'(?=\nBEDEUTUNG|\nUNTER|\nU_|\nUU|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR)')],
                      'Bedeutungsangabe': [re.compile(r'(?=\n\s*[U*])')],
                      'FreierZusatz': [re.compile(r'(?=(?<=}).|\s*\n(?:\s*\n)+.|$)')],
                      'Beleg': [re.compile(r'(?=\s*\*|\nU_|\nUU|\nUNTER|\nBEDEUTUNG|\nANHÄNGER|\nSUB_LEMMA|\nVERWEISE|\nAUTOR|\s*\n(?:\s*\n)+.)')],
                      'BelegText': [re.compile(r'(?=\s*\n(?:\s*\n)+.)'),
                                    re.compile(r'\)\)'),
                                    re.compile(r'\(\('),
                                    re.compile(r'(?<=")')],
                      'VerweisKern': [re.compile(r'(?=\})')],
                      'Anker': [re.compile(r'\}[ \t]*'),
                                re.compile(r'\n[ \t]*')],
                      'Verweis': [re.compile(r'(?=;|\})')]}
    COMMENT__ = r'(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)'
    comment_rx__ = re.compile(COMMENT__)
    comment__ = RegExp(comment_rx__)
    WHITESPACE__ = r'[\t ]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    _LATEIN_GROSS_FOLGE = RegExp('(?x)(?:[\\x41-\\x5A]|[\\xC0-\\xD6]|[\\xD8-\\xDE]|\\u0100|\\u0102|\\u0104|\\u0106|\\u0108|\\u010A|\\u010C\n           |\\u010E|\\u0110|\\u0112|\\u0114|\\u0116|\\u0118|\\u011A|\\u011C|\\u011E|\\u0120|\\u0122|\\u0124\n           |\\u0126|\\u0128|\\u012A|\\u012C|\\u012E|\\u0130|\\u0132|\\u0134|\\u0136|\\u0139|\\u013B|\\u013D\n           |\\u013F|\\u0141|\\u0143|\\u0145|\\u0147|\\u014A|\\u014C|\\u014E|\\u0150|\\u0152|\\u0154|\\u0156\n           |\\u0158|\\u015A|\\u015C|\\u015E|\\u0160|\\u0162|\\u0164|\\u0166|\\u0168|\\u016A|\\u016C|\\u016E\n           |\\u0170|\\u0172|\\u0174|\\u0176|[\\u0178-\\u0179]|\\u017B|\\u017D|[\\u0181-\\u0182]|\\u0184\n           |[\\u0186-\\u0187]|[\\u0189-\\u018B]|[\\u018E-\\u0191]|[\\u0193-\\u0194]|[\\u0196-\\u0198]\n           |[\\u019C-\\u019D]|[\\u019F-\\u01A0]|\\u01A2|\\u01A4|\\u01A7|\\u01A9|\\u01AC|[\\u01AE-\\u01AF]\n           |[\\u01B1-\\u01B3]|\\u01B5|[\\u01B7-\\u01B8]|\\u01BC|[\\u01C4-\\u01C5]|[\\u01C7-\\u01C8]\n           |[\\u01CA-\\u01CB]|\\u01CD|\\u01CF|\\u01D1|\\u01D3|\\u01D5|\\u01D7|\\u01D9|\\u01DB|\\u01DE|\\u01E0\n           |\\u01E2|\\u01E4|\\u01E6|\\u01E8|\\u01EA|\\u01EC|\\u01EE|[\\u01F1-\\u01F2]|\\u01F4\n           |[\\u01F6-\\u01F8]|\\u01FA|\\u01FC|\\u01FE|\\u0200|\\u0202|\\u0204|\\u0206|\\u0208|\\u020A|\\u020C\n           |\\u020E|\\u0210|\\u0212|\\u0214|\\u0216|\\u0218|\\u021A|\\u021C|\\u021E|\\u0220|\\u0222|\\u0224\n           |\\u0226|\\u0228|\\u022A|\\u022C|\\u022E|\\u0230|\\u0232|[\\u023A-\\u023B]|[\\u023D-\\u023E]\n           |\\u0241|[\\u0243-\\u0246]|\\u0248|\\u024A|\\u024C|\\u024E|\\u0262|\\u026A|\\u0274|\\u0276\n           |[\\u0280-\\u0281]|\\u028F|\\u0299|[\\u029B-\\u029C]|\\u029F|[\\u1D00-\\u1D01]|[\\u1D03-\\u1D07]\n           |[\\u1D0A-\\u1D10]|\\u1D15|[\\u1D18-\\u1D1C]|[\\u1D20-\\u1D23]|\\u1D7B|\\u1D7E|\\u1DDB\n           |[\\u1DDE-\\u1DDF]|[\\u1DE1-\\u1DE2]|\\u1E00|\\u1E02|\\u1E04|\\u1E06|\\u1E08|\\u1E0A|\\u1E0C\n           |\\u1E0E|\\u1E10|\\u1E12|\\u1E14|\\u1E16|\\u1E18|\\u1E1A|\\u1E1C|\\u1E1E|\\u1E20|\\u1E22|\\u1E24\n           |\\u1E26|\\u1E28|\\u1E2A|\\u1E2C|\\u1E2E|\\u1E30|\\u1E32|\\u1E34|\\u1E36|\\u1E38|\\u1E3A|\\u1E3C\n           |\\u1E3E|\\u1E40|\\u1E42|\\u1E44|\\u1E46|\\u1E48|\\u1E4A|\\u1E4C|\\u1E4E|\\u1E50|\\u1E52|\\u1E54\n           |\\u1E56|\\u1E58|\\u1E5A|\\u1E5C|\\u1E5E|\\u1E60|\\u1E62|\\u1E64|\\u1E66|\\u1E68|\\u1E6A|\\u1E6C\n           |\\u1E6E|\\u1E70|\\u1E72|\\u1E74|\\u1E76|\\u1E78|\\u1E7A|\\u1E7C|\\u1E7E|\\u1E80|\\u1E82|\\u1E84\n           |\\u1E86|\\u1E88|\\u1E8A|\\u1E8C|\\u1E8E|\\u1E90|\\u1E92|\\u1E94|\\u1E9E|\\u1EA0|\\u1EA2|\\u1EA4\n           |\\u1EA6|\\u1EA8|\\u1EAA|\\u1EAC|\\u1EAE|\\u1EB0|\\u1EB2|\\u1EB4|\\u1EB6|\\u1EB8|\\u1EBA|\\u1EBC\n           |\\u1EBE|\\u1EC0|\\u1EC2|\\u1EC4|\\u1EC6|\\u1EC8|\\u1ECA|\\u1ECC|\\u1ECE|\\u1ED0|\\u1ED2|\\u1ED4\n           |\\u1ED6|\\u1ED8|\\u1EDA|\\u1EDC|\\u1EDE|\\u1EE0|\\u1EE2|\\u1EE4|\\u1EE6|\\u1EE8|\\u1EEA|\\u1EEC\n           |\\u1EEE|\\u1EF0|\\u1EF2|\\u1EF4|\\u1EF6|\\u1EF8|\\u1EFA|\\u1EFC|\\u1EFE|[\\u24B6-\\u24CF]|\\u2C2E\n           |\\u2C60|[\\u2C62-\\u2C64]|\\u2C67|\\u2C69|\\u2C6B|[\\u2C6D-\\u2C70]|\\u2C72|\\u2C75|\\u2C7B\n           |[\\u2C7E-\\u2C7F]|\\uA722|\\uA724|\\uA726|\\uA728|\\uA72A|\\uA72C|\\uA72E|[\\uA730-\\uA732]\n           |\\uA734|\\uA736|\\uA738|\\uA73A|\\uA73C|\\uA73E|\\uA740|\\uA742|\\uA744|\\uA746|\\uA748|\\uA74A\n           |\\uA74C|\\uA74E|\\uA750|\\uA752|\\uA754|\\uA756|\\uA758|\\uA75A|\\uA75C|\\uA75E|\\uA760|\\uA762\n           |\\uA764|\\uA766|\\uA768|\\uA76A|\\uA76C|\\uA76E|\\uA776|\\uA779|\\uA77B|[\\uA77D-\\uA77E]|\\uA780\n           |\\uA782|\\uA784|\\uA786|\\uA78B|\\uA78D|\\uA790|\\uA792|\\uA796|\\uA798|\\uA79A|\\uA79C|\\uA79E\n           |\\uA7A0|\\uA7A2|\\uA7A4|\\uA7A6|\\uA7A8|[\\uA7AA-\\uA7B4]|\\uA7B6|\\uA7B8|\\uA7BA|\\uA7BC|\\uA7BE\n           |\\uA7C2|[\\uA7C4-\\uA7C6]|\\uA7FA|\\uAB46|[\\uFF21-\\uFF3A]|[\\U0001F110-\\U0001F12C]\n           |[\\U0001F130-\\U0001F149]|[\\U0001F150-\\U0001F169]|[\\U0001F170-\\U0001F18A]|\\U0001F520\n           |[\\U000E0041-\\U000E005A])+')
    _LATEIN_GROSS = RegExp('(?x)[\\x41-\\x5A]|[\\xC0-\\xD6]|[\\xD8-\\xDE]|\\u0100|\\u0102|\\u0104|\\u0106|\\u0108|\\u010A|\\u010C\n           |\\u010E|\\u0110|\\u0112|\\u0114|\\u0116|\\u0118|\\u011A|\\u011C|\\u011E|\\u0120|\\u0122|\\u0124\n           |\\u0126|\\u0128|\\u012A|\\u012C|\\u012E|\\u0130|\\u0132|\\u0134|\\u0136|\\u0139|\\u013B|\\u013D\n           |\\u013F|\\u0141|\\u0143|\\u0145|\\u0147|\\u014A|\\u014C|\\u014E|\\u0150|\\u0152|\\u0154|\\u0156\n           |\\u0158|\\u015A|\\u015C|\\u015E|\\u0160|\\u0162|\\u0164|\\u0166|\\u0168|\\u016A|\\u016C|\\u016E\n           |\\u0170|\\u0172|\\u0174|\\u0176|[\\u0178-\\u0179]|\\u017B|\\u017D|[\\u0181-\\u0182]|\\u0184\n           |[\\u0186-\\u0187]|[\\u0189-\\u018B]|[\\u018E-\\u0191]|[\\u0193-\\u0194]|[\\u0196-\\u0198]\n           |[\\u019C-\\u019D]|[\\u019F-\\u01A0]|\\u01A2|\\u01A4|\\u01A7|\\u01A9|\\u01AC|[\\u01AE-\\u01AF]\n           |[\\u01B1-\\u01B3]|\\u01B5|[\\u01B7-\\u01B8]|\\u01BC|[\\u01C4-\\u01C5]|[\\u01C7-\\u01C8]\n           |[\\u01CA-\\u01CB]|\\u01CD|\\u01CF|\\u01D1|\\u01D3|\\u01D5|\\u01D7|\\u01D9|\\u01DB|\\u01DE|\\u01E0\n           |\\u01E2|\\u01E4|\\u01E6|\\u01E8|\\u01EA|\\u01EC|\\u01EE|[\\u01F1-\\u01F2]|\\u01F4\n           |[\\u01F6-\\u01F8]|\\u01FA|\\u01FC|\\u01FE|\\u0200|\\u0202|\\u0204|\\u0206|\\u0208|\\u020A|\\u020C\n           |\\u020E|\\u0210|\\u0212|\\u0214|\\u0216|\\u0218|\\u021A|\\u021C|\\u021E|\\u0220|\\u0222|\\u0224\n           |\\u0226|\\u0228|\\u022A|\\u022C|\\u022E|\\u0230|\\u0232|[\\u023A-\\u023B]|[\\u023D-\\u023E]\n           |\\u0241|[\\u0243-\\u0246]|\\u0248|\\u024A|\\u024C|\\u024E|\\u0262|\\u026A|\\u0274|\\u0276\n           |[\\u0280-\\u0281]|\\u028F|\\u0299|[\\u029B-\\u029C]|\\u029F|[\\u1D00-\\u1D01]|[\\u1D03-\\u1D07]\n           |[\\u1D0A-\\u1D10]|\\u1D15|[\\u1D18-\\u1D1C]|[\\u1D20-\\u1D23]|\\u1D7B|\\u1D7E|\\u1DDB\n           |[\\u1DDE-\\u1DDF]|[\\u1DE1-\\u1DE2]|\\u1E00|\\u1E02|\\u1E04|\\u1E06|\\u1E08|\\u1E0A|\\u1E0C\n           |\\u1E0E|\\u1E10|\\u1E12|\\u1E14|\\u1E16|\\u1E18|\\u1E1A|\\u1E1C|\\u1E1E|\\u1E20|\\u1E22|\\u1E24\n           |\\u1E26|\\u1E28|\\u1E2A|\\u1E2C|\\u1E2E|\\u1E30|\\u1E32|\\u1E34|\\u1E36|\\u1E38|\\u1E3A|\\u1E3C\n           |\\u1E3E|\\u1E40|\\u1E42|\\u1E44|\\u1E46|\\u1E48|\\u1E4A|\\u1E4C|\\u1E4E|\\u1E50|\\u1E52|\\u1E54\n           |\\u1E56|\\u1E58|\\u1E5A|\\u1E5C|\\u1E5E|\\u1E60|\\u1E62|\\u1E64|\\u1E66|\\u1E68|\\u1E6A|\\u1E6C\n           |\\u1E6E|\\u1E70|\\u1E72|\\u1E74|\\u1E76|\\u1E78|\\u1E7A|\\u1E7C|\\u1E7E|\\u1E80|\\u1E82|\\u1E84\n           |\\u1E86|\\u1E88|\\u1E8A|\\u1E8C|\\u1E8E|\\u1E90|\\u1E92|\\u1E94|\\u1E9E|\\u1EA0|\\u1EA2|\\u1EA4\n           |\\u1EA6|\\u1EA8|\\u1EAA|\\u1EAC|\\u1EAE|\\u1EB0|\\u1EB2|\\u1EB4|\\u1EB6|\\u1EB8|\\u1EBA|\\u1EBC\n           |\\u1EBE|\\u1EC0|\\u1EC2|\\u1EC4|\\u1EC6|\\u1EC8|\\u1ECA|\\u1ECC|\\u1ECE|\\u1ED0|\\u1ED2|\\u1ED4\n           |\\u1ED6|\\u1ED8|\\u1EDA|\\u1EDC|\\u1EDE|\\u1EE0|\\u1EE2|\\u1EE4|\\u1EE6|\\u1EE8|\\u1EEA|\\u1EEC\n           |\\u1EEE|\\u1EF0|\\u1EF2|\\u1EF4|\\u1EF6|\\u1EF8|\\u1EFA|\\u1EFC|\\u1EFE|[\\u24B6-\\u24CF]|\\u2C2E\n           |\\u2C60|[\\u2C62-\\u2C64]|\\u2C67|\\u2C69|\\u2C6B|[\\u2C6D-\\u2C70]|\\u2C72|\\u2C75|\\u2C7B\n           |[\\u2C7E-\\u2C7F]|\\uA722|\\uA724|\\uA726|\\uA728|\\uA72A|\\uA72C|\\uA72E|[\\uA730-\\uA732]\n           |\\uA734|\\uA736|\\uA738|\\uA73A|\\uA73C|\\uA73E|\\uA740|\\uA742|\\uA744|\\uA746|\\uA748|\\uA74A\n           |\\uA74C|\\uA74E|\\uA750|\\uA752|\\uA754|\\uA756|\\uA758|\\uA75A|\\uA75C|\\uA75E|\\uA760|\\uA762\n           |\\uA764|\\uA766|\\uA768|\\uA76A|\\uA76C|\\uA76E|\\uA776|\\uA779|\\uA77B|[\\uA77D-\\uA77E]|\\uA780\n           |\\uA782|\\uA784|\\uA786|\\uA78B|\\uA78D|\\uA790|\\uA792|\\uA796|\\uA798|\\uA79A|\\uA79C|\\uA79E\n           |\\uA7A0|\\uA7A2|\\uA7A4|\\uA7A6|\\uA7A8|[\\uA7AA-\\uA7B4]|\\uA7B6|\\uA7B8|\\uA7BA|\\uA7BC|\\uA7BE\n           |\\uA7C2|[\\uA7C4-\\uA7C6]|\\uA7FA|\\uAB46|[\\uFF21-\\uFF3A]|[\\U0001F110-\\U0001F12C]\n           |[\\U0001F130-\\U0001F149]|[\\U0001F150-\\U0001F169]|[\\U0001F170-\\U0001F18A]|\\U0001F520\n           |[\\U000E0041-\\U000E005A]')
    _LATEIN_KLEIN_FOLGE = RegExp('(?x)(?:[\\x61-\\x7A]|[\\xDF-\\xF6]|[\\xF8-\\xFF]|\\u0101|\\u0103|\\u0105|\\u0107|\\u0109|\\u010B|\\u010D\n            |\\u010F|\\u0111|\\u0113|\\u0115|\\u0117|\\u0119|\\u011B|\\u011D|\\u011F|\\u0121|\\u0123|\\u0125\n            |\\u0127|\\u0129|\\u012B|\\u012D|\\u012F|\\u0131|\\u0133|\\u0135|[\\u0137-\\u0138]|\\u013A|\\u013C\n            |\\u013E|\\u0140|\\u0142|\\u0144|\\u0146|[\\u0148-\\u0149]|\\u014B|\\u014D|\\u014F|\\u0151|\\u0153\n            |\\u0155|\\u0157|\\u0159|\\u015B|\\u015D|\\u015F|\\u0161|\\u0163|\\u0165|\\u0167|\\u0169|\\u016B\n            |\\u016D|\\u016F|\\u0171|\\u0173|\\u0175|\\u0177|\\u017A|\\u017C|[\\u017E-\\u0180]|\\u0183|\\u0185\n            |\\u0188|[\\u018C-\\u018D]|\\u0192|\\u0195|[\\u0199-\\u019B]|\\u019E|\\u01A1|\\u01A3|\\u01A5\n            |\\u01A8|\\u01AB|\\u01AD|\\u01B0|\\u01B4|\\u01B6|[\\u01B9-\\u01BA]|\\u01BD|[\\u01C5-\\u01C6]\n            |[\\u01C8-\\u01C9]|[\\u01CB-\\u01CC]|\\u01CE|\\u01D0|\\u01D2|\\u01D4|\\u01D6|\\u01D8|\\u01DA\n            |[\\u01DC-\\u01DD]|\\u01DF|\\u01E1|\\u01E3|\\u01E5|\\u01E7|\\u01E9|\\u01EB|\\u01ED\n            |[\\u01EF-\\u01F0]|[\\u01F2-\\u01F3]|\\u01F5|\\u01F9|\\u01FB|\\u01FD|\\u01FF|\\u0201|\\u0203\n            |\\u0205|\\u0207|\\u0209|\\u020B|\\u020D|\\u020F|\\u0211|\\u0213|\\u0215|\\u0217|\\u0219|\\u021B\n            |\\u021D|\\u021F|\\u0221|\\u0223|\\u0225|\\u0227|\\u0229|\\u022B|\\u022D|\\u022F|\\u0231\n            |[\\u0233-\\u0239]|\\u023C|[\\u023F-\\u0240]|\\u0242|\\u0247|[\\u0249-\\u024B]|\\u024D\n            |[\\u024F-\\u0293]|[\\u0299-\\u02A0]|[\\u02A3-\\u02AB]|[\\u02AE-\\u02AF]|[\\u0363-\\u036F]\n            |[\\u1D00-\\u1D23]|[\\u1D62-\\u1D65]|[\\u1D6B-\\u1D77]|[\\u1D79-\\u1D9A]|\\u1DCA\n            |[\\u1DD3-\\u1DF4]|\\u1E01|\\u1E03|\\u1E05|\\u1E07|\\u1E09|\\u1E0B|\\u1E0D|\\u1E0F|\\u1E11|\\u1E13\n            |\\u1E15|\\u1E17|\\u1E19|\\u1E1B|\\u1E1D|\\u1E1F|\\u1E21|\\u1E23|\\u1E25|\\u1E27|\\u1E29|\\u1E2B\n            |\\u1E2D|\\u1E2F|\\u1E31|\\u1E33|\\u1E35|\\u1E37|\\u1E39|\\u1E3B|\\u1E3D|\\u1E3F|\\u1E41|\\u1E43\n            |\\u1E45|\\u1E47|\\u1E49|\\u1E4B|\\u1E4D|\\u1E4F|\\u1E51|\\u1E53|\\u1E55|\\u1E57|\\u1E59|\\u1E5B\n            |\\u1E5D|\\u1E5F|\\u1E61|\\u1E63|\\u1E65|\\u1E67|\\u1E69|\\u1E6B|\\u1E6D|\\u1E6F|\\u1E71|\\u1E73\n            |\\u1E75|\\u1E77|\\u1E79|\\u1E7B|\\u1E7D|\\u1E7F|\\u1E81|\\u1E83|\\u1E85|\\u1E87|\\u1E89|\\u1E8B\n            |\\u1E8D|\\u1E8F|\\u1E91|\\u1E93|[\\u1E95-\\u1E9D]|\\u1E9F|\\u1EA1|\\u1EA3|\\u1EA5|\\u1EA7|\\u1EA9\n            |\\u1EAB|\\u1EAD|\\u1EAF|\\u1EB1|\\u1EB3|\\u1EB5|\\u1EB7|\\u1EB9|\\u1EBB|\\u1EBD|\\u1EBF|\\u1EC1\n            |\\u1EC3|\\u1EC5|\\u1EC7|\\u1EC9|\\u1ECB|\\u1ECD|\\u1ECF|\\u1ED1|\\u1ED3|\\u1ED5|\\u1ED7|\\u1ED9\n            |\\u1EDB|\\u1EDD|\\u1EDF|\\u1EE1|\\u1EE3|\\u1EE5|\\u1EE7|\\u1EE9|\\u1EEB|\\u1EED|\\u1EEF|\\u1EF1\n            |\\u1EF3|\\u1EF5|\\u1EF7|\\u1EF9|\\u1EFB|\\u1EFD|\\u1EFF|\\u2071|\\u207F|[\\u2090-\\u209C]|\\u2184\n            |[\\u249C-\\u24B5]|[\\u24D0-\\u24E9]|\\u2C5E|\\u2C61|[\\u2C65-\\u2C66]|\\u2C68|\\u2C6A|\\u2C6C\n            |\\u2C71|[\\u2C73-\\u2C74]|[\\u2C76-\\u2C7C]|\\uA723|\\uA725|\\uA727|\\uA729|\\uA72B|\\uA72D\n            |[\\uA72F-\\uA731]|\\uA733|\\uA735|\\uA737|\\uA739|\\uA73B|\\uA73D|\\uA73F|\\uA741|\\uA743|\\uA745\n            |\\uA747|\\uA749|\\uA74B|\\uA74D|\\uA74F|\\uA751|\\uA753|\\uA755|\\uA757|\\uA759|\\uA75B|\\uA75D\n            |\\uA75F|\\uA761|\\uA763|\\uA765|\\uA767|\\uA769|\\uA76B|\\uA76D|\\uA76F|[\\uA771-\\uA778]|\\uA77A\n            |\\uA77C|\\uA77F|\\uA781|\\uA783|\\uA785|\\uA787|\\uA78C|\\uA78E|\\uA791|[\\uA793-\\uA795]|\\uA797\n            |\\uA799|\\uA79B|\\uA79D|\\uA79F|\\uA7A1|\\uA7A3|\\uA7A5|\\uA7A7|\\uA7A9|[\\uA7AE-\\uA7AF]|\\uA7B5\n            |\\uA7B7|\\uA7B9|\\uA7BB|\\uA7BD|\\uA7BF|\\uA7C3|\\uA7FA|[\\uAB30-\\uAB5A]|[\\uAB60-\\uAB64]\n            |[\\uAB66-\\uAB67]|[\\uFB00-\\uFB06]|[\\uFF41-\\uFF5A]|\\U0001F1A5|\\U0001F521\n            |[\\U000E0061-\\U000E007A])+')
    _LATEIN_KLEIN = RegExp('(?x)[\\x61-\\x7A]|[\\xDF-\\xF6]|[\\xF8-\\xFF]|\\u0101|\\u0103|\\u0105|\\u0107|\\u0109|\\u010B|\\u010D\n            |\\u010F|\\u0111|\\u0113|\\u0115|\\u0117|\\u0119|\\u011B|\\u011D|\\u011F|\\u0121|\\u0123|\\u0125\n            |\\u0127|\\u0129|\\u012B|\\u012D|\\u012F|\\u0131|\\u0133|\\u0135|[\\u0137-\\u0138]|\\u013A|\\u013C\n            |\\u013E|\\u0140|\\u0142|\\u0144|\\u0146|[\\u0148-\\u0149]|\\u014B|\\u014D|\\u014F|\\u0151|\\u0153\n            |\\u0155|\\u0157|\\u0159|\\u015B|\\u015D|\\u015F|\\u0161|\\u0163|\\u0165|\\u0167|\\u0169|\\u016B\n            |\\u016D|\\u016F|\\u0171|\\u0173|\\u0175|\\u0177|\\u017A|\\u017C|[\\u017E-\\u0180]|\\u0183|\\u0185\n            |\\u0188|[\\u018C-\\u018D]|\\u0192|\\u0195|[\\u0199-\\u019B]|\\u019E|\\u01A1|\\u01A3|\\u01A5\n            |\\u01A8|\\u01AB|\\u01AD|\\u01B0|\\u01B4|\\u01B6|[\\u01B9-\\u01BA]|\\u01BD|[\\u01C5-\\u01C6]\n            |[\\u01C8-\\u01C9]|[\\u01CB-\\u01CC]|\\u01CE|\\u01D0|\\u01D2|\\u01D4|\\u01D6|\\u01D8|\\u01DA\n            |[\\u01DC-\\u01DD]|\\u01DF|\\u01E1|\\u01E3|\\u01E5|\\u01E7|\\u01E9|\\u01EB|\\u01ED\n            |[\\u01EF-\\u01F0]|[\\u01F2-\\u01F3]|\\u01F5|\\u01F9|\\u01FB|\\u01FD|\\u01FF|\\u0201|\\u0203\n            |\\u0205|\\u0207|\\u0209|\\u020B|\\u020D|\\u020F|\\u0211|\\u0213|\\u0215|\\u0217|\\u0219|\\u021B\n            |\\u021D|\\u021F|\\u0221|\\u0223|\\u0225|\\u0227|\\u0229|\\u022B|\\u022D|\\u022F|\\u0231\n            |[\\u0233-\\u0239]|\\u023C|[\\u023F-\\u0240]|\\u0242|\\u0247|[\\u0249-\\u024B]|\\u024D\n            |[\\u024F-\\u0293]|[\\u0299-\\u02A0]|[\\u02A3-\\u02AB]|[\\u02AE-\\u02AF]|[\\u0363-\\u036F]\n            |[\\u1D00-\\u1D23]|[\\u1D62-\\u1D65]|[\\u1D6B-\\u1D77]|[\\u1D79-\\u1D9A]|\\u1DCA\n            |[\\u1DD3-\\u1DF4]|\\u1E01|\\u1E03|\\u1E05|\\u1E07|\\u1E09|\\u1E0B|\\u1E0D|\\u1E0F|\\u1E11|\\u1E13\n            |\\u1E15|\\u1E17|\\u1E19|\\u1E1B|\\u1E1D|\\u1E1F|\\u1E21|\\u1E23|\\u1E25|\\u1E27|\\u1E29|\\u1E2B\n            |\\u1E2D|\\u1E2F|\\u1E31|\\u1E33|\\u1E35|\\u1E37|\\u1E39|\\u1E3B|\\u1E3D|\\u1E3F|\\u1E41|\\u1E43\n            |\\u1E45|\\u1E47|\\u1E49|\\u1E4B|\\u1E4D|\\u1E4F|\\u1E51|\\u1E53|\\u1E55|\\u1E57|\\u1E59|\\u1E5B\n            |\\u1E5D|\\u1E5F|\\u1E61|\\u1E63|\\u1E65|\\u1E67|\\u1E69|\\u1E6B|\\u1E6D|\\u1E6F|\\u1E71|\\u1E73\n            |\\u1E75|\\u1E77|\\u1E79|\\u1E7B|\\u1E7D|\\u1E7F|\\u1E81|\\u1E83|\\u1E85|\\u1E87|\\u1E89|\\u1E8B\n            |\\u1E8D|\\u1E8F|\\u1E91|\\u1E93|[\\u1E95-\\u1E9D]|\\u1E9F|\\u1EA1|\\u1EA3|\\u1EA5|\\u1EA7|\\u1EA9\n            |\\u1EAB|\\u1EAD|\\u1EAF|\\u1EB1|\\u1EB3|\\u1EB5|\\u1EB7|\\u1EB9|\\u1EBB|\\u1EBD|\\u1EBF|\\u1EC1\n            |\\u1EC3|\\u1EC5|\\u1EC7|\\u1EC9|\\u1ECB|\\u1ECD|\\u1ECF|\\u1ED1|\\u1ED3|\\u1ED5|\\u1ED7|\\u1ED9\n            |\\u1EDB|\\u1EDD|\\u1EDF|\\u1EE1|\\u1EE3|\\u1EE5|\\u1EE7|\\u1EE9|\\u1EEB|\\u1EED|\\u1EEF|\\u1EF1\n            |\\u1EF3|\\u1EF5|\\u1EF7|\\u1EF9|\\u1EFB|\\u1EFD|\\u1EFF|\\u2071|\\u207F|[\\u2090-\\u209C]|\\u2184\n            |[\\u249C-\\u24B5]|[\\u24D0-\\u24E9]|\\u2C5E|\\u2C61|[\\u2C65-\\u2C66]|\\u2C68|\\u2C6A|\\u2C6C\n            |\\u2C71|[\\u2C73-\\u2C74]|[\\u2C76-\\u2C7C]|\\uA723|\\uA725|\\uA727|\\uA729|\\uA72B|\\uA72D\n            |[\\uA72F-\\uA731]|\\uA733|\\uA735|\\uA737|\\uA739|\\uA73B|\\uA73D|\\uA73F|\\uA741|\\uA743|\\uA745\n            |\\uA747|\\uA749|\\uA74B|\\uA74D|\\uA74F|\\uA751|\\uA753|\\uA755|\\uA757|\\uA759|\\uA75B|\\uA75D\n            |\\uA75F|\\uA761|\\uA763|\\uA765|\\uA767|\\uA769|\\uA76B|\\uA76D|\\uA76F|[\\uA771-\\uA778]|\\uA77A\n            |\\uA77C|\\uA77F|\\uA781|\\uA783|\\uA785|\\uA787|\\uA78C|\\uA78E|\\uA791|[\\uA793-\\uA795]|\\uA797\n            |\\uA799|\\uA79B|\\uA79D|\\uA79F|\\uA7A1|\\uA7A3|\\uA7A5|\\uA7A7|\\uA7A9|[\\uA7AE-\\uA7AF]|\\uA7B5\n            |\\uA7B7|\\uA7B9|\\uA7BB|\\uA7BD|\\uA7BF|\\uA7C3|\\uA7FA|[\\uAB30-\\uAB5A]|[\\uAB60-\\uAB64]\n            |[\\uAB66-\\uAB67]|[\\uFB00-\\uFB06]|[\\uFF41-\\uFF5A]|\\U0001F1A5|\\U0001F521\n            |[\\U000E0061-\\U000E007A]')
    _LATEIN_FOLGE = RegExp('(?x)(?:[\\x41-\\x5A]|[\\x61-\\x7A]|[\\xC0-\\xD6]|[\\xD8-\\xF6]|[\\u00F8-\\u02AF]|[\\u0363-\\u036F]\n            |[\\u1D00-\\u1D25]|[\\u1D62-\\u1D65]|[\\u1D6B-\\u1D77]|[\\u1D79-\\u1D9A]|\\u1DCA\n            |[\\u1DD3-\\u1DF4]|[\\u1E00-\\u1EFF]|\\u2071|\\u207F|[\\u2090-\\u209C]|\\u2184|[\\u249C-\\u24E9]\n            |[\\u271D-\\u271F]|\\u2C2E|\\u2C5E|[\\u2C60-\\u2C7C]|[\\u2C7E-\\u2C7F]|[\\uA722-\\uA76F]\n            |[\\uA771-\\uA787]|[\\uA78B-\\uA7BF]|[\\uA7C2-\\uA7C6]|\\uA7F7|[\\uA7FA-\\uA7FF]\n            |[\\uAB30-\\uAB5A]|[\\uAB60-\\uAB64]|[\\uAB66-\\uAB67]|[\\uFB00-\\uFB06]|[\\uFF21-\\uFF3A]\n            |[\\uFF41-\\uFF5A]|[\\U0001F110-\\U0001F12C]|[\\U0001F130-\\U0001F149]\n            |[\\U0001F150-\\U0001F169]|[\\U0001F170-\\U0001F18A]|\\U0001F1A5|[\\U0001F520-\\U0001F521]\n            |\\U0001F524|[\\U0001F546-\\U0001F547]|[\\U000E0041-\\U000E005A]|[\\U000E0061-\\U000E007A])+')
    _LATEIN = RegExp('(?x)[\\x41-\\x5A]|[\\x61-\\x7A]|[\\xC0-\\xD6]|[\\xD8-\\xF6]|[\\u00F8-\\u02AF]|[\\u0363-\\u036F]\n            |[\\u1D00-\\u1D25]|[\\u1D62-\\u1D65]|[\\u1D6B-\\u1D77]|[\\u1D79-\\u1D9A]|\\u1DCA\n            |[\\u1DD3-\\u1DF4]|[\\u1E00-\\u1EFF]|\\u2071|\\u207F|[\\u2090-\\u209C]|\\u2184|[\\u249C-\\u24E9]\n            |[\\u271D-\\u271F]|\\u2C2E|\\u2C5E|[\\u2C60-\\u2C7C]|[\\u2C7E-\\u2C7F]|[\\uA722-\\uA76F]\n            |[\\uA771-\\uA787]|[\\uA78B-\\uA7BF]|[\\uA7C2-\\uA7C6]|\\uA7F7|[\\uA7FA-\\uA7FF]\n            |[\\uAB30-\\uAB5A]|[\\uAB60-\\uAB64]|[\\uAB66-\\uAB67]|[\\uFB00-\\uFB06]|[\\uFF21-\\uFF3A]\n            |[\\uFF41-\\uFF5A]|[\\U0001F110-\\U0001F12C]|[\\U0001F130-\\U0001F149]\n            |[\\U0001F150-\\U0001F169]|[\\U0001F170-\\U0001F18A]|\\U0001F1A5|[\\U0001F520-\\U0001F521]\n            |\\U0001F524|[\\U0001F546-\\U0001F547]|[\\U000E0041-\\U000E005A]|[\\U000E0061-\\U000E007A]')
    DATEI_ENDE = NegativeLookahead(RegExp('.'))
    VERBOTEN = Alternative(VARIANTE, SCHLUESSELWORT)
    VARIANTE.set(Series(wsp__, ZeroOrMore(Alternative(Series(RegExp('[^":\\n/{}()]+'), wsp__), RegExp('\\((?!\\()'), RegExp('\\)(?!\\))'))), wsp__, RegExp(':')))
    KATEGORIENZEILE = Series(wsp__, Option(Series(Token("|"), wsp__)), ZeroOrMore(Alternative(Series(RegExp('[^":\\n/{]+'), wsp__), Zusatz)), wsp__, RegExp(':'), wsp__, RegExp('\\n'))
    KOMMENTARZEILEN = ZeroOrMore(Series(RegExp('[ \\t]*\\n?[ \\t]*'), comment__))
    ZEILENSPRUNG = Series(wsp__, RegExp('\\n'), wsp__)
    LEERZEILEN = Series(RegExp('[ \\t]*(?:\\n[ \\t]*)+\\n'), wsp__, RegExp('\\n?'))
    LÜCKE = Series(KOMMENTARZEILEN, LEERZEILEN, Option(LZ))
    ZWW = Series(ZEILENSPRUNG, Option(LZ))
    ZLL = Synonym(ZWW)
    ZW = Series(NegativeLookahead(LÜCKE), ZEILENSPRUNG)
    KOMMA = Series(Token(","), wsp__)
    DPP = Series(RegExp('::?'), wsp__)
    LZ.set(OneOrMore(Alternative(comment__, RegExp('\\s+'))))
    ABS = Alternative(Series(RegExp('\\s*'), Alternative(Series(RegExp(';;?'), LZ), RegExp('$'))), ZWW)
    LL = Synonym(LZ)
    L = Synonym(wsp__)
    MEHRZEILER = OneOrMore(Alternative(FREITEXT, RegExp('\\s+(?=[\\w,;:.\\-])')))
    ZITAT_ENDE = Series(RegExp("['´’]"), NegativeLookahead(RegExp('\\w')), wsp__)
    ZITAT_ANFANG = Series(NegativeLookbehind(RegExp('\\w')), RegExp("['‘`]"))
    ZITAT = Series(ZITAT_ANFANG, ZeroOrMore(Alternative(TEXTELEMENT, ZITAT_SATZZEICHEN, KLAMMER_AUF, KLAMMER_ZU, ECKIGE_AUF, ECKIGE_ZU, BelegLemma, Zusatz)), ZITAT_ENDE)
    TAG_NAME = Capture(RegExp('\\w+'))
    XML = Series(Token("<"), TAG_NAME, Token(">"), wsp__, FREITEXT, Token("</"), Pop(TAG_NAME), Token(">"), mandatory=5)
    FREITEXT.set(OneOrMore(Alternative(TEXTELEMENT, ZITAT, SATZZEICHEN, ZW, KLAMMER_AUF, KLAMMER_ZU, GROSSSCHRIFT, GRÖßER_ZEICHEN, KLEINER_ZEICHEN)))
    ETYMOLOGIE_TEXT = OneOrMore(Alternative(DEU_GWORT, LAT_GWORT, GRI_WORT, KLAMMER_AUF, KLAMMER_ZU, BINDESTRICH, RegExp('[.]')))
    EINZEILER = OneOrMore(Alternative(TEXTELEMENT, ZITAT, TEIL_SATZZEICHEN, KLAMMER_AUF, KLAMMER_ZU, ECKIGE_AUF, ECKIGE_ZU))
    _STELLENKERN = OneOrMore(Alternative(TEXTELEMENT, TEIL_SATZZEICHEN, AUSGEWICHEN))
    STELLENKERN = OneOrMore(Alternative(TEXTELEMENT, TEIL_SATZZEICHEN, AUSGEWICHEN, Series(RegExp('\\['), wsp__, _STELLENKERN, RegExp('\\]'), wsp__)))
    STELLENTEXT = Alternative(STELLENKERN, Series(KLAMMER_AUF, NegativeLookahead(RegExp('[acs]\\.')), STELLENKERN, KLAMMER_ZU))
    EINSCHUB_ENDE = Series(RegExp('\\)\\)'), wsp__)
    EINSCHUB_ANFANG = Series(RegExp('\\(\\('), wsp__)
    GRÖßER_ZEICHEN.set(Series(RegExp('>(?!>)'), wsp__))
    KLEINER_ZEICHEN.set(Series(RegExp('<(?!<|/)'), wsp__))
    ECKIGE_ZU.set(Series(RegExp('\\](?!\\])'), wsp__))
    ECKIGE_AUF.set(Series(RegExp('\\[(?!\\[)'), wsp__))
    KLAMMER_ZU.set(Series(RegExp('\\)(?!\\))'), wsp__))
    KLAMMER_AUF.set(Series(RegExp('\\((?!\\()'), wsp__))
    AUSGEWICHEN.set(Series(RegExp('\\\\[#{}\\[\\]()\\\\]'), wsp__))
    TEXTELEMENT.set(Alternative(ROEMISCHE_ZAHL, DEU_WORT, DEU_GEMISCHT, GRI_WORT, SEITENZAHL, HOCHGESTELLT, AUSGEWICHEN))
    ZITAT_SATZZEICHEN.set(Series(RegExp('(?!->)(?:(?:,(?!,))|(?:-(?!-))|[.]+)|[/?!]'), wsp__))
    TEIL_SATZZEICHEN.set(Series(RegExp("(?!->)(?:(?:,(?!,))|(?:-(?!-))|[.]+)|[`''‘’/?!]"), wsp__))
    SATZZEICHEN.set(Series(RegExp("(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|(?:-(?!-))|(?:\\[(?!\\[))|(?:\\](?!\\]))|[.]+)|[`''‘’/?!~]"), wsp__))
    BINDESTRICH.set(RegExp('(?:-(?!-))'))
    WERKTITEL_FOLGE = Series(RegExp('(?:\\[?(?:(?:[A-ZÄÖÜa-zäöü]?(?:(?!\\(\\()(?!\\)\\))[a-zäöü.,()?])+)|[MDCLXVI]+|[0-9]|[A-ZÄÖÜ]{1,1}|-{1,1})\\]?)+'), wsp__)
    WERKTITEL_ANFANG = Series(RegExp('\\[?(?:(?:[A-ZÄÖÜ-]{0,3}(?:(?!\\(\\()(?!\\)\\))[a-zäöü.()?])*)|[MDCLXVI]+|-{1,1})\\]?(?![A-ZÄÖÜ])'), wsp__)
    AUTORNAME = Alternative(Series(Token("M."), wsp__), Series(RegExp('\\[?(?:[A-ZÄÖÜ.\\-]+|[0-9\\-]+)\\]?(?=(?:\\s+|;|$))'), wsp__))
    AUTORANFANG = Series(NegativeLookahead(ROEMISCHE_ZAHL), RegExp('\\[?(?:[A-ZÄÖÜ.\\-]+)\\]?(?=(?:\\s+|;|$))'), wsp__)
    SCHLUESSELWORT.set(Series(wsp__, RegExp('\\s*'), wsp__, NegativeLookahead(ROEMISCHE_ZAHL), RegExp('[A-ZÄÖÜ_]{4,}\\s+')))
    HOCHGESTELLT.set(Alternative(Series(Alternative(Series(Token("{^"), wsp__), Series(Token("^{"), wsp__)), FREITEXT, Series(Token("}"), wsp__)), Series(Series(Token("^"), wsp__), RegExp('[\\w.]+'), wsp__)))
    ROEMISCHE_ZAHL.set(Series(RegExp('(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\\w])\\.?'), wsp__))
    SEITENZAHL.set(Series(RegExp('\\d+'), wsp__))
    GRI_VERBOTEN = RegExp('[èéêëìíîïòóôõöùúûüü]')
    GRI_WORT.set(Series(Option(GRI_VERBOTEN), OneOrMore(Series(RegExp('(?x)(?!--)[_\\-.\\[\\]]*\n                   (?:(?:[\\u0370-\\u0377]|[\\u037A-\\u037F]|[\\u0384-\\u038A]|\\u038C|\n                         [\\u038E-\\u03A1]|[\\u03A3-\\u03E1]|[\\u03F0-\\u03FF]|[\\u1D26-\\u1D2A]|\n                         [\\u1D66-\\u1D6A]|[\\u1F00-\\u1F15]|[\\u1F18-\\u1F1D]|[\\u1F20-\\u1F45]|\n                         [\\u1F48-\\u1F4D]|[\\u1F50-\\u1F57]|\\u1F59|\\u1F5B|\\u1F5D|[\\u1F5F-\\u1F7D]|\n                         [\\u1F80-\\u1FB4]|[\\u1FB6-\\u1FC4]|[\\u1FC6-\\u1FD3]|[\\u1FD6-\\u1FDB]|\n                         [\\u1FDD-\\u1FEF]|[\\u1FF2-\\u1FF4]|[\\u1FF6-\\u1FFE]|\\uAB65|\n                         [\\U00010140-\\U0001018D]|\\U000101A0|[\\U0001D200-\\U0001D241]|\n                         \\U0001D245)[_\\-.\\[\\]]*)+(?<!--)'), Option(GRI_VERBOTEN))), wsp__))
    GROSSSCHRIFT.set(Series(_LATEIN_GROSS_FOLGE, ZeroOrMore(Alternative(_LATEIN_GROSS_FOLGE, RegExp('(?:-(?!-))|_+'))), NegativeLookahead(_LATEIN), wsp__))
    LAT_GWORT.set(Series(_LATEIN, ZeroOrMore(Alternative(_LATEIN_KLEIN_FOLGE, RegExp('[\\[\\]_\\-](?![_\\-.|])'), Series(RegExp('(?:\\|\\.?)|(?:\\.\\|)'), _LATEIN_KLEIN_FOLGE))), NegativeLookahead(_LATEIN), wsp__))
    LAT_WORT = Series(_LATEIN_KLEIN_FOLGE, ZeroOrMore(Alternative(_LATEIN_KLEIN_FOLGE, RegExp('(?:-(?!-))|_+'))), RegExp('\\.?'), NegativeLookahead(_LATEIN), wsp__)
    DEU_GEMISCHT.set(Series(_LATEIN, ZeroOrMore(Alternative(_LATEIN_FOLGE, RegExp('(?:-(?!-))|_+'))), RegExp('\\.?'), NegativeLookahead(_LATEIN), wsp__))
    DEU_KLEIN = Series(_LATEIN_KLEIN_FOLGE, ZeroOrMore(Alternative(_LATEIN_KLEIN_FOLGE, RegExp('(?:-(?!-))|_+'))), RegExp('\\.?'), NegativeLookahead(_LATEIN), wsp__)
    GROSSBUCHSTABEN = Series(NegativeLookahead(ROEMISCHE_ZAHL), _LATEIN_GROSS_FOLGE, RegExp('(?=[ ,\\^\\t\\n)]|$)'), wsp__)
    DEU_GROSS = Series(Alternative(_LATEIN_GROSS, Token("˜")), ZeroOrMore(Alternative(_LATEIN_KLEIN_FOLGE, RegExp('(?:-(?!-))|_+'))), RegExp('\\.?'), NegativeLookahead(_LATEIN), wsp__)
    DEU_GWORT.set(Series(_LATEIN, ZeroOrMore(Alternative(_LATEIN_KLEIN_FOLGE, RegExp('(?:-(?!-))|_+'))), RegExp('\\.?'), NegativeLookahead(_LATEIN), wsp__))
    DEU_WORT.set(Alternative(DEU_GROSS, DEU_KLEIN, GROSSBUCHSTABEN))
    NAME = Series(_LATEIN_GROSS, _LATEIN_KLEIN_FOLGE, wsp__)
    NAMENS_ABKÜRZUNG = Series(_LATEIN_GROSS, Token("."), wsp__)
    ANKER_NAME = Series(RegExp('[a-zA-Z0-9_]+'), wsp__)
    PFAD_NAME = RegExp('[\\w=?.,%&\\[\\]]+')
    ziel = Synonym(PFAD_NAME)
    pfad = Series(PFAD_NAME, RegExp('/(?!\\*)'))
    protokoll = RegExp('\\w+://(?!\\*)')
    alias = OneOrMore(Alternative(TEXTELEMENT, GROSSSCHRIFT, HOCHGESTELLT, SATZZEICHEN, Series(RegExp('[\\w/\\t\\n,.⇒→-]+'), wsp__), Kursiv))
    URL = Series(Option(protokoll), ZeroOrMore(pfad), ziel, wsp__)
    Verweis = Alternative(Series(URL, Lookahead(Alternative(Series(Token(";"), wsp__), Series(Token("}"), wsp__)))), Series(alias, Series(Token("|"), wsp__), Alternative(URL, Series(Token("-"), wsp__)), Lookahead(Alternative(Series(Token(";"), wsp__), Series(Token("}"), wsp__))), mandatory=3, err_msgs=error_messages__["Verweis"]))
    Anker = Series(Option(ZW), Series(Token("{"), wsp__), Series(Token("@"), wsp__), Option(ZW), ANKER_NAME, Series(Token("}"), wsp__), mandatory=4, err_msgs=error_messages__["Anker"])
    VerweisKern = Series(Series(Token("=>"), wsp__), Option(ZW), Verweis, ZeroOrMore(Series(Series(Token(";"), wsp__), Option(ZW), Verweis)), mandatory=2, err_msgs=error_messages__["VerweisKern"])
    EinzelVerweis = Series(Series(Token("{"), wsp__), VerweisKern, Series(Token("}"), wsp__), mandatory=2)
    Verweise = OneOrMore(Series(Option(ZW), EinzelVerweis))
    OriginalStelle = Synonym(Stelle)
    OM_WERK = RegExp('[A-Z][A-Z]?[A-Z]?(?![A-Z.])')
    om_regeln = Alternative(OM_WERK, Series(Token("ed."), wsp__), Series(Token("cod. Vat"), wsp__), Series(Token("cod. Paris"), wsp__), Series(Token("cod. Darmst"), wsp__), Series(Token("cod. Guelf"), wsp__))
    om_kern = Series(Lookahead(om_regeln), Werk, Option(Series(Option(Series(Series(Token(";"), wsp__), Option(ZW))), Stelle, Option(Series(Series(Token(";"), wsp__), Option(ZW), OriginalStelle)), Option(BelegText))), Interleave(opus, Zusatz, repetitions=[(0, 1), (0, 1)]), mandatory=1)
    opus_minus = Series(Series(Token("(("), wsp__), om_kern, ZeroOrMore(Series(Series(Token("*"), wsp__), om_kern)), Series(Token("))"), wsp__))
    opus.set(Series(Lookahead(Series(Token("(("), wsp__)), Alternative(opus_minus, Einschub), mandatory=1))
    Stelle.set(Alternative(EinzelVerweis, OneOrMore(Alternative(Series(Option(ZW), NegativeLookahead(VERBOTEN), STELLENTEXT), Kursiv))))
    Werk.set(Series(Option(ZW), RegExp('(?![ap]\\.)(?![0-9])'), WERKTITEL_ANFANG, ZeroOrMore(Series(Option(ZW), WERKTITEL_FOLGE))))
    FALSCHER_MARKER = RegExp('\\§ *\\n? *')
    disambig_marker = Alternative(RegExp('\\$ *\\n? *'), FALSCHER_MARKER)
    Autor = Series(Option(ZW), Option(disambig_marker), AUTORANFANG, ZeroOrMore(Series(Option(ZW), Alternative(ROEMISCHE_ZAHL, AUTORNAME))))
    AutorWerk = Series(Autor, Option(Werk), Lookahead(Alternative(Series(Token(";"), wsp__), Series(Token("))"), wsp__))), mandatory=1, err_msgs=error_messages__["AutorWerk"], skip=skip_rules__["AutorWerk"])
    LEMMAWORT = Alternative(Series(Option(RegExp('[.|]*')), LAT_GWORT), GRI_WORT, DEU_WORT)
    Lemmawort = Alternative(Series(Series(Token("#{"), wsp__), Option(ZW), OneOrMore(Series(Alternative(LEMMAWORT, SATZZEICHEN), Option(ZW))), Series(Token("}"), wsp__), mandatory=2), Series(Series(Token("#"), wsp__), LEMMAWORT, mandatory=1))
    BelegLemma.set(Synonym(Lemmawort))
    BelegKern.set(ZeroOrMore(Alternative(MEHRZEILER, BelegLemma, Verweise, Zusatz, Sperrung, Junktur, Kursiv, opus, Series(KLAMMER_AUF, BelegKern, KLAMMER_ZU))))
    BelegText.set(Series(RegExp('"'), wsp__, BelegKern, RegExp('"'), wsp__, mandatory=3, err_msgs=error_messages__["BelegText"]))
    Datierung = Series(RegExp('\\((?=[\\w])'), wsp__, STELLENKERN, RegExp('\\)'), wsp__)
    Stellenangabe = Series(Alternative(opus, Stelle), Interleave(Zusatz, Datierung, repetitions=[(0, 1), (0, 1)]), ZeroOrMore(Series(Option(ZW), opus, Option(Series(Option(ZW), Datierung)))))
    BelegStelle = Series(ZeroOrMore(Zusatz), Option(ZW), Series(Option(Series(Option(Series(Token("*"), wsp__)), Werk, Series(Token(";"), wsp__))), Stellenangabe, Option(Series(Option(ZW), BelegText))), Option(Series(Option(ZW), Alternative(Series(NegativeLookahead(Beschreibung), Zusatz), Einschub))))
    Autorangabe = ZeroOrMore(DEU_GEMISCHT)
    Sekundärliteratur = Series(ZeroOrMore(Zusatz), Autorangabe, Series(Token(","), wsp__), Option(ZW), Werk, ZeroOrMore(Series(Series(Token(";"), wsp__), Option(ZW), BelegStelle)))
    Quelle = Series(Option(ZW), AutorWerk, Option(Series(NegativeLookahead(Beschreibung), Zusatz)), Option(Einschub), Option(Series(NegativeLookahead(Beschreibung), Zusatz)))
    Quellenangabe = Series(Alternative(Quelle, BelegStelle), ZeroOrMore(Series(Series(Token(";"), wsp__), BelegStelle)))
    Beleg = Alternative(Series(Zusatz, Lookahead(SCHLUESSELWORT), NegativeLookahead(Series(Option(ZW), AutorWerk))), Series(Zusatz, Lookahead(Series(Option(ZW), Series(Token("*"), wsp__)))), Series(Option(Zusatz), Alternative(OneOrMore(Series(Verweise, Option(Series(Option(ZW), NegativeLookahead(Beschreibung), Zusatz)))), Sekundärliteratur, Quellenangabe), Option(Series(Series(Token(";"), wsp__), NegativeLookahead(Beschreibung), Zusatz)), NegativeLookahead(Series(wsp__, RegExp(':'))), Lookahead(Alternative(Series(ZeroOrMore(Series(RegExp('\\s+'), wsp__)), RegExp('\\s*\\)\\)|\\s*\\*|\\s*[A-Z{]')), Series(wsp__, RegExp('\\n\\s*[^:\\n]*:')), RegExp('\\s*$'), RegExp('\\]'))), mandatory=4, err_msgs=error_messages__["Beleg"]))
    Zusatzzeilen = Series(LÜCKE, OneOrMore(Series(Option(ZLL), Alternative(Zusatz, Verweise))))
    Einschub.set(Series(Option(ZW), EINSCHUB_ANFANG, Interleave(Verweise, Zusatz, BelegText, repetitions=[(0, 1), (0, 1), (0, 1)]), ZeroOrMore(Belege), Option(ZW), EINSCHUB_ENDE))
    Belege.set(Series(Alternative(Series(Beleg, ZeroOrMore(Series(Option(LZ), Series(Token("*"), wsp__), Beleg, mandatory=2))), OneOrMore(Series(Option(LZ), Series(Token("*"), wsp__), Beleg, mandatory=2))), Option(Zusatzzeilen)))
    VariaLectioZusatz = Series(Series(Token("{"), wsp__), OneOrMore(Series(TEXTELEMENT, Option(Series(Token("."), wsp__)), Option(ZW))), Lookahead(RegExp('\\}\\)(?!\\))')), Series(Token("}"), wsp__))
    FesterZusatz = Series(Series(Token("{"), wsp__), Alternative(Series(Token("adde-ad"), wsp__), Series(Token("adde"), wsp__), Series(Token("al"), wsp__), Series(Token("ibid-al"), wsp__), Series(Token("ibid-per-saepe"), wsp__), Series(Token("ibid-saepe"), wsp__), Series(Token("ibid-saepius"), wsp__), Series(Token("persaepe"), wsp__), Series(Token("sim"), wsp__), Series(Token("saepe"), wsp__), Series(Token("saepius"), wsp__), Series(Token("vel-rarius"), wsp__), Series(Token("vel-semel"), wsp__), Series(Token("vel"), wsp__)), Option(Series(Token("."), wsp__)), Series(Token("}"), wsp__))
    Junktur.set(Alternative(Series(Series(Token("<<"), wsp__), BelegKern, Series(Token(">>"), wsp__), mandatory=1), Series(Series(Token("˻"), wsp__), BelegKern, Series(Token("˼"), wsp__), mandatory=1)))
    Kursiv.set(Series(Series(Token("{/"), wsp__), OneOrMore(Alternative(FREITEXT, Lemmawort)), Series(Token("}"), wsp__), mandatory=2))
    Sperrung.set(Series(Series(Token("{!"), wsp__), OneOrMore(Alternative(FREITEXT, Lemmawort)), Series(Token("}"), wsp__), mandatory=2))
    ZusatzInhalt = OneOrMore(Alternative(FREITEXT, VerweisKern, Verweise, Anker, BelegText, BelegLemma, Kursiv, Sperrung, Junktur))
    FreierZusatz = Series(Option(ZW), Series(Token("{"), wsp__), NegativeLookahead(Alternative(Series(Token("=>"), wsp__), Series(Token("@"), wsp__), Series(Token("^"), wsp__), Series(Token("!"), wsp__), Series(Token("/"), wsp__), Series(Series(Token("-"), wsp__), Series(Token("}"), wsp__)))), Option(ZusatzInhalt), Series(Token("}"), wsp__), mandatory=4, err_msgs=error_messages__["FreierZusatz"])
    Zusatz.set(OneOrMore(Alternative(FesterZusatz, VariaLectioZusatz, FreierZusatz, Anker)))
    NullVerweis = Series(Series(Token("{"), wsp__), Series(Token("-"), wsp__), Series(Token("}"), wsp__))
    Stellenverweis = Series(AutorWerk, ZeroOrMore(Series(Option(ABS), Stelle, Alternative(NullVerweis, Verweise))))
    Verweisliste = ZeroOrMore(Series(Option(LZ), Series(Token("*"), wsp__), Stellenverweis))
    Stellenverzeichnis = Series(ZWW, Series(Token("STELLENVERZEICHNIS"), wsp__), Option(LemmaWort), ZWW, Verweisliste)
    unbekannt = Series(Token("unbekannt"), wsp__)
    Name = OneOrMore(Series(Alternative(NAME, NAMENS_ABKÜRZUNG, Series(Token("-"), wsp__), unbekannt), Option(Series(Token(","), wsp__))))
    ArtikelVerfasser = Series(ZWW, Alternative(Series(Token("AUTORINNEN"), wsp__), Series(Token("AUTOREN"), wsp__), Series(Token("AUTORIN"), wsp__), Series(Token("AUTOR"), wsp__)), Option(LZ), Name, mandatory=3)
    verweis_stern = Series(Token("*"), wsp__)
    VerweisPosition = Series(ZWW, Series(Token("VERWEISE"), wsp__), ZeroOrMore(Series(Interleave(LZ, Series(Token(","), wsp__), repetitions=[(0, 1), (0, 1)]), Alternative(Verweise, Series(Option(verweis_stern), LemmaWort), Zusatz))))
    BelegPosition = Series(Option(Series(ZWW, Series(Token("*"), wsp__))), Belege)
    DeutscheKlammer = Series(KLAMMER_AUF, DeutscheBedeutung, Option(Series(Series(Token(";"), wsp__), Zusatz)), KLAMMER_ZU)
    LateinischeKlammer = Series(KLAMMER_AUF, LateinischeBedeutung, Option(Series(Series(Token(";"), wsp__), Zusatz)), KLAMMER_ZU)
    DeutschesWort = Alternative(DEU_GWORT, Series(ZITAT_ANFANG, DEU_GWORT, ZITAT_ENDE))
    LateinischesWort = Alternative(Alternative(LAT_WORT, GRI_WORT), Series(ZITAT_ANFANG, Alternative(LAT_WORT, GRI_WORT), ZITAT_ENDE))
    DeutscheEllipse = Alternative(Series(DEU_GWORT, RegExp('(?<=-)')), Series(RegExp('-'), DEU_GWORT))
    LateinischeEllipse = Alternative(Series(Alternative(LAT_WORT, GRI_WORT), RegExp('(?<=-)')), Series(RegExp('-'), Alternative(LAT_WORT, GRI_WORT)))
    Qualifizierung = Series(Alternative(Series(Token("etwa:"), wsp__), Series(Token("viell.:"), wsp__), Series(Token("vielleicht:"), wsp__)), NegativeLookahead(RegExp('\\s*(?:\\*|UNTER|U_|UU)')))
    DeutscherBestandteil = Series(Option(ZW), Alternative(Qualifizierung, DeutscheEllipse, DeutschesWort, DeutscheKlammer, Kursiv))
    LateinischerBestandteil = Series(Option(ZW), Alternative(LateinischeEllipse, LateinischesWort, Lemmawort, LateinischeKlammer, Kursiv))
    unsicher = Series(Token("?"), wsp__)
    DeutscherAusdruck = Series(Option(unsicher), OneOrMore(Series(Option(ZW), Interleave(DeutscherBestandteil, Series(wsp__, Option(ZW), Zusatz), repetitions=[(1, 1), (0, 1)]))))
    LateinischerAusdruck = Series(Option(unsicher), OneOrMore(Series(Option(ZW), Interleave(LateinischerBestandteil, Series(wsp__, Option(ZW), Zusatz), repetitions=[(1, 1), (0, 1)]))))
    DeutscheBedeutung.set(Series(DeutscherAusdruck, ZeroOrMore(Series(Series(Token(","), wsp__), DeutscherAusdruck))))
    LateinischeBedeutung.set(Series(LateinischerAusdruck, ZeroOrMore(Series(Series(Token(","), wsp__), LateinischerAusdruck))))
    Interpretamente = Series(Option(Series(Zusatz, Option(ZW))), Option(LateinischeBedeutung), Option(Series(Option(Series(RegExp(','), wsp__)), Option(ZW), Zusatz)), Series(Option(ZW), Series(Token("--"), wsp__), Option(ZW)), Option(Series(Zusatz, Option(ZW))), DeutscheBedeutung, Option(Series(Option(Series(RegExp(','), wsp__)), Option(ZW), Zusatz)), mandatory=4)
    Kategorienangabe = OneOrMore(Series(Alternative(EINZEILER, Kursiv), Interleave(BelegText, Lemmawort, repetitions=[(0, 1), (0, 1)]), Option(ZW)))
    Klassifikation = Series(Option(Series(Zusatz, Option(ZW))), ZeroOrMore(Series(Kategorienangabe, Interleave(Verweise, Zusatz, ZW, repetitions=[(0, 1), (0, 1), (0, 1)]))))
    NBVerweise = Series(Series(Token(":"), wsp__), OneOrMore(Series(Option(ZW), Interleave(Verweise, Series(Option(ZW), Zusatz), repetitions=[(1, 1), (0, 1)]))))
    Nebenbedeutungen = OneOrMore(Series(Option(ZW), Series(Token(";"), wsp__), Option(ZW), Option(Series(RegExp('\\('), wsp__)), Alternative(Series(Interpretamente, Option(NBVerweise)), Series(Klassifikation, Option(NBVerweise))), Option(Series(RegExp('\\)'), wsp__))))
    Bedeutungsangabe = Alternative(Series(Token("OHNE"), wsp__), Series(Alternative(Interpretamente, Klassifikation), Option(Nebenbedeutungen), Series(Token(":"), wsp__), mandatory=2, err_msgs=error_messages__["Bedeutungsangabe"]))
    Anhänger = Series(ZWW, Series(Token("ANHÄNGER"), wsp__), Option(LZ), Bedeutungsangabe, BelegPosition, mandatory=3)
    U5Bedeutung = Series(ZWW, Series(Token("UUUUU_BEDEUTUNG"), wsp__), Option(LZ), Bedeutungsangabe, BelegPosition, ZeroOrMore(Anhänger), mandatory=3)
    U4Bedeutung = Series(ZWW, Series(Token("UUUU_BEDEUTUNG"), wsp__), Option(LZ), Bedeutungsangabe, Alternative(Series(BelegPosition, ZeroOrMore(Anhänger)), OneOrMore(U5Bedeutung)), mandatory=3)
    U3Bedeutung = Series(ZWW, Series(Token("UUU_BEDEUTUNG"), wsp__), Option(LZ), Bedeutungsangabe, Alternative(Series(BelegPosition, ZeroOrMore(Anhänger)), OneOrMore(U4Bedeutung)), mandatory=3)
    U2Bedeutung = Series(ZWW, Alternative(Series(Token("UU_BEDEUTUNG"), wsp__), Series(Token("UNTER_UNTER_BEDEUTUNG"), wsp__)), Option(LZ), Bedeutungsangabe, Alternative(Series(BelegPosition, ZeroOrMore(Anhänger)), OneOrMore(U3Bedeutung)), mandatory=3)
    U1Bedeutung = Series(ZWW, Alternative(Series(Token("U_BEDEUTUNG"), wsp__), Series(Token("UNTER_BEDEUTUNG"), wsp__)), Option(LZ), Bedeutungsangabe, Alternative(Series(BelegPosition, ZeroOrMore(Anhänger)), OneOrMore(U2Bedeutung)), mandatory=3)
    Bedeutung = Series(ZWW, Series(Token("BEDEUTUNG"), wsp__), Option(LZ), Bedeutungsangabe, Alternative(Series(BelegPosition, ZeroOrMore(Anhänger)), OneOrMore(U1Bedeutung)), mandatory=3)
    BedeutungsPosition = OneOrMore(Bedeutung)
    Ergänzung = Series(Option(Zusatz), OneOrMore(Interleave(EINZEILER, Zusatz, repetitions=[(1, 1), (0, 1)])))
    Beschreibung.set(Series(NegativeLookahead(RegExp('[A-Z][A-Z_][A-Z_]+')), OneOrMore(Interleave(EINZEILER, Zusatz, repetitions=[(1, 1), (0, 1)])), ZeroOrMore(Series(Series(Token(";"), wsp__), Ergänzung)), Lookahead(Series(Token(":"), wsp__))))
    ER4 = Capture(RegExp(' +'))
    ER3 = Capture(RegExp(' +'))
    ER2 = Capture(RegExp(' +'))
    ER1 = Capture(RegExp(' *'))
    ZWS = OneOrMore(Series(wsp__, RegExp('\\n')))
    TAB_4 = Series(ZWS, Retrieve(ER1), Retrieve(ER2), Retrieve(ER3), Retrieve(ER4))
    TAB_3 = Series(ZWS, Retrieve(ER1), Retrieve(ER2), Retrieve(ER3))
    TAB_2 = Series(ZWS, Retrieve(ER1), Retrieve(ER2))
    TAB_1 = Series(ZWS, Retrieve(ER1))
    Variante = Series(NegativeLookahead(KATEGORIENZEILE), Beschreibung, Series(Token(":"), wsp__), Alternative(Belege, Zusatz), mandatory=3)
    Varianten = Series(OneOrMore(Series(TAB_4, Variante)), Option(Lookahead(Pop(ER4, match_func=optional_last_value))))
    Unterkategorie = Series(TAB_3, Beschreibung, Series(Token(":"), wsp__), Varianten)
    Unterkategorien = Series(OneOrMore(Alternative(Series(TAB_3, Variante), Unterkategorie)), Option(Lookahead(Pop(ER3, match_func=optional_last_value))))
    KVarianten = OneOrMore(Series(TAB_3, Variante))
    Kategorie = Series(TAB_2, Beschreibung, Series(Token(":"), wsp__), Alternative(Unterkategorien, KVarianten))
    Kategorien = Series(OneOrMore(Alternative(Series(TAB_2, Variante), Kategorie)), Option(Lookahead(Pop(ER2, match_func=optional_last_value))))
    Besonderheit = Series(TAB_1, Beschreibung, Series(Token(":"), wsp__), Alternative(Kategorien, Belege), mandatory=3, err_msgs=error_messages__["Besonderheit"])
    Besonderheiten = Series(Besonderheit, ZeroOrMore(Besonderheit), Option(Lookahead(Pop(ER1, match_func=optional_last_value))))
    Position = Alternative(Lookahead(Series(ZWW, GROSSBUCHSTABEN)), Series(Lookahead(ZWW), Besonderheiten, Lookahead(Series(ZWW, GROSSBUCHSTABEN)), mandatory=0, err_msgs=error_messages__["Position"]))
    VerwechselungsPosition = Series(ZWW, Alternative(Series(Token("VERWECHSELBARKEIT"), wsp__), Series(Token("VERWECHSELBAR"), wsp__)), Position)
    MetrikPosition = Series(ZWW, Series(Token("METRIK"), wsp__), Position)
    GebrauchsPosition = Series(ZWW, Series(Token("GEBRAUCH"), wsp__), Position)
    FormPosition = Series(ZWW, Series(Token("FORM"), wsp__), Position)
    StrukturPosition = Series(ZWW, Series(Token("STRUKTUR"), wsp__), Position)
    SchreibweisenPosition = Series(ZWW, Series(Token("SCHREIBWEISE"), wsp__), Position)
    ArtikelKopf = Interleave(SchreibweisenPosition, StrukturPosition, FormPosition, GebrauchsPosition, MetrikPosition, VerwechselungsPosition, repetitions=[(0, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)])
    etymologie_stern = Series(Token("*"), wsp__)
    EtymologieSprache = Alternative(Series(Series(Token("anglosax."), wsp__), Option(Series(Token("vet."), wsp__))), Series(Token("arab."), wsp__), Series(Token("bohem."), wsp__), Series(Token("catal."), wsp__), Series(Token("finnice"), wsp__), Series(Series(Token("franc."), wsp__), Option(Alternative(Series(Token("vet."), wsp__), Series(Series(Token("inf."), wsp__), Series(Token("vet."), wsp__))))), Series(Series(Token("francog."), wsp__), Option(Series(Token("vet."), wsp__))), Series(Token("frisic."), wsp__), Series(Token("gall."), wsp__), Series(Token("germ."), wsp__), Series(Token("graec."), wsp__), Series(Token("hebr."), wsp__), Series(Token("hibern."), wsp__), Series(Series(Token("hisp."), wsp__), Option(Series(Token("vet."), wsp__))), Series(Token("hung."), wsp__), Series(Token("ital."), wsp__), Series(Token("lat."), wsp__), Series(Token("lat-klass."), wsp__), Series(Token("lat-mlw."), wsp__), Series(Token("lat-erschlossen"), wsp__), Series(Series(Token("occ."), wsp__), Option(Series(Token("vet."), wsp__))), Series(Series(Token("polon."), wsp__), Option(Series(Token("vet."), wsp__))), Series(Token("port."), wsp__), Series(Token("raetoroman."), wsp__), Series(Series(Token("saxon"), wsp__), Option(Series(Token("vet."), wsp__))), Series(Token("sard."), wsp__), Series(Token("sicil."), wsp__), Series(Token("slav."), wsp__), Series(Series(Token("theod."), wsp__), Option(Series(Token("inf."), wsp__)), Option(Series(Token("vet."), wsp__))), Series(Token("val."), wsp__))
    EtymologieBeispiel = Series(Option(etymologie_stern), OneOrMore(Series(ETYMOLOGIE_TEXT, Interleave(Kursiv, Zusatz, repetitions=[(0, 1), (0, 1)]))))
    EtymologieAngabe = Alternative(Series(EtymologieSprache, Option(EtymologieBeispiel)), EtymologieBeispiel)
    EtymologieDetail = Series(EtymologieAngabe, Option(Series(Series(Token(":"), wsp__), Belege)))
    EtymologiePosition = Series(ZWW, Series(Token("ETYMOLOGIE"), wsp__), Alternative(Lookahead(Series(ZWW, GROSSBUCHSTABEN)), Series(Option(LZ), EtymologieDetail, ZeroOrMore(Series(ZWW, EtymologieDetail)))))
    GVariante = Series(Lookahead(Alternative(wortarten, casus, flexion, genus)), Interleave(Series(wortarten, Option(ABS)), Series(casus, Option(numerus)), Series(flexion, Option(ABS)), Series(genus, Option(ABS)), repetitions=[(0, 1), (0, 1), (0, 1), (0, 1)]))
    GrammatikVariante = Series(GVariante, DPP, Belege, mandatory=1, err_msgs=error_messages__["GrammatikVariante"])
    GrammatikVarianten = OneOrMore(Series(ABS, GrammatikVariante))
    numerus.set(Alternative(Series(Token("singular"), wsp__), Series(Token("sg."), wsp__), Series(Token("sing."), wsp__), Series(Token("plural"), wsp__), Series(Token("pl."), wsp__), Series(Token("plur."), wsp__)))
    casus.set(Alternative(Series(Token("nominativus"), wsp__), Series(Token("nom."), wsp__), Series(Token("genitivus"), wsp__), Series(Token("gen."), wsp__), Series(Token("dativus"), wsp__), Series(Token("dat."), wsp__), Series(Token("accusativus"), wsp__), Series(Token("akk."), wsp__), Series(Token("ablativus"), wsp__), Series(Token("abl."), wsp__), Series(Token("vocativus"), wsp__), Series(Token("voc."), wsp__)))
    genus.set(Alternative(Series(Token("maskulinum"), wsp__), Series(Token("m."), wsp__), Series(Token("masc."), wsp__), Series(Token("femininum"), wsp__), Series(Token("f."), wsp__), Series(Token("fem."), wsp__), Series(Token("neutrum"), wsp__), Series(Token("n."), wsp__), Series(Token("neutr."), wsp__)))
    genera = Series(genus, Option(Series(Series(Token("vel"), wsp__), Option(Alternative(Series(Token("raro"), wsp__), Series(Token("semel"), wsp__), Zusatz)), genus)))
    FLEX = OneOrMore(Series(NegativeLookahead(Alternative(genus, wortart, casus)), RegExp('-?[a-z]+'), wsp__))
    indeclinabile = Alternative(Series(Token("indecl."), wsp__), Series(Token("indeclinabile"), wsp__))
    flexion.set(Alternative(indeclinabile, Series(FLEX, ZeroOrMore(Series(Series(Token(","), wsp__), FLEX)))))
    verb_klasse = Alternative(Series(Token("IV"), wsp__), Series(Token("III"), wsp__), Series(Token("II"), wsp__), Series(Token("I"), wsp__), Series(Token("anormal"), wsp__), Series(Token("unbestimmt"), wsp__))
    nom_klasse = Alternative(Series(Token("IV"), wsp__), Series(Token("V"), wsp__), Series(Token("III"), wsp__), Series(Token("II"), wsp__), Series(Token("I-II"), wsp__), Series(Token("I"), wsp__), Series(Token("anormal"), wsp__), Series(Token("unbestimmt"), wsp__))
    wa_ergänzung = OneOrMore(Alternative(EINZEILER, Zusatz))
    ET_VERBOTEN = Series(Token("et"), wsp__)
    WA_UNBEKANNT = Series(RegExp('\\w+\\.?'), ZeroOrMore(Series(wsp__, RegExp('\\w+\\.?'))))
    wortart.set(Alternative(Series(Token("adverbium"), wsp__), Series(Token("adv."), wsp__), Series(Series(Token("adiectivum"), wsp__), nom_klasse, mandatory=1), Series(Series(Token("adi."), wsp__), nom_klasse, mandatory=1), Series(Series(Token("comparativus"), wsp__), nom_klasse, mandatory=1), Series(Series(Token("compar."), wsp__), nom_klasse, mandatory=1), Series(Series(Token("interiectio"), wsp__), Option(wa_ergänzung)), Series(Series(Token("interi."), wsp__), Option(wa_ergänzung)), Series(Series(Token("littera"), wsp__), Option(wa_ergänzung)), Series(Series(Token("numerale"), wsp__), nom_klasse, mandatory=1), Series(Series(Token("numer."), wsp__), nom_klasse, mandatory=1), Series(Token("particula"), wsp__), Series(Token("praepositio"), wsp__), Series(Token("praep."), wsp__), Series(Series(Token("pronomen"), wsp__), nom_klasse, mandatory=1), Series(Series(Token("pron."), wsp__), nom_klasse, mandatory=1), Series(Series(Token("substantivum"), wsp__), nom_klasse, mandatory=1), Series(Series(Token("subst."), wsp__), nom_klasse, mandatory=1), Series(Series(Token("superlativus"), wsp__), nom_klasse, mandatory=1), Series(Series(Token("superl."), wsp__), nom_klasse, mandatory=1), Series(Series(Token("verbum"), wsp__), verb_klasse, mandatory=1)))
    wortarten.set(Series(wortart, ZeroOrMore(Series(Alternative(Series(Token("vel"), wsp__), ET_VERBOTEN), Option(Alternative(Series(Token("raro"), wsp__), Series(Token("semel"), wsp__), Zusatz)), wortart))))
    Grammatik = Series(Alternative(Series(wortarten, Lookahead(ABS)), WA_UNBEKANNT), Option(Series(ABS, flexion)), Option(Series(Option(ABS), genera)), mandatory=0, err_msgs=error_messages__["Grammatik"], skip=skip_rules__["Grammatik"])
    GrammatikPosition = Series(ZWW, Series(Token("GRAMMATIK"), wsp__), Option(LZ), Grammatik, Option(GrammatikVarianten), Option(Zusatz))
    _lemma_text = Series(LAT_WORT, ZeroOrMore(Series(Option(Alternative(ZEILENSPRUNG, AUSGEWICHEN)), LAT_WORT)))
    LemmaWort.set(Synonym(_lemma_text))
    LemmaVariante = Series(RegExp('\\-?'), _lemma_text, Option(Series(Option(LL), Zusatz)))
    LemmaVarianten = Series(Series(Token("("), wsp__), LemmaVariante, ZeroOrMore(Series(Series(Token(","), wsp__), Option(ZW), LemmaVariante)), Series(Token(")"), wsp__))
    nicht_gesichert = Series(Token("?"), wsp__)
    nicht_klassisch = Series(Token("*"), wsp__)
    _Lemma = Series(Interleave(nicht_klassisch, nicht_gesichert, repetitions=[(0, 1), (0, 1)]), ZeroOrMore(Series(Zusatz, Option(LL))), LemmaWort)
    Lemma = Synonym(_Lemma)
    LemmaBlock = Series(Option(LZ), ZeroOrMore(Series(Zusatz, Option(LL))), Lemma, Series(Interleave(Series(Option(LL), Zusatz), Series(Option(LL), LemmaVarianten), repetitions=[(0, 1), (0, 1)]), Option(Alternative(GrammatikPosition, EtymologiePosition))), mandatory=2, err_msgs=error_messages__["LemmaBlock"])
    LemmaNr = Series(RegExp('\\d+\\.?'), wsp__)
    LemmaPosition = Series(Option(ABS), Series(Token("LEMMA"), wsp__), Option(LemmaNr), LemmaBlock, ZeroOrMore(Series(Option(LZ), Series(Token("VEL"), wsp__), LemmaBlock)), Option(GrammatikPosition), Lookahead(Alternative(Series(ZeroOrMore(Series(RegExp('\\s+'), wsp__)), RegExp('[A-Z][A-Z][A-Z]')), DATEI_ENDE)), mandatory=6, err_msgs=error_messages__["LemmaPosition"])
    NachtragsStelle = Synonym(STELLENTEXT)
    Ziffer = Series(RegExp('\\d+\\.'), wsp__)
    NachtragsLemma = Series(Option(Ziffer), Interleave(nicht_klassisch, nicht_gesichert, repetitions=[(0, 1), (0, 1)]), ZeroOrMore(Series(Zusatz, Option(LL))), LemmaWort)
    post = Series(Series(Token("post"), wsp__), Alternative(NachtragsStelle, NachtragsLemma), mandatory=1)
    ad = Series(Series(Token("ad"), wsp__), Alternative(NachtragsLemma, NachtragsStelle), mandatory=1)
    Nachtrag = Series(Option(Series(ad, Series(Token(";"), wsp__))), post, Series(Token(":"), wsp__), Option(LZ), Option(Ziffer))
    NachtragsPosition = Series(Series(Token("NACHTRAG"), wsp__), Nachtrag, Lookahead(Series(ZeroOrMore(Series(RegExp('\\s+'), wsp__)), Series(Token("LEMMA"), wsp__))), mandatory=1)
    SubLemmaPosition = Series(Series(Token("SUB_LEMMA"), wsp__), Option(LemmaNr), LemmaBlock, ZeroOrMore(Series(Option(LZ), Series(Token("VEL"), wsp__), LemmaBlock)), Lookahead(Series(ZeroOrMore(Series(RegExp('\\s+'), wsp__)), RegExp('[A-Z][A-Z][A-Z]'))), mandatory=4)
    UnterArtikel = Series(ZWW, SubLemmaPosition, Option(EtymologiePosition), ArtikelKopf, BedeutungsPosition, Option(VerweisPosition), mandatory=2)
    PRAETER = Series(Token("PRAETER"), wsp__)
    ET = Series(Token("ET"), wsp__)
    VIDE = Series(Token("VIDE"), wsp__)
    ellipse = Series(Token("-"), wsp__)
    ZielLemma = Synonym(_Lemma)
    VerweisLemmazeile = Series(Option(LemmaNr), ZielLemma, Option(EinzelVerweis), Option(Zusatz), Option(Series(Series(Token(":"), wsp__), Option(LZ), Belege)))
    Vide = Series(Option(LL), VIDE, Option(LL), Alternative(EinzelVerweis, Zusatz, Series(VerweisLemmazeile, ZeroOrMore(Series(Option(LZ), ET, Option(LZ), VerweisLemmazeile)))), mandatory=3, skip=skip_rules__["Vide"])
    VerweisBlock = Series(Option(Series(LemmaNr, NegativeLookahead(unberechtigt), mandatory=1, err_msgs=error_messages__["VerweisBlock"], skip=skip_rules__["VerweisBlock"])), Option(LZ), ZeroOrMore(Series(Zusatz, Option(LL))), Lemma, Option(ellipse), ZeroOrMore(Series(KOMMA, Lemma, Option(ellipse))), Vide)
    unberechtigt.set(Series(Series(Token("["), wsp__), Option(LZ), VerweisBlock, Option(LZ), Series(Token("]"), wsp__), mandatory=4))
    PraeterBlock = Series(Option(LL), PRAETER, VerweisBlock, mandatory=2)
    _VerweisBlöcke = OneOrMore(Series(Option(LZ), Series(Token("LEMMA"), wsp__), Alternative(VerweisBlock, unberechtigt), ZeroOrMore(PraeterBlock)))
    VerweisArtikel = Series(_VerweisBlöcke, Option(ArtikelVerfasser), Option(LZ), DATEI_ENDE, mandatory=3, skip=skip_rules__["VerweisArtikel"])
    Artikel = Alternative(VerweisArtikel, Series(Option(LZ), Option(NachtragsPosition), OneOrMore(LemmaPosition), Option(EtymologiePosition), ArtikelKopf, Option(BedeutungsPosition), Option(VerweisPosition), ZeroOrMore(UnterArtikel), Option(ArtikelVerfasser), Option(Stellenverzeichnis), Option(LZ), DATEI_ENDE, mandatory=2, err_msgs=error_messages__["Artikel"], skip=skip_rules__["Artikel"]))
    root__ = Artikel
    

def get_grammar() -> MLWGrammar:
    """Returns a thread/process-exclusive MLWGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.MLW_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.MLW_00000001_grammar_singleton = MLWGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.MLW_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.MLW_00000001_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

MLW_AST_transformation_table = {
    # AST Transformations for the MLW-grammar
    "<": flatten,
    "Artikel": [],
    "VerweisArtikel": [],
    "_VerweisBlöcke": [],
    "PraeterBlock": [],
    "unberechtigt": [],
    "VerweisBlock": [],
    "Vide": [],
    "VerweisLemmazeile": [],
    "ZielLemma": [],
    "ellipse": [],
    "VIDE": [],
    "ET": [],
    "PRAETER": [],
    "UnterArtikel": [],
    "SubLemmaPosition": [],
    "NachtragsPosition": [],
    "Nachtrag": [],
    "ad": [],
    "post": [],
    "NachtragsLemma": [],
    "Ziffer": [],
    "NachtragsStelle": [],
    "LemmaPosition": [],
    "LemmaNr": [],
    "LemmaBlock": [],
    "Lemma": [],
    "_Lemma": [],
    "nicht_klassisch": [],
    "nicht_gesichert": [],
    "LemmaVarianten": [],
    "LemmaVariante": [],
    "LemmaWort": [],
    "_lemma_text": [],
    "GrammatikPosition": [],
    "Grammatik": [],
    "wortarten": [],
    "wortart": [],
    "WA_UNBEKANNT": [],
    "ET_VERBOTEN": [],
    "wa_ergänzung": [],
    "nom_klasse": [],
    "verb_klasse": [],
    "flexion": [],
    "indeclinabile": [],
    "FLEX": [],
    "genera": [],
    "genus": [],
    "casus": [],
    "numerus": [],
    "GrammatikVarianten": [],
    "GrammatikVariante": [],
    "GVariante": [],
    "EtymologiePosition": [],
    "EtymologieDetail": [],
    "EtymologieAngabe": [],
    "EtymologieBeispiel": [],
    "EtymologieSprache": [],
    "etymologie_stern": [],
    "ArtikelKopf": [],
    "SchreibweisenPosition": [],
    "StrukturPosition": [],
    "FormPosition": [],
    "GebrauchsPosition": [],
    "MetrikPosition": [],
    "VerwechselungsPosition": [],
    "Position": [],
    "Besonderheiten": [],
    "Besonderheit": [],
    "Kategorien": [],
    "Kategorie": [],
    "KVarianten": [],
    "Unterkategorien": [],
    "Unterkategorie": [],
    "Varianten": [],
    "Variante": [],
    "TAB_1": [],
    "TAB_2": [],
    "TAB_3": [],
    "TAB_4": [],
    "ZWS": [],
    "ER1": [],
    "ER2": [],
    "ER3": [],
    "ER4": [],
    "Beschreibung": [],
    "Ergänzung": [],
    "BedeutungsPosition": [],
    "Bedeutung": [],
    "U1Bedeutung": [],
    "U2Bedeutung": [],
    "U3Bedeutung": [],
    "U4Bedeutung": [],
    "U5Bedeutung": [],
    "Anhänger": [],
    "Bedeutungsangabe": [],
    "Nebenbedeutungen": [],
    "NBVerweise": [],
    "Klassifikation": [],
    "Kategorienangabe": [],
    "Interpretamente": [],
    "LateinischeBedeutung": [],
    "DeutscheBedeutung": [],
    "LateinischerAusdruck": [],
    "DeutscherAusdruck": [],
    "unsicher": [],
    "LateinischerBestandteil": [],
    "DeutscherBestandteil": [],
    "Qualifizierung": [],
    "LateinischeEllipse": [],
    "DeutscheEllipse": [],
    "LateinischesWort": [],
    "DeutschesWort": [],
    "LateinischeKlammer": [],
    "DeutscheKlammer": [],
    "BelegPosition": [],
    "VerweisPosition": [],
    "verweis_stern": [],
    "ArtikelVerfasser": [],
    "Name": [],
    "unbekannt": [],
    "Stellenverzeichnis": [],
    "Verweisliste": [],
    "Stellenverweis": [],
    "NullVerweis": [],
    "Zusatz": [],
    "FreierZusatz": [],
    "ZusatzInhalt": [],
    "Sperrung": [],
    "Kursiv": [],
    "Junktur": [],
    "FesterZusatz": [],
    "VariaLectioZusatz": [],
    "Belege": [],
    "Einschub": [],
    "Zusatzzeilen": [],
    "Beleg": [],
    "Quellenangabe": [],
    "Quelle": [],
    "Sekundärliteratur": [],
    "Autorangabe": [],
    "BelegStelle": [],
    "Stellenangabe": [],
    "Datierung": [],
    "BelegText": [],
    "BelegKern": [],
    "BelegLemma": [],
    "Lemmawort": [],
    "LEMMAWORT": [],
    "AutorWerk": [],
    "Autor": [],
    "disambig_marker": [],
    "FALSCHER_MARKER": [],
    "Werk": [],
    "Stelle": [],
    "opus": [],
    "opus_minus": [],
    "om_kern": [],
    "om_regeln": [],
    "OM_WERK": [],
    "OriginalStelle": [],
    "Verweise": [],
    "EinzelVerweis": [],
    "VerweisKern": [],
    "Anker": [],
    "Verweis": [],
    "URL": [],
    "alias": [],
    "protokoll": [],
    "pfad": [],
    "ziel": [],
    "PFAD_NAME": [],
    "ANKER_NAME": [],
    "NAMENS_ABKÜRZUNG": [],
    "NAME": [],
    "DEU_WORT": [],
    "DEU_GWORT": [],
    "DEU_GROSS": [],
    "GROSSBUCHSTABEN": [],
    "DEU_KLEIN": [],
    "DEU_GEMISCHT": [],
    "LAT_WORT": [],
    "LAT_GWORT": [],
    "GROSSSCHRIFT": [],
    "GRI_WORT": [],
    "GRI_VERBOTEN": [],
    "SEITENZAHL": [],
    "ROEMISCHE_ZAHL": [],
    "HOCHGESTELLT": [],
    "SCHLUESSELWORT": [],
    "AUTORANFANG": [],
    "AUTORNAME": [],
    "WERKTITEL_ANFANG": [],
    "WERKTITEL_FOLGE": [],
    "BINDESTRICH": [],
    "SATZZEICHEN": [],
    "TEIL_SATZZEICHEN": [],
    "ZITAT_SATZZEICHEN": [],
    "TEXTELEMENT": [],
    "AUSGEWICHEN": [],
    "KLAMMER_AUF": [],
    "KLAMMER_ZU": [],
    "ECKIGE_AUF": [],
    "ECKIGE_ZU": [],
    "KLEINER_ZEICHEN": [],
    "GRÖßER_ZEICHEN": [],
    "EINSCHUB_ANFANG": [],
    "EINSCHUB_ENDE": [],
    "STELLENTEXT": [],
    "STELLENKERN": [],
    "_STELLENKERN": [],
    "EINZEILER": [],
    "ETYMOLOGIE_TEXT": [],
    "FREITEXT": [],
    "XML": [],
    "TAG_NAME": [],
    "ZITAT": [],
    "ZITAT_ANFANG": [],
    "ZITAT_ENDE": [],
    "MEHRZEILER": [],
    "L": [],
    "LL": [],
    "ABS": [],
    "LZ": [],
    "DPP": [],
    "KOMMA": [],
    "ZW": [],
    "ZLL": [],
    "ZWW": [],
    "LÜCKE": [],
    "LEERZEILEN": [],
    "ZEILENSPRUNG": [],
    "KOMMENTARZEILEN": [],
    "KATEGORIENZEILE": [],
    "VARIANTE": [],
    "VERBOTEN": [],
    "DATEI_ENDE": [],
    "_LATEIN": [],
    "_LATEIN_FOLGE": [],
    "_LATEIN_KLEIN": [],
    "_LATEIN_KLEIN_FOLGE": [],
    "_LATEIN_GROSS": [],
    "_LATEIN_GROSS_FOLGE": [],
    "*": replace_by_single_child
}



def CreateMLWTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=MLW_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.MLW_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.MLW_00000001_transformer_singleton = CreateMLWTransformer()
        transformer = THREAD_LOCALS.MLW_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class MLWCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a MLW source file.
    """

    def __init__(self):
        super(MLWCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_Artikel(self, node):
        return self.fallback_compiler(node)

    # def on_VerweisArtikel(self, node):
    #     return node

    # def on__VerweisBlöcke(self, node):
    #     return node

    # def on_PraeterBlock(self, node):
    #     return node

    # def on_unberechtigt(self, node):
    #     return node

    # def on_VerweisBlock(self, node):
    #     return node

    # def on_Vide(self, node):
    #     return node

    # def on_VerweisLemmazeile(self, node):
    #     return node

    # def on_ZielLemma(self, node):
    #     return node

    # def on_ellipse(self, node):
    #     return node

    # def on_VIDE(self, node):
    #     return node

    # def on_ET(self, node):
    #     return node

    # def on_PRAETER(self, node):
    #     return node

    # def on_UnterArtikel(self, node):
    #     return node

    # def on_SubLemmaPosition(self, node):
    #     return node

    # def on_NachtragsPosition(self, node):
    #     return node

    # def on_Nachtrag(self, node):
    #     return node

    # def on_ad(self, node):
    #     return node

    # def on_post(self, node):
    #     return node

    # def on_NachtragsLemma(self, node):
    #     return node

    # def on_Ziffer(self, node):
    #     return node

    # def on_NachtragsStelle(self, node):
    #     return node

    # def on_LemmaPosition(self, node):
    #     return node

    # def on_LemmaNr(self, node):
    #     return node

    # def on_LemmaBlock(self, node):
    #     return node

    # def on_Lemma(self, node):
    #     return node

    # def on__Lemma(self, node):
    #     return node

    # def on_nicht_klassisch(self, node):
    #     return node

    # def on_nicht_gesichert(self, node):
    #     return node

    # def on_LemmaVarianten(self, node):
    #     return node

    # def on_LemmaVariante(self, node):
    #     return node

    # def on_LemmaWort(self, node):
    #     return node

    # def on__lemma_text(self, node):
    #     return node

    # def on_GrammatikPosition(self, node):
    #     return node

    # def on_Grammatik(self, node):
    #     return node

    # def on_wortarten(self, node):
    #     return node

    # def on_wortart(self, node):
    #     return node

    # def on_WA_UNBEKANNT(self, node):
    #     return node

    # def on_ET_VERBOTEN(self, node):
    #     return node

    # def on_wa_ergänzung(self, node):
    #     return node

    # def on_nom_klasse(self, node):
    #     return node

    # def on_verb_klasse(self, node):
    #     return node

    # def on_flexion(self, node):
    #     return node

    # def on_indeclinabile(self, node):
    #     return node

    # def on_FLEX(self, node):
    #     return node

    # def on_genera(self, node):
    #     return node

    # def on_genus(self, node):
    #     return node

    # def on_casus(self, node):
    #     return node

    # def on_numerus(self, node):
    #     return node

    # def on_GrammatikVarianten(self, node):
    #     return node

    # def on_GrammatikVariante(self, node):
    #     return node

    # def on_GVariante(self, node):
    #     return node

    # def on_EtymologiePosition(self, node):
    #     return node

    # def on_EtymologieDetail(self, node):
    #     return node

    # def on_EtymologieAngabe(self, node):
    #     return node

    # def on_EtymologieBeispiel(self, node):
    #     return node

    # def on_EtymologieSprache(self, node):
    #     return node

    # def on_etymologie_stern(self, node):
    #     return node

    # def on_ArtikelKopf(self, node):
    #     return node

    # def on_SchreibweisenPosition(self, node):
    #     return node

    # def on_StrukturPosition(self, node):
    #     return node

    # def on_FormPosition(self, node):
    #     return node

    # def on_GebrauchsPosition(self, node):
    #     return node

    # def on_MetrikPosition(self, node):
    #     return node

    # def on_VerwechselungsPosition(self, node):
    #     return node

    # def on_Position(self, node):
    #     return node

    # def on_Besonderheiten(self, node):
    #     return node

    # def on_Besonderheit(self, node):
    #     return node

    # def on_Kategorien(self, node):
    #     return node

    # def on_Kategorie(self, node):
    #     return node

    # def on_KVarianten(self, node):
    #     return node

    # def on_Unterkategorien(self, node):
    #     return node

    # def on_Unterkategorie(self, node):
    #     return node

    # def on_Varianten(self, node):
    #     return node

    # def on_Variante(self, node):
    #     return node

    # def on_TAB_1(self, node):
    #     return node

    # def on_TAB_2(self, node):
    #     return node

    # def on_TAB_3(self, node):
    #     return node

    # def on_TAB_4(self, node):
    #     return node

    # def on_ZWS(self, node):
    #     return node

    # def on_ER1(self, node):
    #     return node

    # def on_ER2(self, node):
    #     return node

    # def on_ER3(self, node):
    #     return node

    # def on_ER4(self, node):
    #     return node

    # def on_Beschreibung(self, node):
    #     return node

    # def on_Ergänzung(self, node):
    #     return node

    # def on_BedeutungsPosition(self, node):
    #     return node

    # def on_Bedeutung(self, node):
    #     return node

    # def on_U1Bedeutung(self, node):
    #     return node

    # def on_U2Bedeutung(self, node):
    #     return node

    # def on_U3Bedeutung(self, node):
    #     return node

    # def on_U4Bedeutung(self, node):
    #     return node

    # def on_U5Bedeutung(self, node):
    #     return node

    # def on_Anhänger(self, node):
    #     return node

    # def on_Bedeutungsangabe(self, node):
    #     return node

    # def on_Nebenbedeutungen(self, node):
    #     return node

    # def on_NBVerweise(self, node):
    #     return node

    # def on_Klassifikation(self, node):
    #     return node

    # def on_Kategorienangabe(self, node):
    #     return node

    # def on_Interpretamente(self, node):
    #     return node

    # def on_LateinischeBedeutung(self, node):
    #     return node

    # def on_DeutscheBedeutung(self, node):
    #     return node

    # def on_LateinischerAusdruck(self, node):
    #     return node

    # def on_DeutscherAusdruck(self, node):
    #     return node

    # def on_unsicher(self, node):
    #     return node

    # def on_LateinischerBestandteil(self, node):
    #     return node

    # def on_DeutscherBestandteil(self, node):
    #     return node

    # def on_Qualifizierung(self, node):
    #     return node

    # def on_LateinischeEllipse(self, node):
    #     return node

    # def on_DeutscheEllipse(self, node):
    #     return node

    # def on_LateinischesWort(self, node):
    #     return node

    # def on_DeutschesWort(self, node):
    #     return node

    # def on_LateinischeKlammer(self, node):
    #     return node

    # def on_DeutscheKlammer(self, node):
    #     return node

    # def on_BelegPosition(self, node):
    #     return node

    # def on_VerweisPosition(self, node):
    #     return node

    # def on_verweis_stern(self, node):
    #     return node

    # def on_ArtikelVerfasser(self, node):
    #     return node

    # def on_Name(self, node):
    #     return node

    # def on_unbekannt(self, node):
    #     return node

    # def on_Stellenverzeichnis(self, node):
    #     return node

    # def on_Verweisliste(self, node):
    #     return node

    # def on_Stellenverweis(self, node):
    #     return node

    # def on_NullVerweis(self, node):
    #     return node

    # def on_Zusatz(self, node):
    #     return node

    # def on_FreierZusatz(self, node):
    #     return node

    # def on_ZusatzInhalt(self, node):
    #     return node

    # def on_Sperrung(self, node):
    #     return node

    # def on_Kursiv(self, node):
    #     return node

    # def on_Junktur(self, node):
    #     return node

    # def on_FesterZusatz(self, node):
    #     return node

    # def on_VariaLectioZusatz(self, node):
    #     return node

    # def on_Belege(self, node):
    #     return node

    # def on_Einschub(self, node):
    #     return node

    # def on_Zusatzzeilen(self, node):
    #     return node

    # def on_Beleg(self, node):
    #     return node

    # def on_Quellenangabe(self, node):
    #     return node

    # def on_Quelle(self, node):
    #     return node

    # def on_Sekundärliteratur(self, node):
    #     return node

    # def on_Autorangabe(self, node):
    #     return node

    # def on_BelegStelle(self, node):
    #     return node

    # def on_Stellenangabe(self, node):
    #     return node

    # def on_Datierung(self, node):
    #     return node

    # def on_BelegText(self, node):
    #     return node

    # def on_BelegKern(self, node):
    #     return node

    # def on_BelegLemma(self, node):
    #     return node

    # def on_Lemmawort(self, node):
    #     return node

    # def on_LEMMAWORT(self, node):
    #     return node

    # def on_AutorWerk(self, node):
    #     return node

    # def on_Autor(self, node):
    #     return node

    # def on_disambig_marker(self, node):
    #     return node

    # def on_FALSCHER_MARKER(self, node):
    #     return node

    # def on_Werk(self, node):
    #     return node

    # def on_Stelle(self, node):
    #     return node

    # def on_opus(self, node):
    #     return node

    # def on_opus_minus(self, node):
    #     return node

    # def on_om_kern(self, node):
    #     return node

    # def on_om_regeln(self, node):
    #     return node

    # def on_OM_WERK(self, node):
    #     return node

    # def on_OriginalStelle(self, node):
    #     return node

    # def on_Verweise(self, node):
    #     return node

    # def on_EinzelVerweis(self, node):
    #     return node

    # def on_VerweisKern(self, node):
    #     return node

    # def on_Anker(self, node):
    #     return node

    # def on_Verweis(self, node):
    #     return node

    # def on_URL(self, node):
    #     return node

    # def on_alias(self, node):
    #     return node

    # def on_protokoll(self, node):
    #     return node

    # def on_pfad(self, node):
    #     return node

    # def on_ziel(self, node):
    #     return node

    # def on_PFAD_NAME(self, node):
    #     return node

    # def on_ANKER_NAME(self, node):
    #     return node

    # def on_NAMENS_ABKÜRZUNG(self, node):
    #     return node

    # def on_NAME(self, node):
    #     return node

    # def on_DEU_WORT(self, node):
    #     return node

    # def on_DEU_GWORT(self, node):
    #     return node

    # def on_DEU_GROSS(self, node):
    #     return node

    # def on_GROSSBUCHSTABEN(self, node):
    #     return node

    # def on_DEU_KLEIN(self, node):
    #     return node

    # def on_DEU_GEMISCHT(self, node):
    #     return node

    # def on_LAT_WORT(self, node):
    #     return node

    # def on_LAT_GWORT(self, node):
    #     return node

    # def on_GROSSSCHRIFT(self, node):
    #     return node

    # def on_GRI_WORT(self, node):
    #     return node

    # def on_GRI_VERBOTEN(self, node):
    #     return node

    # def on_SEITENZAHL(self, node):
    #     return node

    # def on_ROEMISCHE_ZAHL(self, node):
    #     return node

    # def on_HOCHGESTELLT(self, node):
    #     return node

    # def on_SCHLUESSELWORT(self, node):
    #     return node

    # def on_AUTORANFANG(self, node):
    #     return node

    # def on_AUTORNAME(self, node):
    #     return node

    # def on_WERKTITEL_ANFANG(self, node):
    #     return node

    # def on_WERKTITEL_FOLGE(self, node):
    #     return node

    # def on_BINDESTRICH(self, node):
    #     return node

    # def on_SATZZEICHEN(self, node):
    #     return node

    # def on_TEIL_SATZZEICHEN(self, node):
    #     return node

    # def on_ZITAT_SATZZEICHEN(self, node):
    #     return node

    # def on_TEXTELEMENT(self, node):
    #     return node

    # def on_AUSGEWICHEN(self, node):
    #     return node

    # def on_KLAMMER_AUF(self, node):
    #     return node

    # def on_KLAMMER_ZU(self, node):
    #     return node

    # def on_ECKIGE_AUF(self, node):
    #     return node

    # def on_ECKIGE_ZU(self, node):
    #     return node

    # def on_KLEINER_ZEICHEN(self, node):
    #     return node

    # def on_GRÖßER_ZEICHEN(self, node):
    #     return node

    # def on_EINSCHUB_ANFANG(self, node):
    #     return node

    # def on_EINSCHUB_ENDE(self, node):
    #     return node

    # def on_STELLENTEXT(self, node):
    #     return node

    # def on_STELLENKERN(self, node):
    #     return node

    # def on__STELLENKERN(self, node):
    #     return node

    # def on_EINZEILER(self, node):
    #     return node

    # def on_ETYMOLOGIE_TEXT(self, node):
    #     return node

    # def on_FREITEXT(self, node):
    #     return node

    # def on_XML(self, node):
    #     return node

    # def on_TAG_NAME(self, node):
    #     return node

    # def on_ZITAT(self, node):
    #     return node

    # def on_ZITAT_ANFANG(self, node):
    #     return node

    # def on_ZITAT_ENDE(self, node):
    #     return node

    # def on_MEHRZEILER(self, node):
    #     return node

    # def on_L(self, node):
    #     return node

    # def on_LL(self, node):
    #     return node

    # def on_ABS(self, node):
    #     return node

    # def on_LZ(self, node):
    #     return node

    # def on_DPP(self, node):
    #     return node

    # def on_KOMMA(self, node):
    #     return node

    # def on_ZW(self, node):
    #     return node

    # def on_ZLL(self, node):
    #     return node

    # def on_ZWW(self, node):
    #     return node

    # def on_LÜCKE(self, node):
    #     return node

    # def on_LEERZEILEN(self, node):
    #     return node

    # def on_ZEILENSPRUNG(self, node):
    #     return node

    # def on_KOMMENTARZEILEN(self, node):
    #     return node

    # def on_KATEGORIENZEILE(self, node):
    #     return node

    # def on_VARIANTE(self, node):
    #     return node

    # def on_VERBOTEN(self, node):
    #     return node

    # def on_DATEI_ENDE(self, node):
    #     return node

    # def on__LATEIN(self, node):
    #     return node

    # def on__LATEIN_FOLGE(self, node):
    #     return node

    # def on__LATEIN_KLEIN(self, node):
    #     return node

    # def on__LATEIN_KLEIN_FOLGE(self, node):
    #     return node

    # def on__LATEIN_GROSS(self, node):
    #     return node

    # def on__LATEIN_GROSS_FOLGE(self, node):
    #     return node



def get_compiler() -> MLWCompiler:
    """Returns a thread/process-exclusive MLWCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.MLW_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.MLW_00000001_compiler_singleton = MLWCompiler()
        compiler = THREAD_LOCALS.MLW_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
        elif parser_update:
            print(os.path.basename(__file__) + ' has changed. '
              'Please run again in order to apply updated compiler')
            sys.exit(0)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
            set_config_value('history_tracking', True)
            set_config_value('resume_notices', True)
            set_config_value('log_syntax_trees', set(('cst', 'ast')))
        start_logging(log_dir)
        result, errors, _ = compile_src(file_name)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.serialize() if isinstance(result, Node) else result)
    else:
        print("Usage: MLWParser.py [FILENAME]")
