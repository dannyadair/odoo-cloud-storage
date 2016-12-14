from contextlib import closing
import os
import psycopg2

import swiftclient

from connect import SwiftClient

try:
    from migrate_conf import (
        DB_HOST,
        DB_NAME,
        DB_PASSWORD,
        DB_PORT,
        DB_USER,
        FILESTORE_ROOT,
        OPENSTACK_AUTH,
    )
except ImportError:
    # Not configured
    OPENSTACK_AUTH = FILESTORE_ROOT = None


def migrate_files_to_openstack():
    """Duplicate of migrate_files_to_s3 for benchmarking upload speeds"""
    container_name = OPENSTACK_AUTH['container_prefix'] + '-' + DB_NAME.lower()
    config_params = {
        'user': OPENSTACK_AUTH['user'],
        'key': OPENSTACK_AUTH['key'],
        'authurl': OPENSTACK_AUTH['authurl'],
        'tenant_name': OPENSTACK_AUTH['tenant_name'],
        'region_name': OPENSTACK_AUTH['region_name'],
    }
    conn = SwiftClient(config_params)
    container = conn.put_container(container_name)

    num_uploaded = 0
    num_skipped = 0
    for dir_path, dir_names, file_names in os.walk(FILESTORE_ROOT):
        for file_name in file_names:
            try:
                existing = conn.get_object(container_name, file_name)
                num_skipped += 1
            except swiftclient.exceptions.ClientException as e:
                if e.http_reason == 'Not Found':
                    conn.put_object(
                        container_name,
                        file_name,
                        contents=file('{}/{}'.format(dir_path, file_name))
                    )
                    num_uploaded += 1
                    continue
                else:
                    raise
            if num_uploaded%100 == 0:
                print(
                    '{} files uploaded, {} files skipped'.format(
                        num_uploaded,
                        num_skipped
                    )
                )

    db_conn = psycopg2.connect(
        "dbname={} user={} password={} host={} port={}".format(
            DB_NAME,
            DB_USER,
            DB_PASSWORD,
            DB_HOST,
            DB_PORT
        )
    )
    with closing(db_conn.cursor()) as cr:
        cr.execute(
            "UPDATE ir_attachment SET store_fname=substring(store_fname from 4) WHERE store_fname LIKE '%/%'"
        )

    # manually update system paramters with postgres
    msg = 'Migrate finished: {} files uploaded. {} files skipped'.format(
        num_uploaded,
        num_skipped
    )
    print(msg)
