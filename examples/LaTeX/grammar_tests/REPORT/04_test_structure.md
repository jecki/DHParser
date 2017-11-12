

Test of parser: "SubParagraph"
==============================


Match-test "1"
--------------

### Test-code:
    \subparagraph{A subparagraph} with some text
    
    and consisting of several
    
    real paragraphs

### AST
    (SubParagraph
        (:Token
            (:RegExp
                "\subparagraph"
            )
        )
        (block
            (text_element
                (text
                    "A subparagraph"
                )
            )
        )
        (WSPC
            " "
        )
        (sequence
            (paragraph
                (text_element
                    (text
                        "with some text"
                    )
                )
            )
            (paragraph
                (text_element
                    (text
                        "and consisting of several"
                    )
                )
            )
            (paragraph
                (text_element
                    (text
                        "real paragraphs"
                    )
                )
            )
        )
    )


Test of parser: "Paragraph"
===========================


Match-test "1"
--------------

### Test-code:
    \paragraph{A paragraph consisting of several subparagraphs}
    
    Some text ahead
    
    \subparagraph{subparagraph 1}
    
    First subparagraph
    
    \subparagraph{subparagraph 2}
    
    Second subparagraph

### AST
    (Paragraph
        (:Token
            (:RegExp
                "\paragraph"
            )
        )
        (block
            (text_element
                (text
                    "A paragraph consisting of several subparagraphs"
                )
            )
        )
        (WSPC
            ""
            ""
            ""
        )
        (:ZeroOrMore
            (sequence
                (paragraph
                    (text_element
                        (text
                            "Some text ahead"
                        )
                    )
                )
            )
            (SubParagraphs
                (SubParagraph
                    (:Token
                        (:RegExp
                            "\subparagraph"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "subparagraph 1"
                            )
                        )
                    )
                    (WSPC
                        ""
                        ""
                        ""
                    )
                    (sequence
                        (paragraph
                            (text_element
                                (text
                                    "First subparagraph"
                                )
                            )
                        )
                    )
                )
                (SubParagraph
                    (:Token
                        (:RegExp
                            "\subparagraph"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "subparagraph 2"
                            )
                        )
                    )
                    (WSPC
                        ""
                        ""
                        ""
                    )
                    (sequence
                        (paragraph
                            (text_element
                                (text
                                    "Second subparagraph"
                                )
                            )
                        )
                    )
                )
            )
        )
    )


Test of parser: "Chapters"
==========================


Match-test "1"
--------------

### Test-code:
    \chapter{Chapter 1}
    \section{Section 1}
    \section{Section 2}
    
    Section 2 contains some text
    
    \section{Section 3}
    \subsection{SubSection 1}
    Text for subsection 1
    \subsection{SubSection 2}
    Text for subsection 2
    
    \subsubsection{A subsubsection}
    Text for subsubsecion
    
    \section{Section 4}
    
    \chapter{Chapter 2}
    
    Some text for chapter 2

### AST
    (Chapters
        (Chapter
            (:Token
                (:RegExp
                    "\chapter"
                )
            )
            (block
                (text_element
                    (text
                        "Chapter 1"
                    )
                )
            )
            (WSPC
                ""
                ""
            )
            (Sections
                (Section
                    (:Token
                        (:RegExp
                            "\section"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "Section 1"
                            )
                        )
                    )
                    (WSPC
                        ""
                        ""
                    )
                )
                (Section
                    (:Token
                        (:RegExp
                            "\section"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "Section 2"
                            )
                        )
                    )
                    (WSPC
                        ""
                        ""
                        ""
                    )
                    (sequence
                        (paragraph
                            (text_element
                                (text
                                    "Section 2 contains some text"
                                )
                            )
                        )
                    )
                )
                (Section
                    (:Token
                        (:RegExp
                            "\section"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "Section 3"
                            )
                        )
                    )
                    (WSPC
                        ""
                        ""
                    )
                    (SubSections
                        (SubSection
                            (:Token
                                (:RegExp
                                    "\subsection"
                                )
                            )
                            (block
                                (text_element
                                    (text
                                        "SubSection 1"
                                    )
                                )
                            )
                            (WSPC
                                ""
                                ""
                            )
                            (sequence
                                (paragraph
                                    (text_element
                                        (text
                                            "Text for subsection 1"
                                        )
                                    )
                                    (:Whitespace
                                        ""
                                        ""
                                    )
                                )
                            )
                        )
                        (SubSection
                            (:Token
                                (:RegExp
                                    "\subsection"
                                )
                            )
                            (block
                                (text_element
                                    (text
                                        "SubSection 2"
                                    )
                                )
                            )
                            (WSPC
                                ""
                                ""
                            )
                            (:ZeroOrMore
                                (sequence
                                    (paragraph
                                        (text_element
                                            (text
                                                "Text for subsection 2"
                                            )
                                        )
                                    )
                                )
                                (SubSubSections
                                    (SubSubSection
                                        (:Token
                                            (:RegExp
                                                "\subsubsection"
                                            )
                                        )
                                        (block
                                            (text_element
                                                (text
                                                    "A subsubsection"
                                                )
                                            )
                                        )
                                        (WSPC
                                            ""
                                            ""
                                        )
                                        (sequence
                                            (paragraph
                                                (text_element
                                                    (text
                                                        "Text for subsubsecion"
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
                (Section
                    (:Token
                        (:RegExp
                            "\section"
                        )
                    )
                    (block
                        (text_element
                            (text
                                "Section 4"
                            )
                        )
                    )
                    (WSPC
                        ""
                        ""
                        ""
                    )
                )
            )
        )
        (Chapter
            (:Token
                (:RegExp
                    "\chapter"
                )
            )
            (block
                (text_element
                    (text
                        "Chapter 2"
                    )
                )
            )
            (WSPC
                ""
                ""
                ""
            )
            (sequence
                (paragraph
                    (text_element
                        (text
                            "Some text for chapter 2"
                        )
                    )
                )
            )
        )
    )