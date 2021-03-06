# -*- coding: utf-8 -*-
# © 2016 Catalyst IT (https://catalyst.net.nz/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os.path
import psycopg2

from connect import get_s3_bucket

try:
    from migrate_conf import (
        DB_HOST,
        DB_NAME,
        DB_PASSWORD,
        DB_PORT,
        DB_USER,
        BUCKET_URL,
        FILESTORE_ROOT
    )
except ImportError:
    # Not configured
    BUCKET_URL = FILESTORE_ROOT = None


def migrate_files_to_s3():
    """
    Upload all existing files from the file system to S3.
    (but not delete them from the file system - do that manually)
    """
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

    if BUCKET_URL is None or FILESTORE_ROOT is None:
        msg = 'You need to copy "migrate_conf.py.in" to "migrate_conf.py" and configure it for your requirements.'
        print(msg)
        return None
    
    s3_bucket = get_s3_bucket(BUCKET_URL)

    # Walk through all filestore subdirectories and upload files to S3
    num_uploaded = 0
    num_skipped = 0
    for dir_path, dir_names, file_names in os.walk(FILESTORE_ROOT):
        for file_name in file_names:
            s3_key = s3_bucket.get_key(file_name)
            if s3_key is None:
                file_path = os.path.join(dir_path, file_name)
                s3_key = s3_bucket.new_key(file_name)
                s3_key.set_contents_from_filename(file_path)

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

    msg = 'Migration to S3 completed (%i uploaded, %i skipped)' % (num_uploaded, num_skipped)
    print(msg)
