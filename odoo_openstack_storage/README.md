# Odoo Openstack Storage

Compatible with Odoo v8.0 and Odoo v9.0.

## Configuration
To switch from filesystem storage to Openstack storage, you will need to create two new system parameters.
One called "ir_attachment.location" and one called "ir_attachment.location.openstack".

* ir_attachment.location needs to be set to the value "openstack"
* ir_attachment.location.openstack needs to be of the form:
```
{
    "user": "Your Openstack user",
    "key": "Api key",
    "authurl": "Auth url for your Openstack instance",
    "tenant_name": "Name of the tenant",
    "region_name": "Region",
    "container_prefix": "Prefix for the container"
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
