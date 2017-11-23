

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
            "\subparagraph"
        )
        (block
            (text
                "A subparagraph"
            )
        )
        (sequence
            (paragraph
                (text
                    "with some text"
                )
            )
            (paragraph
                (text
                    "and consisting of several"
                )
            )
            (paragraph
                (text
                    "real paragraphs"
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
            "\paragraph"
        )
        (block
            (text
                "A paragraph consisting of several subparagraphs"
            )
        )
        (:ZeroOrMore
            (sequence
                (paragraph
                    (text
                        "Some text ahead"
                    )
                )
            )
            (SubParagraphs
                (SubParagraph
                    (:Token
                        "\subparagraph"
                    )
                    (block
                        (text
                            "subparagraph 1"
                        )
                    )
                    (sequence
                        (paragraph
                            (text
                                "First subparagraph"
                            )
                        )
                    )
                )
                (SubParagraph
                    (:Token
                        "\subparagraph"
                    )
                    (block
                        (text
                            "subparagraph 2"
                        )
                    )
                    (sequence
                        (paragraph
                            (text
                                "Second subparagraph"
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
                "\chapter"
            )
            (block
                (text
                    "Chapter 1"
                )
            )
            (Sections
                (Section
                    (:Token
                        "\section"
                    )
                    (block
                        (text
                            "Section 1"
                        )
                    )
                )
                (Section
                    (:Token
                        "\section"
                    )
                    (block
                        (text
                            "Section 2"
                        )
                    )
                    (sequence
                        (paragraph
                            (text
                                "Section 2 contains some text"
                            )
                        )
                    )
                )
                (Section
                    (:Token
                        "\section"
                    )
                    (block
                        (text
                            "Section 3"
                        )
                    )
                    (SubSections
                        (SubSection
                            (:Token
                                "\subsection"
                            )
                            (block
                                (text
                                    "SubSection 1"
                                )
                            )
                            (sequence
                                (paragraph
                                    (text
                                        "Text for subsection 1"
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
                                "\subsection"
                            )
                            (block
                                (text
                                    "SubSection 2"
                                )
                            )
                            (:ZeroOrMore
                                (sequence
                                    (paragraph
                                        (text
                                            "Text for subsection 2"
                                        )
                                    )
                                )
                                (SubSubSections
                                    (SubSubSection
                                        (:Token
                                            "\subsubsection"
                                        )
                                        (block
                                            (text
                                                "A subsubsection"
                                            )
                                        )
                                        (sequence
                                            (paragraph
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
                (Section
                    (:Token
                        "\section"
                    )
                    (block
                        (text
                            "Section 4"
                        )
                    )
                )
            )
        )
        (Chapter
            (:Token
                "\chapter"
            )
            (block
                (text
                    "Chapter 2"
                )
            )
            (sequence
                (paragraph
                    (text
                        "Some text for chapter 2"
                    )
                )
            )
        )
    )