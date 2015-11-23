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


"""Module tests."""

from __future__ import absolute_import, print_function

import os

from click.testing import CliRunner
from flask import Flask
from flask_cli import FlaskCLI, ScriptInfo
from invenio_records import Record

from invenio_documents import Document, InvenioDocuments
from invenio_documents.cli import documents as cmd


def test_version():
    """Test version import."""
    from invenio_documents import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    FlaskCLI(app)
    ext = InvenioDocuments(app)
    assert 'invenio-documents' in app.extensions

    app = Flask('testapp')
    FlaskCLI(app)
    ext = InvenioDocuments()
    assert 'invenio-documents' not in app.extensions
    ext.init_app(app)
    assert 'invenio-documents' in app.extensions


def test_api(app, tmpdir):
    """Test view."""
    hello = tmpdir.join('hello.txt')
    hello.write('Hello world!')

    bye = tmpdir.join('bye.txt')
    bye.write('Bye bye!')

    with app.app_context():
        record = Record.create({'title': 'Greetings',
                                'document': hello.strpath})
        document = Document(record, '/document')

        assert document.open().read() == hello.read()

        # Change document uri
        document.uri = bye.strpath
        assert record['document'] == bye.strpath
        assert document.open().read() == bye.read()

        # Move bye.txt to done.txt
        done = tmpdir.join('done.txt')
        document.move(os.path.abspath(done.strpath))
        assert document.uri == done.strpath
        assert record['document'] == done.strpath
        assert 'Bye bye!' == document.open().read()

        # Copy done.txt to copy.txt
        copy = tmpdir.join('copy.txt')
        copy_patch = document.copy(copy.strpath)
        assert document.uri == done.strpath
        assert copy_patch[0]['value'] == copy.strpath
        assert done.read() == copy.read()

        # Set hello.txt to done.txt
        document.setcontents(hello)
        assert document.open().read() == hello.read()
        assert done.read() == hello.read()

        # Set copy.txt to done.txt via path
        document.setcontents(copy.strpath)
        assert document.open().read() == copy.read()
        assert done.read() == copy.read()

        # Remove done.txt from metadata
        document.remove()
        assert document.uri is None
        assert os.path.exists(done.strpath)

        # Remove copy.txt from filesystem
        assert os.path.exists(copy.strpath)
        document.uri = copy.strpath
        document.remove(force=True)
        assert document.uri is None
        assert not os.path.exists(copy.strpath)


def test_cli(app):
    """Test cli commands."""
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)

    with runner.isolated_filesystem():
        bye_strpath = os.path.abspath('bye.txt')
        hello_strpath = os.path.abspath('hello.txt')
        copy_strpath = os.path.abspath('copy.txt')

        with open(hello_strpath, 'wb') as f:
            f.write(u'Hello world!'.encode('utf-8'))

        assert os.path.exists(hello_strpath)

        with open(bye_strpath, 'wb') as f:
            f.write(u'Bye bye'.encode('utf-8'))

        with app.app_context():
            record = Record.create({'title': 'Greetings',
                                    'document': hello_strpath})
            record_id = record.id

        result = runner.invoke(
            cmd, ['cp', '-i', record_id, '-p', '/document', copy_strpath],
            obj=script_info
        )
        assert result.exit_code == 0
        assert os.path.exists(copy_strpath)
        assert open(copy_strpath).read() == open(hello_strpath).read()

        result = runner.invoke(
            cmd,
            ['setcontents', '-i', record_id, '-p', '/document', bye_strpath],
            obj=script_info
        )
        assert result.exit_code == 0
        assert open(hello_strpath).read() == open(bye_strpath).read()
