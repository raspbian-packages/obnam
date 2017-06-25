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


import os

import tracing

import obnamlib


class RepositoryFS(object):

    '''A wrapper around a VFS object, with calls to hooks.

    This is exactly like a full VFS implementation, but it only wraps
    another instance and provides read/write hooks. The hooks are
    intended for filtering data read from or written to the
    repository, which is then used to implement things like
    compression and encryption.

    FIXME: Some day this might offer only the subset of the full VFS
    that is necessary for repository access, to allow easier
    implementation of new repository storage methods.

    '''

    def __init__(self, repo, fs, hooks):
        self.repo = repo
        self.fs = fs
        self.hooks = hooks

    def _get_toplevel(self, filename):
        parts = filename.split(os.sep)
        if len(parts) >= 1:
            return parts[0]
        else:  # pragma: no cover
            raise ToplevelIsFileError(filename=filename)

    def exists(self, filename):
        return self.fs.exists(filename)

    def lock(self, lockname):
        return self.fs.lock(lockname)

    def unlock(self, lockname):
        return self.fs.unlock(lockname)

    def lstat(self, lockname):
        return self.fs.lstat(lockname)

    def scan_tree(self, dirname):
        return self.fs.scan_tree(dirname)

    def remove(self, filename):
        return self.fs.remove(filename)

    def mkdir(self, dirname):
        return self.fs.mkdir(dirname)

    def makedirs(self, dirname):
        return self.fs.makedirs(dirname)

    def rmdir(self, dirname):
        return self.fs.rmdir(dirname)

    def listdir(self, dirname):
        return self.fs.listdir(dirname)

    def isdir(self, dirname):
        return self.fs.isdir(dirname)

    def rename(self, old_name, new_name):
        return self.fs.rename(old_name, new_name)

    def cat(self, filename, runfilters=True):
        data = self.fs.cat(filename)
        if not runfilters:  # pragma: no cover
            return data
        toplevel = self._get_toplevel(filename)
        return self.hooks.filter_read('repository-data', data,
                                      repo=self.repo, toplevel=toplevel)

    def create_and_init_toplevel(self, filename):
        tracing.trace('filename=%s', filename)
        toplevel = self._get_toplevel(filename)
        if not self.fs.exists(toplevel):
            self.fs.mkdir(toplevel)
            self.hooks.call('repository-toplevel-init', self.repo, toplevel)

    def write_file(self, filename, data, runfilters=True):
        toplevel = self._get_toplevel(filename)
        if runfilters:
            data = self.hooks.filter_write('repository-data', data,
                                           repo=self.repo, toplevel=toplevel)
        self.fs.write_file(filename, data)

    def overwrite_file(self, filename, data, runfilters=True):
        toplevel = self._get_toplevel(filename)
        if runfilters:
            data = self.hooks.filter_write('repository-data', data,
                                           repo=self.repo, toplevel=toplevel)
        self.fs.overwrite_file(filename, data)


class ToplevelIsFileError(obnamlib.ObnamError):

    msg = 'File at repository root: {filename}'
