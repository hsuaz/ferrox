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

class NoSuchTagsException(Exception):
    def __init__(self, *tags):
        self.tags = tags

# TODO share this?
def find_submissions(joined_tables=None,
                     where_clauses=[], tag_string=None,
                     page_num=1, page_size=None):
    """Does all the grunt work for finding specific submissions, including
    tag filtering (plus the user's defaults) and pagination and such.
    
    Returns a two-element tuple.  The first is an array of Submission objects
    with some useful stuff eager-loaded.  The second is the total number of
    submissions found.
    """

    # Some defaults..
    if not joined_tables:
        joined_tables = model.Submission.__table__ \
                        .join(model.UserSubmission.__table__)

    # XXX admins can see more than this
    where_clauses.append(model.UserSubmission.review_status == 'normal')

    ### Tag filtering
    # Construct a list of required and excluded tags
    # XXX user default tags
    required_tags = []
    excluded_tags = []
    invalid_tags = []
    (required_tag_names, excluded_tag_names) \
        = tagging.break_apart_tag_string(tag_string,
                                         include_negative=True)

    for tag_list, tag_name_list in (required_tags, required_tag_names), \
                                   (excluded_tags, excluded_tag_names):
        for tag_name in tag_name_list:
            tag = model.Tag.get_by_text(tag_name)
            if tag:
                tag_list.append(tag)
            else:
                invalid_tags.append(tag_name)

    # Error on invalid tags
    if invalid_tags:
        raise NoSuchTagsException(*invalid_tags)

    # Require tags via simple INNER JOINs
    for tag in required_tags:
        alias = model.SubmissionTag.__table__.alias()
        joined_tables = joined_tables.join(alias, and_(
            model.Submission.id == alias.c.submission_id,
            alias.c.tag_id == tag.id,
            )
        )

    # Exclude tags via LEFT JOIN .. WHERE IS NULL
    excluded_aliases = []
    for tag in excluded_tags:
        alias = model.SubmissionTag.__table__.alias()
        joined_tables = joined_tables.outerjoin(alias, and_(
            model.Submission.id == alias.c.submission_id,
            alias.c.tag_id == tag.id,
            )
        )
        where_clauses.append(alias.c.tag_id == None)

    # Run query, fetching submission ids so we can get objects from orm
    q = sql.select([model.Submission.id], and_(*where_clauses),
                   from_obj=joined_tables) \
        .order_by(model.Submission.time.desc()) \
        .limit(page_size).offset((page_num - 1) * page_size)

    if pylons.config['sqlalchemy.url'][0:5] == 'mysql':
        q = q.prefix_with('SQL_CALC_FOUND_ROWS')

    submission_ids = [row.id for row in model.Session.execute(q)]

    # Fetch the total number of matching submissions
    if pylons.config['sqlalchemy.url'][0:5] == 'mysql':
        submission_ct = model.Session.execute(
                            sqlalchemy.sql.text('SELECT FOUND_ROWS()')) \
                        .fetchone()[0]
    else:
        submission_ct = model.Session.execute(
                sql.select(
                    [sql.func.count(model.Submission.id)],
                    and_(*where_clauses),
                    from_obj=joined_tables,
                    )
                ) \
            .fetchone()[0]

    # Actually fetch submissions
    submissions = model.Session.query(model.Submission) \
                    .filter(model.Submission.id.in_(submission_ids)) \
                    .order_by(model.Submission.time.desc()) \
                    .options(eagerload('thumbnail'),
                             eagerload('primary_artist'),
                             ) \
                    .all()

    return submissions, submission_ct

class GalleryController(BaseController):

    def _generic_gallery(self,joined_tables=model.Submission.__table__,
                         where_clauses=[]):
        """Generic backend for viewing a gallery.
        
        Handles default tag filtering, as well as a set of default controls
        like further filtering, sorting, and pagination.
        
        Pass a pre-joined `joined_tables` sqla.sql object to filter further
        before this method does its mucking around."""

        # Form validation
        validator = model.form.TagFilterForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
            return render('gallery/index.mako')

        c.form = FormGenerator()

        ### SQL
        # Some defaults..
        # XXX admins can see more than this
        where_clauses.append(model.UserSubmission.review_status == 'normal')

        ### Tag filtering
        # Construct a list of required and excluded tags
        required_tags = []
        excluded_tags = []
        invalid_tags = []
        (required_tag_names, excluded_tag_names) \
            = tagging.break_apart_tag_string(form_data['tags'],
                                             include_negative=True)
        
        for tag_list, tag_name_list in (required_tags, required_tag_names), \
                                       (excluded_tags, excluded_tag_names):
            for tag_name in tag_name_list:
                tag = model.Tag.get_by_text(tag_name)
                if tag:
                    tag_list.append(tag)
                else:
                    invalid_tags.append(tag_name)

        # Error on invalid tags
        if invalid_tags:
            c.form.errors['tags'] = 'No such tags: ' + ', '.join(invalid_tags)
            return render('gallery/index.mako')

        # Require tags via simple INNER JOINs
        for tag in required_tags:
            alias = model.SubmissionTag.__table__.alias()
            joined_tables = joined_tables.join(alias, and_(
                model.Submission.id == alias.c.submission_id,
                alias.c.tag_id == tag.id,
                )
            )

        # Exclude tags via LEFT JOIN .. WHERE IS NULL
        excluded_aliases = []
        for tag in excluded_tags:
            alias = model.SubmissionTag.__table__.alias()
            joined_tables = joined_tables.outerjoin(alias, and_(
                model.Submission.id == alias.c.submission_id,
                alias.c.tag_id == tag.id,
                )
            )
            where_clauses.append(alias.c.tag_id == None)

        # Pagination
        pageno = form_data['page'] or 1
        perpage = form_data['perpage'] or \
                      pylons.config.get('gallery.default_perpage', 12)
        c.form.defaults['perpage'] = perpage

        try:
            (c.submissions, submission_ct) = find_submissions(
                joined_tables=joined_tables,
                where_clauses=where_clauses,
                tag_string=form_data['tags'],
                page_num=pageno,
                page_size=perpage,
            )
        except NoSuchTagsException, e:
            c.form.errors['tags'] = 'No such tags: ' + ', '.join(e.tags)
            return render('gallery/index.mako')

        # Preliminaries
        c.javascripts.append('gallery')

        # Pagination links
        # XXX sqlite or otherwise no number of pages?
        num_pages = int((submission_ct + 0.5) // perpage)
        paging_radius = int(pylons.config.get('paging.radius', 3))
        c.paging_links = pagination.populate_paging_links(pageno=pageno,
                                                          num_pages=num_pages,
                                                          perpage=perpage,
                                                          radius=paging_radius
                                                          )

        return render('/gallery/index.mako')

    @check_perm('gallery.view')
    def index(self, username=None):
        """Gallery index, either globally or for one user."""
        if username:
            c.page_owner = model.User.get_by_name(username)
        else:
            c.page_owner = None

        if c.page_owner:
            joined_tables = model.Submission.__table__ \
                            .join(model.UserSubmission.__table__) \
                            .join(model.User.__table__)
            where = [model.User.id == c.page_owner.id]
            return self._generic_gallery(joined_tables=joined_tables,
                                         where_clauses=where)
        else:
            return self._generic_gallery()

    @check_perm('gallery.view')
    def watchstream(self, username):
        """Watches for a given user."""
        c.page_owner = model.User.get_by_name(username)

        joined_tables = model.Submission.__table__ \
                        .join(model.UserSubmission.__table__) \
                        .join(model.UserRelationship.__table__, and_(
                              model.UserRelationship.to_user_id
                                  == model.UserSubmission.user_id,
                              model.UserRelationship.from_user_id
                                  == c.page_owner.id,
                              model.UserRelationship.relationship
                                  == 'watching_submissions',
                              )
                        )
        return self._generic_gallery(joined_tables=joined_tables)

    @check_perm('gallery.view')
    def favorites(self, username):
        """Favorites for a given user."""
        c.page_owner = model.User.get_by_name(username)

        joined_tables = model.Submission.__table__ \
                        .join(model.FavoriteSubmission.__table__, and_(
                              model.FavoriteSubmission.submission_id
                                  == model.Submission.id,
                              model.FavoriteSubmission.user_id
                                  == c.page_owner.id,
                              )
                        )
        return self._generic_gallery(joined_tables=joined_tables)

    @check_perm('gallery.favorite')
    def favorite(self, id=None, username=None):
        submission = get_submission(id)

        if submission in c.auth_user.favorite_submissions:
            c.auth_user.favorite_submissions.remove(submission)
        else:
            c.auth_user.favorite_submissions.append(submission)

        model.Session.commit()
        h.redirect_to(h.url_for(controller='gallery', action='view', id=id, username=username))
    
    @check_perm('gallery.upload')
    def submit(self):
        """Form for uploading new art."""

        c.edit = False
        c.form = FormGenerator()
        return render('/gallery/submit.mako')

    @check_perm('gallery.upload')
    def edit(self, id=None):
        """Form for editing a submission."""

        submission = get_submission(id,['tags'])
        self.is_my_submission(submission, True)
        c.submission = submission
        c.edit = True
        c.form = FormGenerator()
        c.form.defaults['title'] = submission.title
        c.form.defaults['description'] = submission.message.content
        #tag_list = tagging.TagList()
        #tag_list.parse_tag_object_array(submission.tags, negative=False)
        c.form.defaults['tags'] = tagging.make_tag_string(submission.tags)
        return render('/gallery/submit.mako')

    @check_perm('gallery.upload')
    def delete(self, id=None):
        """Form for deleting a submission."""

        submission = get_submission(id)
        self.is_my_submission(submission, True)
        c.text = "Are you sure you want to delete the submission \"%s\"?" % \
                 submission.title
        c.url = h.url_for(controller='gallery', action="delete_commit", id=id)
        c.fields = {}
        return render('/confirm.mako')

    @check_perm('gallery.upload')
    def edit_commit(self, id=None):
        """Form handler for editing a submission."""

        # -- get image from database, make sure user has permission --
        # Error handling needs submission, so we need to get it no matter what.
        submission = get_submission(id,[
            'tags',
            'user_submissions',
            'user_submissions.user',
            'derived_submission',
            'message.editlog',
            'message.editlog.entries'
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


        if not submission.message.editlog:
            editlog = model.EditLog(c.auth_user)
            model.Session.save(editlog)
            submission.message.editlog = editlog

        editlog_entry = model.EditLogEntry(
            user = c.auth_user,
            reason = 'still no reason to the madness',
            previous_title = submission.title,
            previous_text = submission.message.content,
        )
        model.Session.save(editlog_entry)
        submission.message.editlog.update(editlog_entry)

        #form_data['description'] = h.escape_once(form_data['description'])
        submission.title = h.escape_once(form_data['title'])
        submission.message.update_content(form_data['description'])
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


    @check_perm('gallery.upload')
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
            for user_submission in submission.user_submissions:
                user_submission.review_status = 'deleted'
            model.Session.commit()

            if search_enabled:
                xapian_database = xapian.WritableDatabase('submission.xapian',xapian.DB_OPEN)
                xapian_database.delete_document("I%d"%submission.id)
            h.redirect_to(h.url_for(controller='gallery', action='index', username=redirect_username, id=None))
        else:
            h.redirect_to(h.url_for(controller='gallery', action='view', id=submission.id, username=redirect_username))

    @check_perm('gallery.upload')
    def submit_upload(self):
        """Form handler for uploading new art."""

        validator = model.form.SubmitForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.edit = False
            c.form = FormGenerator(form_error=error)
            return render('/gallery/submit.mako')

        # TODO make avatar selector control
        avatar = None
        if form_data['avatar_id']:
            avatar = model.Session.query(model.UserAvatar) \
                                  .filter_by(id=form_data['avatar_id']) \
                                  .one()

        submission = model.Submission(
            title=form_data['title'],
            description=form_data['description'],
            uploader=c.auth_user,
            avatar=avatar,
        )

        submission.set_file(form_data['fullfile'])
        submission.generate_thumbnail(form_data['thumbfile'])
        submission.generate_halfview()

        for tag_text in tagging.break_apart_tag_string(form_data['tags']):
            submission.tags.append(model.Tag.get_by_text(tag_text, create=True))

        model.Session.commit()
        submission.commit_mogile()

        # update xapian
        if search_enabled:
            xapian_database = xapian.WritableDatabase('submission.xapian', xapian.DB_OPEN)
            xapian_document = submission.to_xapian()
            xapian_database.add_document(xapian_document)

        h.redirect_to(h.url_for(controller='gallery', action='view',
                                id=submission.id,
                                username=c.auth_user.username))

    @check_perm('gallery.view')
    def view(self, id=None):
        """View a single submission."""

        c.submission = get_submission(id)
        return render('/gallery/view.mako')

    @check_perm('gallery.view')
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

    def is_my_submission(self, submission, should_abort=False):
        """Returns false (or aborts, if should_abort=True) if the provided
        submission doesn't belong to the current user.
        """

        if c.auth_user and (c.auth_user.can('admin.auth') or
                            c.auth_user in submission.artists):
            return True

        if should_abort:
            c.error_text = 'You cannot edit this submission.'
            c.error_title = 'Forbidden'
            abort(403)
        else:
            return False
