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
    Definition of class VarList
"""

import copy


class LimitedScope:

    def __init__(self):
        self.limit = False
        self.before_limit_list = []
        self.after_limit_list = []


class VarList:

    def __init__(self):
        self.var_list = []
        self.ref_list = []
        self.fun_list = []
        self.limited_scope = LimitedScope()

    def get_var_list(self):
        return self.var_list

    def get_ref_list(self):
        return self.ref_list

    def set_var_list(self, var_list):
        self.var_list = var_list

    def set_ref_list(self, ref_list):
        self.ref_list = ref_list

    def get_fun_list(self):
        return self.fun_list

    def set_fun_list(self, fun_list):
        self.fun_list = fun_list

    def add_el_ref(self, answer):
        self.ref_list.append(answer)

    def update_el_ref(self, index, answer):
        self.ref_list[index] = answer

    def add_el_fun(self, fun):
        self.fun_list.append(fun)

    def update_el_fun(self, index, fun):
        self.fun_list[index] = fun

    def add_var(self, identifier_node, answer=None, fun=False):
        self.var_list.append(identifier_node)
        self.add_el_ref(answer)
        self.add_el_fun(fun)

    def update_var(self, index, identifier_node, answer=None, fun=False):
        self.var_list[index] = identifier_node
        self.update_el_ref(index, answer)
        self.update_el_fun(index, fun)

    def is_equal(self, var_list2):
        if self.var_list == var_list2.var_list and self.ref_list == var_list2.ref_list\
                and self.fun_list == var_list2.fun_list:
            return True
        return False

    def copy_var_list(self):
        var_list = VarList()
        var_list.set_var_list(copy.copy(self.var_list))
        var_list.set_ref_list(copy.copy(self.ref_list))
        var_list.set_fun_list(copy.copy(self.fun_list))
        return var_list

    def get_limit(self):
        return self.limited_scope.limit

    def set_limit(self, limit):
        self.limited_scope.limit = limit

    def get_before_limit_list(self):
        return self.limited_scope.before_limit_list

    def set_before_limit_list(self, limit_list):
        self.limited_scope.before_limit_list = copy.copy(limit_list)

    def get_after_limit_list(self):
        return self.limited_scope.after_limit_list

    def set_after_limit_list(self, limit_list):
        self.limited_scope.after_limit_list = copy.copy(limit_list)

    def add_el_limit_list(self, el):
        self.limited_scope.after_limit_list.append(el)

    def reset_limited_scope(self):
        self.set_limit(False)
        self.set_before_limit_list([])
        self.set_after_limit_list([])
