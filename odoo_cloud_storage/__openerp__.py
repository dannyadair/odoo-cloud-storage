# -*- coding: utf-8 -*-
# 
#     Odoo Cloud Storage
#     Store files in cloud object storage containers instead of file system directories.
#     Copyright (C) 2016 Catalyst IT
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
# 
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

{
    'name': 'Odoo Cloud Storage',
    'version': '9.0.1.0.0',
    'author': 'Danny Adair <danny@catalyst.net.nz>',
    'website': 'https://catalyst.net.nz/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': """Store files in cloud object storage containers instead of file system directories.""",
    'description': """
        This module allows you to switch file storage of your Odoo app server(s) from the
        file system to cloud storage. It currently supports Amazon Web Services S3 or any
        other S3-compatible service. You'll need to install the Python library 'boto' on your
        app server(s) to use this module.
    """,
    'depends': ['base'],
    'external_dependencies': {
        'python': ['boto'],
    },
    'installable': True
}