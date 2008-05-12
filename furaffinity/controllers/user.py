from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.model import form

import logging

log = logging.getLogger(__name__)

class UserController(BaseController):

    def view(self, username=None, sub_domain=None):
        """Default view for a user; shows eir recent activity and some simple
        stats/info.
        """
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/view.mako')

    def profile(self, username=None, sub_domain=None):
        """View a user's profile in painful detail."""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/profile.mako')

    def settings(self):
        """Form for editing user settings.  Eventually."""
        return render('/PLACEHOLDER.mako')
