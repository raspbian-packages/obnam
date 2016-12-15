#!/usr/bin/env python
# Copyright 2014-2015  Lars Wirzenius
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =*= License: GPL-3+ =*=


# This module contains a fair bit of Python magic. Tread carefully.
# Like all the worst magic, it has no automated tests, either. Treat
# this module as if it were a sleeping dragon. Do not meddle in the
# affairs of dragons, for they are cranky and you are good with
# ketchup.


import imp
import inspect
import os


import obnamlib


def find_structured_errors(top_module, plugin_manager):
    modules = _find_modules(top_module)
    modules += _find_plugin_modules(plugin_manager)
    return _find_errors(modules)


def _find_modules(top_module):
    result = set()
    queue = [top_module]
    while queue:
        module = queue.pop()
        if module not in result:
            result.add(module)
            queue.extend(_get_submodules(module))
    return list(result)


def _get_submodules(module):
    objs = [getattr(module, name) for name in dir(module)]
    return [x for x in objs if inspect.ismodule(x)]


def _find_plugin_modules(plugin_manager):
    modules = []
    for filename in plugin_manager.plugin_files:
        module_name, _ = os.path.splitext(os.path.basename(filename))
        with open(filename, 'rb') as f:
            module = imp.load_module(
                module_name, f, filename, ('.py', 'r', imp.PY_SOURCE))
        modules.append(module)
    return modules


def _find_errors(modules):
    result = set()
    for module in modules:
        for name in dir(module):
            obj = getattr(module, name)
            if _is_structured_error(obj):
                result.add(obj)
    return list(result)


def _is_structured_error(obj):
    return (type(obj) is type and
            issubclass(obj, obnamlib.StructuredError) and
            hasattr(obj, 'msg'))
