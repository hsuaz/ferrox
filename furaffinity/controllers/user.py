import logging

import formencode

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate 

from furaffinity.model import form

log = logging.getLogger(__name__)

class UserController(BaseController):

    def view(self):
        return render('user/view.mako')

    def settings(self):
        return render('/PLACEHOLDER.mako')

