# -*- coding: utf-8 -*-
# © 2016 Catalyst IT (https://catalyst.net.nz/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from urlparse import urlparse

import boto
from boto.s3.connection import OrdinaryCallingFormat, SubdomainCallingFormat


class S3ConnectionError(Exception):
    pass


def get_s3_bucket(bucket_url, autocreate=True):
    """
    (http[s]|s3)://key:secret@[host[:port]/]bucketprefix
    """
    url = urlparse(bucket_url)
    if url.scheme not in ('http', 'https', 's3'):
        raise S3ConnectionError(
            'Unsupported scheme "{}" in S3 bucket URL'.format(url.scheme)
        )
    is_secure = url.scheme in ('https', 's3')

    try:
        access_key = url.username
        secret_key = url.password
        api_endpoint = url.hostname
        port = url.port
        bucket_name = url.path
        if bucket_name.startswith('/'):
            # ignore leading '/' when host was specified
            bucket_name = bucket_name[1:]
    except ValueError:
        raise S3ConnectionError('Unable to parse the S3 bucket URL.')

    if not access_key or not secret_key:
        raise S3ConnectionError(
            'No cloud access and secret keys were provided.'
            ' Unable to establish a connection to S3.'
        )

    if not bucket_name:
        raise S3ConnectionError(
            'No bucket name was provided.'
            ' Unable to establish a connection to S3.'
        )

    if api_endpoint.find('amazon') == -1:
        # assume that non-amazon won't use <bucket>.<hostname> format
        calling_format = OrdinaryCallingFormat()
    else:
        calling_format = SubdomainCallingFormat()

    s3_conn = boto.connect_s3(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        is_secure=is_secure,
        port=port,
        host=api_endpoint,
        calling_format=calling_format
    )

    s3_bucket = s3_conn.lookup(bucket_name)
    if s3_bucket is None and autocreate:
        s3_bucket = s3_conn.create_bucket(bucket_name)

    return s3_bucket
