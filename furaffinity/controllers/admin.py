import logging

import formencode

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate 

from furaffinity.model import form

log = logging.getLogger(__name__)

class AdminController(BaseController):

    @check_perm('administrate')
    def index(self):
        return render('admin/index.mako')

    def ip(self):
        page = request.params.get('p', 0)
        ip_q = model.Session.query(model.IPLogEntry)
        ip_q = ip_q.order_by(model.IPLogEntry.end_time.desc())
        c.ip_page = paginate.Page(ip_q, page_nr=page, items_per_page=10)
        c.ip_nav = c.ip_page.navigator(link_var='p')
        return render('admin/ip.mako')

