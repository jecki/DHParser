from DHParser import *

def create_tree(l: list) -> Node:
    name, content, children = l
    if children:
        result = tuple(create_tree(child) for child in children)
        result = Node(name, result)
    else:
        result = Node(name, content)
    print(result.as_sxpr())  # <- debugging code
    return result
