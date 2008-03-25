from pylons.decorators.secure import *

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.lib.formgen import FormGenerator

import formencode
import logging
import md5
import mimetypes
import os
import sqlalchemy.exceptions
from sqlalchemy.orm import eagerload
from tempfile import TemporaryFile

search_enabled = True
try:
    import xapian
except ImportError:
    search_enabled = False

log = logging.getLogger(__name__)

# This tag is only valid or useful for journals and news.

def get_journal(id=None, eagerloads=[]):
    """Fetches a journal entry, and dies nicely if it can't be found."""
    try:
        id = int(id)
    except ValueError:
        c.error_text = 'Journal Entry ID must be a number.'
        c.error_title = 'Not Found'
        abort(404)

    journal_entry = None
    try:
        journal_entry = model.Session.query(model.JournalEntry)
        for el in eagerloads:
            journal_entry = journal_entry.options(eagerload(el))
        journal_entry = journal_entry.get(id)
    except sqlalchemy.exceptions.InvalidRequestError:
        c.error_text = 'Requested journal entry was not found.'
        c.error_title = 'Not Found'
        abort(404)

    return journal_entry


class JournalController(BaseController):
    def index(self, username=None):
        """Journal index for a user."""
        import pylons
        print pylons.config
        user_q = model.Session.query(model.User)
        try:
            c.page_owner = user_q.filter_by(username = username).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = "User %s not found." % h.escape_once(username)
            c.error_title = 'User not found'
            abort(404)

        page = request.params.get('page', 0)
        journal_q = model.Session.query(model.JournalEntry)
        c.journals = journal_q.filter_by(user_id = c.page_owner.id).filter_by(status = 'normal')
        c.journal_page = paginate.Page(journal_q, page_nr=page, items_per_page=2)
        c.journal_nav = c.journal_page.navigator(link_var='page')

        c.is_mine = (c.auth_user and (c.page_owner.id == c.auth_user.id))
        return render('/journal/index.mako')

    @check_perm('post_journal')
    def post(self):
        """Form for posting a journal entry."""
        c.form = FormGenerator()
        c.is_edit = False
        return render('/journal/post.mako')

    @check_perm('post_journal')
    def post_commit(self):
        """Form handler for posting a journal entry."""
        # -- validate form input --
        validator = model.form.JournalForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.is_edit = False
            c.form = FormGenerator(form_error=error)
            return render('/journal/post.mako')

        # -- put journal in database --
        form_data['content'] = h.escape_once(form_data['content'])
        journal_entry = model.JournalEntry(
            user_id=c.auth_user.id,
            title=form_data['title'],
            content=''
        )
        journal_entry.update_content(form_data['content'])
        model.Session.save(journal_entry)
        model.Session.commit()

        if search_enabled:
            xapian_database = xapian.WritableDatabase('journal.xapian',
                                                      xapian.DB_OPEN)
            xapian_document = journal_entry.to_xapian()
            xapian_database.add_document(xapian_document)

        h.redirect_to(h.url_for(controller='journal', action='view',
                                username=c.auth_user.username,
                                id=journal_entry.id))

    @check_perms(['post_journal','administrate'])
    def edit(self,id=None):
        """Form for editing a journal entry."""
        journal_entry = get_journal(id)
        self.is_my_journal(journal_entry,True)

        c.is_edit = True
        c.form = FormGenerator()
        c.form.defaults['title'] = journal_entry.title
        c.form.defaults['content'] = journal_entry.content
        return render('/journal/post.mako')

    @check_perms(['post_journal','administrate'])
    def edit_commit(self, id=None):
        """Form handler for editing a journal entry."""
        # -- validate form input --
        validator = model.form.JournalForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.is_edit = True
            c.form = FormGenerator(form_error=error)
            return render('/journal/post.mako')

        journal_entry = get_journal(id)
        self.is_my_journal(journal_entry, True)

        form_data['content'] = h.escape_once(form_data['content'])
        # -- update journal in database --
        if journal_entry.title != form_data['title'] or \
           journal_entry.content != form_data['content']:
            if journal_entry.editlog == None:
                journal_entry.editlog = model.EditLog(c.auth_user)
            editlog_entry = model.EditLogEntry(c.auth_user, 'no reasons yet',
                                               journal_entry.title,
                                               journal_entry.content,
                                               journal_entry.content_parsed)
            journal_entry.editlog.update(editlog_entry)
            journal_entry.title = form_data['title']
            journal_entry.update_content(form_data['content'])
        model.Session.commit()

        if search_enabled:
            xapian_database = xapian.WritableDatabase('journal.xapian',
                                                      xapian.DB_OPEN)
            xapian_document = journal_entry.to_xapian()
            xapian_database.replace_document("I%d" % journal_entry.id, xapian_document)

        h.redirect_to(h.url_for(controller='journal', action='view', id=journal_entry.id, username=journal_entry.user.display_name))

    @check_perms(['post_journal','administrate'])
    def delete(self,id=None):
        """Form for deleting a journal entry."""
        journal_entry = get_journal(id)
        self.is_my_journal(journal_entry, True)
        c.text = "Are you sure you want to delete the journal \"%s\"?" % \
            journal_entry.title
        c.url = h.url(action="delete_commit", id=id)
        c.fields = {}
        return render('/confirm.mako')

    @check_perms(['post_journal','administrate'])
    def delete_commit(self, id=None):
        """Form handler for deleting a journal entry."""
        # -- validate form input --
        validator = model.form.DeleteForm()
        form_data = None
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return "There were input errors: %s" % (error)
            #return self.delete(id)

        journal_entry = get_journal(id)
        self.is_my_journal(journal_entry,True)

        if form_data['confirm'] != None:
            # -- update journal in database --
            journal_entry.status = 'deleted'
            model.Session.commit()

            if search_enabled:
                xapian_database = WritableDatabase('journal.xapian', DB_OPEN)
                xapian_database.delete_document("I%d" % journal_entry.id)

            h.redirect_to(h.url_for(controller='journal', action='index',
                                    username=journal_entry.user.username))
        else:
            h.redirect_to(h.url_for(controller='journal', action='view',
                                    id=journal_entry.id))

    def view(self, id=None):
        """View a single journal entry."""
        journal_entry = get_journal(id)
        c.journal_entry = journal_entry

        c.is_mine = self.is_my_journal(journal_entry.user)

        return render('/journal/view.mako')

    def is_my_journal(self, journal_entry, abort=False):
        """Returns whether or not the given journal entry can be seen by the
        given user."""
        if not c.auth_user or (not c.auth_user.can('administrate') and
                               c.auth_user.id != journal_entry.user_id):
            if abort:
                c.error_text = 'You cannot edit this journal entry.'
                c.error_title = 'Forbidden'
                abort(403)
            else:
                return False
        return True
