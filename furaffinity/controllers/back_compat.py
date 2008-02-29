from furaffinity.lib.base import *

import logging

log = logging.getLogger(__name__)

class BackCompatController(BaseController):
    """Collection of URL handlers that exist solely for handling old FA URLs
    and redirecting to new, more RESTful URLs.
    """

    def view_submission(self, id):
        """For backwards-compatiblity.  Redirects from a /view/### URL to the
        fully-qualified user URL.
        """

        submission = model.Session.query(model.Submission).get(id)

        h.redirect_to(h.url_for(controller='gallery', action='view', id=id,
                                username=submission.primary_artist.username))
