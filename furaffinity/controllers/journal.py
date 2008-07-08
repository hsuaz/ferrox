from pylons.decorators.secure import *
import pylons.config

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.lib import pagination
from furaffinity.lib.formgen import FormGenerator

import formencode
import logging
import md5
import mimetypes
import os
import sqlalchemy.exceptions
from sqlalchemy.orm import eagerload
from tempfile import TemporaryFile
import datetime
from sqlalchemy import and_, or_, not_

import time, random
import math
import calendar

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
    def index(self, username=None, month=None, year=None, day=None, watchstream=False):
        """Journal index for a user."""
        if username:
            user_q = model.Session.query(model.User)
            try:
                c.page_owner = user_q.filter_by(username = username).one()
            except sqlalchemy.exceptions.InvalidRequestError:
                c.error_text = "User %s not found." % h.escape_once(username)
                c.error_title = 'User not found'
                abort(404)
        else:
            c.page_owner = None

        c.page_link_dict = dict(controller='journal', action='index')
        if c.page_owner:
            c.page_link_dict['username'] = c.page_owner.username
        if year and month and day:
            today = earliest = datetime.date(int(year), int(month), int(day))
            latest = earliest + datetime.timedelta(days=1)
            c.page_link_dict.update({'year':year, 'month':month, 'day':day})
        elif month and year:
            today = earliest = datetime.date(int(year), int(month), 1)
            latest = datetime.date(earliest.year + (earliest.month / 12), (earliest.month + 1) % 12, 1)
            c.page_link_dict.update({'year':year, 'month':month})
        elif year:
            today = earliest = datetime.date(int(year), 1, 1)
            latest = datetime.date(earliest.year+1, earliest.month, earliest.day)
            c.page_link_dict.update({'year':year})
        else:
            today = latest = (datetime.date.today()+datetime.timedelta(days=1))
            earliest = datetime.date(1970,1,1)
            
        max_per_page = int(pylons.config.get('journal.default_perpage',20))
        pageno = int(request.params.get('page',1)) - 1
        
        journal_q = model.Session.query(model.JournalEntry)
        if c.page_owner and not watchstream:
            journal_q = journal_q.filter_by(user_id = c.page_owner.id)
        journal_q = journal_q.filter_by(status = 'normal')
        journal_q = journal_q.filter(model.JournalEntry.c.time >= earliest).filter(model.JournalEntry.c.time < latest)


        #   ... grab c.page_owner's relationships and add them to the where clause
        if watchstream:
            watchstream_where = []
            for r in c.page_owner.relationships:
                if 'watching_journals' in r.relationship:
                    watchstream_where.append(model.UserSubmission.c.user_id == r.to_user_id)
            if watchstream_where:
                journal_q = journal_q.filter(or_(*watchstream_where))
            else:
                # This means that c.page_owner isn't watching anyone.
                # We don't even need to bother querying.
                c.error_text = 'No journals found.'
                c.error_title = "No journals found. User '%s' isn't watching anyone."%c.page_owner.display_name
                return render('/error.mako')

        journal_q = journal_q.order_by(model.JournalEntry.c.time.desc())
        c.journals = journal_q.limit(max_per_page).offset(pageno * max_per_page).all()
        num_journals = journal_q.count()
        
        c.title_only = False
        c.is_mine = c.page_owner and (c.auth_user and (c.page_owner.id == c.auth_user.id))
        
        paging_radius = int(pylons.config.get('paging.radius',3))
        c.paging_links = pagination.populate_paging_links(pageno=pageno, num_pages=int(math.ceil(float(num_journals)/float(max_per_page))), perpage=max_per_page, radius=paging_radius)

        c.form = FormGenerator()
        
        c.by_date_base = dict(controller='journal', action='index')
        if c.page_owner:
            c.by_date_base['username'] = c.page_owner.username
        
        c.next_year = c.by_date_base.copy()
        c.next_year['year'] = today.year + 1
        
        c.last_year = c.by_date_base.copy()
        c.last_year['year'] = today.year - 1
        
        c.next_month = c.by_date_base.copy()
        c.next_month['month'] = today.month + 1
        c.next_month['year'] = today.year
        if c.next_month['month'] > 12:
            c.next_month['month'] -= 12
            c.next_month['year'] += 1
        
        c.last_month = c.by_date_base.copy()
        c.last_month['month'] = today.month - 1
        c.last_month['year'] = today.year
        if c.last_month['month'] < 1:
            c.last_month['month'] += 12
            c.last_month['year'] -= 1
        
        c.tomorrow = c.by_date_base.copy()
        tomorrow = today + datetime.timedelta(days=1)
        c.tomorrow['year'] = tomorrow.year
        c.tomorrow['month'] = tomorrow.month
        c.tomorrow['day'] = tomorrow.day
        
        c.yesterday = c.by_date_base.copy()
        yesterday = today - datetime.timedelta(days=1)
        c.yesterday['year'] = yesterday.year
        c.yesterday['month'] = yesterday.month
        c.yesterday['day'] = yesterday.day
        
        c.year, c.month, c.day = year, month, day
        c.today = datetime.date.today()
        
        if month and year:
            c.days_this_month = max([x for x in calendar.Calendar().itermonthdays(int(year),int(month))])
            
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
        #form_data['content'] = h.escape_once(form_data['content'])
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

        #return journal_entry.id
        h.redirect_to(h.url_for(controller='journal', action='view',
                                username=c.auth_user.username,
                                id=journal_entry.id,
                                year=journal_entry.time.year,
                                month=journal_entry.time.month,
                                day=journal_entry.time.day))

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

        #form_data['content'] = h.escape_once(form_data['content'])
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

    def view(self, id=None, month=None, day=None, year=None):
        """View a single journal entry."""
        c.journal_entry = get_journal(id)
        c.is_mine = self.is_my_journal(c.journal_entry.user)

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

    def fill(self):
        return 'go away'
        time_sub = 94608000
        
        num_rows = 1000

        f = open('/usr/share/dict/words','r')
        lines = [x.strip() for x in f.readlines()]
        numlines = len(lines)
        randomwords = lambda x: ' '.join([lines[random.randint(0,numlines-1)] for x in xrange(x)])

        cur_time = datetime.datetime.fromtimestamp(model.Session.query(model.JournalEntry).max(model.JournalEntry.c.time))
        cur_time = datetime.datetime(2005,1,1) if cur_time < datetime.datetime(2005,1,1) else cur_time
                
        for i in xrange(num_rows):
            entry = model.JournalEntry(random.randint(1,3), randomwords(random.randint(4,10)), randomwords(random.randint(10,50)))
            entry.time = cur_time
            cur_time += datetime.timedelta(seconds=random.randint(0,3600))
            model.Session.save(entry)
            
        model.Session.commit()
        return cur_time
            
            
