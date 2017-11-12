

Test of parser: "text"
======================


Match-test "1"
--------------

### Test-code:
    Some plain text

### AST
    (text
        "Some plain text"
    )

Fail-test "10"
--------------

### Test-code:
    Low-level text must not contain \& escaped characters.

Fail-test "11"
--------------

### Test-code:
    Low-level text must not contain ] [ brackets.

Fail-test "12"
--------------

### Test-code:
    Low-level text must not contain { environments }.

Fail-test "13"
--------------

### Test-code:
    Low-level text must not contain any \commands.


Test of parser: "text_element"
==============================


Match-test "1"
--------------

### Test-code:
    \command

### AST
    (text_element
        (command
            (generic_command
                (CMDNAME
                    "\command"
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    \textbackslash

### AST
    (text_element
        (command
            (text_command
                (TXTCOMMAND
                    "\textbackslash"
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    \footnote{footnote}

### AST
    (text_element
        (command
            (known_command
                (footnote
                    (:Token
                        (:RegExp
                            "\footnote"
                        )
                    )
                    (block_of_paragraphs
                        (:Token
                            (:RegExp
                                "{"
                            )
                        )
                        (sequence
                            (paragraph
                                (text_element
                                    (text
                                        "footnote"
                                    )
                                )
                            )
                        )
                        (:Token
                            (:RegExp
                                "}"
                            )
                        )
                    )
                )
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    [

### AST
    (text_element
        (command
            (text_command
                (BRACKETS
                    "["
                )
            )
        )
    )

Match-test "5"
--------------

### Test-code:
    \begin{generic} unknown inline environment \end{generic}

### AST
    (text_element
        (generic_inline_env
            (begin_environment
                "generic"
            )
            (:Whitespace
                " "
            )
            (paragraph
                (text_element
                    (text
                        "unknown inline environment"
                    )
                )
                (:Whitespace
                    " "
                )
            )
            (end_environment
                "generic"
            )
        )
    )

Match-test "6"
--------------

### Test-code:
    \begin{small} known inline environment \end{small}

### AST
    (text_element
        (generic_inline_env
            (begin_environment
                "small"
            )
            (:Whitespace
                " "
            )
            (paragraph
                (text_element
                    (text
                        "known inline environment"
                    )
                )
                (:Whitespace
                    " "
                )
            )
            (end_environment
                "small"
            )
        )
    )

Match-test "7"
--------------

### Test-code:
    {\em block}

### AST
    (text_element
        (block
            (text_element
                (command
                    (generic_command
                        (CMDNAME
                            "\em"
                        )
                    )
                )
            )
            (text_element
                (text
                    "block"
                )
            )
        )
    )