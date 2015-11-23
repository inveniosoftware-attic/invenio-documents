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

"""Modules that simplifies management of file URIs stored in metadata.

Invenio-Documents is an integration layer between ``pyfilesystem``
and ``Invenio-Records`` libraries. It handles URIs stored in JSON metadata
specified using ``jsonpointer``.

Documents proxy following operations:

- `open`: for working with file handler.
- `setcontents`: given a source file write its content.
- `move`, `copy`, `remove`: simple proxies for standard file operations
  while keeping the stored URI updated.

Initialization
--------------

First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> from flask_cli import FlaskCLI
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> ext_cli = FlaskCLI(app)

You initialize Documents like a normal Flask extension, however
Invenio-Documents depends on Invenio-Records which also depends on
Invenio-DB so you need to initialize following extensions:

>>> from invenio_db import InvenioDB
>>> from invenio_records import InvenioRecords
>>> from invenio_documents import InvenioDocuments
>>> ext_db = InvenioDB(app)
>>> ext_records = InvenioRecords(app)
>>> ext_documents = InvenioDocuments(app)

In order for the following examples to work, you need to work
within an Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and
tables (note, in this example we use an in-memory SQLite
database):

>>> from invenio_db import db
>>> db.create_all()

Document
--------

Document provides easy access to a file handler stored as URI
inside a record metadata.

The example will work with following metadata record:

>>> from invenio_records.api import Record
>>> record = Record.create(
... {'title': 'Test', 'files': [{'uri': '/tmp/hello.txt'}]})


Creating Documents
~~~~~~~~~~~~~~~~~~

First we need the pointer to URI stored in the metadata.

>>> uri_pointer = '/files/0/uri'

With given the ``uri_pointer`` we can instantiate a ``Document``
class and write something to it.

>>> from invenio_documents.api import Document
>>> document = Document(record, uri_pointer)
>>> hello = document.open('wb+')
>>> assert hello.write(b'Hello world!') == 12
>>> hello.close()
>>> assert open('/tmp/hello.txt').read() == 'Hello world!'

Copying Documents
~~~~~~~~~~~~~~~~~

You can simply copy the file by providing destination URI that can
be handled by ``pyfilesystem`` library. The ``copy`` method will
return a JSON patch with new destination of the file that can be
applied to original record metadata.

>>> import os
>>> patch = document.copy('/tmp/hello_copy.txt')
>>> assert os.path.exists('/tmp/hello_copy.txt')
>>> record_copy = record.patch(patch).commit()
>>> document_copy = Document(record_copy, uri_pointer)
>>> assert document_copy.uri == '/tmp/hello_copy.txt'

Moving Documents
~~~~~~~~~~~~~~~~

It is preferable to use ``copy`` method instead of ``move``
because it is easier to recover for filesystem errors without
modifying record metadata.

>>> document_copy.move('/tmp/hello_move.txt')
>>> assert document_copy.uri == '/tmp/hello_move.txt'
>>> assert not os.path.exists('/tmp/hello_copy.txt')
>>> assert os.path.exists('/tmp/hello_move.txt')
>>> record_copy['files'][0]['uri']
'/tmp/hello_move.txt'

Removing Documents
~~~~~~~~~~~~~~~~~~

>>> document_copy.remove(force=True)
>>> record_copy['files'][0]['uri']
>>> assert not os.path.exists('/tmp/hello_move.txt')
>>> os.remove('/tmp/hello.txt')

"""

from __future__ import absolute_import, print_function

from .api import Document
from .ext import InvenioDocuments
from .version import __version__

__all__ = ('__version__', 'Document', 'InvenioDocuments')
