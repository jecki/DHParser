

Test of parser: "content"
=========================


Match-test "simple"
-------------------

### Test-code:
    {Edward N. Zalta}

### AST
    <content>
      <:Token>{</:Token>
      <text>
        <CONTENT_STRING>Edward N. Zalta</CONTENT_STRING>
      </text>
      <:Token>}</:Token>
    </content>

Match-test "nested_braces"
--------------------------

### Test-code:
    {\url{https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/}}

### AST
    <content>
      <:Token>{</:Token>
      <text>
        <CONTENT_STRING>\url</CONTENT_STRING>
        <:Token>{</:Token>
        <text>
          <CONTENT_STRING>https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/</CONTENT_STRING>
        </text>
        <:Token>}</:Token>
      </text>
      <:Token>}</:Token>
    </content>


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

	6:68: Error (1010): '}' ~ expected, "%E2\%80\%9..." found!
	6:69: Error (1040): Parser stopped before end! trying to recover but stopping history recording at this point.
	7:1: Error (1020): Parser did not match!
		    Most advanced:    6, 68:  entry->:ZeroOrMore->:Series->content->:Series->text->:Alternative->CONTENT_STRING->:Alternative->:Series->:Lookahead->/(?i)%/;  MATCH;  "%"
		    Last match:       6, 68:  entry->:ZeroOrMore->:Series->content->plain_content->COMMA_TERMINATED_STRING->:Alternative->:Series->:Lookahead->/(?i)%/;  MATCH;  "%";



### AST
    <__ZOMBIE__>
      <entry>
        <:RegExp>@</:RegExp>
        <type>
          <WORD>Online</WORD>
        </type>
        <:Token>{</:Token>
        <key>
          <NO_BLANK_STRING>wikipedia-duhem-quine</NO_BLANK_STRING>
        </key>
        <:Token>,</:Token>
        <:Whitespace>
          
            
        </:Whitespace>
        <field>
          <WORD>
            <:RegExp>editor</:RegExp>
            <:Whitespace>       </:Whitespace>
          </WORD>
        </field>
        <:Token>=</:Token>
        <:Whitespace> </:Whitespace>
        <content>
          <:Token>{</:Token>
          <text>
            <CONTENT_STRING>Wikipedia</CONTENT_STRING>
          </text>
          <:Token>}</:Token>
        </content>
        <:Token>,</:Token>
        <:Whitespace>
          
            
        </:Whitespace>
        <field>
          <WORD>
            <:RegExp>title</:RegExp>
            <:Whitespace>        </:Whitespace>
          </WORD>
        </field>
        <:Token>=</:Token>
        <:Whitespace> </:Whitespace>
        <content>
          <:Token>{</:Token>
          <text>
            <CONTENT_STRING>Duhem-Quine thesis</CONTENT_STRING>
          </text>
          <:Token>}</:Token>
        </content>
        <:Token>,</:Token>
        <:Whitespace>
          
            
        </:Whitespace>
        <field>
          <WORD>
            <:RegExp>year</:RegExp>
            <:Whitespace>         </:Whitespace>
          </WORD>
        </field>
        <:Token>=</:Token>
        <:Whitespace> </:Whitespace>
        <content>
          <:Token>{</:Token>
          <text>
            <CONTENT_STRING>2017</CONTENT_STRING>
          </text>
          <:Token>}</:Token>
        </content>
        <:Token>,</:Token>
        <:Whitespace>
          
            
        </:Whitespace>
        <field>
          <WORD>
            <:RegExp>date</:RegExp>
            <:Whitespace>         </:Whitespace>
          </WORD>
        </field>
        <:Token>=</:Token>
        <:Whitespace> </:Whitespace>
        <content>
          <:Token>{</:Token>
          <text>
            <CONTENT_STRING>2017-08-19</CONTENT_STRING>
          </text>
          <:Token>}</:Token>
        </content>
        <:Token>,</:Token>
        <:Whitespace>
          
            
        </:Whitespace>
        <field>
          <WORD>
            <:RegExp>url</:RegExp>
            <:Whitespace>          </:Whitespace>
          </WORD>
        </field>
        <:Token>=</:Token>
        <:Whitespace> </:Whitespace>
        <plain_content>
          <COMMA_TERMINATED_STRING>{https://en.wikipedia.org/w/index.php?title=Duhem\</COMMA_TERMINATED_STRING>
        </plain_content>
        <__ZOMBIE__>%</__ZOMBIE__>
      </entry>
      <__ZOMBIE__>
        E2\%80\%93Quine\_thesis\&amp;oldid=772834991},
        
      </__ZOMBIE__>
      <__ZOMBIE__>
          organization = {Wikipedia}
        
      </__ZOMBIE__>
      <__ZOMBIE__>}</__ZOMBIE__>
    </__ZOMBIE__>