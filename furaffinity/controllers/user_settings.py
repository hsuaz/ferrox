from furaffinity.lib.base import *
from furaffinity.model import form
from furaffinity.lib.formgen import FormGenerator

import pylons.config
import logging
import formencode

log = logging.getLogger(__name__)

class UserSettingsController(BaseController):

    def index(self, username=None):
        """Slightly less fillerific settings index."""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        return render('/user/settings/index.mako')
