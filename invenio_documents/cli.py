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

"""Click command-line interface for document management."""

from __future__ import absolute_import, print_function

import json
import sys

import click
from flask_cli import with_appcontext
from invenio_records.api import Record

from .api import Document

__all__ = (
    'copy_document',
    'documents',
    'setcontents',
)


@click.group()
def documents():
    """Document management commands."""


@documents.command(name='cp')
@click.argument('destination')
@click.option('-i', '--identifier')
@click.option('-p', '--pointer')
@with_appcontext
def copy_document(destination, identifier, pointer):
    """Copy file to a new destination."""
    record = Record.get_record(identifier)
    click.echo(json.dumps(
        Document(record, pointer).copy(destination)
    ))


@documents.command()
@click.argument('source', type=click.File('rb'), default=sys.stdin)
@click.option('-i', '--identifier')
@click.option('-p', '--pointer')
@with_appcontext
def setcontents(source, identifier, pointer):
    """Patch existing bibliographic record."""
    record = Record.get_record(identifier)
    Document(record, pointer).setcontents(source)
