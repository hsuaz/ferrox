from __future__ import with_statement

from pylons.decorators.secure import *

from ferrox.lib import filestore, tagging, pagination, mimetype
from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator
from ferrox.lib import mimetype
from ferrox.lib.image import ImageClass

import formencode
import logging
import os
import re
import mimetypes
from sqlalchemy import and_, or_, not_, sql
import sqlalchemy.exceptions
from sqlalchemy.orm import eagerload, eagerload_all
from tempfile import TemporaryFile
import time
import math
import pylons

from ferrox.model import storage
storage_submission = storage.get_instance(pylons.config['storage.submission.url'])
storage_derived = storage.get_instance(pylons.config['storage.derived.url'])

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
    where_clauses.append(model.UserSubmission.deletion_id == None)

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
                    .options(
                             eagerload('primary_artist'),
                             ) \
                    .all()

    return submissions, submission_ct


class GalleryController(BaseController):

    def _generic_gallery(self, joined_tables=None,
                         where_clauses=[]):
        """Generic backend for viewing a gallery.
        
        Handles default tag filtering, as well as a set of default controls
        like further filtering, sorting, and pagination.
        
        Pass a pre-joined `joined_tables` sqla.sql object to filter further
        before this method does its mucking around."""

        # Some defaults
        if not joined_tables:
            joined_tables = model.Submission.__table__ \
                            .join(model.UserSubmission.__table__)

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
        where_clauses.append(model.UserSubmission.deletion_id == None)

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

    @check_perm('gallery.upload', 'gallery.manage')
    def edit(self, id=None, username=None):
        """Form for editing a submission."""
        
        c.submission = get_submission(id,['tags'])
        c.target_user = model.User.get_by_name(username)
        self._check_target_user()

        c.edit = True
        c.form = FormGenerator()
        c.form.defaults['title'] = c.submission.title
        c.form.defaults['description'] = c.submission.get_user_submission(c.target_user).content
        #tag_list = tagging.TagList()
        #tag_list.parse_tag_object_array(submission.tags, negative=False)
        c.form.defaults['tags'] = tagging.make_tag_string(c.submission.tags)
        return render('/gallery/submit.mako')

    @check_perm('gallery.upload')
    def delete(self, id=None, username=None):
        """Form for deleting a submission."""

        c.submission = get_submission(id)
        c.form = FormGenerator()
        c.target_user = model.User.get_by_name(username)
        self._check_target_user()
        c.text = "Are you sure you want to delete the submission \"%s\"?" % \
                 c.submission.title
        c.url = h.url_for(controller='gallery', action="delete_commit", id=id, username=username)
        c.fields = {}
        return render('/gallery/delete.mako')

    @check_perm('gallery.upload', 'gallery.manage')
    def edit_commit(self, id=None, username=None):
        """Form handler for editing a submission."""

        # -- get image from database, make sure user has permission --
        # Error handling needs submission, so we need to get it no matter what.
        c.submission = get_submission(id,[
            'tags',
            'user_submissions',
            'user_submissions.user',
            'user_submissions.editlog',
            'user_submissions.editlog.entries'
        ])
        c.target_user = model.User.get_by_name(username)
        self._check_target_user()
        user_submission = c.submission.get_user_submission(c.target_user)

        # -- validate form input --
        validator = model.form.EditForm()
        form_data = None
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.edit = True
            c.form = FormGenerator(form_error=error)
            return render('/gallery/submit.mako')


        if not user_submission.editlog:
            editlog = model.EditLog(c.auth_user)
            model.Session.add(editlog)
            c.submission.editlog = editlog

        editlog_entry = model.EditLogEntry(
            user = c.auth_user,
            reason = 'still no reason to the madness',
            previous_title = c.submission.title,
            previous_text = user_submission.content,
        )
        model.Session.add(editlog_entry)
        #user_submission.editlog.append(editlog_entry)

        #form_data['description'] = h.html_escape(257402.akkateerel_bondaged_wolf.png?id=Noneform_data['description'])
        c.submission.title = h.html_escape(form_data['title'])
        user_submission.content = form_data['description']
        
        if form_data['fullfile'] or form_data['thumbfile']:
            hs = model.HistoricSubmission(c.auth_user, c.submission)
            if c.submission.main_storage:
                hs.main_storage = model.SubmissionStorage()
                hs.main_storage.storage_key = storage_submission.rename(
                        c.submission.main_storage.storage_key,
                        storage_submission.mangle_key(c.submission.main_storage.storage_key)
                    )
                hs.main_storage.mimetype = c.submission.main_storage.mimetype
            if c.submission.thumbnail_storage:
                hs.thumbnail_storage = model.SubmissionStorage()
                hs.thumbnail_storage.storage_key = storage_submission.rename(
                        c.submission.thumbnail_storage.storage_key,
                        storage_submission.mangle_key(c.submission.thumbnail_storage.storage_key)
                    )
                hs.thumbnail_storage.mimetype = c.submission.thumbnail_storage.mimetype
            c.submission.historic_submissions.append(hs)
            self._process_form_data_files(c.submission, form_data)
            
            # Clear out derived submissions. We have to regenerate them.
            for i in storage_derived.items_by_prefix("%d/"%c.submission.id):
                del(storage_derived[i])


        # Tag shuffle
        #tag_list = tagging.TagList()
        #tag_list.parse_tag_string(form_data['tags'])
        #submission.tags = tag_list.get_positive_tag_object_array()
        
        #for x in submission.tags:
        #    x.cache_me()

        old = list(set([str(x) for x in c.submission.tags]))
        new = list(set(tagging.break_apart_tag_string(form_data['tags'])))
        
        to_append = []
        for x in c.submission.tags:
            if str(x) not in new:
                c.submission.tags.remove(x)
        for x in new:
            if x not in old:
                c.submission.tags.append(model.Tag.get_by_text(x, create=True))
                
        
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
        #model.Session.add(submission)
        '''

        model.Session.commit()
        #submission.commit_mogile()

        h.redirect_to(h.url_for(controller='gallery', action='view', id=c.submission.id, username=c.submission.primary_artist.username))


    @check_perm('gallery.upload')
    def delete_commit(self, id=None, username=None):
        """Form handler for deleting a submission."""

        # -- validate form input --
        validator = model.form.DeleteForm()
        form_data = None
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return render('/error.mako')

        c.submission = get_submission(id)
        c.target_user = model.User.get_by_name(username)
        self._check_target_user()
        c.user_submission = c.submission.get_user_submission(c.target_user)

        if form_data['confirm'] != None:
            # -- update submission in database --
            deletion = model.Deletion()
            deletion.public_reason = form_data['public_reason']
            deletion.private_reason = form_data['private_reason']
            c.user_submission.deletion = deletion
            c.submission.deletion = deletion
            model.Session.commit()

            h.redirect_to(h.url_for(controller='gallery', action='index', username=c.target_user.username))
        else:
            h.redirect_to(h.url_for(controller='gallery', action='view', id=c.submission.id, username=c.target_user.username))

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

        # Create new submission
        submission = model.Submission(
            title=form_data['title'],
            description=form_data['description'],
            uploader=c.auth_user,
            avatar=avatar,
        )
        
        # Image Processing
        self._process_form_data_files(submission, form_data)

        # do tags
        for tag_text in tagging.break_apart_tag_string(form_data['tags']):
            submission.tags.append(model.Tag.get_by_text(tag_text, create=True))

        model.Session.commit()

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

        This should be mod_rewitten to a static content server in production.
        """

        data = storage_submission[filename]
        
        if not data:
            abort(404)

        response.headers['Content-Type'] = mimetypes.guess_type(filename)
        response.headers['Content-Length'] = len(data)
        return data

    @check_perm('gallery.view')
    def derived_file(self, filename=None):
        """Checks for given derived key. If it doesn't exist, create it.
        If the source file doesn't exist, abort(404)

        This should be rewritten to a static content server, but it should also
        be set up to handle 404 errors from that server."""

        data = None
        try:
            data = storage_derived[filename]
        except KeyError:
            k_id, k_type, k_size, k_time = filename.split('/', 3)
            k_time = int(k_time.split('.')[0])
            k_size = int(k_size)
            k_type = k_type[0:1]
            
            submission = get_submission(int(k_id))
            if submission.time.toordinal() != k_time: abort(404)
            if k_type not in ('m', 't'): abort(404)
            allowed_sizes = []
            if k_type == 't': allowed_sizes = [int(x.strip()) for x in pylons.config['submission.thumbnail.allowed_sizes'].split(',')]
            if k_type == 'm': allowed_sizes = [int(x.strip()) for x in pylons.config['submission.main.allowed_sizes'].split(',')]
            if k_size not in allowed_sizes: abort(404)
            if k_type == 't' and not submission.thumbnail_storage: k_type = 'm'

            with ImageClass() as t:
                if k_type == 'm':
                    t.set_data(storage_submission[submission.main_storage.storage_key])
                elif k_type == 't':
                    t.set_data(storage_submission[submission.thumbnail_storage.storage_key])

                derived = t.get_resized(k_size)
                if derived:
                    data = derived.get_data()
                    storage_derived[filename] = data
                else:
                    data = t.get_data()
                    storage_derived[filename] = data

        response.headers['Content-Type'] = mimetypes.guess_type(filename)
        response.headers['Content-Length'] = len(data)
        return data

    @check_perm('gallery.manage')
    def log(self):
        """
        """
        c.submission = get_submission(id,[
            'user_submissions',
            'user_submissions.user',
            'user_submissions.editlog',
            'user_submissions.editlog.entries',
            'historic_submissions',
        ])
        return 'not implemented'

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

    def _process_form_data_files(self, submission, form_data):    
        # Image Processing...
        main = None
        if not submission.main_storage:
            main = model.SubmissionStorage() 
        else:
            main = submission.main_storage
        thumbnail = None

        # ... for thumbnail
        if form_data['thumbfile']:
            proposed_mimetype = mimetype.get_mime_type(form_data['thumbfile'])
            if submission.get_submission_type(proposed_mimetype) == 'image':
                if not submission.thumbnail_storage:
                    thumbnail = model.SubmissionStorage()
                else:
                    thumbnail = submission.thumbnail_storage
                thumbnail.mimetype = proposed_mimetype
                with ImageClass() as t:
                    t.set_data(form_data['thumbfile']['content'])
                    t_prime = t.get_resized(int(pylons.config['submission.thumbnail.max_size']))
                    if t_prime: 
                        thumbnail.blob = t_prime.get_data()
                    else:
                        thumbnail.blob = form_data['thumbfile']['content']
        
        # ... for main submission
        if form_data['fullfile']:
            main.mimetype = mimetype.get_mime_type(form_data['fullfile'])
            main.blob = None
            if submission.get_submission_type(main.mimetype) == 'image':
                with ImageClass() as t:
                    t.set_data(form_data['fullfile']['content'])
                    
                    toobig = t.get_resized(int(pylons.config['submission.main.max_size']))
                    if toobig:
                        main.blob = toobig.get_data()
                    else:
                        main.blob = form_data['fullfile']['content']
            else:
                main_blob = form_data['fullfile']['content']
                
        # Commit main submission to storage.
        key = '/'.join([c.auth_user.username, mimetype.mangle_filename(form_data['fullfile']['filename'], main.mimetype)])
        main.storage_key = key
        ct = 0
        if main.storage_key in storage_submission:
            main.storage_key = storage_submission.mangle_key(key)

        storage_submission[main.storage_key] = main.blob
        del(main.blob)
        submission.main_storage = main
        
        # Commit Thumbnail to storage and make DerivedSubmission for it.
        if thumbnail:
            thumbnail.storage_key = '/t/'.join(main.storage_key.rsplit('/', 1))
            storage_submission[thumbnail.storage_key] = thumbnail.blob
            del(thumbnail.blob)
            submission.thumbnail_storage = thumbnail

    def _check_target_user(self):
        if c.target_user not in c.submission.artists:
            abort(404)
        if c.auth_user != c.target_user:
            if c.auth_user.can('gallery.manage'):
                return True
            else:
                abort(403)
        return True


