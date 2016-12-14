{
    'name': 'Odoo Openstack Storage',
    'version': '9.0.1.0.0',
    'author': 'Danny Adair <danny@catalyst.net.nz>',
    'website': 'https://catalyst.net.nz/',
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': """Store files in Openstack object storage containers instead of file system directories.""",
    'description': """
        This module allows you to switch file storage of your Odoo app server(s) from the
        file system to the Openstack object storage.
    """,
    'depends': ['base'],
    'external_dependencies': {
        'python': ['swiftclient'],
    },
    'installable': True
}