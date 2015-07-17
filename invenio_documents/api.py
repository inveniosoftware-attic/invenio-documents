# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Define document API.

Following example shows how to handle documents metadata::

    >>> from flask import g
    >>> from invenio.base.factory import create_app
    >>> app = create_app()
    >>> ctx = app.test_request_context()
    >>> ctx.push()
    >>> from invenio_documents import api
    >>> d = api.Document.create({'title': 'Title 1'})
    >>> d['title']
    'Title 1'
    >>> d['creator']
    0
    >>> d['title'] = 'New Title 1'
    >>> d = d.update()
    >>> api.Document.get_document(d['_id'])['title']
    'New Title 1'
    >>> ctx.pop()
"""

import uuid
from datetime import datetime

import fs
import six
from flask import current_app
from fs.opener import opener
from jsonschema import validate

from invenio.base.utils import toposort_send
from invenio.ext.sqlalchemy import db
from invenio.utils.datastructures import SmartDict

from . import errors, signals
from .models import Document as DocumentMetadata


class Document(SmartDict):

    """Represent a document object."""

    def __init__(self, data, model=None):
        self.model = model
        super(Document, self).__init__(data)

    @classmethod
    def create(cls, data, schema=None, **kwargs):
        db.session.begin(subtransactions=True)
        try:
            data.setdefault('_id', str(uuid.uuid4()))
            data.setdefault('creation_date', datetime.now().isoformat())

            document = cls(data)

            from invenio.modules.jsonalchemy.registry import functions
            list(functions('documentext'))

            toposort_send(signals.before_document_insert, document)

            if schema is not None:
                validate(document, schema)

            model = DocumentMetadata(id=document['_id'], json=dict(document))
            db.session.add(model)
            db.session.commit()

            document.model = model

            toposort_send(signals.after_document_insert, document)
            return document
        except Exception:
            current_app.logger.exception("Problem creating a document.")
            db.session.rollback()
            raise

    @classmethod
    def get_document(cls, uuid, include_deleted=False):
        """Returns document instance identified by UUID.

        Find existing document::

            >>> from flask import g
            >>> from invenio.base.factory import create_app
            >>> app = create_app()
            >>> ctx = app.test_request_context()
            >>> ctx.push()
            >>> from invenio_document import api
            >>> d = api.Document.create({'title': 'Title 1'})
            >>> e = api.Document.get_document(d['_id'])

        If you try to find deleted document you will get an exception::

            >>> e.delete()
            >>> api.Document.get_document(d['_id'])
            Traceback (most recent call last):
             ...
            DeletedDocument

        and also if you try to find not existing document::

            >>> import uuid
            >>> api.Document.get_document(str(uuid.uuid4()))
            Traceback (most recent call last):
             ...
            DocumentNotFound
            >>> ctx.pop()


        :returns: a :class:`Document` instance.
        :raises: :class:`~.errors.DocumentNotFound`
            or :class:`~.errors.DeletedDocument`
        """
        try:
            model = DocumentMetadata.query.one(uuid)
            document = cls(model.json, model=model)

            document.setdefault('_id', model.id)
        except Exception:
            raise errors.DocumentNotFound

        if not include_deleted and document['deleted']:
            raise errors.DeletedDocument
        return document

    def commit(self):
        db.session.begin(subtransactions=True)
        try:
            toposort_send(signals.before_document_update, self)

            if self.model is None:
                self.model = DocumentMetadata.query.get(self['_id'])

            self.model.json = self.dumps()

            db.session.add(self.model)
            db.session.commit()

            toposort_send(signals.after_document_update, self)

            return self
        except Exception:
            db.session.rollback()
            raise

    def dumps(self, **kwargs):
        # FIXME add keywords filtering
        return dict(self)

    def update(self):
        """Update document object."""
        self['modification_date'] = datetime.now().isoformat()
        return self.commit()

    def setcontents(self, source, name, chunk_size=65536):
        """Create a new file from a string or file-like object.

        :note: All paths has to be absolute or specified in full URI format.

        :param data: .
        :param name: File URI or filename generator taking `self` as argument.
        """

        if isinstance(source, six.string_types):
            self['source'] = source
            f = opener.open(source, 'rb')
        else:
            f = source

        if callable(name):
            name = name(self)
        else:
            name = fs.path.abspath(name)

        signals.document_before_content_set.send(self, name=name)

        if self.get('source', '') != name:
            data = f.read()
            _fs, filename = opener.parse(name)
            _fs.setcontents(filename, data, chunk_size)
            _fs.close()

        signals.document_after_content_set.send(self, name=name)

        if hasattr(f, 'close'):
            f.close()

        self['uri'] = name
        self.commit()

    def open(self, mode='r', **kwargs):
        """Open a the 'uri' as a file-like object."""
        _fs, filename = opener.parse(self['uri'])
        return _fs.open(filename, mode=mode, **kwargs)

    def delete(self, force=False):
        """Deletes the instance of document.

        :param force: If it is True then the document is deleted including
            attached files and metadata.
        """

        self['deleted'] = True

        if force and self.get('uri') is not None:
            signals.document_before_file_delete.send(self)
            fs, filename = opener.parse(self['uri'])
            fs.remove(filename)
            self['uri'] = None

        self.commit()
