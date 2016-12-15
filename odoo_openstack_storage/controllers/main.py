import operator

from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import Database


class DuplicateFileStoreDatabase(Database):
    """Pass the new 'duplicate_filestore' checkbox parameter"""
    @http.route('/web/database/duplicate', type='json', auth='none')
    def duplicate(self, fields):
        params = dict(map(operator.itemgetter('name', 'value'), fields))
        duplicate_attrs = (
            params['super_admin_pwd'],
            params['db_original_name'],
            params['db_name'],
            # --- added parameter START --->>>
            params.get('duplicate_filestore', False),
            # <<<--- added parameter END
        )
        return request.session.proxy('db').duplicate_database(*duplicate_attrs)