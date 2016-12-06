# Odoo S3 Storage

Compatible with Odoo v8.0 and Odoo v9.0.

## Configuration
To switch from filesystem storage to cloud storage, create a new system parameter with key "ir_attachment.location".
If you use Amazon Web Services S3, simply use the following format for the parameter value:

```
s3://key:secret@bucketprefix
```

If you use a non-Amazon S3-compatible cloud service, you can specify host and port of your API endpoint:

```
http[s]://key:secret@[host[:port]/]bucketprefix
```

The schema will determine the "is_secure" parameter for boto's S3Connection.

The actual bucket name will be your specified prefix followed by "-YourDatabaseName".
When you duplicate a database, the corresponding bucket objects will be copied into the new bucket.

## Requirements
[`boto`](https://github.com/boto/boto) needs to be installed on your Odoo application server(s).

## Copyright / License
(C) 2016 [`Catalyst IT`](https://catalyst.net.nz/)
License [`AGPL-3.0 or later'](http://www.gnu.org/licenses/agpl.html)

## Credits
Written by Danny W. Adair <danny@catalyst.net.nz>

Inspired by [`Odoo-S3`](https://github.com/tvanesse/odoo-s3) (V9) by Thomas Vanesse <http://www.creo2.org>
which in turn was partly based on [`document_amazons3`](https://apps.odoo.com/apps/modules/7.0/document_amazons3/) (V7) by Hugo Santos <hugo.santos@factolibre.com>
