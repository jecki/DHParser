General TODO-List
-----------------

- Position Handling: `Node._pos` and `Node._len` should be set by 
  parser guard to allow for early dropping of nodes. (Should speed
  up tree-traversal later)
 
- Position handling should provide for position shifts during preprocessing
