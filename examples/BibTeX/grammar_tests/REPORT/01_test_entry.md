

Test of parser: "content"
=========================


Match-test "simple"
-------------------

### Test-code:
    {Edward N. Zalta}

### AST
    (content (:Token "{") (text (CONTENT_STRING "Edward N. Zalta")) (:Token "}"))

Match-test "nested_braces"
--------------------------

### Test-code:
    {\url{https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/}}

### AST
    content
      :Token
        "{"
      text
        CONTENT_STRING
          "\url"
        :Token
          "{"
        text
          CONTENT_STRING
            "https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/"
        :Token
          "}"
      :Token
        "}"


Test of parser: "entry"
=======================


Match-test "entry"
------------------

### Test-code:
    @Online{wikipedia-duhem-quine,
      editor       = {Wikipedia},
      title        = {Duhem-Quine thesis},
      year         = {2017},
      date         = {2017-08-19},
      url          = {https://en.wikipedia.org/w/index.php?title=Duhem\%E2\%80\%93Quine\_thesis\&oldid=772834991},
      organization = {Wikipedia}
    }

### Error:
Match test "entry" for parser "entry" failed:
	Expr.:  @Online{wikipedia-duhem-quine,
	  editor       = {Wikipedia},
	  title        = {Duhem-Quine thesis},
	  year         = {2017},
	  date         = {2017-08-19},
	  url          = {https://en.wikipedia.org/w/index.php?title=Duhem\%E2\%80\%93Quine\_thesis\&oldid=772834991},
	  organization = {Wikipedia}
	}

	6:68: Error (1010): '}' ~ expected by parser entry, »%E2\%80\%9...« found!
	6:69: Error (1040): Parser stopped before end! trying to recover but stopping history recording at this point.
	7:1: Error (1020): Parser "entry = /(?i)@/ type '{' ~ key {',' ~ field § '=' ~ content} [',' ~] § '}' ~" did not match!
		    Most advanced:    6, 68:  entry->:ZeroOrMore->:Series->content->:Series->text->:Alternative->CONTENT_STRING->:Alternative->:Series->:Lookahead->/(?i)%/;  MATCH;  "%"
		    Last match:       6, 68:  entry->:ZeroOrMore->:Series->content->plain_content->COMMA_TERMINATED_STRING->:Alternative->:Series->:Lookahead->/(?i)%/;  MATCH;  "%";



### AST
    ZOMBIE__
      entry
        :RegExp
          "@"
        type
          WORD
            "Online"
        :Token
          "{"
        key
          NO_BLANK_STRING
            "wikipedia-duhem-quine"
        :Token
          ","
        :Whitespace
          ""
          "  "
        field
          WORD
            :RegExp
              "editor"
            :Whitespace
              "       "
        :Token
          "="
        :Whitespace
          " "
        content
          :Token
            "{"
          text
            CONTENT_STRING
              "Wikipedia"
          :Token
            "}"
        :Token
          ","
        :Whitespace
          ""
          "  "
        field
          WORD
            :RegExp
              "title"
            :Whitespace
              "        "
        :Token
          "="
        :Whitespace
          " "
        content
          :Token
            "{"
          text
            CONTENT_STRING
              "Duhem-Quine thesis"
          :Token
            "}"
        :Token
          ","
        :Whitespace
          ""
          "  "
        field
          WORD
            :RegExp
              "year"
            :Whitespace
              "         "
        :Token
          "="
        :Whitespace
          " "
        content
          :Token
            "{"
          text
            CONTENT_STRING
              "2017"
          :Token
            "}"
        :Token
          ","
        :Whitespace
          ""
          "  "
        field
          WORD
            :RegExp
              "date"
            :Whitespace
              "         "
        :Token
          "="
        :Whitespace
          " "
        content
          :Token
            "{"
          text
            CONTENT_STRING
              "2017-08-19"
          :Token
            "}"
        :Token
          ","
        :Whitespace
          ""
          "  "
        field
          WORD
            :RegExp
              "url"
            :Whitespace
              "          "
        :Token
          "="
        :Whitespace
          " "
        plain_content
          COMMA_TERMINATED_STRING
            "{https://en.wikipedia.org/w/index.php?title=Duhem\"
        ZOMBIE__ `(err "'}' ~ expected by parser entry, »%E2\%80\%9...« found!"
          "%"
      ZOMBIE__
        "E2\%80\%93Quine\_thesis\&oldid=772834991},"
        ""
      ZOMBIE__
        "  organization = {Wikipedia}"
        ""
      ZOMBIE__
        "}"