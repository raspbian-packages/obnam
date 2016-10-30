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

import obnamlib


_algorithm_list = [
    ('md5', obnamlib.REPO_FILE_MD5, hashlib.md5),
    ('sha224', obnamlib.REPO_FILE_SHA224, hashlib.sha224),
    ('sha256', obnamlib.REPO_FILE_SHA256, hashlib.sha256),
    ('sha384', obnamlib.REPO_FILE_SHA384, hashlib.sha384),
    ('sha512', obnamlib.REPO_FILE_SHA512, hashlib.sha512),
]


checksum_algorithms = [_name for _name, _, _ in _algorithm_list]


def get_checksum_algorithm(wanted):
    for name, _, func in _algorithm_list:
        if wanted == name:
            return func()
    raise UnknownChecksumAlgorithm(algorithm=wanted)


def get_checksum_algorithm_name(wanted_key):
    for name, key, _ in _algorithm_list:
        if key == wanted_key:
            return name
    raise UnknownChecksumAlgorithm(
        algorithm=obnamlib.repo_key_name(wanted_key))


def get_checksum_algorithm_key(wanted_name):
    for name, key, _ in _algorithm_list:
        if name == wanted_name:
            return key
    raise UnknownChecksumAlgorithm(algorithm=wanted_name)


class UnknownChecksumAlgorithm(obnamlib.ObnamError):

    msg = 'Unknown checksum algorithm {algorithm}.'
