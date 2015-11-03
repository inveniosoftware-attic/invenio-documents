# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Implement the API for document management."""

from __future__ import absolute_import, print_function

from collections import namedtuple

import jsonpointer
import six
from fs.opener import opener
from fs.utils import copyfile, movefile


class Document(namedtuple('Document', ('record', 'pointer'))):
    """Represent a file in record object."""

    __slots__ = ()  # keep the memory footprint for wrapper class low

    @property
    def uri(self):
        """Read uri from given record."""
        return jsonpointer.resolve_pointer(self.record, self.pointer)

    @uri.setter
    def uri(self, value):
        """Set new uri value in record.

        It will not change the location of the underlying file!
        """
        jsonpointer.set_pointer(self.record, self.pointer, value)

    def open(self, mode='r', **kwargs):
        """Open file ``uri`` under the pointer."""
        _fs, filename = opener.parse(self.uri)
        return _fs.open(filename, mode=mode, **kwargs)

    def move(self, dst, **kwargs):
        """Move file to a new destination and update ``uri``."""
        _fs, filename = opener.parse(self.uri)
        _fs_dst, filename_dst = opener.parse(dst)
        movefile(_fs, filename, _fs_dst, filename_dst, **kwargs)
        self.uri = dst

    def copy(self, dst, **kwargs):
        """Copy file to a new destination.

        Returns JSON Patch with proposed change pointing to new copy.
        """
        _fs, filename = opener.parse(self.uri)
        _fs_dst, filename_dst = opener.parse(dst)
        copyfile(_fs, filename, _fs_dst, filename_dst, **kwargs)
        return [{'op': 'replace', 'path': self.pointer, 'value': dst}]

    def setcontents(self, source, **kwargs):
        """Create a new file from a string or file-like object."""
        if isinstance(source, six.string_types):
            _file = opener.open(source, 'rb')
        else:
            _file = source

        # signals.document_before_content_set.send(self)

        data = _file.read()
        _fs, filename = opener.parse(self.uri)
        _fs.setcontents(filename, data, **kwargs)
        _fs.close()

        # signals.document_after_content_set.send(self)

        if isinstance(source, six.string_types) and hasattr(_file, 'close'):
            _file.close()

    def remove(self, force=False):
        """Remove file reference from record.

        If force is True it removes the file from filesystem
        """
        if force:
            _fs, filename = opener.parse(self.uri)
            _fs.remove(filename)
        self.uri = None
