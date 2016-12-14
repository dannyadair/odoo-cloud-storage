from contextlib import closing
import json
import logging
import os
import swiftclient

import openerp
from openerp.service.db import _drop_conn, exp_list

from connect import SwiftClient

_logger = logging.getLogger(__name__)


def duplicate_container(source_conn, target_conn, source_container_name, target_container_name):
    """Copy source container to a target container"""
    source_container = source_conn.get_container(
        container_name=source_container_name,
        full_listing=True
    )[1]
    for source_data in source_container:
        object_name = source_data['name']
        source_object = source_conn.get_object(
            source_container_name,
            object_name
        )
        target_conn.put_object(
            container_name=target_container_name,
            file_name=object_name,
            contents=source_object[1]
        )


def sync_containers(source_conn, target_conn, source_container_name, target_container_name):
    """Sync a target container with a source container

    If there exists objects in the source container that is not in the target
    container it is added. And if there exists an object in the target
    container that is not in the source container it is deleted from the
    target.
    """
    source_container = source_conn.get_container(
        container_name=source_container_name,
        full_listing=True
    )[1]
    for source_data in source_container:
        object_name = source_data['name']
        source_object = source_conn.get_object(
            source_container_name,
            object_name
        )
        # Check to see if the object is already in the target container
        target_object = target_conn.get_object(
            target_container_name,
            object_name
        )
        if target_object is None:
            target_conn.put_object(
                container_name=target_container_name,
                file_name=object_name,
                contents=source_object[1],
                autocreate_container=False
            )

    target_container = target_conn.get_container(
        container_name=target_container_name,
        full_listing=True
    )[1]
    for target_data in target_container:
        object_name = target_data['name']
        # Check if the object exists in the source container
        source_object = source_conn.get_object(
            source_container_name,
            object_name
        )
        if source_object is None:
            target_conn.delete_object(
                target_container_name,
                object_name
            )


# TODO: IMPLEMENT THIS PROPERLY USING LINGXIAN ADVICE
def delete_container(conn, container_name):
    """Delete container and all objects inside it"""
    for data in conn.get_container(container_name, full_listing=True)[1]:
        try:
            conn.delete_object(container_name, data['name'])
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason == 'Not Found':
                continue
            else:
                raise
    conn.delete_container(container_name)


def exp_duplicate_database(db_original_name, db_name, duplicate_filestore=True):
    """Monkeypatched to duplicate cloud container instead of filesystem directory"""
    _logger.info('Duplicate database `%s` to `%s`.', db_original_name, db_name)
    openerp.sql_db.close_db(db_original_name)
    db = openerp.sql_db.db_connect('postgres')
    with closing(db.cursor()) as cr:
        cr.autocommit(True)     # avoid transaction block
        _drop_conn(cr, db_original_name)
        cr.execute(
            """CREATE DATABASE "%s" ENCODING 'unicode' TEMPLATE "%s" """ % (
                db_name,
                db_original_name
            )
        )

    # Determine storage "on foot" with raw SQL
    db = openerp.sql_db.db_connect(db_original_name)
    with closing(db.cursor()) as cr:
        cr.execute(
            """SELECT value FROM ir_config_parameter WHERE key='ir_attachment.location'"""
        )
        result = cr.dictfetchone()
        storage = result and result['value'] or 'file'

    if duplicate_filestore:
        if storage == 'openstack':
            with closing(db.cursor()) as cr:
                cr.execute(
                    """SELECT value FROM ir_config_parameter WHERE key='ir_attachment.location.openstack'"""
                )
                result = cr.dictfetchone()
                config_params = result and json.loads(result['value'])

            # Copy container objects
            source_container_name = '{}-{}'.format(
                config_params['container_prefix'],
                db_original_name.lower()
            )
            source_conn = SwiftClient(config_params)
            source_container = source_conn.get_container(source_container_name)

            target_container_name = '{}-{}'.format(
                config_params['container_prefix'],
                db_name.lower()
            )
            target_conn = SwiftClient(config_params)
            target_container = target_conn.get_container(target_container_name)

            # Only copy if source bucket exists and target bucket does not
            if source_container and not target_container:
                _logger.info(
                    'Duplicate object storage container `%s` to `%s`',
                    source_container_name,
                    target_container_name
                )
                duplicate_container(
                    source_conn,
                    target_conn,
                    source_container_name,
                    target_container_name
                )
        else:
            # File system copy as per original Odoo
            from_fs = openerp.tools.config.filestore(db_original_name)
            to_fs = openerp.tools.config.filestore(db_name)
            if os.path.exists(from_fs) and not os.path.exists(to_fs):
                _logger.info(
                    'Duplicate file system directory `%s` to `%s`',
                    from_fs,
                    to_fs
                )
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
        cr.execute("""SELECT value FROM ir_config_parameter WHERE key='ir_attachment.location'""")
        result = cr.dictfetchone()
        storage = result and result['value'] or 'file'

    openerp.modules.registry.RegistryManager.delete(db_name)
    openerp.sql_db.close_db(db_name)

    db = openerp.sql_db.db_connect('postgres')
    with closing(db.cursor()) as cr:
        cr.autocommit(True)  # avoid transaction block
        _drop_conn(cr, db_name)

        try:
            cr.execute('DROP DATABASE "%s"' % db_name)
        except Exception, e:
            _logger.error('DROP DB: %s failed:\n%s', db_name, e)
            raise Exception("Couldn't drop database %s: %s" % (db_name, e))
        else:
            _logger.info('DROP DB: %s', db_name)

    if storage == 'openstack':
        # Delete entire bucket
        with closing(db.cursor()) as cr:
            cr.execute(
                """SELECT value FROM ir_config_parameter WHERE key='ir_attachment.location.openstack'"""
            )
            result = cr.dictfetchone()
            config_params = result and json.loads(result['value'])

        container_name = '{}-{}'.format(
                config_params['container_prefix'],
                db_name.lower()
            )
        conn = SwiftClient(config_params)
        container = conn.get_container(container_name=container_name)
        if container:
            delete_container(conn, container_name)
    else:
        fs = openerp.tools.config.filestore(db_name)
        if os.path.exists(fs):
            shutil.rmtree(fs)
        return True

openerp.service.db.exp_drop = exp_drop
