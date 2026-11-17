.. _content_mappings:

Content Mappings
================

DHParser also provides some functionality of standoff markup, like a
"markup anywhere" function (:py:meth:`~standoff.ContentMapping.markup`)
that allows to add markup anywhere, irrespective of the existing
markup and tree structure. (By appropriately deviding tags the algorithm
ensures that tha tags remain in the nested tree-structure.) This
functionality is concentrated in the module :py:mod:`standoff`.
Its basic component is the class :py:class:`~standoff.ContentMapping`
which relates the tree-structure to the tree's concatenated string content.


Basics
------

For finding a passage in the text or identifying certain textual
features like, for example, matching brackets, traversing the
document-tree is not really an option, if only, because a passage may
extend over several nodes, possibly even on different levels of the tree
hierarchy. For such cases it is possible to generate a content mapping
that maps text positions within the pure string-content to the paths of
the leaf-nodes to which they belong. This mapping can be thought of as a
"string-view" on the tree::

    >>> from DHParser.nodetree import *
    >>> from DHParser.standoff import *
    >>> sentence = parse_sxpr(
    ...     '(sentence (word "This") (blank " ") (word "is") (blank " ")'
    ...     ' (phrase (word "Buckingham") (blank " ") (word "Palace")))')
    >>> ctx_mapping = ContentMapping(sentence)
    >>> print(ctx_mapping.content)
    This is Buckingham Palace
    >>> print(ctx_mapping)
    0 -> sentence, word "This"
    4 -> sentence, blank " "
    5 -> sentence, word "is"
    7 -> sentence, blank " "
    8 -> sentence, phrase, word "Buckingham"
    18 -> sentence, phrase, blank " "
    19 -> sentence, phrase, word "Palace"

Note that the path in the first line of the output is different from the path
in the third line, although the sequence of node-names that appears in the
pretty-printed version shown here is the same, i.e. "sentence, word", because
the paths really consist of different Nodes.

Now let's find all letters that are followed by a whitespace character::

    >>> import re
    >>> locations = [m.start() for m in re.finditer(r'\w ', ctx_mapping.content)]
    >>> targets = [ctx_mapping.get_path_and_offset(loc) for loc in locations]

.. tip::
    Other than the node's content property, the content mappings content
    field is not generated on the fly every time it is retrieved, but
    only when instantiating or rebuilding the mapping. Performance-wise
    it is advisable to always use the content mapping's content field.

The target returned by :py:meth:`~standoff.ContentMapping.get_path_and_offset`
is a tuple of the target path and the relative position of the location that
falls within this path::

    >>> [(pp_path(path), relative_pos) for path, relative_pos in targets]
    [('sentence <- word', 3), ('sentence <- word', 1), ('sentence <- phrase <- word', 9)]

Now, the structured text can be manipulated at the precise locations where
string search yielded a match. Let's turn our text into a little riddle by
replacing the letters of the leaf-nodes before the match locations with three
dots::

    >>> for path, pos in targets:
    ...     path[-1].result = '...' + path[-1].content[pos:]
    >>> str(sentence)
    '...s ...s ...m Palace'

The positions resemble the text positions of the text represented by the
tree at the very moment when the path mapping is generated, not the
source positions captured by the `pos`-property of the node-objects!
This also means that the mapping becomes outdated, when the tree is
being restructured. Unless you use the methods provided by
:py:class:`~standoff.ContentMapping` itself in order to make changes to
the tree, you need to either call
:py:meth:`~standoff.ContentMapping.rebuild_mapping` to update the
content mapping at the affected places or instantiate an entirely new
content mapping.

.. note::
    Content mappings are somwhat similar to and provide some of the
    functionality of *standoff markup*-techniques. Unlike most
    standoff-markup-tools, however, they remain connected to the
    tree structure. Changes made with methods of
    :py:class:`~standoff.ContentMapping` will directly be reflected
    in the tree structure (unless the instance-variable auto_cleanup
    is set to "False"). Changes made directly to the tree structure
    will require a manual update of the content mapping with
    :py:meth:`~standoff.ContentMapping.rebuild_mapping`.

Restricted Mappings
-------------------

A very powerful feature of context mappings is that they allow to
restrict the string view onto the document tree to selected parts of the
tree, which makes it possible to exclude these parts from the search,
e.g.::

    >>> xml = '''<doc><p>In München<footnote><em>München</em> is the German
    ... name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>'''
    >>> tree = parse_xml(xml)

Now, assume you would like to find all occurrences of "München" in the main
text but not in the footnotes, then you can issue a context mapping that
ignores all footnotes::

    >>> cm = ContentMapping(tree, select=LEAF_PATH, ignore={'footnote'})
    >>> list(re.finditer('München', cm.content))
    [<re.Match object; span=(3, 10), match='München'>]

In order to restrict the content mapping to certain parts of the tree, the
ContentMapping-class takes a same pair of path selectors similar to the
"criteria" and "skip_subtree" parameters of :py:meth:`Node.select_path`
and :py:meth:`Node.pick`. However, there is a subtle but important difference:
If the select parameter matches paths that do not end in a leaf-node, all
path-extensions from this path that end in a leaf node will be selected.
(See also :py:func:`~standoff.leaf_paths`.)

In contrast to the restricted content mapping, the search in the
string-content of the entire tree yields::

    >>> from DHParser.toolkit import printw
    >>> printw(list(re.finditer('München', tree.content)))
    [<re.Match object; span=(3, 10), match='München'>, <re.Match object; span=(10,
     17), match='München'>]

Although, the string locations in a context mappings that has been
restricted to certain parts of the tree have shifted with respect to the
string locations in the full document tree, there is no need to worry
that the mapped locations within the tree have changed::

    >>> tree_pos = tree.content.find('Hofbräuhaus')
    >>> print(tree_pos)
    64
    >>> tm = ContentMapping(tree)
    >>> tm.content.find('Hofbräuhaus')  # should be the same as above
    64
    >>> cm_pos = cm.content.find('Hofbräuhaus')
    >>> print(cm_pos)
    16

The string-position is not the same, because the mapping ``cm`` omits the
footnote-text. Yet, the path and offset within the tree remain the same.
(Remember that the ``:Text``-nodes are "anonymous" nodes that the XML-parser
inserts for the character data of XML-elements with `mixed content`_.)::

    >>> cm_path, cm_offset = cm.get_path_and_offset(cm_pos)
    >>> print(pp_path(cm_path, delimiter=', '), '->', cm_offset)
    doc, p, :Text -> 6
    >>> tm_path, tm_offset = tm.get_path_and_offset(tree_pos)
    >>> print(pp_path(tm_path, delimiter=', '), '->', tm_offset)
    doc, p, :Text -> 6
    >>> assert tm_path == cm_path  # paths are really the same sequence of nodes

This can easily be confirmed by looking at the complete mappings in
direct comparison. First the unrestricted mapping::

    >>> print(tm)
    0 -> doc, p, :Text "In München"
    10 -> doc, p, footnote, em "München"
    17 -> doc, p, footnote, :Text " is the German" "name of the city of Munich"
    58 -> doc, p, :Text " is a Hofbräuhaus"

Now, the mapping that omits the footnotes::

    >>> print(cm)
    0 -> doc, p, :Text "In München"
    10 -> doc, p, :Text " is a Hofbräuhaus"

Note, that the numbers at the beginning of each line represent the
string position which is different for the same path, but this has no
bearing on the offsets which count from the content-mapping-specific
position of each path in the content mapping.

Conversely, we could also have restricted the content mapping only to
the footnote(s)::

    >>> fm = ContentMapping(tree, select='footnote', ignore=NO_PATH)
    >>> print(fm)
    0 -> doc, p, footnote, em "München"
    7 -> doc, p, footnote, :Text " is the German" "name of the city of Munich"

Here, the parameter ``ignore=NO_PATH`` has to be understood as "from the
selected paths do not ignore any paths". In case the select-parameter matches
for nodes that are not leave-nodes, ContentMapping will map all leave nodes
that are reachable from there. In this case these are all leaf-nodes "above"
a "footnote" node.

Now, let's look for the string "München" in the footnotes only::

    >>> i = fm.content.find('München')
    >>> path, offset = fm.get_path_and_offset(i)
    >>> pp_path(path, 1)
    'doc <- p <- footnote <- em "München"'
    >>> print(offset)
    0

We can now manipulate the tree through the path and offset. Let's insert
the word "Stadt" in front of "München". We do so by changing the result
of the leaf node of the path to the term at the given offset::

    >>> path[-1].result = path[-1].result[:offset] + "Stadt " + \
    ...                   path[-1].result[offset:]

In this particular case, because the offset is zero, we could also have
written ``"Stadt " + path[-1].result``, but the formula above also
works for the general case where cannot be sure that the offset will
always be 0.

We expect that the change is reflected in the tree at the right position, i.e.
inside the footnote::

    >>> printw(tree.as_xml(inline_tags={'doc'}))
    <doc><p>In München<footnote><em>Stadt München</em> is the German
    name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>

As mentioned earlier, the content mapping should be considered tainted if the
underlying tree has been changed by any other means than the methods of the
ContentMapping-object itself. In order to rebuild the affected path of the
content mapping :py:meth:`ContentMapping.rebuild_mapping` must be called for
the affected sections of the content mapping which are defined by the first
and last path index of the content mapping where a change has taken place::

    >>> fm.rebuild_mapping(i, i)
    >>> print(fm)
    0 -> doc, p, footnote, em "Stadt München"
    13 -> doc, p, footnote, :Text " is the German" "name of the city of Munich"


Limitations
-----------

A limitation shared with other techniques of standoff-markup
consists in the fact that content mappings remain
completely agnostic with respect to any textual meaning of the nodes.
For example assume that the node-name "pb" signifies a page break, which
implies that there is a gap between the two parts separated by the page
break. However, because this is considered part of the meaning
of "pb" it may not be required by the encoding guide-lines for the
document that a gap, say, a blank character or a linefeed is also
redundantly encoded in the string content of the document.
(It may even be forbidden to do so!) But then a search on the
string content may miss phrases separated by a page break::

    >>> tree = parse_xml('<doc>xyz New<pb/>York xyz</doc>')
    >>> print(tree.content)
    xyz NewYork xyz
    >>> m = re.search(r'New\s+York', tree.content)
    >>> print(m)
    None

Currently, the only remedy is to either allow redundant encoding
of textual meanings within the string-content or adding specific
nodes that carry the redundant textual meanings within their
string-content and removing them again, after searches etc. have
been finished. In the example above one can implement the
first suggestion either by adding "\n" before or after
the <pb/>-node, or, more elegantly, by turning the empty <pb/> node
into a node with content: <pb>\n</pb>. The same trick can be applied
for practically any kind empty node.


Markup insertion
----------------

Class :py:class:`ContentMapping` provides powerful markup-methods
that allows you to add markup at any position you like simply by
passing the start- and end-position in the string-representation of
the document-tree and "automagically" taking care of such perils
as cross-cutting tag-boundaries or overlapping hierarchies.

This solves a common challenge when processing tree structured text-data
which consists in adding new nodes that cover certain ranges of the
string content that may already have been covered by other elements. The
problem is the same as adding further markup to an existing XML or
HTML-document. In trivial cases like::

    >>> trivial_xml = parse_xml("<trivial>Please mark up Stadt München "
    ...     "in Bavaria in this sentence.</trivial>")

we would hardly need any help by a library to markup a string "Stadt München".
But both to find certain sub-strings and to mark them up can easily become
complicated::

    >>> hard_xml = parse_xml("<hard>Please mark up Stadt\n<lb/>"
    ...     "<location><em>München</em> in Bavaria</location> in this "
    ...     "sentence.</hard>")

Let's start with the simple case to see how searching and marking
strings works with DHParser::

    >>> mapping = ContentMapping(trivial_xml)
    >>> match = re.search(r"Stadt\s+München", mapping.content)
    >>> _ = mapping.markup(match.start(), match.end(), "foreign",
    ...                    attributes={'lang': 'de'})
    >>> printw(trivial_xml.as_xml(inline_tags={'trivial'}))
    <trivial>Please mark up <foreign lang="de">Stadt München</foreign>
     in Bavaria in this sentence.</trivial>

In order to search for the text-string, a regular expression is used
rather than a simple search for "Stadt München", because we cannot
assume that it appears in exactly the same form in the text. For
example, it could be broken up by a line break, e.g. "Stadt\\nMünchen".

Now, let's try the more complicated case. Because we will try
different configurations, we use copied of the tree "hard_xml"::

    >>> import copy
    >>> hard_xml_copy = copy.deepcopy(hard_xml)
    >>> mapping = ContentMapping(hard_xml_copy)
    >>> match = re.search(r"Stadt\s+München", mapping.content)
    >>> _ = mapping.markup(match.start(), match.end(), "foreign",
    ...                    attributes={'lang': 'de'})
    >>> xml_str = hard_xml_copy.as_xml(empty_tags={'lb'})
    >>> print(xml_str)
    <hard>
      Please mark up
      <foreign lang="de">
        Stadt
        <lb/>
      </foreign>
      <location>
        <foreign lang="de">
          <em>München</em>
        </foreign>
        in Bavaria
      </location>
      in this sentence.
    </hard>

As can be seen the <foreign>-tag is split into two parts, because the markup
runs across the border of another tag, in this case <location>. Note, that the
<lb/>-tag lies inside the <foreign>-tag. But that makes sense, because it would
also have been inside the <foreign>-tag, had there been no <location>-tag and
no need to split. (Per default, the algorithm behaves somewhat "greedy", which,
however can be configured with a parameter with the same name passed to the
constructor of class ContentMapping.)

But what if you don't want the <foreign>-tag to be split up in two or
more parts, as the case may be. Well, in this case, you need to allow
those tags, the borders of which the new markup runs across, to be split
by that markup::

    >>> hard_xml_copy = copy.deepcopy(hard_xml)
    >>> divisibility_map = {'foreign': {'location', ':Text'},
    ...                     '*': {':Text'}}
    >>> mapping = ContentMapping(hard_xml_copy, divisibility=divisibility_map)
    >>> match = re.search(r"Stadt\s+München", mapping.content)
    >>> _ = mapping.markup(match.start(), match.end(), "foreign",
    ...                    attributes={'lang': 'de'})
    >>> xml_str = hard_xml_copy.as_xml(empty_tags={'lb'})
    >>> print(xml_str)
    <hard>
      Please mark up
      <foreign lang="de">
        Stadt
        <lb/>
        <location>
          <em>München</em>
        </location>
      </foreign>
      <location>
        in Bavaria
      </location>
      in this sentence.
    </hard>

See the difference? This time the <foreign>-element remains intact,
while the <location>-element has been split. This behavior can be
configures by the divisibility-map that is passed to the parameter
``divisibility`` of the ContentMapping-constructor. It maps elements
(or, rather, their names) to sets of elements that can be cut by them.
The asterisk ``*`` is a wildcard and contains those elements that can be
cut by any other element. An element that does not appear in the
value-set anywhere in the mapping cannot be cut by any other element. It
is also possible to pass a simple set of element-names instead of a
dictionary to the divisibility-parameter. In this case any element with
a name in this set can be cut by any other element. Any element the name
of which is not a member of the set cannot be cut when markup is added.

In cases where markup overlaps element-borders, it is unavoidable to
decide which element will be divided and which not. It is a general
limitation of tree structures that they do not allow overlapping
hierarchies. In this particular example, it would most probably be more
reasonable to keep the <location>-element intact, because locations
should probably be recognizable as units, while this does not really
seem to matter for a foreign language annotation.

The case may arise, though, where you cannot avoid splitting elements
that form units. At this point you probably should consider using an
entirely different data-structure, say, a graph. But if this is not an
option, :py:mod:`DHParser.nodetree` allows you to mark split elements as
belonging to the same "chain" of elements. In order to do so you can
pass a ``chain_attr_name`` to the constructor of class ContentMapping.
This is an (arbitrary) name for an attribute which will contain a unique
short string that all elements (of the same name) belonging to one and
the same chain share with each other, but not with any other elements.
Let's try this on the previous example::

    >>> reset_chain_ID()  # just to ensure deterministic ID values for doctest, here

    >>> hard_xml_copy = copy.deepcopy(hard_xml)
    >>> match = re.search(r"Stadt\s+München", hard_xml_copy.content)
    >>> divisibility_map = {'foreign': {'location', ':Text'},
    ...                     '*': {':Text'}}
    >>> mapping = ContentMapping(hard_xml_copy, divisibility=divisibility_map,
    ...                          chain_attr_name="chain")
    >>> _ = mapping.markup(match.start(), match.end(), "foreign",
    ...                    {'lang': 'de'})
    >>> xml_str = hard_xml_copy.as_xml(empty_tags={'lb'})
    >>> print(xml_str)
    <hard>
      Please mark up
      <foreign lang="de">
        Stadt
        <lb/>
        <location chain="VZT">
          <em>München</em>
        </location>
      </foreign>
      <location chain="VZT">
        in Bavaria
      </location>
      in this sentence.
    </hard>

Markup plays well together with restricted content mappings as the
following example may show::

    >>> xml = ("<doc>Please mark up Stadt\n<lb/>"
    ...        "<em>München</em><footnote>'Stadt <em>München</em>'"
    ...        " is German for 'City of Munich'</footnote> in Bavaria"
    ...        " in this sentence.</doc>")
    >>> tree = parse_xml(xml)

Let's assume we'd like to markup locations and text-passages in foreign
languages, but only in the main text and not within footnotes and the
like. For that purpose, we build a context mapping that is restricted to
non-footnote-text::

    >>> cm = ContentMapping(tree, select=LEAF_PATH, ignore='footnote',
    ...                     chain_attr_name='chain')
    >>> print(cm.content)
    Please mark up Stadt
    München in Bavaria in this sentence.

Now, let's assume for the sake of the example that we have list of
location names to be marked up that contains the phrase "München in
Bavaria". So, we search for this phrase and add the required location
markup::

    >>> m = re.search(r"München\s+in\s+Bavaria", cm.content)
    >>> print(m)
    <re.Match object; span=(21, 39), match='München in Bavaria'>

    >>> _ = cm.markup(m.start(), m.end(), 'location')
    >>> print(tree.as_xml(empty_tags={'lb'}))
    <doc>
      Please mark up Stadt
      <lb/>
      <location>
        <em>München</em>
        <footnote>
          'Stadt
          <em>München</em>
          ' is German for 'City of Munich'
        </footnote>
        in Bavaria
      </location>
      in this sentence.
    </doc>

The <location>-element covers the entire span, including the footnote. This
is to be expected as changes are always carried out on the full tree. Only,
the mapping is restricted to certain parts of the document. Often, this
is indeed the desired behavior. Depending on the use case, however,
another behavior (e.g. splitting the <location>-element into one part before
the <footnote>-element and one part after that element) might be preferable (see
further below).

Because, the <location>-element did not need to be split, it does not need
and therefore does not have a "chain"-attribute.

Next, let's add the <foreign>-element. (We substitute the value of its
chain-attribute, so that the doctest does not break, when another random
key is picked!)::

    >>> m = re.search(r'Stadt\s+München', cm.content)
    >>> _ = cm.markup(m.start(), m.end(), 'foreign', lang="de")
    >>> print(tree.as_xml(empty_tags={'lb'}))
    <doc>
      Please mark up
      <foreign lang="de" chain="RZC">
        Stadt
        <lb/>
      </foreign>
      <location>
        <foreign lang="de" chain="RZC">
          <em>München</em>
        </foreign>
        <footnote>
          'Stadt
          <em>München</em>
          ' is German for 'City of Munich'
        </footnote>
        in Bavaria
      </location>
      in this sentence.
    </doc>

Here again, one might ask, why the <foreign>-tag contains the <lb>-tag,
but the choice makes sense, because if put together again, it should
cover the complete stretch including the line-break.

As said earlier, different use cases and different choices are imaginable.
What if, you prefer to exclude any footnotes from markup that you
add to the main text? For this purpose, you can use the exclude_regions
parameter which takes a list of tuples (start, end) as value which
represent half-open intervalls of character positions start <= n < end
within the string content. Because of this, if you need to exclude particular
tags, you first need to determine the start and end of each of theses tags.
While this deviates from the practice of defining (sub-)regions of the
tree-structured document by path-select functions, it has the advantage
that one can easily exclude regions that are not delineated by markup,
but merely but textual characteristics like, for examples, bracketed text.
Let's see how this can be done, with out original XML-snippet::

    >>> tree = parse_xml(xml)
    >>> cm = ContentMapping(tree, ignore='footnote')
    >>> m = re.search(r"München\s+in\s+Bavaria", cm.content)
    >>> exclude = content_regions(tree, 'footnote')
    >>> _ = cm.markup(m.start(), m.end(), 'location', exclude)
    >>> print(tree.as_xml(empty_tags={'lb'}))
    <doc>
      Please mark up Stadt
      <lb/>
      <em>
        <location>München</location>
      </em>
      <footnote>
        'Stadt
        <em>München</em>
        ' is German for 'City of Munich'
      </footnote>
      <location> in Bavaria</location>
      in this sentence.
    </doc>

.. note::
   If one prefers to define include-regions instead of exclude-regions for markup,
   the exclude-regions that must be passt to the :py:meth:`~standoff.ContentMapping.markup`
   method can easily be derived from the input-regions by substracting the input regions
   from the region covering the full string content (or any superset of it in case you'd
   like to avoid a potentially costly :py:meth:`~nodetree.Node.strlen` call) with
   the function :py:func:`~standoff.range_difference`. The list of exclude regions passed
   to :py:meth:`~standoff.ContentMapping.markup` must be sorted and overlapping regions
   be merged beforehand. Any list of ranges can be sorted and merged
   with :py:func:`~standoff.sort_and_merge`. Likewise, the range-algebraic functions in
   module :mod:`~standoff` expect sorted and merged input but are - under this condition -
   guaranteed to yield sorted and merged results.

In case empty nodes shall be excluded from the markup, it suffices to pass a zero-length
range at the first character after the empty node (wihtin the content). Say, we have an
xml document ``<doc>Die Stadt<lb/>München liegt in Bayern</doc>``. Here, the letter after
the empty tag <lb/> is the "M" of the word "München". In the string
content of this document "Die StadtMünchen liegt in Bayern", the "M" of München is the ninth
letter. In order to avoid it being included in a newly markedup region the range (9, 9)
must be added to the exclude region. The simplest way of obtaining all the regions where
a particular type of tag is located is, again, the function :py:func:`~standoff.content_regions`,
e.g. exlude = content_regions(tree, "lb"). Here is the full example:

    >>> xml = "<doc>Die Stadt<lb/>München liegt in Bayern</doc>"
    >>> tree = parse_xml(xml)
    >>> cm = ContentMapping(tree)
    >>> exclude = content_regions(tree, 'lb')
    >>> print(exclude)
    [(9, 9)]
    >>> _ = cm.markup(0, 16, "X", exclude_regions=exclude)  # assignment just to mute output, here
    >>> print(tree.as_xml(inline_tags={'doc'}))
    <doc><X>Die Stadt</X><lb/><X>München</X> liegt in Bayern</doc>


*Classes and Functions-Reference*
---------------------------------

The full documentation of all classes and functions can be found in module
:py:mod:`DHParser.standoff`. The following table of contents lists the most
important of these:


class ContentMapping
^^^^^^^^^^^^^^^^^^^^

ContentMapping represents a path-mapping of the string-content of
all or a specific selection of the leave-nodes of a tree. A
content-mapping is an ordered mapping of the first text position of
every (selected) leaf-node to the path of this node.

The class provides methods for mapping string positions to paths and
offsets (relative to the beginning of the leaf-node of the path)

* :py:func:`~standoff.content_regions`: Returns a list of string-regions,
    i.e. half-open intervalls. for given path-selectors.

* :py:class:`~standoff.ContentMapping`: Mapping the tree to its string-content

    * :py:meth:`~standoff.ContentMapping.get_path_and_offset`:
      Maps positions in string-content of the ContentMapping to the
      leaf-path into which they fall

    * :py:meth:`~standoff.ContentMapping.iterate_paths`:
      Yields all paths from
      position ``start_pos`` up to and including position ``end_pos``.

    * :py:meth:`~standoff.ContentMapping.insert_node`:
      Inserts a node at a
      particular text-position.

    * :py:meth:`~standoff.ContentMapping.markup`:
       Adds markup (i.e. an element) to a particular stretch of text.



.. _mixed content: https://www.w3.org/TR/xml/#sec-mixed-content