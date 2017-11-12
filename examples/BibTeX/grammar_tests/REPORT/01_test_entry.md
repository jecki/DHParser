

Test of parser: "content"
=========================


Match-test "simple"
-------------------

### Test-code:
    {Edward N. Zalta}

### AST
    (content
        (:Token
            "{"
        )
        (text
            (CONTENT_STRING
                "Edward N. Zalta"
            )
        )
        (:Token
            "}"
        )
    )

Match-test "nested_braces"
--------------------------

### Test-code:
    {\url{https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/}}

### AST
    (content
        (:Token
            "{"
        )
        (text
            (CONTENT_STRING
                "\url"
            )
            (:Series
                (:Token
                    "{"
                )
                (text
                    (CONTENT_STRING
                        "https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/"
                    )
                )
                (:Token
                    "}"
                )
            )
        )
        (:Token
            "}"
        )
    )