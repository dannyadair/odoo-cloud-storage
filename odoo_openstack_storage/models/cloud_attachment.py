import base64
import hashlib
import json
import os
import logging

import openerp
from openerp.osv import osv
from openerp import SUPERUSER_ID

from openerp.addons.odoo_openstack_storage.swift.connect import SwiftClient


_logger = logging.getLogger(__name__)


class OpenstackAttachment(osv.osv):
    """Read/Write/Delete attachments in Openstack Object storage instead of the file system"""
    _inherit = 'ir.attachment'

    def _get_path(self, cr, uid, store_fname):
        """Support retro compatibility"""
        retro_fname = '{}/{}'.format(store_fname[:3], store_fname)
        full_path = super(OpenstackAttachment, self)._full_path(cr, uid, retro_fname)
        if os.path.isfile(full_path):
            return retro_fname
        return '{}/{}'.format(store_fname[:2], store_fname)

    def _storage_config(self, cr, uid, context=None):
        config_param = 'ir_attachment.location.openstack'
        config = self.pool['ir.config_parameter'].get_param(
            cr,
            SUPERUSER_ID,
            config_param,
            'file'
        )
        if config:
            config = json.loads(config)
            # Make container name unique for the particular database
            config['container_name'] = '{}-{}'.format(
                config['container_prefix'],
                cr.dbname.lower()
            )
            return config
        else:
            raise ValueError(
                'System parameter "{}" not configured'.format(config_param)
            )

    def _file_read(self, cr, uid, fname, bin_size=False):
        storage = self._storage(cr, uid)
        if storage == 'openstack':
            config_params = self._storage_config(cr, uid)
            conn = SwiftClient(config_params)
            cloud_object = conn.get_object(config_params['container_name'], fname)
            if cloud_object is None:
                # Fall back to file system (e.g. migration still in progress)
                fname = self._get_path(cr, uid, fname)
                try:
                    return super(
                        OpenstackAttachment,
                        self
                    )._file_read(cr, uid, fname, bin_size=False)
                except OSError:
                    # File not found
                    return False
            else:
                return base64.b64encode(''.join(cloud_object[1]))
        else:
            _logger.info(
                'Failed to find file in object storage - failing back to filesystem'
            )
            return super(
                OpenstackAttachment,
                self
            )._file_read(cr, uid, fname, bin_size=False)

    if openerp.release.version == '8.0':
        def _file_write(self, cr, uid, value):
            storage = self._storage(cr, uid)
            if storage == 'openstack':
                config_params = self._storage_config(cr, uid)
                conn = SwiftClient(config_params)
                bin_value = value.decode('base64')
                fname = hashlib.sha1(bin_value).hexdigest()
                conn.put_object(config_params['container_name'], fname, bin_value)

            else:
                fname = super(OpenstackAttachment, self)._file_write(cr, uid, value)

            return fname

    else:
        # Version 9 added checklsum
        def _file_write(self, cr, uid, value, checksum):
            storage = self._storage(cr, uid)
            if storage == 'openstack':
                config_params = self._storage_config(cr, uid)
                conn = SwiftClient(config_params)
                bin_value = value.decode('base64')
                fname = hashlib.sha1(bin_value).hexdigest()
                conn.put_object(config_params['container_name'], fname, bin_value)

            else:
                fname = super(OpenstackAttachment, self)._file_write(cr, uid, value, checksum)

            return fname

    def _file_delete(self, cr, uid, fname):
        storage = self._storage(cr, uid)
        if storage == 'openstack':
            # using SQL to include files hidden through unlink or due to record rules
            cr.execute("SELECT COUNT(*) FROM ir_attachment WHERE store_fname = %s", (fname,))
            count = cr.fetchone()[0]
            if not count:
                config_params = self._storage_config(cr, uid)
                conn = SwiftClient(config_params)
                conn.delete_object(config_params['container_name'], fname)
        else:
            return super(OpenstackAttachment, self)._file_delete(cr, uid, fname)
