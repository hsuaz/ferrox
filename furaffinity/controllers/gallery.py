from __future__ import with_statement

from pylons.decorators.secure import *

from furaffinity.lib import filestore, tagging
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

def get_submission(id, eagerloads=[]):
    """Fetches a submission, and dies nicely if it can't be found."""
    try:
        q = model.Session.query(model.Submission)
        for el in eagerloads:
            q = q.options(eagerload(el))
        submission = q.get(id)
        c.tags = tagging.make_tags_into_string(submission.tags)
        return submission
    except sqlalchemy.exceptions.InvalidRequestError:
        c.error_text = 'Requested submission was not found.'
        c.error_title = 'Not Found'
        abort(404)


class GalleryController(BaseController):

    def index(self, username=None):
        """Gallery index, either globally or for one user."""

        if username != None:
            c.page_owner = model.User.get_by_name(username)
        else:
            c.page_owner = None

        validator = model.form.TagFilterForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error

        (positive_tags, negative_tags) = tagging.get_neg_and_pos_tags_from_string(form_data['tags'])
        c.form = FormGenerator()
        c.form.defaults['tags'] = tagging.recreate_tag_string(positive_tags, negative_tags)

        all_tags = negative_tags + positive_tags
        fetched = tagging.cache_by_list(all_tags)

        q = model.Session.query(model.Submission)

        select_from_object = model.submission_table

        for tag_text in positive_tags:
            tag_id = tagging.get_id_by_text(tag_text)
            alias = model.submission_tag_table.alias()
            select_from_object = select_from_object.join(
                alias,
                and_(
                    model.submission_table.c.id == alias.c.submission_id,
                    alias.c.tag_id == tag_id
                    )
            )

        negative_aliases = []
        for tag_text in negative_tags:
            tag_id = tagging.get_id_by_text(tag_text)
            alias = model.submission_tag_table.alias()
            negative_aliases.append(alias)
            select_from_object = select_from_object.outerjoin(
                alias,
                and_(
                    model.submission_table.c.id == alias.c.submission_id,
                    alias.c.tag_id == tag_id
                    )
                )

        q = q.select_from(select_from_object)
        for alias in negative_aliases:
            q = q.filter(alias.c.tag_id == None)
        q = q.options(
            eagerload_all('user_submission.user'),
            eagerload_all('derived_submission')
            )

        if c.page_owner != None:
            q = q.filter(model.UserSubmission.c.user_id == c.page_owner.id)

        q = q.filter(model.UserSubmission.c.review_status == 'normal')

        c.submissions = q.all()
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
        c.form.defaults['tags'] = tagging.make_tags_into_string(submission.tags)
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

        form_data['description'] = h.escape_once(form_data['description'])
        submission.title = h.escape_once(form_data['title'])
        submission.description = form_data['description']
        if form_data['fullfile']:
            submission.set_file(form_data['fullfile'])
            submission.generate_halfview()
        submission.generate_thumbnail(form_data['thumbfile'])


        # Tag shuffle
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

        form_data['description'] = h.escape_once(form_data['description'])
        submission.title = h.escape_once(form_data['title'])
        submission.description = form_data['description']
        submission.set_file(form_data['fullfile'])
        submission.generate_thumbnail(form_data['thumbfile'])
        submission.generate_halfview()

        form_data['tags'] = tagging.get_tags_from_string(form_data['tags'])
        tagging.cache_by_list(form_data['tags'])
        for tag in form_data['tags']:
            tag_object = tagging.get_by_text(tag, True)
            submission.tags.append(tag_object)

        user_submission = model.UserSubmission(
            user_id = session['user_id'],
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

