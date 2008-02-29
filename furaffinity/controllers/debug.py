from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.model import form

import logging

log = logging.getLogger(__name__)

class DebugController(BaseController):

    @check_perm('administrate')
    def index(self):
        """Debugging index.  Doesn't do a lot."""

        return render('debug/index.mako')

    @check_perm('administrate')
    def crash(self):
        """Throws a fatal error.  The real man's way."""

        x = 133
        y = 0
        z = x / y
