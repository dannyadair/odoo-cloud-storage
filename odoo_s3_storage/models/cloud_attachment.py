# -*- coding: utf-8 -*-
# © 2016 Catalyst IT (https://catalyst.net.nz/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import hashlib
import os

import openerp
from openerp.osv import osv

from openerp.addons.odoo_cloud_storage.s3.connect import get_s3_bucket


class S3Attachment(osv.osv):
    """Read/write attachments from/to cloud storage instead of the file system"""
    _inherit = 'ir.attachment'

    def _get_path(self, cr, uid, store_fname):
        """Support retro compatibility"""
        retro_fname = '{}/{}'.format(store_fname[:3], store_fname)
        full_path = super(S3Attachment, self)._full_path(cr, uid, retro_fname)
        if os.path.isfile(full_path):
            return retro_fname
        return '{}/{}'.format(store_fname[:2], store_fname)

    def _file_read(self, cr, uid, fname, bin_size=False):
        storage = self._storage(cr, uid)
        if storage.startswith('http://') or storage.startswith('https://') or storage.startwith('s3://'):
            s3_bucket_url = storage + '-' + cr.dbname.lower()
            s3_bucket = get_s3_bucket(s3_bucket_url)
            s3_key = s3_bucket.get_key(fname)
            if s3_key is None:
                # Fall back to file system (e.g. migration still in progress)
                fname = self._get_path(cr, uid, fname)
                try:
                    return super(S3Attachment, self)._file_read(cr, uid, fname, bin_size=False)
                except OSError:
                    # File not found
                    return False
            else:
                return base64.b64encode(s3_key.get_contents_as_string())
        else:
            return super(S3Attachment, self)._file_read(cr, uid, fname, bin_size=False)

    if openerp.release.version == '8.0':
        def _file_write(self, cr, uid, value):
            storage = self._storage(cr, uid)
            if storage.startswith('http://') or storage.startswith('https://') or storage.startwith('s3://'):
                s3_bucket_url = storage + '-' + cr.dbname.lower()
                s3_bucket = get_s3_bucket(s3_bucket_url)
                bin_value = value.decode('base64')
                fname = hashlib.sha1(bin_value).hexdigest()
    
                s3_key = s3_bucket.get_key(fname)
                if s3_key is None:
                    s3_key = s3_bucket.new_key(fname)
    
                s3_key.set_contents_from_string(bin_value)
            else:
                fname = super(S3Attachment, self)._file_write(cr, uid, value)
    
            return fname
    else:
        # Version 9 added checksum
        def _file_write(self, cr, uid, value, checksum):
            storage = self._storage(cr, uid)
            if storage.startswith('http://') or storage.startswith('https://') or storage.startwith('s3://'):
                s3_bucket_url = storage + '-' + cr.dbname.lower()
                s3_bucket = get_s3_bucket(s3_bucket_url)
                bin_value = value.decode('base64')
                fname = hashlib.sha1(bin_value).hexdigest()
    
                s3_key = s3_bucket.get_key(fname)
                if s3_key is None:
                    s3_key = s3_bucket.new_key(fname)
    
                s3_key.set_contents_from_string(bin_value)
            else:
                fname = super(S3Attachment, self)._file_write(cr, uid, value, checksum)
    
            return fname

    def _file_delete(self, cr, uid, fname):
        storage = self._storage(cr, uid)
        if storage.startswith('http://') or storage.startswith('https://') or storage.startwith('s3://'):
            # using SQL to include files hidden through unlink or due to record rules
            cr.execute("SELECT COUNT(*) FROM ir_attachment WHERE store_fname = %s", (fname,))
            count = cr.fetchone()[0]
            if not count:
                s3_bucket_url = storage + '-' + cr.dbname.lower()
                s3_bucket = get_s3_bucket(s3_bucket_url)
                s3_key = s3_bucket.get_key(fname)
                if s3_key is not None:
                    s3_bucket.delete_key(s3_key)
        else:
            return super(S3Attachment, self)._file_delete(cr, uid, fname)
