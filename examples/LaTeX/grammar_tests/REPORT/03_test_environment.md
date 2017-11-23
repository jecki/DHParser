

Test of parser: "block_environment"
===================================


Match-test "1"
--------------

### Test-code:
    \begin{generic}
    A generic block element is a block element
    that is unknown to DHParser.
    
    Unknown begin-end-structures are always
    considered as block elements and not
    as inline elements.
    \end{generic}
    

### AST
    (generic_block
        (begin_generic_block
            (begin_environment
                "generic"
            )
            (NEW_LINE
                ""
                ""
            )
        )
        (sequence
            (paragraph
                (text
                    "A generic block element is a block element"
                    "that is unknown to DHParser."
                )
            )
            (paragraph
                (text
                    "Unknown begin-end-structures are always"
                    "considered as block elements and not"
                    "as inline elements."
                )
                (:Whitespace
                    ""
                    ""
                )
            )
        )
        (end_generic_block
            (end_environment
                "generic"
            )
            (NEW_LINE
                ""
                ""
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    \begin{generic}
    a single block paragraph
    \end{generic} % ending with
    % a comment
    

### AST
    (generic_block
        (begin_generic_block
            (begin_environment
                "generic"
            )
            (NEW_LINE
                ""
                ""
            )
        )
        (sequence
            (paragraph
                (text
                    "a single block paragraph"
                )
                (:Whitespace
                    ""
                    ""
                )
            )
        )
        (end_generic_block
            (end_environment
                "generic"
            )
            (NEW_LINE
                (:RegExp
                    " "
                )
                (:RegExp
                    "% ending with"
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
    \begin{quote}
    a known block element
    \end{quote}

### AST
    (quotation
        (sequence
            (paragraph
                (text
                    "a known block element"
                )
                (:Whitespace
                    ""
                    ""
                )
            )
        )
    )

Fail-test "10"
--------------

### Test-code:
    \begin{generic}inline environment\end{generic}
    

Fail-test "11"
--------------

### Test-code:
    \begin{generic}inline environment
    \end{generic}
    

Fail-test "12"
--------------

### Test-code:
    \begin{generic}
    invalid enivronment \end{generic}
    


Test of parser: "inline_environment"
====================================


Match-test "1"
--------------

### Test-code:
    \begin{generic}inline environment\end{generic}

### AST
    (generic_inline_env
        (begin_environment
            "generic"
        )
        (paragraph
            (text
                "inline environment"
            )
        )
        (end_environment
            "generic"
        )
    )

Match-test "2"
--------------

### Test-code:
    \begin{generic}inline environment
    \end{generic}

### AST
    (generic_inline_env
        (begin_environment
            "generic"
        )
        (paragraph
            (text
                "inline environment"
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

Match-test "3"
--------------

### Test-code:
    $ inline math $

### AST
    (inline_math
        " inline math "
    )

Fail-test "10"
--------------

### Test-code:
    \begin{generic}
    invalid enivronment \end{generic}
    


Test of parser: "itemize"
=========================


Match-test "1"
--------------

### Test-code:
    \begin{itemize}
    \item Items doe not need to be
    \item separated by empty lines.
    \end{itemize}

### AST
    (itemize
        (item
            (sequence
                (paragraph
                    (text
                        "Items doe not need to be"
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
        (item
            (sequence
                (paragraph
                    (text
                        "separated by empty lines."
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    \begin{itemize}
    
    \item But items may be
    
    \item separated by blank lines.
    
    \item
    
    Empty lines at the beginning of an item will be ignored.
    
    \end{itemize}

### AST
    (itemize
        (item
            (sequence
                (paragraph
                    (text
                        "But items may be"
                    )
                )
            )
        )
        (item
            (sequence
                (paragraph
                    (text
                        "separated by blank lines."
                    )
                )
            )
        )
        (item
            (sequence
                (paragraph
                    (text
                        "Empty lines at the beginning of an item will be ignored."
                    )
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    \begin{itemize}
    \item Items can consist of
    
    several paragraphs.
    \item Or of one paragraph
    \end{itemize}

### AST
    (itemize
        (item
            (sequence
                (paragraph
                    (text
                        "Items can consist of"
                    )
                )
                (paragraph
                    (text
                        "several paragraphs."
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
        (item
            (sequence
                (paragraph
                    (text
                        "Or of one paragraph"
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    \begin{itemize}
    \item
    \begin{itemize}
    \item Item-lists can be nested!
    \end{itemize}
    \end{itemize}

### AST
    (itemize
        (item
            (sequence
                (itemize
                    (item
                        (sequence
                            (paragraph
                                (text
                                    "Item-lists can be nested!"
                                )
                                (:Whitespace
                                    ""
                                    ""
                                )
                            )
                        )
                    )
                )
            )
        )
    )

Match-test "5"
--------------

### Test-code:
    \begin{itemize}
    \item Item-lists may consist of just one item.
    \end{itemize}

### AST
    (itemize
        (item
            (sequence
                (paragraph
                    (text
                        "Item-lists may consist of just one item."
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
    )

Fail-test "11"
--------------

### Test-code:
    \begin{itemize}
    Free text is not allowed within an itemized environment!
    \end{itemize}


Test of parser: "enumerate"
===========================


Match-test "1"
--------------

### Test-code:
    \begin{enumerate}
    \item Enumerations work just like item-lists.
    \item Only that the bullets are numbers.
    \end{enumerate}

### AST
    (enumerate
        (item
            (sequence
                (paragraph
                    (text
                        "Enumerations work just like item-lists."
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
        (item
            (sequence
                (paragraph
                    (text
                        "Only that the bullets are numbers."
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    \begin{enumerate}
    \item \begin{itemize}
    \item Item-lists and
    \item Enumeration-lists
    \begin{enumerate}
    \item can be nested
    \item arbitrarily
    \end{enumerate}
    \item Another item
    \end{itemize}
    \item Plain numerated item.
    \end{enumerate}

### AST
    (enumerate
        (item
            (sequence
                (itemize
                    (item
                        (sequence
                            (paragraph
                                (text
                                    "Item-lists and"
                                )
                                (:Whitespace
                                    ""
                                    ""
                                )
                            )
                        )
                    )
                    (item
                        (sequence
                            (paragraph
                                (text
                                    "Enumeration-lists"
                                )
                                (:Whitespace
                                    ""
                                    ""
                                )
                            )
                            (enumerate
                                (item
                                    (sequence
                                        (paragraph
                                            (text
                                                "can be nested"
                                            )
                                            (:Whitespace
                                                ""
                                                ""
                                            )
                                        )
                                    )
                                )
                                (item
                                    (sequence
                                        (paragraph
                                            (text
                                                "arbitrarily"
                                            )
                                            (:Whitespace
                                                ""
                                                ""
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                    (item
                        (sequence
                            (paragraph
                                (text
                                    "Another item"
                                )
                                (:Whitespace
                                    ""
                                    ""
                                )
                            )
                        )
                    )
                )
            )
        )
        (item
            (sequence
                (paragraph
                    (text
                        "Plain numerated item."
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    \begin{enumerate} % comment
    
    
    % more comments and paragraph separators
    % yet some more
    
    
    \item %another comment
    finally, the first item
    
    
    % comment
    
    
    \end{enumerate}

### AST
    (enumerate
        (item
            (sequence
                (paragraph
                    (text
                        "finally, the first item"
                    )
                )
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    \begin{enumerate}
    \item An item
    
    \begin{itemize}
    \item with an enumeration
    \end{itemize}
    as a separate paragraph
    \end{enumerate}

### AST
    (enumerate
        (item
            (sequence
                (paragraph
                    (text
                        "An item"
                    )
                )
                (itemize
                    (item
                        (sequence
                            (paragraph
                                (text
                                    "with an enumeration"
                                )
                                (:Whitespace
                                    ""
                                    ""
                                )
                            )
                        )
                    )
                )
                (paragraph
                    (text
                        "as a separate paragraph"
                    )
                    (:Whitespace
                        ""
                        ""
                    )
                )
            )
        )
    )