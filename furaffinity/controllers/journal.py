import logging

from furaffinity.lib.base import *

from pylons.decorators.secure import *

import os
import md5
import mimetypes
import sqlalchemy.exceptions
import pprint
from PIL import Image
from PIL import ImageFile
import StringIO
from tempfile import TemporaryFile

log = logging.getLogger(__name__)

class JournalController(BaseController):

    def index(self):
        c.error_text = 'Doesn\'t work yet.'
        c.error_title = 'WUT'
        return render('/error.mako')
        
    @check_perm('post_journal')
    def post(self):
        #c.submitoptions = self.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), 'image')
        c.prefill['title'] = ''
        c.prefill['content'] = ''
        return render('/journal/post.mako')

    @check_perm('post_journal')
    def post_commit(self):
        # -- validate form input --
        validator = model.form.JournalForm();
        journal_data = None
        try:
            journal_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            pp = pprint.PrettyPrinter(indent=4)
            c.prefill = request.params
            c.input_errors = "There were input errors: %s<br><pre>%s</pre>" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
            #return self.submit()
        
        # -- put journal in database --
        journal_entry = model.JournalEntry(
            user_id = c.auth_user.id,
            title = journal_data['title'],
            content = journal_data['content'],
            content_parsed = journal_data['content'] # placeholder for bbcode parser
        )
        model.Session.save(journal_entry)
        model.Session.commit()
        h.redirect_to(h.url_for(controller='journal', action='view', id = journal_entry.id))
            
    def view(self,id=None):
        try:
            id = int(id)
        except ValueError:
            c.error_text = 'Journal Entry ID must be a number.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        submission = None
        try:
            journal_entry = model.Session.query(model.JournalEntry).filter(model.JournalEntry.id==id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = 'Requested journal entry was not found.'
            c.error_title = 'Not Found'
            abort ( 404 )

        c.journal_entry_title = journal_entry.title
        c.journal_entry_content = journal_entry.content
        c.journal_entry_author = journal_entry.user.display_name
        c.journal_entry_time = journal_entry.time
        
        pp = pprint.PrettyPrinter (indent=4)
        return render('/journal/view.mako');
        
