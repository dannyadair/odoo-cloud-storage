# -*- coding: utf-8 -*-
# © 2016 Catalyst IT (https://catalyst.net.nz/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from contextlib import closing
import logging
import os

import openerp
from openerp.service.db import _drop_conn, exp_list

from connect import get_s3_bucket


_logger = logging.getLogger(__name__)


def sync_buckets(source_bucket, target_bucket, may_delete=None):
    """Sync files between two buckets"""
    _logger.info('Copying files from {} to {}'.format(source_bucket, target_bucket))

    for key in source_bucket:
        if key not in target_bucket:
            key.copy(target_bucket, key)

    if may_delete is not None:
        # Delete files in the target bucket that are not in the source bucket
        _logger.info('Deleting files in {} that are not in {}'.format(target_bucket, source_bucket))
        for key in target_bucket:
            if key not in source_bucket:
                key.delete()


def delete_bucket(bucket):
    _logger.info('Deleting {}'.format(bucket))
    for key in bucket:
        key.delete()
    bucket.delete()


def exp_duplicate_database(db_original_name, db_name):
    """Monkeypatched to duplicate cloud container instead of filesystem directory"""
    _logger.info('Duplicate database `%s` to `%s`.', db_original_name, db_name)
    openerp.sql_db.close_db(db_original_name)
    db = openerp.sql_db.db_connect('postgres')
    with closing(db.cursor()) as cr:
        cr.autocommit(True)     # avoid transaction block
        _drop_conn(cr, db_original_name)
        cr.execute("""CREATE DATABASE "%s" ENCODING 'unicode' TEMPLATE "%s" """ % (db_name, db_original_name))

    # Determine storage "on foot" with raw SQL
    db = openerp.sql_db.db_connect(db_original_name)
    with closing(db.cursor()) as cr:
        cr.execute("""SELECT value FROM ir_config_parameter WHERE key='ir_attachment.location""")
        result = cr.dictfetchone()
        storage = result and result['value'] or 'file'

    if storage.startswith('http://') or storage.startswith('https://') or storage.startwith('s3://'):
        # Copy bucket objects
        source_bucket_url = storage + '-' + db_original_name.lower()
        source_bucket = get_s3_bucket(source_bucket_url, autocreate=False)
        target_bucket_url = storage + '-' + db_name.lower()
        target_bucket = get_s3_bucket(target_bucket_url, autocreate=False)
        if source_bucket and not target_bucket:
            target_bucket = get_s3_bucket(target_bucket_url)
            sync_buckets(source_bucket, target_bucket)
    else:
        # File system copy as per original Odoo
        from_fs = openerp.tools.config.filestore(db_original_name)
        to_fs = openerp.tools.config.filestore(db_name)
        if os.path.exists(from_fs) and not os.path.exists(to_fs):
            shutil.copytree(from_fs, to_fs)
    return True

openerp.service.db.exp_duplicate_database = exp_duplicate_database


def exp_drop(db_name):
    """Monkeypatched to delete cloud container instead of filesystem directory"""
    if db_name not in exp_list(True):
        return False
    
    # Determine storage "on foot" with raw SQL (while the database is still there)
    db = openerp.sql_db.db_connect(db_name)
    with closing(db.cursor()) as cr:
        cr.execute("""SELECT value FROM ir_config_parameter WHERE key='ir_attachment.location""")
        result = cr.dictfetchone()
        storage = result and result['value'] or 'file'
    
    openerp.modules.registry.RegistryManager.delete(db_name)
    openerp.sql_db.close_db(db_name)

    db = openerp.sql_db.db_connect('postgres')
    with closing(db.cursor()) as cr:
        cr.autocommit(True) # avoid transaction block
        _drop_conn(cr, db_name)

        try:
            cr.execute('DROP DATABASE "%s"' % db_name)
        except Exception, e:
            _logger.error('DROP DB: %s failed:\n%s', db_name, e)
            raise Exception("Couldn't drop database %s: %s" % (db_name, e))
        else:
            _logger.info('DROP DB: %s', db_name)

    if storage.startswith('http://') or storage.startswith('https://') or storage.startwith('s3://'):
        # Delete entire bucket
        bucket_url = storage + '-' + db_name.lower()
        bucket = get_s3_bucket(bucket_url, autocreate=False)
        if bucket:
            delete_bucket(bucket)
    else:
        fs = openerp.tools.config.filestore(db_name)
        if os.path.exists(fs):
            shutil.rmtree(fs)
        return True

openerp.service.db.exp_drop = exp_drop