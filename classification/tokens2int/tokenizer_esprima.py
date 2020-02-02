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
    Configuration file storing the dictionary TOKENS_DICO.
        Key: Esprima lexical unit (token);
        Value: Unique integer.
    Complete list: <https://github.com/jquery/esprima/blob/master/features/token.ts>.
"""


TOKENS_DICO = {
    'Boolean': 0,
    '<end>': 1,
    'Identifier': 2,
    'Keyword': 3,
    'Null': 4,
    'Numeric': 5,
    'Punctuator': 6,
    'String': 7,
    'RegularExpression': 8,
    'Template': 9,
    'LineComment': 10,
    'BlockComment': 11
}
