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
        
        # Need to weave historic_submission and editlog.entries together.
        c.editlog_entries = []
        
        historic_len = len(submission.historic_submission)
        editlog_len = 0;
        if submission.editlog:
            editlog_len = len(submission.editlog.entries)
            
        editlog_index = 0
        historic_index = 0
        
        while editlog_index < editlog_len or historic_index < historic_len:
            if editlog_index < editlog_len and historic_index < historic_len:
                if submission.editlog.entries[editlog_index].edited_at < submission.historic_submission[historic_index].edited_at:
                    c.editlog_entries.append(submission.editlog.entries[editlog_index])
                    editlog_index += 1
                else:
                    c.editlog_entries.append(submission.historic_submission[historic_index])
                    historic_index += 1
            elif editlog_index < editlog_len:
                c.editlog_entries.append(submission.editlog.entries[editlog_index])
                editlog_index += 1
            else: #if historic_index < historic_len:
                c.editlog_entries.append(submission.historic_submission[historic_index])
                historic_index += 1
            
                
        
        return render('/editlog/show.mako')
