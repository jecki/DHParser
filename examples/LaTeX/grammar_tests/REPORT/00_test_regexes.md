

Test of parser: "LB"
====================


Match-test "1"
--------------

### Test-code:
    
    

### CST
    (LB
        ""
        ""
    )

Fail-test "10"
--------------

### Test-code:
     


Test of parser: "GAP"
=====================


Match-test "1"
--------------

### Test-code:
    
    
    

### AST
    (GAP
        (:RegExp
            ""
            ""
            ""
        )
        (:Whitespace
            " "
        )
    )

Match-test "2"
--------------

### Test-code:
    
    
    % Comment
    

### AST
    (GAP
        (:RegExp
            ""
            ""
            ""
        )
        (:Whitespace
            ""
            ""
        )
    )

Match-test "3"
--------------

### Test-code:
    
    
    
    

### AST
    (GAP
        (:RegExp
            ""
            ""
            ""
            ""
        )
        (:Whitespace
            " "
        )
    )

Fail-test "10"
--------------

### Test-code:
    
    

Fail-test "11"
--------------

### Test-code:
    
    
    % Comment
    
    % Comment
    


Test of parser: "PARSEP"
========================


Match-test "1"
--------------

### Test-code:
    
    
    

### AST
    (PARSEP
        ""
        ""
        ""
    )

Match-test "2"
--------------

### Test-code:
    
    
    % Comment
    

### AST
    (PARSEP
        ""
        ""
        ""
    )

Match-test "3"
--------------

### Test-code:
    
    
    
    

### AST
    (PARSEP
        ""
        ""
        ""
    )

Match-test "4"
--------------

### Test-code:
    
    
    % Comment
    
    % Comment
    

### AST
    (PARSEP
        ""
        ""
        ""
    )

Match-test "5"
--------------

### Test-code:
     % Comment
    % Comment
    
    % Comment

### AST
    (PARSEP
        ""
        ""
        ""
    )

Fail-test "10"
--------------

### Test-code:
     

Fail-test "11"
--------------

### Test-code:
    
    

Fail-test "12"
--------------

### Test-code:
    
    % Comment

Fail-test "13"
--------------

### Test-code:
     % Comment
    % Comment
    % Comment


Test of parser: "WSPC"
======================


Match-test "1"
--------------

### Test-code:
     

### AST
    (WSPC
        " "
    )

Match-test "2"
--------------

### Test-code:
     % Comment

### AST
    (WSPC
        (:RegExp
            " "
        )
        (:RegExp
            "% Comment"
        )
    )

Match-test "3"
--------------

### Test-code:
      

### AST
    (WSPC
        "  "
    )

Match-test "4"
--------------

### Test-code:
    % Comment

### AST
    (WSPC
        "% Comment"
    )

Match-test "5"
--------------

### Test-code:
    % Comment
    

### AST
    (WSPC
        (:RegExp
            "% Comment"
        )
        (:RegExp
            ""
            ""
        )
    )

Match-test "6"
--------------

### Test-code:
    
    % Comment
    
    % Comment
    
    

### AST
    (WSPC
        (:RegExp
            ""
            ""
        )
        (:RegExp
            "% Comment"
        )
        (:RegExp
            ""
            ""
            ""
        )
        (:RegExp
            "% Comment"
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
    (WSPC
        ""
        ""
        ""
        ""
    )

Fail-test "10"
--------------

### Test-code:
    X


Test of parser: "LFF"
=====================


Match-test "1"
--------------

### Test-code:
    
    

### AST
    (NEW_LINE
        ""
        ""
    )

Match-test "2"
--------------

### Test-code:
    
    % Comment

### AST
    (NEW_LINE
        ""
        ""
    )

Match-test "3"
--------------

### Test-code:
    
    % Comment
    

### AST
    (NEW_LINE
        ""
        ""
    )

Match-test "4"
--------------

### Test-code:
    
    
    
    

### AST
    (NEW_LINE
        ""
        ""
    )

Fail-test "10"
--------------

### Test-code:
     


Test of parser: "LF"
====================


Match-test "1"
--------------

### Test-code:
    
    

### AST
    (LF
        (NEW_LINE
            ""
            ""
        )
    )

Match-test "2"
--------------

### Test-code:
    
    % Comment

### AST
    (LF
        (NEW_LINE
            ""
            ""
        )
        (:RegExp
            "% Comment"
        )
    )

Match-test "3"
--------------

### Test-code:
    
    % Comment
    % Comment
    

### AST
    (LF
        (NEW_LINE
            ""
            ""
        )
        (:RegExp
            "% Comment"
        )
        (:RegExp
            ""
            ""
        )
        (:RegExp
            "% Comment"
        )
        (:RegExp
            ""
            ""
        )
    )

Fail-test "10"
--------------

### Test-code:
    
    
    