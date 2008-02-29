from furaffinity.lib.base import *
from pylons.decorators.secure import *

from furaffinity.controllers.gallery import get_submission
from furaffinity.controllers.journal import get_journal

class EditlogController(BaseController):

    def news(self, id=None):
        """Edit log for a news post."""

        news = model.Session.query(model.News).get(id)
        if not news:
            abort(404)

        c.original = news
        c.original_controller = 'news'
        c.editlog_entries = news.editlog.entries

        return render('/editlog/show.mako')

    def journal(self, id=None):
        """Edit log for a journal entry."""

        journal = get_journal(id)

        c.original = journal
        c.original_controller = 'journal'
        c.editlog_entries = journal.editlog.entries

        return render('/editlog/show.mako')

    def submission(self, id=None):
        """Edit log for a submission's description."""

        submission = get_submission(id)

        c.original = submission
        c.original_controller = 'gallery'
        c.editlog_entries = submission.editlog.entries

        return render('/editlog/show.mako')
