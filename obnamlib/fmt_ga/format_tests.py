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


import shutil
import tempfile
import time

import obnamlib


class RepositoryFormatGATests(obnamlib.RepositoryInterfaceTests):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        fs = obnamlib.LocalFS(self.tempdir)
        self.hooks = obnamlib.HookManager()

        repo_factory = obnamlib.RepositoryFactory()
        repo_factory.setup_hooks(self.hooks)

        self.repo = obnamlib.RepositoryFormatGA(
            hooks=self.hooks,
            current_time=time.time,
            dir_bag_size=1,
            dir_cache_size=0)
        self.repo.set_fs(fs)

    def tearDown(self):
        shutil.rmtree(self.tempdir)
