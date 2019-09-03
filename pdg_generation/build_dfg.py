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
    Builds a Code Dependency Graph..
"""

import logging
import copy

import js_reserved
import var_list


DECLARATIONS = ['VariableDeclaration', 'FunctionDeclaration']
EXPRESSIONS = ['AssignmentExpression', 'ArrayExpression', 'ArrowFunctionExpression',
               'AwaitExpression', 'BinaryExpression', 'CallExpression', 'ClassExpression',
               'ConditionalExpression', 'FunctionExpression', 'LogicalExpression',
               'MemberExpression', 'NewExpression', 'ObjectExpression', 'SequenceExpression',
               'TaggedTemplateExpression', 'ThisExpression', 'UnaryExpression', 'UpdateExpression',
               'YieldExpression']


def get_pos_identifier(identifier_node, my_var_list):
    """
        Position of identifier_node in var_list.

        -------
        Parameters:
        - identifier_node: Node
            Node whose name Identifier is.
        - my_var_list: VarList
            Stores the variables currently declared and where they should be referred to.

        -------
        Returns:
        - int
            The position of identifier_node in var_list.
        - or None if it is not in the list.
    """

    id_name_list = [elt.attributes['name'] for elt in my_var_list.var_list]
    var_name = identifier_node.attributes['name']
    if var_name in id_name_list:
        return id_name_list.index(var_name)
    return None


def get_nearest_statement(node, answer=None):
    """
        Gets the statement node nearest to node (using CF).

        -------
        Parameters:
        - node: Node
            Current node.
        - answer: Node
            Such as answer.is_statement() = True. Used to force taking a statement node parent
            of the nearest node (use case: boolean data flow dependencies). Default: None.

        -------
        Returns:
        - Node:
            answer, if given, otherwise the statement node nearest to node.
    """

    if answer is not None:
        return answer
    else:
        if node.is_statement():
            return node
        else:
            if len(node.statement_dep_parents) > 1:
                logging.warning('Several statement dependencies are joining on the same node %s',
                                node.name)
            # return get_nearest_statement(node.statement_dep_parents[0].extremity)
            return get_nearest_statement(node.parent)


def is_descendant(node1, node2):
    """
        Indicates whether node1 is a descendant of node2 (using CF).

        -------
        Parameters:
        - node1: Node
        - node2: Node

        -------
        Returns:
        - Bool
    """

    if node2.id == node1.id:
        return True
    if node2.is_leaf():
        return False

    res = []
    for child in node2.control_dep_children:
        res.append(is_descendant(node1, child.extremity))
    for child in node2.statement_dep_children:
        res.append(is_descendant(node1, child.extremity))
    if True in res:
        return True
    return False


def get_nearest_common_statement(node1, node2):
    """
        Gets the nearest common statement node between two statement nodes node1 and node2
        (using CF).

        -------
        Parameters:
        - node1: Node
        - node2: Node

        -------
        Returns:
        - Node:
            Nearest common statement node between node1 and node2.
    """

    nearest_statement1 = get_nearest_statement(node1)
    nearest_statement2 = get_nearest_statement(node2)
    if nearest_statement1.id == nearest_statement2.id:
        return nearest_statement1
    if is_descendant(nearest_statement1, nearest_statement2):
        return get_nearest_common_statement(nearest_statement1.control_dep_parents[0].extremity,
                                            nearest_statement2)
    return get_nearest_common_statement(nearest_statement1,
                                        nearest_statement2.control_dep_parents[0].extremity)


def set_df(var, var_index, identifier_node):
    """
        Sets the data flow dependencies from the statement node nearest to the variable in var at
        position var_index, to the statement node nearest to identifier_node.

        -------
        Parameters:
        - var: VarList
            Either var_loc or var_glob
        - var_index: int
            Position of the variable considered in var.
        - identifier_node: Node
            End of the DF.
    """

    if not isinstance(var, var_list.VarList):
        logging.error('The parameter given should be typed var_list.VarList. Got %s', str(var))
    else:
        begin_df = get_nearest_statement(var.var_list[var_index], var.ref_list[var_index])
        begin_id_df = var.var_list[var_index]
        if isinstance(begin_df, list):
            for i, _ in enumerate(begin_df):
                get_nearest_statement(begin_df[i]).\
                    set_data_dependency(extremity=get_nearest_statement(identifier_node),
                                        begin=begin_df[i], end=identifier_node)
        else:
            begin_df.set_data_dependency(extremity=get_nearest_statement(identifier_node),
                                         begin=begin_id_df, end=identifier_node)


def assignment_df(identifier_node, var_loc, var_glob, unknown_var):
    """
        Add data flow for Identifiers.

        -------
        Parameters:
        - identifier_node: Node
            Node whose name Identifier is.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
    """

    # Position of identifier in the list a
    var_index = get_pos_identifier(identifier_node, var_loc)
    if var_index is not None:
        logging.debug('The variable %s was used', identifier_node.attributes['name'])
        # Data dependency between last time variable used and now
        set_df(var_loc, var_index, identifier_node)

    else:
        var_index = get_pos_identifier(identifier_node, var_glob)
        if var_index is not None:
            logging.debug('The global variable %s was used', identifier_node.attributes['name'])
            # Data dependency between last time variable used and now
            set_df(var_glob, var_index, identifier_node)
        elif identifier_node.attributes['name'].lower() not in js_reserved.RESERVED_WORDS_LOWER:
            unknown_var.append(identifier_node)  # TODO: handle scope of unknown var


def var_decl_df(node, var_loc, var_glob, unknown_var, entry, assignt=False, obj=False):
    """
        Handles the variables declared.

        -------
        Parameters:
        - node: Node
            Node whose name Identifier is.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - entry: int
            Indicates if we are in the global scope (1) or not (0).
        - assignt: Bool
            False if this is a variable declaration with var/let, True if with AssignmentExpression.
            Default: False.
        - obj: Bool
            True if node an object is, False if it is a variable. Default: False.
    """

    if entry == 1 or (assignt and get_pos_identifier(node, var_loc) is None):
        # Global scope or (directly assigned and not known as a local variable)
        my_var_list = var_glob
    else:
        my_var_list = var_loc

    var_index = get_pos_identifier(node, my_var_list)
    if var_index is None:
        my_var_list.add_var(node)  # Add variable in the list
        if not assignt:
            logging.debug('The variable %s was declared', node.attributes['name'])
        else:
            logging.debug('The global variable %s was declared', node.attributes['name'])
        # hoisting(node, unknown_var)  # Hoisting only for FunctionDeclaration
    else:
        if assignt:
            if obj:  # In the case of objects, we will always keep their AST order
                logging.debug('The object %s was used and modified', node.attributes['name'])
                # Data dependency between last time object used and now
                set_df(my_var_list, var_index, node)
            else:
                logging.debug('The variable %s was modified', node.attributes['name'])
        else:
            logging.debug('The variable %s was redefined', node.attributes['name'])
        # Order in the case that assignt and obj are true: data flow before modifying object
        my_var_list.update_var(var_index, node)  # Update last time with current


def var_declaration_df(node, var_loc, var_glob, unknown_var, id_list, entry):
    """
        Handles the node VariableDeclaration:
            # Element0: id
            # Element1: init

        -------
        Parameters:
        - node: Node
            Node whose name should be VariableDeclarator.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).
    """

    if node.name == 'VariableDeclarator':
        identifiers = search_identifiers(node.children[0], id_list, tab=[])  # Variable definition
        for decl in identifiers:
            id_list.append(decl.id)
            var_decl_df(node=decl, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                        entry=entry)
        if not identifiers:
            logging.warning('No identifier variable found')

        if len(node.children) > 1:  # Variable initialized
            var_loc = build_dfg(node.children[1], var_loc, var_glob, unknown_var=unknown_var,
                                id_list=id_list, entry=entry)
            """
            search_handle_fun_expr(node, var_loc, var_glob, id_list)
            identifiers = search_identifiers(node.children[1], id_list, tab=[])
            for init in identifiers:
                if init.id not in id_list:
                    id_list.append(init.id)
                    assignment_df(identifier_node=init, var_loc=var_loc, var_glob=var_glob)
            """
        else:
            logging.debug('The variable %s was not initialized', decl.attributes['name'])

    # else:  # Could be a Line (comment)
        # logging.warning('Expected a VariableDeclarator node, but got a ' + node.name)
    return var_loc


def limit_scope(var_loc):
    """
        Handles the scope of let/const variable declarations.

        -------
        Parameter:
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
    """

    if var_loc.get_limit():
        var_loc.set_limit(False)
        var_loc.var_list = var_loc.get_before_limit_list()


def search_identifiers(node, id_list, tab, rec=True):
    """
        Searches the Identifier nodes children of node.
        -------
        Parameters:
        - node: Node
            Current node.
        - id_list: list
            Stores the id of the node already handled.
        - tab: list
            To store the Identifier nodes found.
        - rec: Bool
            Indicates whether to go recursively in the node or not. Default: True (i.e. recursive).

        -------
        Returns:
        - list
            Stores the Identifier nodes found.
    """

    if node.name == 'ObjectExpression':  # Only consider the object name, no properties
        pass
    elif node.name == 'Identifier':
        """
        MemberExpression can be:
        - obj.prop[.prop.prop...]: we consider only obj;
        - this.something or window.something: we consider only something.
        """
        if node.parent.name == 'MemberExpression':
            if node.parent.children[0] == node:  # current = obj, this or window
                # if node.attributes['name'].lower() in js_reserved.RESERVED_WORDS_LOWER:
                if node.attributes['name'] == 'this' or node.attributes['name'] == 'window':
                    id_list.append(node.id)  # As window an Identifier is
                    logging.debug('%s is not the variable\'s name', node.attributes['name'])
                    prop = node.parent.children[1]
                    if prop.name == 'Identifier':
                        tab.append(prop)  # We want the something after this/window
                else:
                    tab.append(node)  # otherwise current = obj, which we store
            elif node.parent.children[0].name == 'ThisExpression':  # Parent of this=ThisExpression
                tab.append(node)  # node is actually node.parent.children[1]
            else:
                if node.parent.attributes['computed']:  # Access through a table, could be an index
                    logging.debug('The variable %s was considered', node.attributes['name'])
                    tab.append(node)
        else:
            tab.append(node)  # Otherwise this is just a variable
    else:
        if rec:
            for child in node.children:
                search_identifiers(child, id_list, tab, rec)
    return tab


def assignment_expr_df(node, var_loc, var_glob, unknown_var, id_list, entry, call_expr=False):
    """
        Handles the node AssignmentExpression:
            # Element0: left (referred to as assignee)
            # Element1: right (referred to as assignt)

        -------
        Parameters:
        - node: Node
            Node whose name should be VariableDeclarator.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).
    """

    identifiers = search_identifiers(node.children[0], id_list, tab=[])
    for assignee in identifiers:
        id_list.append(assignee.id)
        if (assignee.parent.name == 'MemberExpression'
                and assignee.parent.children[0].name != 'ThisExpression'
                and 'window' not in assignee.parent.children[0].attributes.values())\
                or (assignee.parent.name == 'MemberExpression'
                    and assignee.parent.parent.name == 'MemberExpression'):
            # assignee is an object, we excluded window/this.var, but not window/this.obj.prop
            # logging.warning(assignee.attributes['name'])
            if assignee.parent.attributes['computed']:  # Access through a table, could be an index
                assignment_df(identifier_node=assignee, var_loc=var_loc, var_glob=var_glob,
                              unknown_var=unknown_var)
            else:
                if call_expr:
                    if (get_pos_identifier(assignee, var_loc) is not None
                            or get_pos_identifier(assignee, var_glob) is not None):
                        # Only if the obj assignee already defined, avoids DF on console.log
                        var_decl_df(node=assignee, var_loc=var_loc, var_glob=var_glob, assignt=True,
                                    obj=True, entry=entry, unknown_var=unknown_var)
                else:
                    var_decl_df(node=assignee, var_loc=var_loc, var_glob=var_glob, assignt=True,
                                obj=True, entry=entry, unknown_var=unknown_var)
        else:  # assignee is a variable
            var_decl_df(node=assignee, var_loc=var_loc, var_glob=var_glob, assignt=True,
                        entry=entry, unknown_var=unknown_var)

        if 'operator' in assignee.parent.attributes:
            if assignee.parent.attributes['operator'] != '=':  # Could be += where assignee is used
                assignment_df(identifier_node=assignee, var_loc=var_loc, var_glob=var_glob,
                              unknown_var=unknown_var)

    if not identifiers:
        logging.warning('No identifier assignee found')

    for i in range(1, len(node.children)):
        var_loc = build_dfg(node.children[i], var_loc, var_glob, unknown_var=unknown_var,
                            id_list=id_list, entry=entry)
    """
    identifiers = search_identifiers(node.children[1], id_list, tab=[])
    for assignt in identifiers:
        id_list.append(assignt.id)
        assignment_df(identifier_node=assignt, var_loc=var_loc, var_glob=var_glob)
    """
    return var_loc


def update_expr_df(node, var_loc, var_glob, unknown_var, id_list, entry):
    """
        Handles the node UpdateExpression:
            # Element0: argument

        -------
        Parameters:
        - node: Node
            Node whose name should be VariableDeclarator.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).
    """

    arguments = search_identifiers(node.children[0], id_list, tab=[])
    for argument in arguments:
        # Variable used, modified, used to have 2 data dependencies, one on the original variable
        # and one of the variable modified that will be used after.
        assignment_df(identifier_node=argument, var_loc=var_loc, var_glob=var_glob,
                      unknown_var=unknown_var)
        var_decl_df(node=argument, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                    assignt=True, entry=entry)
        assignment_df(identifier_node=argument, var_loc=var_loc, var_glob=var_glob,
                      unknown_var=unknown_var)

    if not arguments:
        logging.warning('No identifier assignee found')


def identifier_update(node, var_loc, var_glob, unknown_var, id_list, entry):
    """
        Adds data flow dependency to the considered node.
        -------
        Parameters:
        - node: Node
            Current node.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).
    """

    identifiers = search_identifiers(node, id_list, rec=False, tab=[])
    # rec=False so as to not get the same Identifier multiple times by going through its family.
    for identifier in identifiers:
        if identifier.parent.name == 'CatchClause':  # As an identifier can be used as a parameter
            # Ex: catch(err) {}, err has to be defined here
            var_decl_df(node=node, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                        entry=entry)
        else:
            assignment_df(identifier_node=identifier, var_loc=var_loc, var_glob=var_glob,
                          unknown_var=unknown_var)


def search_function_expression(node, tab):
    """ Seaches the FunctionExpression nodes descendant of node. """

    if node.name == 'FunctionExpression':
        tab.append(node)
    else:
        for child in node.children:
            search_function_expression(child, tab)
    return tab


def link_fun_expr(node):
    """
        Make the link between a function expression and the variable where it may be stored.

        -------
        Parameter:
        - node: Node
            FunctionExpression node.

        -------
        Returns:
        - Node
            Variable referring to the function expression.
    """

    fun_expr_node = node

    while node.name != 'VariableDeclarator' and node.name != 'AssignmentExpression'\
            and node.name != 'Property' and node.name != 'Program':
        if node.name == 'CallExpression':
            break  # To avoid e.g. assigning a to ex, var ex = fun(function(a) {return a});
        node = node.parent

    if node.name == 'VariableDeclarator' or node.name == 'AssignmentExpression'\
            or node.name == 'Property':
        variables = search_identifiers(node.children[0], id_list=[], tab=[])

        functions = search_function_expression(node.children[1], tab=[])

        for i, _ in enumerate(functions):
            if fun_expr_node.id == functions[i].id:
                node_nb = i  # Position of the function expression name in the function_names list
                break

        if 'node_nb' in locals():
            if len(variables) != len(functions):
                logging.warning('Trying to map %s FunctionExpression nodes to %s '
                                + 'VariableDecaration nodes',
                                str(len(functions)), str(len(variables)))
            else:
                fun_expr_def = variables[node_nb]  # Variable storing the function expression
                anonym = True
                for child in fun_expr_node.children:
                    if child.body == 'id':
                        logging.debug('The variable %s refers to the function expression %s',
                                      fun_expr_def.attributes['name'], child.attributes['name'])
                        anonym = False
                    elif anonym:
                        logging.debug('The variable %s refers to an anonymous function ',
                                      fun_expr_def.attributes['name'])
                        anonym = False
                return fun_expr_def
    return None


def hoisting(node, unknown_var):
    """
        Checks if unknown variables are in fact function names which were hoisted.

        -------
        Parameters:
        - node: Node
            Node corresponding to a function's name.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
    """

    unknown_var_copy = copy.copy(unknown_var)
    for unknown in unknown_var_copy:
        if node.attributes['name'] == unknown.attributes['name']:
            logging.debug('Using hoisting, the function %s was first used, then defined',
                          node.attributes['name'])
            get_nearest_statement(node).set_data_dependency(extremity=get_nearest_statement(
                unknown), begin=node, end=unknown)
            unknown_var.remove(unknown)


def function_scope(node, var_loc, var_glob, unknown_var, id_list, fun_expr):
    """
        Function scope for local variables.

        -------
        Parameters:
        - node: Node
            Current node.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - fun_expr: bool
            Indicates if we handle a function declaration or expression. In the expression case,
            the function cannot be called from an outer scope.

        -------
        Returns:
        - VarList
            Variables declared and where they should be referred to before entering the function.
    """

    out_var_list = var_loc.copy_var_list()  # save var_loc before
    # use it in the function scope
    for child in node.children:
        if child.body == 'id' or child.body == 'params':
            identifiers = search_identifiers(child, id_list, tab=[])
            for param in identifiers:
                id_list.append(param.id)
                if child.body == 'id' and not fun_expr:
                    # Stores the function name, so that it can be used in the upper scope
                    # out_var_list.add_var(child, fun=True)
                    var_decl_df(node=param, var_loc=out_var_list, var_glob=var_glob,
                                unknown_var=unknown_var, entry=0)
                    var_loc = out_var_list.copy_var_list()  # to know the function name in the func
                    hoisting(param, unknown_var)
                else:
                    var_decl_df(node=param, var_loc=var_loc, var_glob=var_glob,
                                unknown_var=unknown_var, entry=0)

        else:
            var_loc = build_dfg(child, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                                id_list=id_list, entry=0)

    if fun_expr:
        link_fun_expr(node)
        # fun_expr_var = link_fun_expr(node)
        # if fun_expr_var is not None:
        # hoisting(fun_expr_var, unknown_var)  # Hoisting only for FunctionDeclaration

    limit_scope(var_loc=var_loc)

    return out_var_list  # back to the old var_loc.var_list when we are not in the function anymore


def obj_expr_scope(node, var_loc, var_glob, unknown_var, id_list):
    """
        ObjectExpression scope for local variables.

        -------
        Parameters:
        - node: Node
            Current node.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.

        -------
        Returns:
        - VarList
            Variables declared and where they should be referred to before entering the function.
    """

    out_var_list = var_loc.copy_var_list()  # save var_loc before
    # use it in the object scope
    for prop in node.children:
        for child in prop.children:
            if child.body == 'key':
                identifiers = search_identifiers(child, id_list, tab=[])
                for param in identifiers:
                    id_list.append(param.id)
                    var_decl_df(node=param, var_loc=var_loc, var_glob=var_glob,
                                unknown_var=unknown_var, entry=0)
                    hoisting(param, unknown_var)

            else:
                var_loc = build_dfg(child, var_loc=var_loc, var_glob=var_glob,
                                    unknown_var=unknown_var, id_list=id_list, entry=0)

    limit_scope(var_loc=var_loc)

    return out_var_list  # back to the old var_loc.var_list when we are not in the object anymore


def boolean_cf_dep(node_list, var_loc, var_glob, unknown_var, id_list, entry):
    """
        Statement scope for boolean conditions.

        -------
        Parameters:
        - node_list: list of Nodes
            Current nodes to be handled.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).

        -------
        Returns:
        - var_loc
            In its input state.

    - SwitchCase: several True possible
    """

    temp_list_loc = var_loc.copy_var_list()
    temp_list_glob = var_glob.copy_var_list()

    for boolean_node in node_list:
        # var_loc.var_list modified for the branch
        var_loc = build_dfg(boolean_node, var_loc=var_loc, var_glob=var_glob,
                            unknown_var=unknown_var, id_list=id_list, entry=entry)

    return [temp_list_loc, temp_list_glob, var_loc]  # returns the initial variables list + var_loc


def merge_var_boolean_cf(var_list_before_cond, var_list_true, var_list_false):
    """
        Merges in var_list_true the variables declared on a true and false branches.

        -------
        Parameters:
        - var_list_before_cond: VarList
            Stores the variables declared before entering any conditions and where they should be
            referred to.
        - var_list_true: VarList
            Stores the variables currently declared if cond = true and where they should be
            referred to.
        - var_list_false: VarList
            Stores the variables currently declared if cond = false and where they should be
            referred to.
    """

    # display_temp('True', var_list_true)
    # display_temp('False', var_list_false)
    for node_false in var_list_false.var_list:
        if not any(node_false.attributes['name'] == node_true.attributes['name']
                   for node_true in var_list_true.var_list):
            logging.debug('The variable %s  was added to the list', node_false.attributes['name'])
            var_list_true.add_var(node_false)
        for node_true in var_list_true.var_list:
            if node_false.attributes['name'] == node_true.attributes['name']\
                    and node_false.id != node_true.id:  # The variable was modified in >=1 branch
                var_index = get_pos_identifier(node_true, var_list_true)
                if any(node_true.id == node.id for node in var_list_before_cond.var_list):
                    logging.debug('The variable %s has been modified in the branch False',
                                  node_false.attributes['name'])
                    var_list_true.update_var(var_index, node_false)
                elif any(node_false.id == node.id for node in var_list_before_cond.var_list):
                    logging.debug('The variable %s has been modified in the branch True',
                                  node_true.attributes['name'])
                    # Already handled, as we work on var_list_true
                else:  # Both were modified, we refer to the nearest common statement
                    logging.debug('The variable %s has been modified in the branches True and '
                                  + 'False', node_false.attributes['name'])
                    # var_list_true.update_el_ref(var_index,
                    # get_nearest_common_statement(node_true, node_false))
                    var_list_true.update_el_ref(var_index, [node_true, node_false])


def display_temp(title, temp):
    """ Display known variable's name. """

    print(title)
    for el in temp.var_list:
        print(el.attributes['name'])
        # print(el.id)


def statement_scope(node, var_loc, var_glob, unknown_var, id_list, entry):
    """
        Statement scope.

        -------
        Parameters:
        - node: Node
            Current node.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).
    """

    todo_true = []
    todo_false = []

    # Statements that do belong after one another
    for child_statement_dep in node.statement_dep_children:
        child_statement = child_statement_dep.extremity
        logging.debug('The node %s has a statement dependency', child_statement.name)
        var_loc = build_dfg(child_statement, var_loc=var_loc, var_glob=var_glob,
                            unknown_var=unknown_var, id_list=id_list, entry=entry)

    for child_cf_dep in node.control_dep_children:  # Control flow statements
        child_cf = child_cf_dep.extremity
        if isinstance(child_cf_dep.label, bool):  # Several branches according to the cond
            logging.debug('The node %s has a boolean CF dependency', child_cf.name)
            var_list_before_cond_loc = var_loc.copy_var_list()
            var_list_before_cond_glob = var_glob.copy_var_list()
            if child_cf_dep.label:
                todo_true.append(child_cf)  # In reality does not contain only true variables
            else:
                todo_false.append(child_cf)

        else:  # Epsilon statements
            logging.debug('The node %s has an epsilon CF dependency', child_cf.name)
            var_loc = build_dfg(child_cf, var_loc=var_loc, var_glob=var_glob,
                                unknown_var=unknown_var, id_list=id_list, entry=entry)

    # Separate variables if separate true/false branches
    [var_list_temp_loc, var_list_temp_glob, var_loc] = boolean_cf_dep(todo_true, var_loc=var_loc,
                                                                      var_glob=var_glob,
                                                                      unknown_var=unknown_var,
                                                                      id_list=id_list, entry=entry)
    [_, _, var_list_temp_loc] = boolean_cf_dep(todo_false, var_loc=var_list_temp_loc,
                                               var_glob=var_list_temp_glob, unknown_var=unknown_var,
                                               id_list=id_list, entry=entry)

    if not var_loc.is_equal(var_list_temp_loc):  # Here we have
        # var_loc: variables declared in a branch when the condition was true
        # var_list_temp_loc: variables declared in a branch when the condition was false
        merge_var_boolean_cf(var_list_before_cond_loc, var_loc, var_list_temp_loc)
        # Finally var_loc contains all variables defined in the true + false branches

    if not var_glob.is_equal(var_list_temp_glob):  # Here we have
        # var_glob: variables declared in a branch when the condition was true
        # var_list_temp_glob: variables declared in a branch when the condition was false
        merge_var_boolean_cf(var_list_before_cond_glob, var_glob, var_list_temp_glob)
        # Finally var_glob contains all variables defined in the true + false branches

    limit_scope(var_loc=var_loc)

    return var_loc


def build_df_variable_declaration(node, var_loc, var_glob, unknown_var, id_list, entry):
    """ VariableDeclaration data dependencies. """

    logging.debug('The node %s is a variable declaration', node.name)
    for child in node.children:
        var_loc = var_declaration_df(child, var_loc=var_loc, var_glob=var_glob,
                                     unknown_var=unknown_var, id_list=id_list, entry=entry)
    return var_loc


def build_df_assignment(node, var_loc, var_glob, unknown_var, id_list, entry):
    """ AssignmentExpression data dependencies. """

    logging.debug('The node %s is an assignment expression', node.name)
    var_loc = assignment_expr_df(node, var_loc=var_loc, var_glob=var_glob,
                                 unknown_var=unknown_var, id_list=id_list, entry=entry)
    return var_loc


def build_df_call_expr(node, var_loc, var_glob, unknown_var, id_list, entry):
    """ CallExpression on object data dependencies. """

    logging.debug('The node %s is a call expression on an object', node.name)
    var_loc = assignment_expr_df(node, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                                 id_list=id_list, entry=entry, call_expr=True)
    return var_loc


def build_df_update(node, var_loc, var_glob, unknown_var, id_list, entry):
    """ UpdateExpression data dependencies. """

    logging.debug('The node %s is an update expression', node.name)
    update_expr_df(node, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                   id_list=id_list, entry=entry)


def build_df_function(node, var_loc, var_glob, unknown_var, id_list, fun_expr=False):
    """ FunctionDeclaration and FunctionExpression data dependencies. """

    logging.debug('The node %s is a function declaration', node.name)
    return function_scope(node=node, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                          id_list=id_list, fun_expr=fun_expr)


def build_df_statement(node, var_loc, var_glob, unknown_var, id_list, entry):
    """ Statement (statement, epsilon, boolean) data dependencies. """

    logging.debug('The node %s is a statement', node.name)
    return statement_scope(node=node, var_loc=var_loc, var_glob=var_glob,
                           unknown_var=unknown_var, id_list=id_list, entry=entry)


def build_df_identifier(node, var_loc, var_glob, unknown_var, id_list, entry):
    """ Identifier data dependencies. """

    if node.id not in id_list:
        logging.debug('The variable %s has not been handled yet', node.attributes['name'])
        identifier_update(node, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                          id_list=id_list, entry=entry)
    else:
        logging.debug('The variable %s has already been handled', node.attributes['name'])


def build_dfg(child, var_loc, var_glob, unknown_var, id_list, entry):
    """
        Data dependency for a given node whatever it is.

        -------
        Parameters:
        - child: Node
            Current node to be handled.
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0).

        -------
        Returns:
        - list
            Variables currently declared.
    """

    if child.name == 'VariableDeclaration':
        if child.attributes['kind'] != 'var':  # let or const
            if not var_loc.limited_scope.before_limit_list:  # If before_list is empty
                var_loc.set_before_limit_list(var_loc.var_list)  # We fill it
            # Otherwise it stays as it is

            var_loc = build_df_variable_declaration(child, var_loc=var_loc, var_glob=var_glob,
                                                    unknown_var=unknown_var, id_list=id_list,
                                                    entry=entry)
            var_loc.set_limit(True)  # To limit the visibility only to the upper block
            for node in var_loc.var_list:
                # If we have a node that is not in the before_list and has not been handled yet
                if not any(node.id == before_node.id for before_node
                           in var_loc.limited_scope.before_limit_list)\
                        and not any(node.id == after_node.id for after_node
                                    in var_loc.limited_scope.after_limit_list):
                    logging.debug('The variable %s has a limited scope', node.attributes['name'])
                    var_loc.add_el_limit_list(node)  # Add to after_list
        else:
            var_loc = build_df_variable_declaration(child, var_loc=var_loc, var_glob=var_glob,
                                                    unknown_var=unknown_var, id_list=id_list,
                                                    entry=entry)

    elif child.name == 'AssignmentExpression':
        var_loc = build_df_assignment(child, var_loc=var_loc, var_glob=var_glob,
                                      unknown_var=unknown_var, id_list=id_list, entry=entry)

    elif (child.name == 'CallExpression' and child.children[0].name == 'MemberExpression'
          and child.children[0].children[0].name != 'ThisExpression'
          and 'window' not in child.children[0].children[0].attributes.values())\
            or (child.name == 'CallExpression' and child.children[0].name == 'MemberExpression'
                and child.children[0].parent.name == 'MemberExpression'):
        var_loc = build_df_call_expr(child, var_loc=var_loc, var_glob=var_glob,
                                     unknown_var=unknown_var, id_list=id_list, entry=entry)

    elif child.name == 'UpdateExpression':
        build_df_update(child, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                        id_list=id_list, entry=entry)

    elif child.name == 'FunctionDeclaration':
        var_loc = build_df_function(child, var_loc=var_loc, var_glob=var_glob,
                                    unknown_var=unknown_var, id_list=id_list)

    elif child.name == 'FunctionExpression':
        var_loc = build_df_function(child, var_loc=var_loc, var_glob=var_glob,
                                    unknown_var=unknown_var, id_list=id_list, fun_expr=True)

    elif child.is_statement():
        var_loc = build_df_statement(child, var_loc=var_loc, var_glob=var_glob,
                                     unknown_var=unknown_var, id_list=id_list, entry=entry)

    elif child.name == 'ObjectExpression':  # Only consider the object name, no properties
        var_loc = obj_expr_scope(child, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                                 id_list=id_list)

    elif child.name == 'Identifier':
        build_df_identifier(child, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                            id_list=id_list, entry=entry)

    else:
        var_loc = df_scoping(child, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                             id_list=id_list)[1]
    # display_temp('> Local: ', var_loc)
    # display_temp('> Global: ', var_glob)

    return var_loc


def df_scoping(cfg_nodes, var_loc, var_glob, unknown_var, id_list, entry=0):
    """
        Data dependency for a complete CFG.

        -------
        Parameters:
        - cfg_nodes: Node
            Output of produce_cfg(ast_to_ast_nodes(<ast>, ast_nodes=Node('Program'))).
        - var_loc: VarList
            Stores the variables currently declared and where they should be referred to.
        - var_glob: VarList
            Stores the global variables currently declared and where they should be referred to.
        - unknown_var: list
            Contains the variables currently not defined (could be valid because of hosting,
            therefore we check them later again).
        - id_list: list
            Stores the id of the node already handled.
        - entry: int
            Indicates if we are in the global scope (1) or not (0). Default: 0.

        -------
        Returns:
        - Node
            With data flow dependencies added.
    """

    for child in cfg_nodes.children:
        var_loc = build_dfg(child, var_loc=var_loc, var_glob=var_glob, unknown_var=unknown_var,
                            id_list=id_list, entry=entry)
    return [cfg_nodes, var_loc]
