

Test of parser: "SCHLUESSELWORT"
================================


Match-test "m1"
---------------

### Test-code:
    
    AUTORIN 

### AST
    (SCHLUESSELWORT
        (:RegExp
            ""
            ""
        )
        (:RegExp
            "AUTORIN "
        )
    )


Test of parser: "RZS"
=====================


Match-test "m1"
---------------

### Test-code:
    
    

### CST
    (RZS
        ""
        ""
    )


Test of parser: "LEERZEILE"
===========================


Match-test "m1"
---------------

### Test-code:
    
    
    

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
    )

Match-test "m2"
---------------

### Test-code:
    
    
    // Kommentar

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
        (:RE
            "// Kommentar"
        )
    )

Match-test "m3"
---------------

### Test-code:
    
    
    
    

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
            ""
        )
    )

Match-test "m4"
---------------

### Test-code:
    
    
    /* Kommentar
    
    Kommentar fortsetzung */
    

### CST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
        (:RE
            (:Whitespace
                "/* Kommentar"
                ""
                "Kommentar fortsetzung */"
            )
            (:RegExp
                ""
                ""
            )
        )
    )

Fail-test "f1"
--------------

### Test-code:
    
    

Fail-test "f2"
--------------

### Test-code:
    
    
    // Kommentar
    
    // Kommentar
    


Test of parser: "LÜCKE"
=======================


Match-test "m1"
---------------

### Test-code:
    
    
    

### AST
    (LÜCKE
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
        )
    )

Match-test "m2"
---------------

### Test-code:
    
    
    // Kommentar
    

### AST
    (LÜCKE
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                (:Whitespace
                    "// Kommentar"
                )
                (:RegExp
                    ""
                    ""
                )
            )
        )
    )

Match-test "m3"
---------------

### Test-code:
    
    
    
    

### AST
    (LÜCKE
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
                ""
            )
        )
    )

Match-test "m4"
---------------

### Test-code:
    
    
    // Kommentar
    
    // Kommentar
    

### AST
    (LÜCKE
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                (:Whitespace
                    "// Kommentar"
                )
                (:RegExp
                    ""
                    ""
                )
            )
        )
        (LZ
            (:RegExp
                ""
                ""
            )
            (:RegExp
                "// Kommentar"
            )
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "m5"
---------------

### Test-code:
     //Kommentar
    //Kommentar
    
    // Kommentar

### AST
    (LÜCKE
        (KOMMENTARZEILEN
            (:Series
                (:RegExp
                    " "
                )
                (:RegExp
                    "//Kommentar"
                )
            )
            (:Series
                (:RegExp
                    ""
                    ""
                )
                (:RegExp
                    "//Kommentar"
                )
            )
        )
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                "// Kommentar"
            )
        )
    )

Fail-test "f1"
--------------

### Test-code:
     

Fail-test "f2"
--------------

### Test-code:
    
    

Fail-test "f3"
--------------

### Test-code:
    
    // Kommentar

Fail-test "f4"
--------------

### Test-code:
     //Kommentar
    // Kommentar
    // Kommentar

Fail-test "f5"
--------------

### Test-code:
     //Kommentar
    /* Kommentar
    
    Kommentar */


Test of parser: "LZ"
====================


Match-test "m1"
---------------

### Test-code:
     

### AST
    (LZ
        (:RegExp
            " "
        )
    )

Match-test "m2"
---------------

### Test-code:
     // Kommentar

### AST
    (LZ
        (:RegExp
            " "
        )
        (:RegExp
            "// Kommentar"
        )
    )

Match-test "m3"
---------------

### Test-code:
      

### AST
    (LZ
        (:RegExp
            "  "
        )
    )

Match-test "m4"
---------------

### Test-code:
    // Kommentar

### AST
    (LZ
        (:RegExp
            "// Kommentar"
        )
    )

Match-test "m5"
---------------

### Test-code:
    // Kommentar
    

### AST
    (LZ
        (:RegExp
            "// Kommentar"
        )
        (:RegExp
            ""
            ""
        )
    )

Match-test "m6"
---------------

### Test-code:
    
    // Kommentar
    
    // Kommentar
    
    

### AST
    (LZ
        (:RegExp
            ""
            ""
        )
        (:RegExp
            "// Kommentar"
        )
        (:RegExp
            ""
            ""
            ""
        )
        (:RegExp
            "// Kommentar"
        )
        (:RegExp
            ""
            ""
            ""
        )
    )

Match-test "m7"
---------------

### Test-code:
    
    
    
    

### AST
    (LZ
        (:RegExp
            ""
            ""
            ""
            ""
        )
    )

Fail-test "f1"
--------------

### Test-code:
    X


Test of parser: "ZWW"
=====================


Match-test "m1"
---------------

### Test-code:
    
    

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "m2"
---------------

### Test-code:
    
    // Kommentar

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "// Kommentar"
            )
        )
    )

Match-test "m3"
---------------

### Test-code:
    
    // Kommentar
    

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "// Kommentar"
            )
        )
        (LZ
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "m4"
---------------

### Test-code:
    
    
    
    

### AST
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
                ""
            )
        )
    )

Fail-test "f1"
--------------

### Test-code:
     


Test of parser: "ZW"
====================


Match-test "m1"
---------------

### Test-code:
    
    

### AST
    (ZW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "m2"
---------------

### Test-code:
    
    // Kommentar

### AST
    (ZW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "// Kommentar"
            )
        )
    )

Fail-test "f1"
--------------

### Test-code:
    
    
    


Test of parser: "FREITEXT"
==========================


Fail-test "f1"
--------------

### Test-code:
    Text -> Verweis