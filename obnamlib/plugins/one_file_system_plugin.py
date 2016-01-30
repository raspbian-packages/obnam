# Copyright (C) 2015  Lars Wirzenius
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


import logging

import obnamlib


class OneFileSystemPlugin(obnamlib.ObnamPlugin):

    def enable(self):
        backup_group = obnamlib.option_group['backup'] = 'Backing up'

        self.app.settings.boolean(
            ['one-file-system'],
            'exclude directories (and their subdirs) '
            'that are in a different filesystem',
            group=backup_group)

        self.app.hooks.add_callback('config-loaded', self.config_loaded)

    def config_loaded(self):
        if self.app.settings['one-file-system']:
            self.app.hooks.add_callback('backup-exclude', self.exclude)

    def exclude(self, **kwargs):
        st = kwargs['stat_result']
        root_metadata = kwargs['root_metadata']
        pathname = kwargs['pathname']
        exclude = kwargs['exclude']

        if st.st_dev != root_metadata.st_dev:
            logging.debug('Excluding (one-file-system): %s', pathname)
            exclude[0] = True
