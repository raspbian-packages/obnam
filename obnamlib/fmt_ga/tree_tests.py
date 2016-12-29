# Copyright 2015  Lars Wirzenius
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


import unittest

import obnamlib


class GATreeTests(unittest.TestCase):

    def setUp(self):
        self.blob_store = obnamlib.BlobStore()
        self.blob_store.set_bag_store(DummyBagStore())

        self.tree = obnamlib.GATree()
        self.tree.set_blob_store(self.blob_store)

    def test_has_no_root_dir_initially(self):
        self.assertEqual(self.tree.get_directory('/'), None)

    def test_sets_root_dir(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/', dir_obj)
        self.assertEqual(self.tree.get_directory('/'), dir_obj)

    def test_sets_subdir_and_creates_all_parents(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/foo/bar', dir_obj)
        self.assertEqual(self.tree.get_directory('/foo/bar'), dir_obj)
        self.assertNotEqual(self.tree.get_directory('/foo'), None)
        self.assertNotEqual(self.tree.get_directory('/'), None)

    def test_stores_objects_persistently(self):
        orig = obnamlib.GADirectory()
        self.tree.set_directory('/foo/bar', orig)
        self.tree.flush()

        tree2 = obnamlib.GATree()
        tree2.set_blob_store(self.blob_store)
        tree2.set_root_directory_id(self.tree.get_root_directory_id())
        retrieved = tree2.get_directory('/foo/bar')
        self.assertEqual(orig.as_dict(), retrieved.as_dict())

    def test_updates_subdirectory_of_persistent_directory(self):
        # Create original subdir.
        self.tree.set_directory('/foo/bar', obnamlib.GADirectory())
        self.tree.flush()

        # Load new tree, so no cached objects. Update a subdir with a file.
        tree2 = obnamlib.GATree()
        tree2.set_blob_store(self.blob_store)
        tree2.set_root_directory_id(self.tree.get_root_directory_id())
        new_subdir = obnamlib.GADirectory()
        new_subdir.add_file('README')
        tree2.set_directory('/foo/bar', new_subdir)
        tree2.flush()

        # Another new tree. The added file should be visible.
        tree3 = obnamlib.GATree()
        tree3.set_blob_store(self.blob_store)
        tree3.set_root_directory_id(tree2.get_root_directory_id())
        subdir = tree3.get_directory('/foo/bar')
        self.assertIn('README', subdir.get_file_basenames())

    def test_removes_root_directory(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/', dir_obj)
        self.tree.remove_directory('/')
        self.assertEqual(self.tree.get_directory('/'), None)
        self.assertEqual(self.tree.get_root_directory_id(), None)

    def test_removes_directory(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/foo/bar', dir_obj)
        self.tree.remove_directory('/foo/bar')
        self.assertEqual(self.tree.get_directory('/foo/bar'), None)

    def test_removes_persistent_directory(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/foo/bar', dir_obj)
        self.tree.flush()

        tree2 = obnamlib.GATree()
        tree2.set_blob_store(self.blob_store)
        tree2.set_root_directory_id(self.tree.get_root_directory_id())
        tree2.remove_directory('/foo/bar')
        self.assertEqual(tree2.get_directory('/foo/bar'), None)

    def test_removes_persistent_directory_persistently(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/foo/bar', dir_obj)
        self.tree.flush()

        tree2 = obnamlib.GATree()
        tree2.set_blob_store(self.blob_store)
        tree2.set_root_directory_id(self.tree.get_root_directory_id())
        tree2.remove_directory('/foo/bar')
        tree2.flush()

        tree3 = obnamlib.GATree()
        tree3.set_blob_store(self.blob_store)
        tree3.set_root_directory_id(tree2.get_root_directory_id())
        self.assertEqual(tree3.get_directory('/foo/bar'), None)

    def test_removes_nonexistent_directory(self):
        self.tree.remove_directory('/foo/bar')
        self.assertEqual(self.tree.get_directory('/foo/bar'), None)

    def test_removes_nonexistent_directory_when_tree_is_not_empty(self):
        dir_obj = obnamlib.GADirectory()
        self.tree.set_directory('/foo/bar', dir_obj)
        self.tree.flush()

        tree2 = obnamlib.GATree()
        tree2.set_blob_store(self.blob_store)
        tree2.set_root_directory_id(self.tree.get_root_directory_id())
        tree2.remove_directory('/some/other/path')

        self.assertEqual(tree2.get_directory('/some/other/path'), None)
        self.assertEqual(
            self.tree.get_root_directory_id(),
            tree2.get_root_directory_id())


class DummyBagStore(object):

    def __init__(self):
        self._bags = {}
        self._prev_id = 0

    def reserve_bag_id(self):
        self._prev_id += 1
        return self._prev_id

    def put_bag(self, bag):
        self._bags[bag.get_id()] = bag

    def has_bag(self, bag_id):
        return bag_id in self._bags

    def get_bag(self, bag_id):
        return self._bags[bag_id]
