from __future__ import with_statement

import pylons

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


# Database specific types
submission_status_type = Enum('normal', 'under_review', 'removed_by_admin', 'unlinked', 'deleted')
user_submission_ownership_status_type = Enum('primary', 'normal')
user_submission_review_status_type = Enum('normal', 'under_review', 'removed_by_admin', 'deleted')
user_submission_relationship_type = Enum('artist', 'commissioner', 'gifted', 'isin')


class Submission(BaseTable):
    __tablename__       = 'submissions'
    id                  = Column(types.Integer, primary_key=True)
    discussion_id       = Column(types.Integer, ForeignKey('discussions.id'))
    time                = Column(DateTime, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    status              = Column(submission_status_type, index=True, nullable=False)
    main_storage_id     = Column(types.Integer, ForeignKey('submissions_storage.id'))
    thumbnail_storage_id= Column(types.Integer, ForeignKey('submissions_storage.id'))

    def __init__(self, title, description, uploader, avatar=None):
        self.status = 'normal'
        self.file_blob = None
        self.storage_key = None
        self.title = title
        self.discussion = Discussion()

        user_submission = UserSubmission(
            user=uploader,
            relationship='artist',
            ownership_status='primary',
            review_status='normal',
            content=description,
        )
        if avatar and avatar.user == uploader:
            user_submission.avatar = avatar
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
            if us.user == user:
                return us
        return None

    def get_submission_type(self, mime_type=None):
        """Determines what kind of supported filetype the provided MIME-type
        corresponds to.

        Uses self.mimetype if none is provided.
        """

        if not mime_type:
            mime_type = self.main_storage.mimetype

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
    type = property(lambda self: self.get_submission_type())

    def get_derived_key(self, type):
        source, mimetype = '', ''
        size = 0

        if type == 'thumbnail':
            size = pylons.config['gallery.thumbnail_size']
            if self.thumbnail_storage:
                source = 'thumbnail'
            elif self.type == 'image':
                source = 'main'
            else:
                return pylons.config['gallery.default_thumbnail']
        elif type == 'halfview':
            size = pylons.config['gallery.halfview_size']
            if self.type == 'image':
                source = 'main'
            elif self.thumbnail_storage:
                source = 'thumbnail'
            else:
                return pylons.config['gallery.default_halfview']
        elif type == 'fullview':
            size = pylons.config['gallery.fullview_size']
            if self.type == 'image':
                source = 'main'
            else:
                raise RuntimeError('"fullview" is not valid for submission not of type "image"')
        else:
            raise RuntimeError("Unknown derived type: \"%s\"" % type)

        if source == 'thumbnail':
            mimetype = self.thumbnail_storage.mimetype
        elif source == 'main':
            mimetype = self.main_storage.mimetype
        else:
            raise NotImplementedError("Unknown source: \"%s\"" % source)

        size = int(size)

        return "%d/%s/%d/%d%s" % (
                self.id,
                source,
                size,
                int(self.time.toordinal()),
                mimetypes.guess_extension(mimetype)
            )

            
            

class FavoriteSubmission(BaseTable):
    __tablename__       = 'favorite_submissions'
    user_id             = Column(types.Integer, ForeignKey('users.id'), primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'), primary_key=True)

class SubmissionStorage(BaseTable):
    __tablename__       = 'submissions_storage'
    id                  = Column(types.Integer, primary_key=True)
    storage_key         = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)

class DefaultThumbnail(object):
    def __init__(self, type='image'):
        self.storage_key = 'default.gif'
        self.mimetype = 'image/gif'

class HistoricSubmission(BaseTable):
    __tablename__       = 'historic_submissions'
    id                  = Column(types.Integer, primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submissions.id'), nullable=False)
    storage_key         = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)
    edited_at           = Column(DateTime, nullable=False, default=datetime.now)
    edited_by_id        = Column(types.Integer, ForeignKey('users.id'))

    def __init__(self, user):
        self.edited_by = user

    def _get_previous_title(self):
        return "Historic Submission: %s" % self.storage_key
    previous_title = property(_get_previous_title)

    def _get_previous_text_parsed(self):
        return "[%s]"%h.link_to('View Historic Submission',h.url_for(controller='gallery', action='file', filename=self.storage_key))
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
                    Session.add(tag)
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

HistoricSubmission.edited_by    = relation(User)
HistoricSubmission.submission   = relation(Submission, backref='historic_submission')

Submission.tags                 = relation(Tag, backref='submissions', secondary=SubmissionTag.__table__)
Submission.discussion           = relation(Discussion, backref='submission')
Submission.favorited_by         = relation(User, secondary=FavoriteSubmission.__table__, backref='favorite_submissions')

Submission.main_storage         = relation(SubmissionStorage, 
    primaryjoin=Submission.main_storage_id == SubmissionStorage.id,
    lazy=False
    )
Submission.thumbnail_storage    = relation(SubmissionStorage,
    primaryjoin=Submission.thumbnail_storage_id == SubmissionStorage.id,
    lazy=False
    )

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


