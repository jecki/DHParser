

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
    (generic_command
        (CMDNAME
            "\command"
        )
    )

Match-test "2"
--------------

### Test-code:
    \textbackslash

### AST
    (text_command
        (TXTCOMMAND
            "\textbackslash"
        )
    )

Match-test "3"
--------------

### Test-code:
    \footnote{footnote}

### AST
    (footnote
        (block_of_paragraphs
            (text
                "footnote"
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    [

### AST
    (text_command
        (BRACKETS
            "["
        )
    )

Match-test "5"
--------------

### Test-code:
    \begin{generic} unknown inline environment \end{generic}

### AST
    (generic_inline_env
        (begin_environment
            "generic"
        )
        (:Whitespace
            " "
        )
        (paragraph
            (text
                "unknown inline environment"
            )
            (:Whitespace
                " "
            )
        )
        (end_environment
            "generic"
        )
    )

Match-test "6"
--------------

### Test-code:
    \begin{small} known inline environment \end{small}

### AST
    (generic_inline_env
        (begin_environment
            "small"
        )
        (:Whitespace
            " "
        )
        (paragraph
            (text
                "known inline environment"
            )
            (:Whitespace
                " "
            )
        )
        (end_environment
            "small"
        )
    )

Match-test "7"
--------------

### Test-code:
    {\em block}

### AST
    (block
        (generic_command
            (CMDNAME
                "\em"
            )
        )
        (text
            "block"
        )
    )