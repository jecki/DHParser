

Test of parser: "Lemma"
=======================


Match-test "1"
--------------

### Test-code:
    facitergula

### AST
    (Lemma
        (LemmaWort
            (LAT_WORT_TEIL
                "facitergula"
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    facitergul|a

### AST
    (Lemma
        (LemmaWort
            (LAT_WORT_TEIL
                "facitergul"
            )
            (:Series
                (:Token
                    "|"
                )
                (LAT_WORT_TEIL
                    "a"
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    fasc|itergula

### AST
    (Lemma
        (LemmaWort
            (LAT_WORT_TEIL
                "fasc"
            )
            (:Series
                (:Token
                    "|"
                )
                (LAT_WORT_TEIL
                    "itergula"
                )
            )
        )
    )


Test of parser: "LemmaVarianten"
================================


Match-test "1"
--------------

### Test-code:
    
    fasc-itergula
    fac-iet-ergula
    fac-ist-ergula
    fa-rcu-tergula
    

### AST
    (LemmaVarianten
        (LZ
            ""
            ""
        )
        (:OneOrMore
            (:Series
                (LemmaWort
                    (LAT_WORT_TEIL
                        "fasc"
                    )
                    (:Series
                        (:Token
                            "-"
                        )
                        (LAT_WORT_TEIL
                            "itergula"
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
                )
            )
            (:Series
                (LemmaWort
                    (LAT_WORT_TEIL
                        "fac"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "iet"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ergula"
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
                )
            )
            (:Series
                (LemmaWort
                    (LAT_WORT_TEIL
                        "fac"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ist"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ergula"
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
                )
            )
            (:Series
                (LemmaWort
                    (LAT_WORT_TEIL
                        "fa"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "rcu"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "tergula"
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
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
     fasc-itergula;

### AST
    (LemmaVarianten
        (LZ
            " "
        )
        (:Series
            (LemmaWort
                (LAT_WORT_TEIL
                    "fasc"
                )
                (:Series
                    (:Token
                        "-"
                    )
                    (LAT_WORT_TEIL
                        "itergula"
                    )
                )
            )
            (ABS
                ";"
            )
        )
    )

Match-test "3"
--------------

### Test-code:
     fasc-itergula fac-iet-ergula ZUSATZ sim.
    

### AST
    (LemmaVarianten
        (LZ
            " "
        )
        (:OneOrMore
            (:Series
                (LemmaWort
                    (LAT_WORT_TEIL
                        "fasc"
                    )
                    (:Series
                        (:Token
                            "-"
                        )
                        (LAT_WORT_TEIL
                            "itergula"
                        )
                    )
                )
                (LZ
                    " "
                )
            )
            (:Series
                (LemmaWort
                    (LAT_WORT_TEIL
                        "fac"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "iet"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ergula"
                            )
                        )
                    )
                )
                (LZ
                    " "
                )
            )
        )
        (:Series
            (LemmaZusatz
                (:Token
                    (:RegExp
                        "ZUSATZ"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (lzs_typ
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


Test of parser: "LemmaPosition"
===============================


Match-test "1"
--------------

### Test-code:
    LEMMA facitergul|a
    
    fasc-itergula
    fac-iet-ergula
    fac-ist-ergula
    fascite-rcu-la
    
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
                (LAT_WORT_TEIL
                    "facitergul"
                )
                (:Series
                    (:Token
                        "|"
                    )
                    (LAT_WORT_TEIL
                        "a"
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
                    (LemmaWort
                        (LAT_WORT_TEIL
                            "fasc"
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "itergula"
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
                    )
                )
                (:Series
                    (LemmaWort
                        (LAT_WORT_TEIL
                            "fac"
                        )
                        (:ZeroOrMore
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "iet"
                                )
                            )
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "ergula"
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
                    )
                )
                (:Series
                    (LemmaWort
                        (LAT_WORT_TEIL
                            "fac"
                        )
                        (:ZeroOrMore
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "ist"
                                )
                            )
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "ergula"
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
                    )
                )
                (:Series
                    (LemmaWort
                        (LAT_WORT_TEIL
                            "fascite"
                        )
                        (:ZeroOrMore
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "rcu"
                                )
                            )
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "la"
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
                )
            )
            (:Series
                (LemmaZusatz
                    (:Token
                        (:RegExp
                            "ZUSATZ"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (lzs_typ
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