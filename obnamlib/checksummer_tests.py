# Copyright 2016  Lars Wirzenius
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


class TestGetChecksummer(unittest.TestCase):

    def test_knows_some_algorithms(self):
        self.assertEqual(type(obnamlib.checksum_algorithms), list)
        self.assertNotEqual(obnamlib.checksum_algorithms, [])

    def test_raises_error_if_algorithm_is_unknown(self):
        self.assertRaises(
            obnamlib.ObnamError, obnamlib.get_checksum_algorithm, 'unknown')

    def test_finds_name_from_file_key_for_sha512(self):
        self.assertEqual(
            obnamlib.get_checksum_algorithm_name(obnamlib.REPO_FILE_SHA512),
            'sha512')

    def test_raises_error_if_algorithm_name_is_unknown_for_key(self):
        self.assertRaises(
            obnamlib.ObnamError,
            obnamlib.get_checksum_algorithm_name, -1)

    def test_finds_file_key_from_name_for_sha512(self):
        self.assertEqual(
            obnamlib.get_checksum_algorithm_key('sha512'),
            obnamlib.REPO_FILE_SHA512)

    def test_raises_error_if_algorithm_key_is_unknown_for_name(self):
        self.assertRaises(
            obnamlib.ObnamError,
            obnamlib.get_checksum_algorithm_key, 'unknown')

    def test_returns_working_sha512(self):
        summer = obnamlib.get_checksum_algorithm('sha512')
        summer.update('hello, world')
        self.assertEqual(
            summer.hexdigest(),
            '8710339dcb6814d0d9d2290ef422285c9322b7163951f9a0ca8f883d3305286f'
            '44139aa374848e4174f5aada663027e4548637b6d19894aec4fb6c46a139fbf9')

    def test_every_algorithm_has_right_api(self):
        for name in obnamlib.checksum_algorithms:
            summer = obnamlib.get_checksum_algorithm(name)
            summer.update('hello, world')

            digest = summer.hexdigest()
            self.assertEqual(type(digest), str)
            self.assertNotEqual(digest, '')

            hexdigest = summer.hexdigest()
            self.assertEqual(type(hexdigest), str)
            self.assertNotEqual(hexdigest, '')
            for c in hexdigest:
                self.assertTrue(c in '0123456789abcdef')
