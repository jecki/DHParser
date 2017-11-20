

Test of parser: "Lemma"
=======================


Match-test "1"
--------------

### Test-code:
    facitergula

### AST
    (Lemma
        (LemmaWort
            (LAT_WORT
                (:RegExp
                    "facitergula"
                )
            )
        )
    )

Fail-test "99"
--------------

### Test-code:
    duo vocabula


Test of parser: "LemmaVarianten"
================================


Match-test "1"
--------------

### Test-code:
    
    fascitergula
    facietergula
    facistergula
    farcutergula
    

### AST
    (LemmaVarianten
        (LZ
            ""
            ""
        )
        (:OneOrMore
            (:Series
                (LAT_WORT_TEIL
                    "fascitergula"
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
            (:Series
                (LAT_WORT_TEIL
                    "facietergula"
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
            (:Series
                (LAT_WORT_TEIL
                    "facistergula"
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
            (:Series
                (LAT_WORT_TEIL
                    "farcutergula"
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
     fascitergula;

### AST
    (LemmaVarianten
        (LZ
            " "
        )
        (:Series
            (LAT_WORT_TEIL
                "fascitergula"
            )
            (ABS
                ";"
            )
        )
    )

Match-test "3"
--------------

### Test-code:
     fascitergula facietergula ZUSATZ sim.
    

### AST
    (LemmaVarianten
        (LZ
            " "
        )
        (:OneOrMore
            (:Series
                (LAT_WORT_TEIL
                    "fascitergula"
                )
                (LZ
                    " "
                )
            )
            (:Series
                (LAT_WORT_TEIL
                    "facietergula"
                )
                (LZ
                    " "
                )
            )
        )
        (:Series
            (Zusatz
                (:Token
                    (:RegExp
                        "ZUSATZ"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (zusatz_typ
                    "sim."
                )
            )
            (ZWW
                (ZEILENSPRUNG
                    (:RegExp
                        ""
                        ""
                    )
                )
            )
        )
    )

Fail-test "99"
--------------

### Test-code:
    * fascitergula


Test of parser: "LemmaPosition"
===============================


Match-test "1"
--------------

### Test-code:
    LEMMA facitergula
    
    fascitergula
    facietergula
    facistergula
    fascitercula
    
    ZUSATZ sim.
    
    GRAMMATIK
    nomen; -ae f.
    

### AST
    (LemmaPosition
        (:Token
            (:RegExp
                "LEMMA"
            )
            (:Whitespace
                " "
            )
        )
        (Lemma
            (LemmaWort
                (LAT_WORT
                    (:RegExp
                        "facitergula"
                    )
                )
            )
        )
        (ZWW
            (ZEILENSPRUNG
                (:RegExp
                    ""
                    ""
                )
            )
            (LEERRAUM
                (:RegExp
                    ""
                    ""
                )
            )
        )
        (LemmaVarianten
            (:OneOrMore
                (:Series
                    (LAT_WORT_TEIL
                        "fascitergula"
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
                (:Series
                    (LAT_WORT_TEIL
                        "facietergula"
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
                (:Series
                    (LAT_WORT_TEIL
                        "facistergula"
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
                (:Series
                    (LAT_WORT_TEIL
                        "fascitercula"
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                        (LEERRAUM
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
            )
            (:Series
                (Zusatz
                    (:Token
                        (:RegExp
                            "ZUSATZ"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (zusatz_typ
                        "sim."
                    )
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                    (LEERRAUM
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
        )
        (GrammatikPosition
            (:Token
                "GRAMMATIK"
            )
            (LZ
                ""
                ""
            )
            (Grammatik
                (wortart
                    "nomen"
                )
                (ABS
                    "; "
                )
                (flexion
                    (FLEX
                        (:RegExp
                            "-ae"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                )
                (genus
                    "f."
                )
            )
            (ZWW
                (ZEILENSPRUNG
                    (:RegExp
                        ""
                        ""
                    )
                )
            )
        )
    )