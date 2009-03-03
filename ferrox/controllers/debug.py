from ferrox.lib.base import *
from ferrox.model import form

import logging

log = logging.getLogger(__name__)

class DebugController(BaseController):

    @check_perm('debug')
    def index(self):
        """Debugging index.  Doesn't do a lot."""

        return render('debug/index.mako')

    @check_perm('debug')
    def crash(self):
        """Throws a fatal error.  The real man's way."""

        x = 133
        y = 0
        z = x / y
