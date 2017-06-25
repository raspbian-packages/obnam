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


import hashlib
import unittest

import obnamlib


class WholeFileCheckSummerTests(unittest.TestCase):

    def test_computes_nothing_if_repo_wants_no_checksum(self):
        summer = obnamlib.WholeFileCheckSummer(None)
        chunk = 'hello'
        summer.append_chunk(chunk, None)
        self.assertEqual(summer.get_checksum(), None)

    def test_computes_checksum_for_md5(self):
        summer = obnamlib.WholeFileCheckSummer(obnamlib.REPO_FILE_MD5)
        chunk = 'hello'
        chunk_id = None
        summer.append_chunk(chunk, chunk_id)
        self.assertEqual(
            summer.get_checksum().encode('hex'),
            '5d41402abc4b2a76b9719d911017c592')

    def test_computes_checksum_for_sha512(self):
        summer = obnamlib.WholeFileCheckSummer(obnamlib.REPO_FILE_SHA512)
        chunk = 'hello'
        chunk_id = '123'
        summer.append_chunk(chunk, chunk_id)

        expected = hashlib.sha512('{},{};'.format(len(chunk), chunk_id))

        self.assertEqual(summer.get_checksum(), expected.hexdigest())
