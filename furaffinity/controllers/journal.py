import logging

from furaffinity.lib.base import *

from pylons.decorators.secure import *

import os
import md5
import mimetypes
import sqlalchemy.exceptions
import pprint
import StringIO
from tempfile import TemporaryFile

log = logging.getLogger(__name__)

class JournalController(BaseController):

    def index(self, username='None', pageno=1, perpage=5):
        try:
            pageno = int(pageno)
        except ValueError:
            c.error_text = 'Page number must be a number.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        try:
            perpage = int(perpage)
        except ValueError:
            c.error_text = 'Per page must be a number.'
            c.error_title = 'Not Found'
            abort ( 400 )
            
        user_q = model.Session.query(model.User)
        try:
            c.page_owner = user_q.filter_by(username = username).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = "User %s not found." % h.escape_once(username)
            c.error_title = 'User not found'
            return render('/error.mako')

        journal_q = model.Session.query(model.JournalEntry)
        #count = journal_q.filter_by(status = 'normal').count()
        offset = (pageno-1)*perpage
        c.journals = journal_q.filter_by(user_id = c.page_owner.id).filter_by(status = 'normal')[offset:offset+perpage]

        c.is_mine = (c.auth_user and (c.page_owner.id == c.auth_user.id))
        return render('/journal/index.mako')
        
    @check_perm('post_journal')
    def post(self):
        c.edit = False;
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
            c.edit = False;
            c.prefill = request.params
            c.input_errors = "There were input errors: %s<br><pre>%s</pre>" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
        
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
            
    @check_perms(['post_journal','administrate'])
    def edit(self,id=None):
        journal_entry = self.get_journal(id)
        self.is_my_journal(journal_entry,True)
        c.edit = True;
        c.prefill['title'] = journal_entry.title
        c.prefill['content'] = journal_entry.content_parsed
        return render('/journal/post.mako')

    @check_perms(['post_journal','administrate'])
    def edit_commit(self, id=None):
        # -- validate form input --
        validator = model.form.JournalForm();
        journal_data = None
        try:
            journal_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            pp = pprint.PrettyPrinter(indent=4)
            c.edit = True;
            c.prefill = request.params
            c.input_errors = "There were input errors: %s<br><pre>%s</pre>" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
        
        journal_entry = self.get_journal(id)
        self.is_my_journal(journal_entry,True)
        
        # -- update journal in database --
        journal_entry.title = journal_data['title']
        journal_entry.content = journal_data['content']
        journal_entry.content_parsed = journal_data['content'] # placeholder for bbcode parser
        model.Session.commit()
        h.redirect_to(h.url_for(controller='journal', action='view', id = journal_entry.id))

    @check_perms(['post_journal','administrate'])
    def delete(self,id=None):
        journal_entry = self.get_journal(id)
        self.is_my_journal(journal_entry,True)
        c.text = "Are you sure you want to delete the journal titled \" %s \"?"%journal_entry.title
        c.url = h.url(action="delete_commit",id=id)
        c.fields = {}
        return render('/confirm.mako')

    @check_perms(['post_journal','administrate'])
    def delete_commit(self, id=None):
        # -- validate form input --
        pp = pprint.PrettyPrinter(indent=4)
        validator = model.form.DeleteForm();
        delete_form_data = None
        try:
            delete_form_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            return "There were input errors: %s" % (error)
            #return self.delete(id)
        
        journal_entry = self.get_journal(id)
        self.is_my_journal(journal_entry,True)
        
        if (delete_form_data['confirm'] != None):
            # -- update journal in database --
            journal_entry.status = 'deleted'
            model.Session.commit()
            h.redirect_to(h.url_for(controller='journal', action='index', username = journal_entry.user.username))
        else:
            h.redirect_to(h.url_for(controller='journal', action='view', id = journal_entry.id))

    def view(self,id=None):
        journal_entry = self.get_journal(id)

        c.journal_entry_title = journal_entry.title
        c.journal_entry_content = journal_entry.content
        c.journal_entry_author = journal_entry.user.display_name
        c.journal_entry_time = journal_entry.time
        c.journal_entry_id = journal_entry.id
        c.is_mine = self.is_my_journal(journal_entry.user)

        return render('/journal/view.mako');
        
    def get_journal(self,id=None):
        try:
            id = int(id)
        except ValueError:
            c.error_text = 'Journal Entry ID must be a number.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        journal_entry = None
        try:
            journal_entry = model.Session.query(model.JournalEntry).filter(model.JournalEntry.id==id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = 'Requested journal entry was not found.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        return journal_entry

    def is_my_journal(self,journal_entry,abort=False):
        if ( not c.auth_user or (not c.auth_user.can('administrate') and (c.auth_user.id != journal_entry.user_id)) ):
            if (abort):
                c.error_text = 'You cannot edit this journal entry.'
                c.error_title = 'Forbidden'
                abort ( 403 )
            else:
                return False
        return True

