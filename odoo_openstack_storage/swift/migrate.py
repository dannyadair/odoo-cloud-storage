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
    # manually update system paramters with postgres
    db_conn = psycopg2.connect(
        "dbname={} user={} password={} host={} port={}".format(
            DB_NAME,
            DB_USER,
            DB_PASSWORD,
            DB_HOST,
            DB_PORT
        )
    )
    db_cur = db_conn.cursor()

    container_name = OPENSTACK_AUTH['container_prefix'] + '-' + DB_NAME.lower()
    config_params = {
        'user': OPENSTACK_AUTH['user'],
        'key': OPENSTACK_AUTH['key'],
        'authurl': OPENSTACK_AUTH['authurl'],
        'tenant_name': OPENSTACK_AUTH['tenant_name'],
        'region_name': OPENSTACK_AUTH['region_name'],
    }
    swift_conn = SwiftClient(config_params)
    container = swift_conn.put_container(container_name)

    num_uploaded = 0
    num_skipped = 0

    for dir_path, dir_names, file_names in os.walk(FILESTORE_ROOT):
        for file_name in file_names:
            existing = swift_conn.get_object(container_name, file_name)
            if existing is None:
                swift_conn.put_object(
                    container_name,
                    file_name,
                    contents=file('{}/{}'.format(dir_path, file_name))
                )

                # Flat structure no longer needs directory name in the store_fname
                cmd = "UPDATE ir_attachment SET store_fname=substring(store_fname from {}) where store_fname = '{}/{}'"

                # account for retro compatibility
                db_cur.execute(cmd.format(4, file_name[:2], file_name))
                rows_affected = db_cur.rowcount

                if rows_affected == 1:
                    db_conn.commit()

                else:
                    db_cur.execute(cmd.format(5, file_name[:3], file_name))
                    db_conn.commit()

                num_uploaded += 1
            else:
                num_skipped += 1
            if (num_uploaded + num_skipped) % 100 == 0:
                print(
                    '{} files uploaded, {} files skipped'.format(
                        num_uploaded,
                        num_skipped
                    )
                )

    msg = 'Migrate finished: {} files uploaded. {} files skipped'.format(
        num_uploaded,
        num_skipped
    )
    print(msg)
