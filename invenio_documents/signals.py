# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Define signals used in Document API."""

from blinker import Namespace

_signals = Namespace()

before_document_insert = _signals.signal('before-document-insert')
"""Signal sent before a document is inserted.

Example subscriber

.. code-block:: python

    def listener(sender, *args, **kwargs):
        sender['key'] = sum(args)

    from invenio_documents.signals import before_document_insert

    before_document_insert.connect(
        listener
    )
"""

after_document_insert = _signals.signal('before-document-insert')
"""Signal sent after a document is inserted.

.. note::
    No modification are allowed on document object.
"""

before_document_update = _signals.signal('before-document-update')
"""Signal sent before a document is update."""

after_document_update = _signals.signal('before-document-update')
"""Signal sent after a document is updated."""

document_before_content_set = _signals.signal(
    'document-before-content-set')
"""
This signal is send right before data are written to the document.
"""

document_after_content_set = _signals.signal(
    'document-after-content-set')
"""
This signal is send right after data are written to the document.
"""

document_before_file_delete = _signals.signal(
    'document-before-file-delete')
"""
This signal is send right before data are deleted from filesystem.
"""
