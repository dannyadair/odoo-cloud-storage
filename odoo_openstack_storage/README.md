# Odoo Openstack Storage

Compatible with Odoo v8.0 and Odoo v9.0.

## Configuration
To switch from filesystem storage to Openstack storage, you will need to create two new system parameters.
One called "ir_attachment.location" and one called "ir_attachment.location.openstack".

* ir_attachment.location needs to be set to the value "openstack"
* ir_attachment.location.openstack needs to be of the form:
```
FILESTORE_ROOT = 'path/to/your/filestore/MyDatabase/'
OPENSTACK_AUTH = {
    'user': '',
    'key': '',
    'authurl': '',
    'tenant_name': '',
    'region_name': '',
    'container_prefix': ''
}
```

The "container_prefix" will be followed by "-yourdatabasename" (lowercase for DNS compliance)
When you duplicate a database, the corresponding objects will be copied into the new container.

## Requirements
[`python-swiftclient`](https://github.com/openstack/python-swiftclient) needs to be installed on your Odoo application server(s).

## Copyright / License
(C) 2016 [`Catalyst IT`](https://catalyst.net.nz/)
License [`AGPL-3.0 or later'](http://www.gnu.org/licenses/agpl.html)

## Credits
Written by:
* Danny W. Adair <danny@catalyst.net.nz>
* Chris Herrmann <chris.herrmann@catalyst.net.nz>

Inspired by [`Odoo-S3`](https://github.com/tvanesse/odoo-s3) (V9) by Thomas Vanesse <http://www.creo2.org>
which in turn was partly based on [`document_amazons3`](https://apps.odoo.com/apps/modules/7.0/document_amazons3/) (V7) by Hugo Santos <hugo.santos@factolibre.com>
