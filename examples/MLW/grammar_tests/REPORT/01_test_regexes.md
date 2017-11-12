

Test of parser: "RZS"
=====================


Match-test "1"
--------------

### Test-code:
    
    

### CST
    (RZS
        ""
        ""
    )


Test of parser: "LEERZEILE"
===========================


Match-test "1"
--------------

### Test-code:
    
    
    

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
    )

Match-test "2"
--------------

### Test-code:
    
    
    # Kommentar

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
        (:RE
            "# Kommentar"
        )
    )

Match-test "3"
--------------

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


Test of parser: "LÜCKE"
=======================


Match-test "1"
--------------

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

Match-test "2"
--------------

### Test-code:
    
    
    # Kommentar
    

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
                    "# Kommentar"
                )
                (:RegExp
                    ""
                    ""
                )
            )
        )
    )

Match-test "3"
--------------

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

Match-test "4"
--------------

### Test-code:
    
    
    # Kommentar
    
    # Kommentar
    

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
                    "# Kommentar"
                )
                (:RegExp
                    ""
                    ""
                )
            )
        )
        (LEERRAUM
            (:RegExp
                ""
                ""
            )
            (:RegExp
                "# Kommentar"
            )
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "5"
--------------

### Test-code:
     #Kommentar
    # Kommentar
    
    # Kommentar

### AST
    (LÜCKE
        (KOMMENTARZEILEN
            (:Series
                (:RegExp
                    " "
                )
                (:RegExp
                    "#Kommentar"
                )
            )
            (:Series
                (:RegExp
                    ""
                    ""
                )
                (:RegExp
                    "# Kommentar"
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
                "# Kommentar"
            )
        )
    )


Test of parser: "LEERRAUM"
==========================


Match-test "1"
--------------

### Test-code:
     

### AST
    (LEERRAUM
        (:RegExp
            " "
        )
    )

Match-test "2"
--------------

### Test-code:
     # Kommentar

### AST
    (LEERRAUM
        (:RegExp
            " "
        )
        (:RegExp
            "# Kommentar"
        )
    )

Match-test "3"
--------------

### Test-code:
      

### AST
    (LEERRAUM
        (:RegExp
            "  "
        )
    )

Match-test "4"
--------------

### Test-code:
    # Kommentar

### AST
    (LEERRAUM
        (:RegExp
            "# Kommentar"
        )
    )

Match-test "5"
--------------

### Test-code:
    # Kommentar
    

### AST
    (LEERRAUM
        (:RegExp
            "# Kommentar"
        )
        (:RegExp
            ""
            ""
        )
    )

Match-test "6"
--------------

### Test-code:
    
    # Kommentar
    
    # Kommentar
    
    

### AST
    (LEERRAUM
        (:RegExp
            ""
            ""
        )
        (:RegExp
            "# Kommentar"
        )
        (:RegExp
            ""
            ""
            ""
        )
        (:RegExp
            "# Kommentar"
        )
        (:RegExp
            ""
            ""
            ""
        )
    )

Match-test "7"
--------------

### Test-code:
    
    
    
    

### AST
    (LEERRAUM
        (:RegExp
            ""
            ""
            ""
            ""
        )
    )


Test of parser: "ZWW"
=====================


Match-test "1"
--------------

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

Match-test "2"
--------------

### Test-code:
    
    # Kommentar

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "# Kommentar"
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    
    # Kommentar
    

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "# Kommentar"
            )
        )
        (LEERRAUM
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    
    
    
    

### AST
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
                ""
            )
        )
    )


Test of parser: "ZW"
====================


Match-test "1"
--------------

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

Match-test "2"
--------------

### Test-code:
    
    # Kommentar

### AST
    (ZW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "# Kommentar"
            )
        )
    )