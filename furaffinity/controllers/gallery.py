from __future__ import with_statement

from pylons.decorators.secure import *

from furaffinity.lib import filestore, tagging
from furaffinity.lib.base import *
from furaffinity.lib.formgen import FormGenerator
from furaffinity.lib.thumbnailer import Thumbnailer

from chardet.universaldetector import UniversalDetector
import codecs
import formencode
import logging
import md5
import os
import re
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

log = logging.getLogger(__name__)

fullfile_size = 1280
thumbnail_size = 120
halfview_size = 300

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
            eagerload_all('derived_submission.metadata')
            )

        if c.page_owner != None:
            q = q.filter(model.UserSubmission.c.user_id == c.page_owner.id)

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
        c.url = h.url(action="delete_commit", id=id)
        c.fields = {}
        return render('/confirm.mako')

    @check_perms(['submit_art','administrate'])
    def edit_commit(self, id=None):
        """Form handler for editing a submission."""

        # -- validate form input --
        validator = model.form.SubmitForm()
        form_data = None
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.edit = True
            c.form = FormGenerator(form_error=error)
            return render('/gallery/submit.mako')

        # -- get image from database, make sure user has permission --
        submission = get_submission(id,[
            'tags',
            'user_submission',
            'user_submission.user',
            'derived_submission',
            'derived_submission.metadata',
            'metadata',
            'editlog',
            'editlog.entries'
        ])
        self.is_my_submission(submission,True)

        # -- get relevant information from submission_data --
        submission_data = self.set_up_submission_data(form_data, submission)

        # -- store image in mogile or wherever, if it's been changed --
        if submission_data['fullfile'] != None:
            submission.metadata.count_dec()
            submission_data['fullfile']['metadata'] = filestore.store( submission_data['fullfile']['hash'], submission_data['fullfile']['mimetype'], submission_data['fullfile']['content'] )
            submission_data['fullfile']['metadata'].height = submission_data['fullfile']['height']
            submission_data['fullfile']['metadata'].width = submission_data['fullfile']['width']

        # -- store thumbnail in mogile or wherever --
        if submission_data['thumbfile'] != None:
            tn_ind = submission.get_derived_index(['thumb'])
            if submission.get_derived_index(['thumb']) != None:
                submission.derived_submission[0].metadata.count_dec()
            submission_data['thumbfile']['metadata'] = filestore.store ( submission_data['thumbfile']['hash'], submission_data['thumbfile']['mimetype'], submission_data['thumbfile']['content'] )
            submission_data['thumbfile']['metadata'].height = submission_data['thumbfile']['height']
            submission_data['thumbfile']['metadata'].width = submission_data['thumbfile']['width']

        # -- store halfview in mogile or wherever --
        if submission_data['halffile'] != None:
            tn_ind = submission.get_derived_index(['halfview'])
            if submission.get_derived_index(['halfview']) != None:
                submission.derived_submission[0].metadata.count_dec()
            submission_data['halffile']['metadata'] = filestore.store ( submission_data['halffile']['hash'], submission_data['halffile']['mimetype'], submission_data['halffile']['content'] )
            submission_data['halffile']['metadata'].height = submission_data['halffile']['height']
            submission_data['halffile']['metadata'].width = submission_data['halffile']['width']

        # -- put submission in database --
        if submission.title != submission_data['title'] or \
           submission.description != submission_data['description']:
            if submission.editlog == None:
                submission.editlog = model.EditLog(c.auth_user)
            editlog_entry = model.EditLogEntry(c.auth_user,'no reasons yet',submission.title,submission.description,submission.description_parsed)
            submission.editlog.update(editlog_entry)
            submission.title = submission_data['title']
            submission.description = submission_data['description']
            submission.description_parsed = submission_data['description'] # waiting for bbcode parser
        submission.type = submission_data['type']
        submission.status = 'normal'
        if submission_data['fullfile'] != None:
            submission_data['fullfile']['metadata'].count_inc()
            submission.metadata = submission_data['fullfile']['metadata']

        tn_ind = submission.get_derived_index(['thumb'])
        if submission_data['thumbfile'] != None:
            submission_data['thumbfile']['metadata'].count_inc()
            if tn_ind == None:
                derived_submission = model.DerivedSubmission(derivetype='thumb')
                derived_submission.metadata = submission_data['thumbfile']['metadata']
                submission.derived_submission.append(derived_submission)
            else:
                submission.derived_submission[tn_ind].metadata.count_dec()
                submission.derived_submission[tn_ind].metadata = submission_data['thumbfile']['metadata']

        hv_ind = submission.get_derived_index(['halfview'])
        if submission_data['halffile'] != None:
            submission_data['halffile']['metadata'].count_inc()
            if hv_ind == None:
                derived_submission = model.DerivedSubmission(derivetype='halfview')
                derived_submission.metadata = submission_data['halffile']['metadata']
                submission.derived_submission.append(derived_submission)
            else:
                submission.derived_submission[hv_ind].metadata.count_dec()
                submission.derived_submission[hv_ind].metadata = submission_data['halffile']['metadata']

        # Tag shuffle
        for tag_object in submission.tags:
            if not (tag_object.text in submission_data['tags']):
                submission.tags.remove(tag_object)
                #model.Session.delete(submission_tag_object)
            else:
                submission_data['tags'].remove(tag_object.text)

        tagging.cache_by_list(submission_data['tags'])
        for tag in submission_data['tags']:
            tag_object = tagging.get_by_text(tag, True)
            submission.tags.append(tag_object)
        #model.Session.save(submission)

        model.Session.commit()

        if search_enabled:
            xapian_database = xapian.WritableDatabase('submission.xapian', xapian.DB_OPEN)
            xapian_document = submission.to_xapian()
            xapian_database.replace_document("I%d"%submission.id,xapian_document)

        h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id))


    @check_perms(['submit_art','administrate'])
    def delete_commit(self, id=None):
        """Form handler for deleting a submission."""

        # -- validate form input --
        validator = model.form.DeleteForm()
        delete_form_data = None
        try:
            delete_form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return "There were input errors: %s" % (error)

        submission = get_submission(id)
        self.is_my_submission(submission,True)

        if delete_form_data['confirm'] != None:
            # -- update submission in database --
            submission.status = 'deleted'
            submission.user_submission[0].status = 'deleted'
            model.Session.commit()

            if search_enabled:
                xapian_database = WritableDatabase('submission.xapian',DB_OPEN)
                xapian_database.delete_document("I%d"%submission.id)
            h.redirect_to(h.url_for(controller='gallery', action='index', username=submission.user_submission[0].user.username, id=None))
        else:
            h.redirect_to(h.url_for(controller='gallery', action='view', id=submission.id))

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

        # -- fill out submission_data --
        submission_data = self.set_up_submission_data(form_data,None)

        # -- store image in mogile or wherever --
        submission_data['fullfile']['metadata'] = filestore.store( submission_data['fullfile']['hash'], submission_data['fullfile']['mimetype'], submission_data['fullfile']['content'] )
        submission_data['fullfile']['metadata'].height = submission_data['fullfile']['height']
        submission_data['fullfile']['metadata'].width = submission_data['fullfile']['width']

        # -- store thumbnail in mogile or wherever --
        if submission_data['thumbfile']:
            submission_data['thumbfile']['metadata'] = filestore.store ( submission_data['thumbfile']['hash'], submission_data['thumbfile']['mimetype'], submission_data['thumbfile']['content'] )
            submission_data['thumbfile']['metadata'].height = submission_data['thumbfile']['height']
            submission_data['thumbfile']['metadata'].width = submission_data['thumbfile']['width']
        else:
            # FIXME: Default thumbnail?
            pass

        # -- store halfview in mogile or wherever --
        if submission_data['halffile']:
            submission_data['halffile']['metadata'] = filestore.store ( submission_data['halffile']['hash'], submission_data['halffile']['mimetype'], submission_data['halffile']['content'] )
            submission_data['halffile']['metadata'].height = submission_data['halffile']['height']
            submission_data['halffile']['metadata'].width = submission_data['halffile']['width']

        submission = model.Submission(
            title = submission_data['title'],
            description = submission_data['description'],
            description_parsed = submission_data['description'], # FIXME: waiting for bbcode parser
            type = submission_data['type'],
            discussion_id = 0,
            status = 'normal'
            )
        submission_data['fullfile']['metadata'].count_inc()
        submission.metadata = submission_data['fullfile']['metadata']

        tagging.cache_by_list(submission_data['tags'])
        for tag in submission_data['tags']:
            tag_object = tagging.get_by_text(tag, True)
            submission.tags.append(tag_object)
        user_submission = model.UserSubmission(
            user_id = session['user_id'],
            relationship = 'artist',
            status = 'primary'
        )
        submission.user_submission.append(user_submission)

        if submission_data['thumbfile'] != None:
            thumbfile_derived_submission = model.DerivedSubmission(derivetype='thumb')
            submission_data['thumbfile']['metadata'].count_inc()
            thumbfile_derived_submission.metadata = submission_data['thumbfile']['metadata']
            submission.derived_submission.append(thumbfile_derived_submission)

        if submission_data['halffile'] != None:
            thumbfile_derived_submission = model.DerivedSubmission(derivetype='halfview')
            submission_data['halffile']['metadata'].count_inc()
            thumbfile_derived_submission.metadata = submission_data['halffile']['metadata']
            submission.derived_submission.append(thumbfile_derived_submission)

        model.Session.commit()

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

        submission = get_submission(id)
        filename=filestore.get_submission_file(submission.metadata)

        c.submission_thumbnail = submission.get_derived_index(['thumb'])
        if c.submission_thumbnail != None:
            tn_filename=filestore.get_submission_file(submission.derived_submission[c.submission_thumbnail].metadata)
            c.submission_thumbnail = h.url_for(controller='gallery',
                                               action='file',
                                               filename=tn_filename, id=None)
        else:
            # supply default thumbnail for type here
            c.submission_thumbnail = ''
        c.submission_halfview = submission.get_derived_index(['halfview'])
        if c.submission_halfview != None:
            hv_filename=filestore.get_submission_file(submission.derived_submission[c.submission_halfview].metadata)
            c.submission_halfview = h.url_for(controller='gallery',
                                              action='file',
                                              filename=hv_filename, id=None)
        else:
            # supply default thumbnail for type here
            c.submission_thumbnail = ''
        c.submission_file = h.url_for(controller='gallery', action='file',
                                      filename=filename, id=None)
        c.submission = submission

        if submission.type == 'text':
            filedata = filestore.dump(filestore.get_submission_file(submission.metadata))
            c.submission_content = filedata[0]

        return render('/gallery/view.mako')

    def file(self, filename=None):
        """Sets up headers for downloading the requested file and returns its
        contents.
        """

        filename = os.path.basename(filename)
        try:
            filedata = filestore.dump(filename)
        except filestore.ImageManagerExceptionFileNotFound:
            c.error_text = 'Requested file was not found.'
            c.error_title = 'Not Found'
            abort(404)

        response.headers['Content-Type'] = filedata[1].mimetype
        response.headers['Content-Length'] = len(filedata[0])
        return filedata[0]

    def hash(self, s):
        """Returns the MD5 hash of a single string."""

        m = md5.new()
        m.update(s)
        return m.hexdigest()

    def get_submission_type(self, mime_type):
        """Determines what kind of supported filetype the provided MIME-type
        corresponds to.
        """

        (major, minor) = mime_type.split('/')
        if major == 'image':
            if minor in ('png','gif','jpeg'):
                return 'image'
            else:
                return 'unknown'
        elif major == 'application' and minor == 'x-shockwave-flash':
            return 'video'
        elif major == 'audio' and minor == 'mpeg':
            return 'audio'
        elif major == 'text':
            if minor in ('plain','html'):
                return 'text'
            else:
                return 'unknown'
        else:
            return 'unknown'

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

    def set_up_submission_data(self, submission_data, submission):
        """Makes thumbnails and..  stuff."""

        # Is there a new image uploaded?
        if submission_data['fullfile']:
            # Yes, find out what type of submission we're dealing with...
            submission_data['fullfile']['mimetype'] = h.get_mime_type(submission_data['fullfile'])
            submission_type = self.get_submission_type(submission_data['fullfile']['mimetype'])
            if submission_type == 'unknown':
                abort(403)
        else:
            # No, grab it out of current submission.
            submission_type = submission.type

        submission_data['type'] = submission_type
        submission_data['tags'] = tagging.get_tags_from_string(submission_data['tags'])

        # If it's not an image, there are no dimensions
        if submission_type != 'image':
            submission_data['fullfile']['height'] = 0
            submission_data['fullfile']['width'] = 0

        # Do we have a thumbnail?
        if submission_data['thumbfile']:
            # Yes we do.

            # Is it an image?
            submission_data['thumbfile']['mimetype'] = h.get_mime_type(submission_data['thumbfile'])
            if self.get_submission_type(submission_data['thumbfile']['mimetype']) == 'image':
                # Yes it is
                with Thumbnailer() as t:
                    t.parse(submission_data['thumbfile']['content'],submission_data['thumbfile']['mimetype'])

                    # Is it too big?
                    toobig = t.generate(thumbnail_size)
                    if toobig != None:
                        # Yes it is.
                        submission_data['thumbfile'].update(toobig)
                        toobig.clear()
                    else:
                        # No it isn't
                        submission_data['thumbfile']['width'] = t.width
                        submission_data['thumbfile']['height'] = t.height
            else:
                # No, it isn't. So we may as well not have one.
                submission_data['thumbfile'].clear()
                submission_data['thumbfile'] = None


        # Do we have a half view?
        if submission_data['halffile']:
            # Yes we do.

            # Do we care?
            if submission_type == 'image':
                # Yes we do
                # Is it an image?
                submission_data['halffile']['mimetype'] = h.get_mime_type(submission_data['halffile'])
                if self.get_submission_type(submission_data['halffile']['mimetype']) == 'image':
                    # Yes it is
                    with Thumbnailer() as t:
                        t.parse(submission_data['halffile']['content'],submission_data['halffile']['mimetype'])

                        # Is it too big?
                        toobig = t.generate(halfview_size)
                        if toobig != None:
                            # Yes it is.
                            submission_data['halffile'].update(toobig)
                            toobig.clear()
                        else:
                            # No it isn't
                            submission_data['halffile']['width'] = t.width
                            submission_data['halffile']['height'] = t.height
                else:
                    # No, it isn't. So we may as well not have one.
                    submission_data['halffile'].clear()
                    submission_data['halffile'] = None
            else:
                # No we don't
                submission_data['halffile'].clear()
                submission_data['halffile'] = None

        # Do any required image processing on the main image now. If it's an image.

        # Do we even need to generate new thumbnail/halfview?
        if submission_data['fullfile']:
            if submission_type == 'image':
                with Thumbnailer() as t:
                    t.parse(submission_data['fullfile']['content'],submission_data['fullfile']['mimetype'])
                    submission_data['fullfile']['width'] = t.width
                    submission_data['fullfile']['height'] = t.height

                    # Do we need to make a thumbnail?
                    if not submission_data['thumbfile']:
                        # Yes we do

                        # Can we derive one from the submission?
                        if submission_type == 'image':
                            # Yes, we can.
                            submission_data['thumbfile'] = t.generate(thumbnail_size)
                            submission_data['thumbfile']['mimetype'] = submission_data['fullfile']['mimetype']

                    # Do we need to make a half view image?
                    if not submission_data['halffile']:
                        submission_data['halffile'] = t.generate(halfview_size)
                        submission_data['halffile']['mimetype'] = submission_data['fullfile']['mimetype']

                    # Is the submission itself too big?
                    toobig = t.generate(fullfile_size)
                    if toobig:
                        # Yes it is
                        submission_data['fullfile'].update(toobig)
                        toobig.clear()
            elif submission_type == 'text':
                if submission_data['fullfile']['mimetype'] == 'text/plain' or submission_data['fullfile']['mimetype'] == 'text/html':
                    detector = UniversalDetector()
                    detector.feed(submission_data['fullfile']['content'])
                    detector.close()
                    decoded = codecs.getdecoder(detector.result['encoding'])(submission_data['fullfile']['content'],'replace')[0]
                    submission_data['fullfile']['content'] = codecs.getencoder('utf_8')(h.escape_once(decoded),'replace')[0]


            submission_data['fullfile']['hash'] = self.hash(submission_data['fullfile']['content'])

        if submission_data['halffile'] != None:
            submission_data['halffile']['hash'] = self.hash(submission_data['halffile']['content'])
        if submission_data['thumbfile'] != None:
            submission_data['thumbfile']['hash'] = self.hash(submission_data['thumbfile']['content'])

        return submission_data

