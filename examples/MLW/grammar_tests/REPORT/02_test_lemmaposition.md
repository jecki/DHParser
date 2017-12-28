

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
                "facitergula"
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
            "fascitergula"
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
                    "facietergula"
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
                    "facistergula"
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
                    "farcutergula"
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
            "fascitergula"
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
                (DEU_WORT
                    "sim."
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
            "fascitergula"
        )
        (:ZeroOrMore
            (LAT_WORT
                "facietergula"
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
                    (DEU_WORT
                        "sim."
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
        (Lemma
            (LemmaWort
                (LAT_WORT
                    "facitergula"
                )
            )
        )
        (LemmaVarianten
            (LAT_WORT
                "fascitergula"
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
                        "facietergula"
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
                        "facistergula"
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
                            (DEU_WORT
                                "sim."
                            )
                        )
                    )
                )
            )
        )
        (GrammatikPosition
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
        )
    )