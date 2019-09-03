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
    Definition of classes Dependence and Node.
"""

import logging


class Dependence:

    def __init__(self, dependency_type, extremity, label, begin=None, end=None):
        self.type = dependency_type
        self.extremity = extremity
        self.id_begin = begin
        self.id_end = end
        self.label = label

    def get_type(self):
        return self.type

    def set_type(self, dependency_type):
        self.type = dependency_type

    def get_extremity(self):
        return self.extremity

    def set_extremity(self, extremity):
        self.extremity = extremity

    def get_id_begin(self):
        return self.id_begin

    def set_id_begin(self, id_begin):
        self.id_begin = id_begin

    def get_id_end(self):
        return self.id_end

    def set_id_end(self, id_end):
        self.id_end = id_end

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label


class Node:
    id = 0

    def __init__(self, name, parent=None):
        self.name = name
        self.id = Node.id
        Node.id += 1
        self.clone = False
        self.attributes = {}
        self.body = None
        self.body_list = False
        self.parent = parent
        self.children = []
        self.data_dep_parents = []
        self.data_dep_children = []
        self.control_dep_parents = []
        self.control_dep_children = []
        self.comment_dep_parents = []
        self.comment_dep_children = []
        self.statement_dep_parents = []
        self.statement_dep_children = []

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_id(self):
        return self.id

    def set_id(self, node_id):
        self.id = node_id

    def set_clone_true(self):
        self.clone = True

    def get_attributes(self):
        return self.attributes

    def is_leaf(self):
        return not self.children

    def is_statement(self):
        statements = ['BlockStatement', 'BreakStatement', 'ContinueStatement', 'DoWhileStatement',
                      'DebuggerStatement', 'EmptyStatement', 'ExpressionStatement', 'ForStatement',
                      'ForOfStatement', 'ForInStatement', 'IfStatement', 'LabeledStatement',
                      'ReturnStatement', 'SwitchStatement', 'ThrowStatement', 'TryStatement',
                      'WhileStatement', 'WithStatement',
                      'VariableDeclaration', 'CatchClause', 'SwitchCase', 'ConditionalExpression',
                      'FunctionDeclaration', 'ClassDeclaration']
        if self.name in statements:
            return True
        return False

    def is_comment(self):
        comments = ['Line', 'Block']
        if self.name in comments:
            return True
        return False

    def get_attribute(self, attribute_type):
        return self.attributes[attribute_type]

    def get_type(self):
        return self.get_attribute('type')

    def get_value(self):
        return self.get_attribute('name')

    def get_range(self):
        return self.get_attribute('range')

    def set_attribute(self, attribute_type, node_attribute):
        self.attributes[attribute_type] = node_attribute

    def set_type(self, node_type):
        self.set_attribute('type', node_type)

    def set_value(self, node_value):
        self.set_attribute('name', node_value)

    def set_range(self, node_range):
        self.set_attribute('range', node_range)

    def get_body(self):
        return self.body

    def set_body(self, body):
        self.body = body

    def get_body_list(self):
        return self.body_list

    def set_body_list(self, bool_body_list):
        self.body_list = bool_body_list

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent

    def get_children(self):
        return self.children

    def set_child(self, child):
        self.children.append(child)

    def literal_type(self):
        if 'value' in self.attributes:
            literal = self.attributes['value']
            if isinstance(literal, str):
                return 'String'
            elif isinstance(literal, int):
                return 'Int'
            elif isinstance(literal, float):
                return 'Numeric'
            elif isinstance(literal, bool):
                return 'Bool'
            elif literal == 'null' or literal is None:
                return 'Null'
        if 'regex' in self.attributes:
            return 'RegExp'
        if self.name != 'Literal':
            logging.warning('The node %s is not a Literal', self.name)
        else:
            logging.warning('The literal %s has an unknown type', self.attributes['raw'])
        return None

    def get_data_dependencies(self, im_src=True):
        if im_src:
            return [['data dependency', dep.extremity.name, dep.label]
                    for dep in self.data_dep_children]
        return [['data dependency', dep.extremity.name, dep.label]
                for dep in self.data_dep_parents]

    def set_data_dependency(self, extremity, begin, end):
        self.data_dep_children.append(Dependence('data dependency', extremity, 'data', begin, end))
        extremity.data_dep_parents.append(Dependence('data dependency', self, 'data', begin, end))

    def get_control_dependencies(self, im_src=True):
        if im_src:
            return [['control dependency', dep.extremity.name, dep.label]
                    for dep in self.control_dep_children]
        return [['control dependency', dep.extremity.name, dep.label]
                for dep in self.control_dep_parents]

    def set_control_dependency(self, extremity, label):
        self.control_dep_children.append(Dependence('control dependency', extremity, label))
        extremity.control_dep_parents.append(Dependence('control dependency', self, label))

    def set_comment_dependency(self, extremity):
        self.comment_dep_children.append(Dependence('comment dependency', extremity, 'c'))
        extremity.comment_dep_parents.append(Dependence('comment dependency', self, 'c'))

    def remove_control_dependency(self, extremity):
        for i, _ in enumerate(self.control_dep_children):
            elt = self.control_dep_children[i]
            if elt.extremity.id == extremity.id:
                del self.control_dep_children[i]
                del extremity.control_dep_parents[i]

    def get_statement_dependencies(self, im_src=True):
        if im_src:
            return [['statement dependency', dep.extremity.name, dep.label]
                    for dep in self.statement_dep_children]
        return [['statement dependency', dep.extremity.name, dep.label]
                for dep in self.statement_dep_parents]

    def set_statement_dependency(self, extremity):
        self.statement_dep_children.append(Dependence('statement dependency', extremity, 's'))
        extremity.statement_dep_parents.append(Dependence('statement dependency', self, 's'))
