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


"""Minimal Flask application example for development.

Create database and tables:

.. code-block:: console

   $ cd examples
   $ flask -a app.py db init
   $ flask -a app.py db create

Create a record:

.. code-block:: console

   $ echo 'Hello world!' > /tmp/hello.txt
   $ echo '{"title": "Test", "files": [{"uri": "/tmp/hello.txt"}]}' > r.json
   $ flask -a app.py records create < r.json

Modify content of the file stored in record:

.. code-block:: console

   $ echo 'Bye bye!' | flask -a app documents setcontents -r 1 -p /files/0/uri
   $ cat /tmp/hello.txt
   Bye bye!

"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_celeryext import create_celery_app
from flask_cli import FlaskCLI
from invenio_db import InvenioDB
from invenio_records import InvenioRecords

from invenio_documents import InvenioDocuments

# Create Flask application
app = Flask(__name__)
app.config.update(
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND="memory",
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND="cache",
    SECRET_KEY="CHANGE_ME",
    SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
)

db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
if db_uri is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

FlaskCLI(app)
InvenioDB(app)
InvenioRecords(app)
InvenioDocuments(app)

celery = create_celery_app(app)
