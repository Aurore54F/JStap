# Copyright (C) 2019 Aurore Fass
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
    Builds a Control Flow Graph..
"""


EPSILON = ['BlockStatement', 'DebuggerStatement', 'EmptyStatement',
           'ExpressionStatement', 'LabeledStatement', 'ReturnStatement',
           'ThrowStatement', 'WithStatement', 'CatchClause', 'VariableDeclaration',
           'FunctionDeclaration']

CONDITIONAL = ['DoWhileStatement', 'ForStatement', 'ForOfStatement', 'ForInStatement',
               'IfStatement', 'SwitchCase', 'SwitchStatement', 'TryStatement',
               'WhileStatement', 'ConditionalExpression']

UNSTRUCTURED = ['BreakStatement', 'ContinueStatement']


# The comments just automatically link to a Statement node somewhere below them.
def extra_comment_node(node, max_children):
    """ If a comment has linked to a node. """
    if len(node.children) > max_children:
        if node.children[max_children].is_comment():
            node.set_comment_dependency(extremity=node.children[max_children])


def link_expression(node, node_parent):
    """ Non-statement node. """
    if node.is_comment():
        node_parent.set_comment_dependency(extremity=node)
    else:
        node_parent.set_statement_dependency(extremity=node)
    return node


def epsilon_statement_cf(node):
    """ Non-conditional statements. """
    for child in node.children:
        if child.is_statement():
            node.set_control_dependency(extremity=child, label='e')
        else:
            link_expression(node=child, node_parent=node)


def break_statement_cf(node):
    """ BreakStatement, breaks the loop. """
    if_cond = node.control_dep_parents[0].extremity.control_dep_parents[0].extremity
    block_statmt = if_cond.control_dep_parents[0].extremity
    if_all = [elt.extremity for elt in block_statmt.control_dep_children]
    for i, _ in enumerate(if_all):
        if if_cond.id == if_all[i].id:
            break
    print(if_all)
    if_false = if_all[i+1:]
    print(if_false)
    for elt in if_false:
        print(if_cond.name)
        print(if_cond.id)
        print(elt.name)
        print(elt.id)
        if_cond.set_control_dependency(extremity=elt, label=False)
        block_statmt.remove_control_dependency(extremity=elt)


def do_while_cf(node):
    """ DoWhileStatement. """
    # Element 0: body (Statement)
    # Element 1: test (Expression)
    node.set_control_dependency(extremity=node.children[0], label=True)
    link_expression(node=node.children[1], node_parent=node)
    extra_comment_node(node, 2)


def for_cf(node):
    """ ForStatement. """
    # Element 0: init
    # Element 1: test (Expression)
    # Element 2: update (Expression)
    # Element 3: body (Statement)
    """ ForOfStatement. """
    # Element 0: left
    # Element 1: right
    # Element 2: body (Statement)
    i = 0
    for child in node.children:
        if child.body != 'body':
            link_expression(node=child, node_parent=node)
        elif not child.is_comment():
            node.set_control_dependency(extremity=child, label=True)
        i += 1
    extra_comment_node(node, i)


def if_cf(node):
    """ IfStatement. """
    # Element 0: test (Expression)
    # Element 1: consequent (Statement)
    # Element 2: alternate (Statement)
    link_expression(node=node.children[0], node_parent=node)
    node.set_control_dependency(extremity=node.children[1], label=True)
    if len(node.children) > 2:
        if node.children[2].is_comment():
            node.set_comment_dependency(extremity=node.children[2])
        else:
            node.set_control_dependency(extremity=node.children[2], label=False)
            extra_comment_node(node, 3)


def try_cf(node):
    """ TryStatement. """
    # Element 0: block (Statement)
    # Element 1: handler (Statement) / finalizer (Statement)
    # Element 2: finalizer (Statement)
    node.set_control_dependency(extremity=node.children[0], label=True)
    if node.children[1].body == 'handler':
        node.set_control_dependency(extremity=node.children[1], label=False)
    else:  # finalizer
        node.set_control_dependency(extremity=node.children[1], label='e')
    if len(node.children) > 2:
        if node.children[2].body == 'finalizer':
            node.set_control_dependency(extremity=node.children[2], label='e')
            extra_comment_node(node, 3)
        else:
            extra_comment_node(node, 2)


def while_cf(node):
    """ WhileStatement. """
    # Element 0: test (Expression)
    # Element 1: body (Statement)
    link_expression(node=node.children[0], node_parent=node)
    node.set_control_dependency(extremity=node.children[1], label=True)
    extra_comment_node(node, 2)


def switch_cf(node):
    """ SwitchStatement. """
    # Element 0: discriminant
    # Element 1: cases (SwitchCase)

    switch_cases = node.children
    link_expression(node=switch_cases[0], node_parent=node)
    if len(switch_cases) > 1:
        # SwitchStatement -> True -> SwitchCase for first one
        node.set_control_dependency(extremity=switch_cases[1], label='e')
        switch_case_cf(switch_cases[1])
        for i in range(2, len(switch_cases)):
            if switch_cases[i].is_comment():
                node.set_comment_dependency(extremity=switch_cases[i])
            else:
                # SwitchCase -> False -> SwitchCase for the other ones
                switch_cases[i - 1].set_control_dependency(extremity=switch_cases[i], label=False)
                if i != len(switch_cases) - 1:
                    switch_case_cf(switch_cases[i])
                else:  # Because the last switch is executed per default, i.e. without condition 1st
                    switch_case_cf(switch_cases[i], last=True)
    # Otherwise, we could just have a switch(something) {}


def switch_case_cf(node, last=False):
    """ SwitchCase. """
    # Element 0: test
    # Element 1: consequent (Statement)
    nb_child = len(node.children)
    if nb_child > 1:
        if not last:  # As all switches but the last has to respect a condition to enter the branch
            link_expression(node=node.children[0], node_parent=node)
            j = 1
        else:
            j = 0
        for i in range(j, nb_child):
            if node.children[i].is_comment():
                node.set_comment_dependency(extremity=node.children[i])
            else:
                node.set_control_dependency(extremity=node.children[i], label=True)
    elif nb_child == 1:
        node.set_control_dependency(extremity=node.children[0], label=True)


def conditional_statement_cf(node):
    """ For the conditional nodes. """
    if node.name == 'DoWhileStatement':
        do_while_cf(node)
    elif node.name == 'ForStatement' or node.name == 'ForOfStatement'\
            or node.name == 'ForInStatement':
        for_cf(node)
    elif node.name == 'IfStatement' or node.name == 'ConditionalExpression':
        if_cf(node)
    elif node.name == 'WhileStatement':
        while_cf(node)
    elif node.name == 'TryStatement':
        try_cf(node)
    elif node.name == 'SwitchStatement':
        switch_cf(node)
    elif node.name == 'SwitchCase':
        pass  # Already handled in SwitchStatement


def unstructured_statement_cf(node):
    """ For the unstructured nodes. """
    if node.name == 'ContinueStatement':
        continue_statement_cf(node)
    elif node.name == 'BreakStatement':
        break_statement_cf(node)


def build_cfg(ast_nodes):
    """
        Produce a CFG by adding statement and control dependencies to each Node.

        -------
        Parameters:
        - ast_nodes: Node
            Output of ast_to_ast_nodes(<ast>, ast_nodes=Node('Program')).

        -------
        Returns:
        - Node
            With statement and control dependencies added.
    """

    for child in ast_nodes.children:
        if child.name in EPSILON or child.name in UNSTRUCTURED:
            epsilon_statement_cf(child)
        elif child.name in CONDITIONAL:
            conditional_statement_cf(child)
        else:
            for grandchild in child.children:
                if not grandchild.is_statement():
                    link_expression(node=grandchild, node_parent=child)
                else:
                    child.set_control_dependency(extremity=grandchild, label='e')
        build_cfg(child)
    return ast_nodes
