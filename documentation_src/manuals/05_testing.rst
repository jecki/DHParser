Testing
=======

DHParser provides a powerful unit-testing framework that allows testing 
individual components of a grammar separately through all stages of
the :ref:`processing pipeline <processing_pipelines>`. DHParser's 
unit-testing framework allows to::

    - break down the complicated process of writing a grammar into
      relatively simpler tasks of designing grammar-components each
      of which can be tested individually

    - turn writing and refactoring grammars into controlled and 
      manageable process. In fact, without unit-testing, refactoring
      of grammars is hardly feasible at all.

    - extend a grammar incrementally without breaking existing code.

    - check the syntax-tree-construction as well as all subsequent
      transformations (as long as their result is serializable).
      



