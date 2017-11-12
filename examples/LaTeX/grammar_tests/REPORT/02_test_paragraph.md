

Test of parser: "paragraph"
===========================


Match-test "1"
--------------

### Test-code:
    Im allgemeinen werden die Bewohner Göttingens eingeteilt in Studenten,
    Professoren, Philister und Vieh; welche vier Stände doch nichts weniger
    als streng geschieden sind. Der Viehstand ist der bedeutendste.

### AST
    (paragraph
        (text_element
            (text
                "Im allgemeinen werden die Bewohner Göttingens eingeteilt in Studenten,"
                "Professoren, Philister und Vieh; welche vier Stände doch nichts weniger"
                "als streng geschieden sind. Der Viehstand ist der bedeutendste."
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    Paragraphs may contain {\em inline blocks} as well as \emph{inline commands}
    and also special \& characters.

### AST
    (paragraph
        (text_element
            (text
                "Paragraphs may contain"
            )
        )
        (:Whitespace
            " "
        )
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
                        "inline blocks"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "as well as"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (generic_command
                    (CMDNAME
                        "\emph"
                    )
                    (block
                        (text_element
                            (text
                                "inline commands"
                            )
                        )
                    )
                )
            )
        )
        (:Whitespace
            ""
            ""
        )
        (text_element
            (text
                "and also special"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (text_command
                    (ESCAPED
                        "&"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "characters."
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    Paragraphs are separated only by at least one blank line.
    Therefore,
    this line still belongs to the same paragraph.

### AST
    (paragraph
        (text_element
            (text
                "Paragraphs are separated only by at least one blank line."
                "Therefore,"
                "this line still belongs to the same paragraph."
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    Paragraphs   % may contain comments
    like the comment above
    % or like thist comment.
    Comment lines do not break paragraphs.
    % There can even be several comment lines,
    % even indented comment lines,
    in sequence.

### AST
    (paragraph
        (text_element
            (text
                "Paragraphs"
                "like the comment above"
                "Comment lines do not break paragraphs."
                "in sequence."
            )
        )
    )

Match-test "5"
--------------

### Test-code:
    Paragraphs may contain {\em emphasized} or {\bf bold} text.
    Most of these commands can have different forms as, for example:
    \begin{small} small \end{small} or {\large large}.

### AST
    (paragraph
        (text_element
            (text
                "Paragraphs may contain"
            )
        )
        (:Whitespace
            " "
        )
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
                        "emphasized"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "or"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (block
                (text_element
                    (command
                        (generic_command
                            (CMDNAME
                                "\bf"
                            )
                        )
                    )
                )
                (text_element
                    (text
                        "bold"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "text."
                "Most of these commands can have different forms as, for example:"
            )
        )
        (:Whitespace
            ""
            ""
        )
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
                            "small"
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
        (:Whitespace
            " "
        )
        (text_element
            (text
                "or"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (block
                (text_element
                    (command
                        (generic_command
                            (CMDNAME
                                "\large"
                            )
                        )
                    )
                )
                (text_element
                    (text
                        "large"
                    )
                )
            )
        )
        (text_element
            (text
                "."
            )
        )
    )

Match-test "6"
--------------

### Test-code:
    Paragraphs may also contain {\xy unknown blocks }.

### AST
    (paragraph
        (text_element
            (text
                "Paragraphs may also contain"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (block
                (text_element
                    (command
                        (generic_command
                            (CMDNAME
                                "\xy"
                            )
                        )
                    )
                )
                (text_element
                    (text
                        "unknown blocks"
                    )
                )
                (:Whitespace
                    " "
                )
            )
        )
        (text_element
            (text
                "."
            )
        )
    )

Match-test "7"
--------------

### Test-code:
    Paragraphs may contain \xy[xycgf]{some {\em unbknown}} commands.

### AST
    (paragraph
        (text_element
            (text
                "Paragraphs may contain"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (generic_command
                    (CMDNAME
                        "\xy"
                    )
                    (config
                        (text
                            "xycgf"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "some"
                            )
                        )
                        (:Whitespace
                            " "
                        )
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
                                        "unbknown"
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "commands."
            )
        )
    )

Match-test "8"
--------------

### Test-code:
    Unknwon \xy commands within paragraphs may be simple
    or \xy{complex}.

### AST
    (paragraph
        (text_element
            (text
                "Unknwon"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (generic_command
                    (CMDNAME
                        "\xy"
                    )
                )
            )
        )
        (text_element
            (text
                "commands within paragraphs may be simple"
                "or"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (generic_command
                    (CMDNAME
                        "\xy"
                    )
                    (block
                        (text_element
                            (text
                                "complex"
                            )
                        )
                    )
                )
            )
        )
        (text_element
            (text
                "."
            )
        )
    )

Match-test "9"
--------------

### Test-code:
    paragraphs may contain all of these: \{ escaped \} characters,
    {\bf blocks}, [ brackets ], \begin{tiny} environments \end{tiny}
    and \textbackslash text-commands or other commands like this
    \footnote{footnote}

### AST
    (paragraph
        (text_element
            (text
                "paragraphs may contain all of these:"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (text_command
                    (ESCAPED
                        "{"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "escaped"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (text_command
                    (ESCAPED
                        "}"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "characters,"
            )
        )
        (:Whitespace
            ""
            ""
        )
        (text_element
            (block
                (text_element
                    (command
                        (generic_command
                            (CMDNAME
                                "\bf"
                            )
                        )
                    )
                )
                (text_element
                    (text
                        "blocks"
                    )
                )
            )
        )
        (text_element
            (text
                ","
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (text_command
                    (BRACKETS
                        "["
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "brackets"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (text_command
                    (BRACKETS
                        "]"
                    )
                )
            )
        )
        (text_element
            (text
                ","
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (generic_inline_env
                (begin_environment
                    "tiny"
                )
                (:Whitespace
                    " "
                )
                (paragraph
                    (text_element
                        (text
                            "environments"
                        )
                    )
                    (:Whitespace
                        " "
                    )
                )
                (end_environment
                    "tiny"
                )
            )
        )
        (:Whitespace
            ""
            ""
        )
        (text_element
            (text
                "and"
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (command
                (text_command
                    (TXTCOMMAND
                        "\textbackslash"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text_element
            (text
                "text-commands or other commands like this"
            )
        )
        (:Whitespace
            ""
            ""
        )
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
    )

Match-test "10"
---------------

### Test-code:
    \begin{generic}inline environment\end{generic}
    

### AST
    (paragraph
        (text_element
            (generic_inline_env
                (begin_environment
                    "generic"
                )
                (paragraph
                    (text_element
                        (text
                            "inline environment"
                        )
                    )
                )
                (end_environment
                    "generic"
                )
            )
        )
        (:Whitespace
            ""
            ""
        )
    )

Match-test "11"
---------------

### Test-code:
    \begin{generic}inline environment
    \end{generic}
    

### AST
    (paragraph
        (text_element
            (generic_inline_env
                (begin_environment
                    "generic"
                )
                (paragraph
                    (text_element
                        (text
                            "inline environment"
                        )
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
                (end_environment
                    "generic"
                )
            )
        )
        (:Whitespace
            ""
            ""
        )
    )

Fail-test "20"
--------------

### Test-code:
    Paragraphs are separated by gaps.
    
    Like this one.

Fail-test "21"
--------------

### Test-code:
    \begin{enumerate}

Fail-test "22"
--------------

### Test-code:
    \item

Fail-test "23"
--------------

### Test-code:
    und Vieh; \paragraph

Fail-test "24"
--------------

### Test-code:
    Paragraphs will end
    \begin{quotation}
    at block environments
    \end{quotation}
    like block quotes.


Test of parser: "sequence"
==========================


Match-test "1"
--------------

### Test-code:
    Paragraphs are separated by gaps.
    
    Like this one.

### AST
    (sequence
        (paragraph
            (text_element
                (text
                    "Paragraphs are separated by gaps."
                )
            )
        )
        (paragraph
            (text_element
                (text
                    "Like this one."
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    The second paragraph follows after a long gap.
    
    
    The parser should accept this, too.

### AST
    (sequence
        (paragraph
            (text_element
                (text
                    "The second paragraph follows after a long gap."
                )
            )
        )
        (paragraph
            (text_element
                (text
                    "The parser should accept this, too."
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    Paragraphs can be delimited by  % comment
    
    % sequences of separators
    
    % and comments
    % or sequences of comment lines
    
    In the end such a sequence counts
    % merely as one comment

### AST
    (sequence
        (paragraph
            (text_element
                (text
                    "Paragraphs can be delimited by"
                )
            )
            (:Whitespace
                ""
                ""
            )
        )
        (paragraph
            (text_element
                (text
                    "In the end such a sequence counts"
                )
            )
            (:Whitespace
                ""
                ""
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    Sequences of paragraphs may
    \begin{quotation}
    include block environments
    \end{quotation}
    like block quotes.

### AST
    (sequence
        (paragraph
            (text_element
                (text
                    "Sequences of paragraphs may"
                )
            )
            (:Whitespace
                ""
                ""
            )
        )
        (quotation
            (sequence
                (paragraph
                    (text_element
                        (text
                            "include block environments"
                        )
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
        (paragraph
            (text_element
                (text
                    "like block quotes."
                )
            )
        )
    )