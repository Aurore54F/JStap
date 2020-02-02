#!/usr/bin/python

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
    Configuration file storing the dictionary AST_UNITS_DICO.
        Key: Esprima syntactical unit;
        Value: Unique integer.
"""


AST_UNITS_DICO = {
    'ArrayExpression': 0,
    'ArrayPattern': 1,
    'ArrowFunctionExpression': 2,
    'AssignmentExpression': 3,
    'AssignmentPattern': 4,
    'AwaitExpression': 5,
    'BinaryExpression': 6,
    'BlockStatement': 7,
    'BreakStatement': 8,
    'CallExpression': 9,
    'CatchClause': 10,
    'ClassBody': 11,
    'ClassDeclaration': 12,
    'ClassExpression': 13,
    'ConditionalExpression': 14,
    'ContinueStatement': 15,
    'DebuggerStatement': 16,
    'DoWhileStatement': 17,
    'EmptyStatement': 18,
    'ExportAllDeclaration': 19,
    'ExportDefaultDeclaration': 20,
    'ExportNamedDeclaration': 21,
    'ExportSpecifier': 22,
    'ExpressionStatement': 23,
    'ForInStatement': 24,
    'ForOfStatement': 25,
    'ForStatement': 26,
    'FunctionDeclaration': 27,
    'FunctionExpression': 28,
    'Identifier': 29,
    'IfStatement': 30,
    'Import': 31,
    'ImportDeclaration': 32,
    'ImportDefaultSpecifier': 33,
    'ImportNamespaceSpecifier': 34,
    'ImportSpecifier': 35,
    'LabeledStatement': 36,
    'Literal': 37,
    'LogicalExpression': 38,
    'MemberExpression': 39,
    'MetaProperty': 40,
    'MethodDefinition': 41,
    'NewExpression': 42,
    'ObjectExpression': 43,
    'ObjectPattern': 44,
    'Program': 45,
    'Property': 46,
    'RestElement': 47,
    'ReturnStatement': 48,
    'SequenceExpression': 49,
    'SpreadElement': 50,
    'Super': 51,
    'SwitchCase': 52,
    'SwitchStatement': 53,
    'TaggedTemplateExpression': 54,
    'TemplateElement': 55,
    'TemplateLiteral': 56,
    'ThisExpression': 57,
    'ThrowStatement': 58,
    'TryStatement': 59,
    'UnaryExpression': 60,
    'UpdateExpression': 61,
    'VariableDeclaration': 62,
    'VariableDeclarator': 63,
    'WhileStatement': 64,
    'WithStatement': 65,
    'YieldExpression': 66,
    'Line': 67,
    'Block': 68,
    'String': 69,
    'Int': 70,
    'Numeric': 71,
    'Bool': 72,
    'Null': 73,
    'RegExp': 74
}
