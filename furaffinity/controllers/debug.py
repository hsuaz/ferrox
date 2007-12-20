import logging

import formencode

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate

from furaffinity.model import form

log = logging.getLogger(__name__)

class DebugController(BaseController):

    @check_perm('administrate')
    def index(self):
        return render('debug/index.mako')

    @check_perm('administrate')
    def crash(self):
        """Throws a fatal error.  The real man's way."""
        x = 133
        y = 0
        z = x / y

