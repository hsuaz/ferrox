from __future__ import with_statement

import pylons

from ferrox.lib.image import ImageClass
from ferrox.lib.mimetype import get_mime_type
from ferrox.lib import helpers as h
import ferrox.lib.bbcode_for_fa as bbcode

from sqlalchemy import Column, MetaData, Table, ForeignKey, types, sql
from sqlalchemy.orm import relation
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.sql import and_

import cStringIO
import chardet
import codecs
from datetime import datetime
import mimetypes
import os.path
import random
import re
import time

from ferrox.model.db import BaseTable, DateTime, Enum, Session
from ferrox.model.db.users import *
from ferrox.model.db.messages import *


# -- This stuff is tied to class Submission --
if pylons.config['mogilefs.tracker'] == 'FAKE':
    from ferrox.lib import fakemogilefs as mogilefs
else:
    from ferrox.lib import mogilefs

search_enabled = True
try:
    import xapian
    if xapian.major_version() < 1:
        search_enabled = False
except ImportError:
    search_enabled = False


# Database specific types
submission_type_type = Enum('image', 'video', 'audio', 'text')
submission_status_type = Enum('normal', 'under_review', 'removed_by_admin', 'unlinked', 'deleted')
derived_submission_derivetype_type = Enum('thumb', 'halfview')
user_submission_ownership_status_type = Enum('primary', 'normal')
user_submission_review_status_type = Enum('normal', 'under_review', 'removed_by_admin', 'deleted')
user_submission_relationship_type = Enum('artist', 'commissioner', 'gifted', 'isin')


class Submission(BaseTable):
    __tablename__       = 'submissions'
    id                  = Column(types.Integer, primary_key=True)
    discussion_id       = Column(types.Integer, ForeignKey('discussions.id'))
    type                = Column(submission_type_type, nullable=False)
    time                = Column(DateTime, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    status              = Column(submission_status_type, index=True, nullable=False)
    mogile_key          = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)

    def __init__(self, title, description, uploader, avatar=None):
        self.type = None
        self.status = 'normal'
        self.file_blob = None
        self.old_mogile_key = None
        self.mogile_key = None
        self.message = Message(title=title, content=description, user=uploader)
        if avatar and avatar.user == uploader:
            self.avatar = avatar
        self.discussion = Discussion()

        user_submission = UserSubmission(
            user=uploader,
            relationship='artist',
            ownership_status='primary',
            review_status='normal',
        )
        self.user_submissions.append(user_submission)


    def get_derived_by_type(self, type):
        for ds in self.derived_submission:
            if ds.derivetype == type:
                return ds
        return None

    def get_users_by_relationship(self, relationship):
        users = []
        for user_submission in self.user_submissions:
            if user_submission.relationship == relationship:
                users.append(user_submission)
        return users

    def get_user_submission(self, user):
        """Returns the UserSubmission object belonging to a specific user."""
        for us in self.user_submissions:
            print us.user, user
            if us.user == user:
                return us
        return None

    def to_xapian(self):
        if search_enabled:
            xapian_document = xapian.Document()
            xapian_document.add_term("I%s" % self.id)
            xapian_document.add_value(0, "I%s" % self.id)
            xapian_document.add_term("A%s" % self.primary_artist.id)

            # tags
            for tag in self.tags:
                xapian_document.add_term("G%s" % tag.text)

            # title
            words = []
            rmex = re.compile(r'[^a-z0-9-]')
            for word in self.title.lower().split(' '):
                words.append(rmex.sub('', word[0:20]))
            words = set(words)
            for word in words:
                xapian_document.add_term("T%s" % word)

            # description
            words = []
            # FIX ME: needs bbcode parser. should be plain text representation.
            for word in self.content.lower().split(' '):
                words.append(rmex.sub('', word[0:20]))
            words = set(words)
            for word in words:
                xapian_document.add_term("P%s" % word)

            return xapian_document
        else:
            return None

    def hash(self, s):
        """Returns the MD5 hash of a single string."""

        m = md5.new()
        m.update(s)
        return m.hexdigest()

    def get_submission_type(self, mime_type=None):
        """Determines what kind of supported filetype the provided MIME-type
        corresponds to.

        Uses self.mimetype if none is provided.
        """

        if not mime_type:
            mime_type = self.mimetype

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

    def set_file(self, file_object):
        """Sets self's properties based on provided fileobject.

        fileobject is a dictionary with 'content' and 'filename'

        Resizes input image if it is too big. (Specified in ini file.)

        Sets file_blob, mogile_key and old_mogile_key. (See commit_mogile() for more details.)
        """

        self.file_blob = file_object['content']
        self.filename = file_object['filename']

        self.mimetype = get_mime_type(file_object)
        self.type = self.get_submission_type()

        if self.type == 'image':
            toobig = None
            with ImageClass() as t:
                t.set_data(self.file_blob)
                toobig = t.get_resized(int(pylons.config['gallery.fullfile_size']))

            if toobig:
                self.file_blob = toobig.get_data()
        elif self.type == 'text':
            detection_result = chardet.detect(self.file_blob)
            if detection_result['encoding'].lower() != 'utf-8' and detection_result['encoding'].lower() != 'ascii':
                unicode_string = codecs.getdecoder(detection_result['encoding'])(self.file_blob)
                self.file_blob = codecs.getencoder('utf-8')(unicode_string)

        self.old_mogile_key = None
        if self.mogile_key != None:
            historic = HistoricSubmission(self.primary_artist)
            historic.mogile_key = self.mogile_key
            historic.mimetype = self.mimetype
            self.historic_submission.append(historic)

            #No more deleting!
            #self.old_mogile_key = self.mogile_key

        fn = os.path.splitext(re.sub(r'[^a-zA-Z0-9\.\-]','_',file_object['filename']))[0]
        self.mogile_key = hex(int(time.time()) + random.randint(-100,100))[2:] + '_' + fn
        self.mogile_key = self.mogile_key[0:135] + mimetypes.guess_extension(self.mimetype)

    def generate_halfview(self):
        """Creates, updates or deletes the 'half' DerivedSubmission

        MUST USE set_file() FIRST! Needs self.file_blob.

        If self.file_blob is smaller than half view size (ini file) or is not 'image',
        delete or don't create DerivedSubmission.

        If self.file_blob is larger than half view size, create or update DerivedSubmission.

        Sets file_blob, mogile_key and old_mogile_key in DerivedSubmission.
        (See commit_mogile() for more details.)
        """

        old_mogile_key = None
        current = self.get_derived_by_type('halfview')
        if current:
            old_mogile_key = current.mogile_key
            #self.derived_submission.remove(current)
            #Session.delete(current)

        if self.type == 'image':
            half_fileobject = None
            with ImageClass() as t:
                t.set_data(self.file_blob)
                half_fileobject = t.get_resized(int(pylons.config['gallery.halfview_size']))

            if half_fileobject:
                new_derived_submission = False
                if not current:
                    current = DerivedSubmission('halfview')
                    new_derived_submission = True
                filename_parts = os.path.splitext(self.mogile_key)
                current.mogile_key = filename_parts[0] + '.half' + filename_parts[1]
                current.mimetype = self.mimetype
                current.file_blob = half_fileobject.get_data()
                current.old_mogile_key = old_mogile_key
                if new_derived_submission:
                    self.derived_submission.append(current)
                else:
                    Session.update(current)

        elif current:
            self.derived_submission.remove(current)
            Session.delete(current)

    def generate_thumbnail(self, proposed=None):
        """Creates, updates or deletes the 'thumb' DerivedSubmission

        Needs self.file_blob if proposed is None. Must use set_file() first in that case.

        If proposed is not None, create or update DerivedSubmission

        If self.file_blob is larger than thumbnail size (ini file), create or update DerivedSubmission.

        If self.file_blob is smaller than thumbnail size or is not 'image',
        delete or don't create DerivedSubmission.

        Sets file_blob, mogile_key and old_mogile_key in DerivedSubmission.
        (See commit_mogile() for more details.)
        """

        if not hasattr(self, 'file_blob'):
            self.file_blob = None

        old_mogile_key = None
        current = self.get_derived_by_type('thumb')
        if current:
            old_mogile_key = current.mogile_key
            #self.derived_submission.remove(current)
            #Session.delete(current)

        thumb_fileobject = None
        with ImageClass() as t:
            use_self = True
            dont_bother = False
            if proposed:
                proposed_mimetype = get_mime_type(proposed)
                proposed_type = self.get_submission_type(proposed_mimetype)
                if proposed_type == 'image':
                    t.set_data(proposed['content'])
                    use_self = False

            if use_self:
                if self.type == 'image' and self.file_blob:
                    t.set_data(self.file_blob)
                else:
                    dont_bother = True

            if not dont_bother:
                thumb_fileobject = t.get_resized(int(pylons.config['gallery.thumbnail_size']))
            else:
                old_mogile_key = None

        if thumb_fileobject:
            new_derived_submission = False
            if not current:
                current = DerivedSubmission('thumb')
                new_derived_submission = True
            else:
                historic = HistoricSubmission(self.primary_artist)
                historic.mogile_key = current.mogile_key
                historic.mimetype = current.mimetype
                self.historic_submission.append(historic)

            filename_parts = os.path.splitext(self.mogile_key)
            current.mogile_key = filename_parts[0] + '.tn' + filename_parts[1]
            current.mimetype = self.mimetype
            current.file_blob = thumb_fileobject.get_data()
            #no more deleting
            #current.old_mogile_key = old_mogile_key

            if new_derived_submission:
                self.derived_submission.append(current)
            else:
                Session.update(current)
        elif current:
            self.derived_submission.remove(current)
            Session.delete(current)

    def commit_mogile(self):
        """
        Need to roll this into the session commit mechanism somehow.

        For self and each derived_submission...
            if self.file_blob, send to mogile using self.mogile key
            if self.old_mogile_key, remove self.old_mogile_key from mogile
        """
        store = mogilefs.Client(pylons.config['mogilefs.domain'], [pylons.config['mogilefs.tracker']])

        if self.file_blob:
            blobstream = cStringIO.StringIO(self.file_blob)
            if self.old_mogile_key:
                store.delete(self.old_mogile_key)
            store.send_file(self.mogile_key, blobstream)
            blobstream.close()

        for d in self.derived_submission:
            if hasattr(d,'file_blob') and d.file_blob:
                if hasattr(d,'old_mogile_key') and d.old_mogile_key:
                    store.delete(d.old_mogile_key)
                blobstream = cStringIO.StringIO(d.file_blob)
                store.send_file(d.mogile_key, blobstream)
                blobstream.close()

class FavoriteSubmission(BaseTable):
    __tablename__       = 'favorite_submissions'
    user_id             = Column(types.Integer, ForeignKey('users.id'), primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'), primary_key=True)

class DerivedSubmission(BaseTable):
    __tablename__       = 'derived_submissions'
    id                  = Column(types.Integer, primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'), nullable=False)
    derivetype          = Column(derived_submission_derivetype_type, nullable=False)
    mogile_key          = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)

    def __init__(self, derivetype):
        self.derivetype = derivetype


class HistoricSubmission(BaseTable):
    __tablename__       = 'historic_submissions'
    id                  = Column(types.Integer, primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'), nullable=False)
    mogile_key          = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)
    edited_at           = Column(DateTime, nullable=False, default=datetime.now)
    edited_by_id        = Column(types.Integer, ForeignKey('users.id'))

    def __init__(self, user):
        self.edited_by = user

    def _get_previous_title(self):
        return "Historic Submission: %s" % self.mogile_key
    previous_title = property(_get_previous_title)

    def _get_previous_text_parsed(self):
        return "[%s]"%h.link_to('View Historic Submission',h.url_for(controller='gallery', action='file', filename=self.mogile_key))
    previous_text_parsed = property(_get_previous_text_parsed)

class UserSubmission(BaseTable):
    __tablename__       = 'user_submissions'
    id                  = Column(types.Integer, primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'))
    relationship        = Column(user_submission_relationship_type, nullable=False)
    ownership_status    = Column(user_submission_ownership_status_type, nullable=False)
    review_status       = Column(user_submission_review_status_type, nullable=False)

    # Message columns
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, index=True, nullable=False, default=datetime.now)
    content             = Column(types.UnicodeText, nullable=False)
    avatar              = relation(UserAvatar)
    editlog             = relation(EditLog)

    def __init__(self, user, relationship, ownership_status, review_status):
        self.user = user
        self.relationship = relationship
        self.ownership_status = ownership_status
        self.review_status = review_status
        self.avatar_id = None

class Tag(BaseTable):
    __tablename__       = 'tags'
    id                  = Column(types.Integer, primary_key=True, autoincrement=True)
    text                = Column(types.String(length=20), index=True, unique=True)

    cache_by_text = {}
    cache_by_id = {}

    @classmethod
    def sanitize(cls, text):
        rmex = re.compile(r'[^a-z0-9]')
        return rmex.sub('', text)

    @classmethod
    def get_by_text(cls, text, create = False):
        text = Tag.sanitize(text)
        if not Tag.cache_by_text.has_key(text):
            try:
                tag = Session.query(Tag).filter(Tag.text == text).one()
                Tag.cache_by_id[tag.id] = tag
            except InvalidRequestError:
                if create:
                    # Need to create tag
                    tag = Tag(text=text)
                    Session.save(tag)
                else:
                    return None
            Tag.cache_by_text[text] = tag
        return Tag.cache_by_text[text]

    @classmethod
    def get_by_id(cls, id):
        id = int(id)
        if not Tag.cache_by_id.has_key(id):
            tag = Session.query(Tag).filter(Tag.id == id).one()
            Tag.cache_by_text[int(tag)] = tag
            Tag.cache_by_id[int(tag)] = tag
        return Tag.cache_by_id[id]

    def cache_me(self):
        if not Tag.cache_by_text.has_key(self.text):
            Tag.cache_by_text[self.text] = self
        if not Tag.cache_by_id.has_key(self.id):
            Tag.cache_by_id[self.id] = self

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text if self.text else ''

    def __int__(self):
        return self.id if self.id else 0

class SubmissionTag(BaseTable):
    __tablename__       = 'submission_tags'
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'), primary_key=True, autoincrement=False)
    tag_id              = Column(types.Integer, ForeignKey('tags.id'), primary_key=True, autoincrement=False)

    def __init__(self, tag):
        self.tag = tag

DerivedSubmission.submission    = relation(Submission, backref='derived_submission', lazy=False)

HistoricSubmission.edited_by    = relation(User)
HistoricSubmission.submission   = relation(Submission, backref='historic_submission')

Submission.tags                 = relation(Tag, backref='submissions', secondary=SubmissionTag.__table__)
Submission.discussion           = relation(Discussion, backref='submission')
Submission.favorited_by         = relation(User, secondary=FavoriteSubmission.__table__, backref='favorite_submissions')

Submission.halfview             = relation(DerivedSubmission,
    primaryjoin=and_(Submission.id == DerivedSubmission.submission_id,
                     DerivedSubmission.derivetype == 'halfview'),
    uselist=False)
Submission.thumbnail            = relation(DerivedSubmission,
    primaryjoin=and_(Submission.id == DerivedSubmission.submission_id,
                     DerivedSubmission.derivetype == 'thumb'),
    uselist=False)

Submission.artists              = relation(User, secondary=UserSubmission.__table__,
    primaryjoin=and_(Submission.id == UserSubmission.submission_id,
                     UserSubmission.ownership_status == 'primary'),
    secondaryjoin=(UserSubmission.user_id == User.id),
    )
Submission.primary_artist       = relation(User, secondary=UserSubmission.__table__,
    primaryjoin=and_(Submission.id == UserSubmission.submission_id,
                     UserSubmission.ownership_status == 'primary'),
    secondaryjoin=(UserSubmission.user_id == User.id),
    uselist=False,
    )

UserSubmission.avatar           = relation(UserAvatar, uselist=False, lazy=False)
UserSubmission.submission       = relation(Submission, backref='user_submissions')
UserSubmission.user             = relation(User, backref='user_submissions')
