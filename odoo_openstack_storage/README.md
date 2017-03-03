# Odoo Openstack Storage

Compatible with Odoo v8.0 and Odoo v9.0.


## Set-up

#### 1 - Add System Parameters
System parameters tell the module to use the Openstack object storage instead of the
default file system storage.

 * The system parameters must be added. See [Configuration](#configuration)

#### 2 - Install Module
 * Add the 'odoo_openstack_storage' directory to your addons path
 * Update the module list
 * Install the module
 
**At this point Odoo will add any new files to the Openstack container but will fall back
to the file system if an existing file is not found there (yet) - see next steps.**

#### 3 - Add migrate_conf
Before the migration of existing files from the filesystem to Openstack object storage can be done
migration configs must be set up.

 * Create and configure 'migrate_conf.py'
 * Use the example file, 'migrate_conf.py.in' or see [Migration](#migration)
 
#### 4 - Run Migration
Migrating the existing files from the filesystem to Openstack object storage.

 * Ensuring that the config is correct, run swift.migrate.migrate_files_to_openstack()

## Configuration
To switch from filesystem storage to Openstack storage, you will need to create two new system parameters.
One called "ir_attachment.location" and one called "ir_attachment.location.openstack".

* ir_attachment.location must have the value "openstack"
* ir_attachment.location.openstack needs to be of the form:
```
{
    "user": "Your Openstack user",
    "key": "Api key",
    "authurl": "Auth url for your Openstack instance",
    "tenant_name": "Name of the tenant (project)",
    "region_name": "Region",
    "container_prefix": "Prefix for the container"
}
```

 * The "container_prefix" will be followed by "-yourdatabasename" (lowercase for DNS compliance)


## Migration
The option of migrating the filesystem is provided in migrate.py. This allows you to
upload your current filestore to your object-storage container. However, first the
configs must be set.

 * Configs set in 'migrate_conf.py'
 * An example file is given under the name 'migrate_conf.py.in'
```
DB_NAME = 'Database name'
DB_HOST = 'Database host name'
DB_PORT = 'Database port number'
DB_USER = 'Database user'
DB_PASSWORD = 'Database password'
FILESTORE_ROOT = 'path/to/your/filestore/MyDatabase/'
OPENSTACK_AUTH = {
    'user': 'Your Opentsack user',
    'key': 'Api key',
    'authurl': 'Auth url for your Openstack instance',
    'tenant_name': 'Name of the tenant (project)',
    'region_name': 'Region',
    'container_prefix': 'Prefix for the container'
}
```
 * Start the migration by calling the function 'migrate_files_to_openstack()'

 
## Duplicating and Dropping Databases
Dropping and duplicating database functionality is provided.

 * When the 'duplicate filesystem' option is selected, a new container will be created The name will have
 the container_prefix followed by '-newdatabasename' and objects copied to it from the original container

 * Upon dropping a database, the corresponding object storage container and its contents will be deleted

**Important:** There is an existing problem in Odoo where a timeout during database duplication will lead to an incomplete
filestore in the new copy. Because the object storage is likely to be slower than the local file system, it also more
likely that this is going to happen. You can manually run the 'duplicate_container' function in storage.py from the command line
where you will not get a time out. Patches welcome to make this asynchronous so it doesn't time out.


## Requirements
[`python-swiftclient`](https://github.com/openstack/python-swiftclient) (version 2.0.3) needs to be installed on your Odoo application server(s). 


## Copyright / License
(C) 2016 [`Catalyst IT`](https://catalyst.net.nz/)
License [`AGPL-3.0 or later'](http://www.gnu.org/licenses/agpl.html)


## Credits
Written by:
* Danny W. Adair <danny@catalyst.net.nz>
* Chris Herrmann <chris.herrmann@catalyst.net.nz>
