

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
        (LAT_WORT
            (:RegExp
                "fascitergula"
            )
        )
        (:ZeroOrMore
            (:Series
                (ZW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
                (LAT_WORT
                    (:RegExp
                        "facietergula"
                    )
                )
            )
            (:Series
                (ZW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
                (LAT_WORT
                    (:RegExp
                        "facistergula"
                    )
                )
            )
            (:Series
                (ZW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
                (LAT_WORT
                    (:RegExp
                        "farcutergula"
                    )
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    fascitergula

### AST
    (LemmaVarianten
        (LAT_WORT
            (:RegExp
                "fascitergula"
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    fascitergula facietergula {sim.}

### AST
    (LemmaVarianten
        (LAT_WORT
            (:RegExp
                "fascitergula"
            )
            (:Whitespace
                " "
            )
        )
        (LemmaVariante
            (LAT_WORT
                (:RegExp
                    "facietergula"
                )
                (:Whitespace
                    " "
                )
            )
            (Zusatz
                (:Series
                    (:Token
                        "{"
                    )
                    (DEU_WORT
                        (DEU_KLEIN
                            (:RegExp
                                "sim."
                            )
                        )
                    )
                    (:Token
                        "}"
                    )
                )
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    fascitergula, facietergula, fascistergula {sim.}

### AST
    (LemmaVarianten
        (LAT_WORT
            (:RegExp
                "fascitergula"
            )
        )
        (:ZeroOrMore
            (:Series
                (:Token
                    (:RegExp
                        ","
                    )
                    (:Whitespace
                        " "
                    )
                )
                (LAT_WORT
                    (:RegExp
                        "facietergula"
                    )
                )
            )
            (:Series
                (:Token
                    (:RegExp
                        ","
                    )
                    (:Whitespace
                        " "
                    )
                )
                (LemmaVariante
                    (LAT_WORT
                        (:RegExp
                            "fascistergula"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (Zusatz
                        (:Series
                            (:Token
                                "{"
                            )
                            (DEU_WORT
                                (DEU_KLEIN
                                    (:RegExp
                                        "sim."
                                    )
                                )
                            )
                            (:Token
                                "}"
                            )
                        )
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
    fascitercula {sim.}
    
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
            (LZ
                (:RegExp
                    ""
                    ""
                )
            )
        )
        (LemmaVarianten
            (LAT_WORT
                (:RegExp
                    "fascitergula"
                )
            )
            (:ZeroOrMore
                (:Series
                    (ZW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                    (LAT_WORT
                        (:RegExp
                            "facietergula"
                        )
                    )
                )
                (:Series
                    (ZW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                    (LAT_WORT
                        (:RegExp
                            "facistergula"
                        )
                    )
                )
                (:Series
                    (ZW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                    (LemmaVariante
                        (LAT_WORT
                            (:RegExp
                                "fascitercula"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (Zusatz
                            (:Series
                                (:Token
                                    "{"
                                )
                                (DEU_WORT
                                    (DEU_KLEIN
                                        (:RegExp
                                            "sim."
                                        )
                                    )
                                )
                                (:Token
                                    "}"
                                )
                            )
                        )
                    )
                )
            )
        )
        (GrammatikPosition
            (ZWW
                (ZEILENSPRUNG
                    (:RegExp
                        ""
                        ""
                    )
                )
                (LZ
                    (:RegExp
                        ""
                        ""
                    )
                )
            )
            (:Token
                "GRAMMATIK"
            )
            (LZ
                (:RegExp
                    ""
                    ""
                )
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
        )
    )