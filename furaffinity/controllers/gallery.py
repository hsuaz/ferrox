from __future__ import with_statement

from pylons.decorators.secure import *

from furaffinity.lib import filestore, tagging, pagination
from furaffinity.lib.base import *
from furaffinity.lib.formgen import FormGenerator
from furaffinity.lib.mimetype import get_mime_type

import formencode
import logging
import md5
import os
import re
import mimetypes
from sqlalchemy import and_, or_, not_, sql
import sqlalchemy.exceptions
from sqlalchemy.orm import eagerload, eagerload_all
#from sqlalchemy.sql.expression import prefix_with
from tempfile import TemporaryFile
import time
import math

search_enabled = True
try:
    import xapian
    if xapian.major_version() < 1:
        search_enabled = False
except ImportError:
    search_enabled = False

import pylons
if pylons.config['mogilefs.tracker'] == 'FAKE':
    from furaffinity.lib import fakemogilefs as mogilefs
else:
    from furaffinity.lib import mogilefs


log = logging.getLogger(__name__)

#fullfile_size = 1280
#thumbnail_size = 120
#halfview_size = 300

# Since this isn't the only action to use /gallery/index.mako and all the other actions that use it use sqlalchemy.orm, 
# we're going to make rows look like objects using some good, old fashion Pythonic magic.
# This isn't a pretty hack. Do yourself a favor and don't read it.
class ObjectEmulator:
    def __init__(self, row, prefix):
        self.row = row
        self.prefix = prefix

    def __eq__(self, other):
        # this can only compare to None
        if other == None:
            return self.id == None
        else:
            raise ValueError('You must override __eq__ and __ne__ to compare to anything other than id == None')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getattr__(self, name):
        return self.row["%s_%s"%(self.prefix, name)]

class SubmissionEmulator(ObjectEmulator):
    def __init__(self, row, prefix):
        ObjectEmulator.__init__(self, row, prefix)

    def get_derived_by_type(self, type):
        if type=='thumb':
            return ObjectEmulator(self.row, model.DerivedSubmission.__table__.name)

    def __getattr__(self, name):
        if name == 'primary_artist':
            return ObjectEmulator(self.row, model.User.__table__.name)
        elif name == 'thumbnail':
            return None
        else:
            return ObjectEmulator.__getattr__(self, name)

def get_submission(id, eagerloads=[]):
    """Fetches a submission, and dies nicely if it can't be found."""
    q = model.Session.query(model.Submission)
    for el in eagerloads:
        q = q.options(eagerload(el))
    submission = q.get(id)
    if not submission:
        c.error_text = 'Requested submission was not found.'
        c.error_title = 'Not Found'
        abort(404)

    #c.tags = tagging.make_tags_into_string(submission.tags)
    #tag_list = tagging.TagList()
    #tag_list.parse_tag_object_array(submission.tags, negative=False)
    c.tags = tagging.make_tag_string(submission.tags)
    return submission

class GalleryController(BaseController):

    def index(self, username=None, watchstream=False):
        """Gallery index, either globally or for one user.
        
        This is huge, so I'mma comment it."""
        
        # Preliminaries
        c.javascripts = ['gallery']

        if username != None:
            c.page_owner = model.User.get_by_name(username)
        else:
            c.page_owner = None

        validator = model.form.TagFilterForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error

        c.form = FormGenerator()
        
        pageno = (form_data['page'] if form_data['page'] else 1) - 1
        perpage = form_data['perpage'] if form_data['perpage'] else int(pylons.config.get('gallery.default_perpage',12))
        
        # Retrieve tags from the database, if needed
        positive_tags = []
        negative_tags = []
        if ( form_data['tags'] == form_data['original_tags'] ):
            # use compiled tag string (faster because it's by tag.id)
            (positive_tag_strings, negative_tag_strings) = tagging.break_apart_tag_string(form_data['compiled_tags'], include_negative=True)
            
            for x in positive_tag_strings:
                try:
                    positive_tags.append(model.Tag.get_by_id(x))
                except sqlalchemy.exceptions.InvalidRequestError:
                    pass
            
            for x in negative_tag_strings:
                try:
                    negative_tags.append(model.Tag.get_by_id(x))
                except sqlalchemy.exceptions.InvalidRequestError:
                    pass
                    
        else:
            # recompile tag string (slower because it's by tag.text)
            (positive_tag_strings, negative_tag_strings) = tagging.break_apart_tag_string(form_data['tags'], include_negative=True)
            
            for x in positive_tag_strings:
                try:
                    positive_tags.append(model.Tag.get_by_text(x))
                except sqlalchemy.exceptions.InvalidRequestError:
                    pass
            
            for x in negative_tag_strings:
                try:
                    negative_tags.append(model.Tag.get_by_text(x))
                except sqlalchemy.exceptions.InvalidRequestError:
                    pass

        # Done making tag strings, print them out to the form.
        c.form.defaults['compiled_tags'] = tagging.make_compiled_tag_string(positive_tags, negative_tags)
        c.form.defaults['original_tags'] = c.form.defaults['tags'] = tagging.make_tag_string(positive_tags, negative_tags)
        c.form.defaults['perpage'] = perpage

        # The big query that better by bleeping efficient.
        # It's not using sqlalchemy.orm because we can't quite get it to be efficient.
        table_object = model.Submission.__table__
        
        #   ... join user_submissions and users. Will filter later.
        table_object = table_object.join(model.UserSubmission.__table__, model.UserSubmission.__table__.c.submission_id == model.Submission.__table__.c.id)
        table_object = table_object.join(model.User.__table__, model.UserSubmission.__table__.c.user_id == model.User.__table__.c.id)

        #   ... for every positive tag, join the submission_tags table
        # JOIN submission_tags st ON submission.id = st.submission_id AND st.tag_id == (tag id from list)
        for tag_object in positive_tags:
            tag_id = int(tag_object)
            alias = model.SubmissionTag.__table__.alias()
            table_object = table_object.join(
                alias,
                and_(
                    model.Submission.__table__.c.id == alias.c.submission_id,
                    alias.c.tag_id == tag_id
                    )
            )

        #   ... for every negative tag, outer join the submission_tags table. Will filter later.
        # LEFT OUTER JOIN submission_tags st ON submission.id = st.submission_id AND st.tag_id == (tag id from list)
        negative_aliases = []
        for tag_object in negative_tags:
            tag_id = int(tag_object)
            alias = model.SubmissionTag.__table__.alias()
            negative_aliases.append(alias)
            table_object = table_object.outerjoin(
                alias,
                and_(
                    model.Submission.__table__.c.id == alias.c.submission_id,
                    alias.c.tag_id == tag_id
                    )
                )

        #   ... outer join the derived submission table, but only on thumbnail.
        # outer join because the submission isn't garunteed to have a thumbnail.
        table_object = table_object.outerjoin(model.DerivedSubmission.__table__, and_(model.Submission.__table__.c.id==model.DerivedSubmission.__table__.c.submission_id, model.DerivedSubmission.__table__.c.derivetype == 'thumb'))

        #   ... filter out negative tags. This is why it has to be outer join.
        # Since it's outer join, tags that aren't present will be NULL. Since these are tags we don't want, WHERE st.tag_id == NULL
        tag_where_object = and_(*[alias.c.tag_id == None for alias in negative_aliases]) if negative_aliases else 1
        
        #   ... filter out other extra user_submissions.
        # Since the users:user_submissions relationship is one:many, we need to insure that we only get one back.
        if c.page_owner and not watchstream:
            owner_where_object = model.UserSubmission.c.user_id == c.page_owner.id
        else:
            owner_where_object = model.UserSubmission.c.ownership_status == 'primary'



        #   ... also limit by deletion status check deletion status
        review_status_where_object = model.UserSubmission.c.review_status == 'normal'
       
        #   ... finally, bring all the where clauses into one object
        final_where_object = and_(tag_where_object, owner_where_object, review_status_where_object)
        
        #   ... grab c.page_owner's relationships and add them to the where clause
        if watchstream:
            watchstream_where = []
            for r in c.page_owner.relationships:
                if 'watching_submissions' in r.relationship:
                    watchstream_where.append(model.UserSubmission.c.user_id == r.to_user_id)
            if watchstream_where:
                final_where_object = and_(final_where_object, or_(*watchstream_where))
            else:
                # This means that c.page_owner isn't watching anyone.
                # We don't even need to bother querying.
                c.submission = []
                return render('/gallery/index.mako')
            
        #   ... construct and execute the query. (And count the total number of images that the query would return without LIMIT/OFFSET.)
        q = table_object.select(final_where_object, use_labels=True).apply_labels()
        
        q = q.order_by(model.Submission.c.time.desc())

        if pylons.config['sqlalchemy.url'][0:5] == 'mysql':
            q = q.prefix_with('SQL_CALC_FOUND_ROWS')
        
        q = q.limit(perpage).offset(perpage*pageno)
        
        results = model.Session.execute(q)

        if pylons.config['sqlalchemy.url'][0:5] == 'mysql':
            number_of_submissions = model.Session.execute(sqlalchemy.sql.text('SELECT FOUND_ROWS()')).fetchone()[0]
        else:
            # If you want to use a non-MySQL database in production, FIX THIS.
            number_of_submissions = 1000000
        
        # Now that we have all the paging data, we can do the final number crunch.
        num_pages = int(math.ceil(float(number_of_submissions) / float(perpage)))
        
        paging_radius = int(pylons.config.get('paging.radius', 3))
            
        c.paging_links = pagination.populate_paging_links(pageno=pageno, num_pages=num_pages, perpage=perpage, radius=paging_radius)
        
        # And finally, convert our results to "objects" and stuff them into the template.
        c.submissions = [SubmissionEmulator(r, model.Submission.__table__.name) for r in results]
        return render('/gallery/index.mako')


    @check_perm('submit_art')
    def submit(self):
        """Form for uploading new art."""

        c.edit = False
        c.form = FormGenerator()
        return render('/gallery/submit.mako')

    @check_perms(['submit_art','administrate'])
    def edit(self, id=None):
        """Form for editing a submission."""

        submission = get_submission(id,['tags'])
        self.is_my_submission(submission, True)
        c.submission = submission
        c.edit = True
        c.form = FormGenerator()
        c.form.defaults['title'] = submission.title
        c.form.defaults['description'] = submission.description
        #tag_list = tagging.TagList()
        #tag_list.parse_tag_object_array(submission.tags, negative=False)
        c.form.defaults['tags'] = tagging.make_tag_string(submission.tags)
        return render('/gallery/submit.mako')

    @check_perms(['submit_art','administrate'])
    def delete(self, id=None):
        """Form for deleting a submission."""

        submission = get_submission(id)
        self.is_my_submission(submission, True)
        c.text = "Are you sure you want to delete the submission \"%s\"?" % \
                 submission.title
        c.url = h.url_for(controller='gallery', action="delete_commit", id=id)
        c.fields = {}
        return render('/confirm.mako')

    @check_perms(['submit_art','administrate'])
    def edit_commit(self, id=None):
        """Form handler for editing a submission."""

        # -- get image from database, make sure user has permission --
        # Error handling needs submission, so we need to get it no matter what.
        submission = get_submission(id,[
            'tags',
            'user_submission',
            'user_submission.user',
            'derived_submission',
            'editlog',
            'editlog.entries'
        ])
        self.is_my_submission(submission,True)

        # -- validate form input --
        validator = model.form.EditForm()
        form_data = None
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.edit = True
            c.submission = submission
            c.form = FormGenerator(form_error=error)
            return render('/gallery/submit.mako')


        if not submission.editlog:
            editlog = model.EditLog(c.auth_user)
            model.Session.save(editlog)
            submission.editlog = editlog

        editlog_entry = model.EditLogEntry(
            user = c.auth_user,
            reason = 'still no reason to the madness',
            previous_title = submission.title,
            previous_text = submission.description,
            previous_text_parsed = submission.description_parsed
        )
        model.Session.save(editlog_entry)
        submission.editlog.update(editlog_entry)

        #form_data['description'] = h.escape_once(form_data['description'])
        submission.title = h.escape_once(form_data['title'])
        submission.update_description(form_data['description'])
        if form_data['fullfile']:
            submission.set_file(form_data['fullfile'])
            submission.generate_halfview()
        submission.generate_thumbnail(form_data['thumbfile'])


        # Tag shuffle
        #tag_list = tagging.TagList()
        #tag_list.parse_tag_string(form_data['tags'])
        #submission.tags = tag_list.get_positive_tag_object_array()
        
        #for x in submission.tags:
        #    x.cache_me()

        old = list(set([str(x) for x in submission.tags]))
        new = list(set(tagging.break_apart_tag_string(form_data['tags'])))
        
        to_append = []
        for x in submission.tags:
            if str(x) not in new:
                submission.tags.remove(x)
        for x in new:
            if x not in old:
                submission.tags.append(model.Tag.get_by_text(x, create=True))
                
        
        '''
        form_data['tags'] = tagging.get_tags_from_string(form_data['tags'])
        for tag_object in submission.tags:
            if not (tag_object.text in form_data['tags']):
                submission.tags.remove(tag_object)
                #model.Session.delete(submission_tag_object)
            else:
                form_data['tags'].remove(tag_object.text)

        tagging.cache_by_list(form_data['tags'])
        for tag in form_data['tags']:
            tag_object = tagging.get_by_text(tag, True)
            submission.tags.append(tag_object)
        #model.Session.save(submission)
        '''

        model.Session.commit()
        submission.commit_mogile()

        if search_enabled:
            xapian_database = xapian.WritableDatabase('submission.xapian', xapian.DB_OPEN)
            xapian_document = submission.to_xapian()
            xapian_database.replace_document("I%d"%submission.id,xapian_document)

        h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id, username=submission.primary_artist.username))


    @check_perms(['submit_art','administrate'])
    def delete_commit(self, id=None):
        """Form handler for deleting a submission."""

        # -- validate form input --
        validator = model.form.DeleteForm()
        delete_form_data = None
        try:
            delete_form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return render('/error.mako')

        submission = get_submission(id)
        self.is_my_submission(submission,True)
        redirect_username=submission.primary_artist.username

        if delete_form_data['confirm'] != None:
            # -- update submission in database --
            submission.status = 'deleted'
            for user_submission in submission.user_submission:
                user_submission.review_status = 'deleted'
            model.Session.commit()

            if search_enabled:
                xapian_database = xapian.WritableDatabase('submission.xapian',xapian.DB_OPEN)
                xapian_database.delete_document("I%d"%submission.id)
            h.redirect_to(h.url_for(controller='gallery', action='index', username=redirect_username, id=None))
        else:
            h.redirect_to(h.url_for(controller='gallery', action='view', id=submission.id, username=redirect_username))

    @check_perm('submit_art')
    def submit_upload(self):
        """Form handler for uploading new art."""

        validator = model.form.SubmitForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.edit = False
            c.form = FormGenerator(form_error=error)
            return render('/gallery/submit.mako')

        submission = model.Submission()

        #form_data['description'] = h.escape_once(form_data['description'])
        submission.title = h.escape_once(form_data['title'])
        submission.update_description(form_data['description'])
        submission.set_file(form_data['fullfile'])
        submission.generate_thumbnail(form_data['thumbfile'])
        submission.generate_halfview()

        for tag_text in tagging.break_apart_tag_string(form_data['tags']):
            submission.tags.append(model.Tag.get_by_text(tag_text, create=True))

        user_submission = model.UserSubmission(
            user = c.auth_user,
            relationship = 'artist',
            ownership_status = 'primary',
            review_status = 'normal'
        )
        submission.user_submission.append(user_submission)

        model.Session.commit()
        submission.commit_mogile()


        # update xapian
        if search_enabled:
            xapian_database = xapian.WritableDatabase('submission.xapian',
                                                      xapian.DB_OPEN)
            xapian_document = submission.to_xapian()
            xapian_database.add_document(xapian_document)

        h.redirect_to(h.url_for(controller='gallery', action='view',
                                id=submission.id,
                                username=c.auth_user.username))

    def view(self, id=None):
        """View a single submission."""

        c.submission = get_submission(id)
        return render('/gallery/view.mako')

    def file(self, filename=None):
        """Sets up headers for downloading the requested file and returns its
        contents.

        This should be mod_rewitten to reference mogilefs directly in production.
        """

        store = mogilefs.Client(pylons.config['mogilefs.domain'], [pylons.config['mogilefs.tracker']])
        data = store.get_file_data(filename)

        if not data:
            abort(404)

        response.headers['Content-Type'] = mimetypes.guess_type(filename)
        response.headers['Content-Length'] = len(data)
        return data

    def is_my_submission(self, submission, abort=False):
        """Returns false (or aborts, if abort=True) if the provided submission
        doesn't belong to the current user.
        """

        if not c.auth_user or (not c.auth_user.can('administrate') and
                               c.auth_user.id != journal_entry.user_id):
            if abort:
                c.error_text = 'You cannot edit this submission.'
                c.error_title = 'Forbidden'
                abort(403)
            else:
                return False
        return True

