# Copyright 2015-2016  Lars Wirzenius
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


class BagTests(unittest.TestCase):

    def test_has_no_bag_id_initially(self):
        bag = obnamlib.Bag()
        self.assertEqual(bag.get_id(), None)

    def test_sets_bag_id_to_integer(self):
        bag = obnamlib.Bag()
        bag.set_id(123)
        self.assertEqual(bag.get_id(), 123)

    def test_sets_bag_id_to_string(self):
        bag = obnamlib.Bag()
        bag.set_id('well-known')
        self.assertEqual(bag.get_id(), 'well-known')

    def test_is_empty_initially(self):
        bag = obnamlib.Bag()
        self.assertEqual(len(bag), 0)

    def test_has_no_bytes_initially(self):
        bag = obnamlib.Bag()
        self.assertEqual(bag.get_bytes(), 0)

    def test_raises_error_if_appending_blob_without_id_being_set(self):
        bag = obnamlib.Bag()
        self.assertRaises(
            obnamlib.BagIdNotSetError,
            bag.append, 'blob')

    def test_appends_a_blob(self):
        blob = 'foo'
        bag = obnamlib.Bag()
        bag.set_id(1)
        bag.append(blob)
        self.assertEqual(len(bag), 1)
        self.assertEqual(bag.get_bytes(), len(blob))
        self.assertEqual(bag[0], blob)

    def test_appending_returns_object_id(self):
        bag = obnamlib.Bag()
        bag.set_id(1)
        object_id = bag.append('foo')
        self.assertEqual(object_id, obnamlib.make_object_id(1, 0))

    def test_appending_returns_object_id_when_bag_id_is_a_string(self):
        bag = obnamlib.Bag()
        bag.set_id('well-known')
        object_id = bag.append('foo')
        self.assertEqual(object_id, obnamlib.make_object_id('well-known', 0))


class ObjectIdTests(unittest.TestCase):

    def test_round_trip_works(self):
        bag_id = 123
        object_index = 456
        object_id = obnamlib.make_object_id(bag_id, object_index)
        self.assertEqual(
            obnamlib.parse_object_id(object_id),
            (bag_id, object_index))
