General TODO-List
=================



Optimizations
-------------

**Early discarding of nodes**: 
Reason: `traverse_recursive` and `Node.result-setter` are top time consumers!

Allow to specify parsers/nodes, the result of which
will be dropped right away, so that the nodes they produce do not need to be
removed during the AST-Transformations. Typical candidates would be:
1. Tokens ":Token"
2. Whitespace ":Whitespace" (in some cases)
3. empty Nodes
and basically anything that would be removed globally ("+" entry in the
AST-Transformation dictionary) later anyway.
A directive ("@discarable = ...") could be introduced to specify the discardables

Challenges:

1. Discardable Nodes should not even be created in the first place to avoid
   costly object creation and assignment of result to the Node object on 
   creation.
   
2. ...but discarded or discardable nodes are not the same as a not matching parser.
   Possible solution would be to introduce a dummy/zombie-Node that will be discarded
   by the calling Parser, i.e. Zero or More, Series etc. 

3. Two kinds of conditions for dis

4. Capture/Retrieve/Pop - need the parsed data even if the node would otherwise
   be discardable (Example: Variable Delimiters.) So, either:
   
   a. temporarily suspend discarding by gramma-object-flag set and cleared by
      Capture/Retrieve/Pop. Means yet another flag has to be checked every time
      the decision to discard or not needs to be taken... 

   b. statically check (i.e. check at compile time) that Capture/Retrieve/Pop 
      neither directly nor indirectly call a discardable parser. Downside:
      Some parsers cannot profit from the optimization. For example variable
      delimiters, otherwise as all delimiters a good candidate for discarding
      cannot be discarded any more.  
