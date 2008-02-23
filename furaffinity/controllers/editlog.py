from furaffinity.lib.base import *
from pylons.decorators.secure import *

from furaffinity.controllers.gallery import get_submission
from furaffinity.controllers.journal import get_journal

class EditlogController(BaseController):
    def journal(self, id=None):
        journal = get_journal(id)

        c.original = journal
        c.original_controller = 'journal'
        self.get_editlog_entries(journal.editlog_id)

        return render('/editlog/show.mako')

    def submission(self, id=None):
        submission = get_submission(id)

        c.original = submission
        c.original_controller = 'gallery'
        self.get_editlog_entries(submission.editlog_id)

        return render('/editlog/show.mako')

    def get_editlog_entries(self, editlog_id):
        editlog_entry_q = model.Session.query(model.EditLogEntry)
        editlog_entries = editlog_entry_q.filter(model.EditLogEntry.editlog_id == editlog_id).all()

        c.editlog_entries = []
        for entry in editlog_entries:
            dictentry = h.to_dict(entry)
            dictentry.update ( dict ( edited_by = entry.edited_by ) )
            c.editlog_entries.append(dictentry)

        return c.editlog_entries

