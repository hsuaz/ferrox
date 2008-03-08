from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.model import form

import logging

log = logging.getLogger(__name__)

class UserController(BaseController):

    def view(self, username=None, sub_domain=None):
        """View a userpage."""
        return render('user/view.mako')

    def settings(self):
        """Form for editing user settings.  Eventually."""
        return render('/PLACEHOLDER.mako')
