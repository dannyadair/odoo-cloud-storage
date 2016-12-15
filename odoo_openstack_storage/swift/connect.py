import swiftclient

from urlparse import urlparse


class SwiftConnectionError(Exception):
    pass


class SwiftClient(object):
    """Wrapper around swiftclient.Connection

    Wrapper functions for get, put, delete for objects and containers.
    All this does is add some extra logic around whether the container exists
    or should be created if it doesnt.
    """
    def __init__(self, openstack_auth):
        try:
            self.user = openstack_auth['user']
            self.key = openstack_auth['key']
            self.raw_authurl = openstack_auth['authurl']
            self.auth_options = {
                'tenant_name': openstack_auth['tenant_name'],
                'region_name': openstack_auth['region_name']
            }
            self.authurl = urlparse(openstack_auth['authurl'])
            if self.authurl.scheme == 'https':
                self.insecure=False
            else:
                raise SwiftConnectionError('Auth URL not secure (requires "https")')
            if self.authurl.path == '/v2.0':
                self.auth_version = 2
            else:
                raise SwiftConnectionError('Auth version must be version v2.0')
        except KeyError:
            raise SwiftConnectionError(
                'Incorrect openstack_auth configuration'
            )
        except ValueError:
            raise SwiftConnectionError(
                'Unable to parse authurl'
            )
        self.connection = swiftclient.Connection(
            user=self.user,
            key=self.key,
            authurl=self.raw_authurl,
            insecure=self.insecure,
            auth_version=self.auth_version,
            os_options=self.auth_options
        )

    def check_container_exists(self, container_name):
        try:
            self.connection.get_container(container_name)
            return True
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason == 'Not Found':
                return False
            else:
                raise

    def get_container(self, container_name, full_listing=False, autocreate=False):
        """Add additional logic to getting a container"""
        try:
            container = self.connection.get_container(
                container_name,
                full_listing=full_listing
            )
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason == 'Not Found':
                if autocreate:
                    container = self.connection.put_container(container_name)
                else:
                    container = None
            else:
                raise
        return container

    def get_object(self, container_name, object_name):
        """Add additional logic to getting an object """
        try:
            result = self.connection.get_object(container_name, object_name)
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason == 'Not Found':
                result = None
            else:
                raise
        return result

    def put_object(self, container_name, file_name, contents, autocreate_container=True):
        """Add additional logic to putting an object"""
        if not self.check_container_exists(container_name):
            if autocreate_container:
                container = self.get_container(container_name, autocreate=True)
            else:
                raise SwiftConnectionError(
                    'Container Not Found and Not Created: {}'.format(container_name)
                )
        self.connection.put_object(
            container=container_name,
            obj=file_name,
            contents=contents
        )

    def put_container(self, container_name):
        try:
            self.connection.get_container(self, container_name)
            raise SwiftConnectionError(
                'Container {} already exists'.format(container_name)
            )
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason == 'Not Found':
                self.connection.put_container(self, container_name)
            else:
                raise

    def delete_object(self, container_name, object_name):
        try:
            self.connection.delete_object(container_name, object_name)
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason  == 'Not Found':
                pass
            else:
                raise

    def delete_container(self, container_name):
        try:
            self.connection.delete_container(container_name)
        except swiftclient.exceptions.ClientException as e:
            if e.http_reason  == 'Not Found':
                pass
            else:
                raise
