from __future__ import with_statement

import pylons

from furaffinity.lib.image import ImageClass
from furaffinity.lib.mimetype import get_mime_type
from furaffinity.lib import helpers as h
import furaffinity.lib.bbcode_for_fa as bbcode

from sqlalchemy import Column, MetaData, Table, ForeignKey, types, sql
from sqlalchemy.orm import mapper, object_mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.databases.mysql import MSInteger, MSEnum
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base

from binascii import crc32
import cStringIO
import chardet
import codecs
from datetime import datetime, timedelta
import hashlib
import mimetypes
import os.path
import random
import re
import sys

from furaffinity.model.db import BaseTable, Session
from furaffinity.model.db.user import *
from furaffinity.model.datetimeasint import *
from furaffinity.model.enum import *

# -- This stuff is tied to class Submission --
if pylons.config['mogilefs.tracker'] == 'FAKE':
    from furaffinity.lib import fakemogilefs as mogilefs
else:
    from furaffinity.lib import mogilefs

search_enabled = True
try:
    import xapian
    if xapian.major_version() < 1:
        search_enabled = False
except ImportError:
    search_enabled = False
# -- end --


# Database specific types.
journal_status_type = Enum(['normal','under_review','removed_by_admin','deleted'])
submission_type_type = Enum(['image','video','audio','text'])
submission_status_type = Enum(['normal','under_review','removed_by_admin','unlinked','deleted'])
derived_submission_derivetype_type = Enum(['thumb','halfview'])
user_submission_ownership_status_type = Enum(['primary','normal'])
user_submission_review_status_type = Enum(['normal','under_review','removed_by_admin','deleted'])
user_submission_relationship_type = Enum(['artist','commissioner','gifted','isin'])
user_relationship_type = Enum(['watching_submissions','watching_journals','friend_to'])


class EditLog(BaseTable):
    __tablename__       = 'editlog'
    id                  = Column(types.Integer, primary_key=True)
    last_edited_at      = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    last_edited_by_id   = Column(types.Integer, ForeignKey('user.id'))

    def __init__(self,user):
        self.last_edited_by = user
        self.last_edited_at = datetime.now

    def update(self,editlog_entry):
        self.last_edited_by = editlog_entry.edited_by
        self.last_edited_at = editlog_entry.edited_at
        self.entries.append(editlog_entry)

class EditLogEntry(BaseTable):
    __tablename__       = 'editlog_entry'
    id                  = Column(types.Integer, primary_key=True)
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    edited_at           = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    edited_by_id        = Column(types.Integer, ForeignKey('user.id'))
    reason              = Column(types.String(length=250))
    previous_title      = Column(types.UnicodeText, nullable=False)
    previous_text       = Column(types.UnicodeText, nullable=False)
    previous_text_parsed= Column(types.UnicodeText, nullable=False)
    #mysql_engine='InnoDB

    def __init__(self, user, reason, previous_title, previous_text, previous_text_parsed):
        self.edited_by = user
        self.edited_at = datetime.now()
        self.reason = reason
        self.previous_title = previous_title
        self.previous_text = previous_text
        self.previous_text_parsed = previous_text_parsed

class JournalEntry(BaseTable):
    __tablename__       = 'journal_entry'
    id                  = Column(types.Integer, primary_key=True)
    user_id             = Column(types.Integer, ForeignKey("user.id"))
    discussion_id       = Column(types.Integer, nullable=False)
    title               = Column(types.UnicodeText, nullable=False)
    content             = Column(types.UnicodeText, nullable=False)
    content_parsed      = Column(types.UnicodeText, nullable=False)
    content_short       = Column(types.UnicodeText, nullable=False)
    time                = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    status              = Column(journal_status_type, index=True )
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    
    def __init__(self, user_id, title, content):
        content = h.escape_once(content)
        self.user_id = user_id
        self.discussion_id = 0
        self.title = title
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)

        self.status = 'normal'

    def __str__(self):
        return "Journal entry titled %s" % self.title
    
    def update_content (self, content):
        self.content = h.escape_once(content)
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        self.content_plain = bbcode.parser_plaintext.parse(content)

    def to_xapian(self):
        if search_enabled:
            xapian_document = xapian.Document()
            xapian_document.add_term("I%d"%self.id)
            xapian_document.add_value(0,"I%d"%self.id)
            xapian_document.add_term("A%s"%self.user.id)

            # title
            words = []
            rmex = re.compile(r'[^a-z0-9-]')
            for word in self.title.lower().split(' '):
                words.append(rmex.sub('',word[0:20]))
            words = set(words)
            for word in words:
                xapian_document.add_term("T%s"%word)

            # description
            words = []
            # FIX ME: needs bbcode parser. should be plain text representation.
            for word in self.content_plain.lower().split(' '):
                words.append(rmex.sub('',word[0:20]))
            words = set(words)
            for word in words:
                xapian_document.add_term("P%s"%word)

            return xapian_document
        else:
            return None

class News(BaseTable):
    __tablename__       = 'news'
    id                  = Column(types.Integer, primary_key=True)
    author_user_id      = Column(types.Integer, ForeignKey("user.id"))
    title               = Column(types.UnicodeText, nullable=False)
    content             = Column(types.UnicodeText, nullable=False)
    content_parsed      = Column(types.UnicodeText, nullable=False)
    content_short       = Column(types.UnicodeText, nullable=False)
    time                = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    is_anonymous        = Column(types.Boolean, nullable=False, default=False)
    is_deleted          = Column(types.Boolean, nullable=False, default=False)
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))

    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        self.author = author

    def update_content (self, content):
        self.content = h.escape_once(content)
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)

class Submission(BaseTable):
    __tablename__       = 'submission'
    id                  = Column(types.Integer, primary_key=True)
    title               = Column(types.String(length=128), nullable=False)
    description         = Column(types.UnicodeText, nullable=False)
    description_parsed  = Column(types.UnicodeText, nullable=False)
    type                = Column(submission_type_type, nullable=False)
    discussion_id       = Column(types.Integer, nullable=False)
    time                = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    status              = Column(submission_status_type, index=True, nullable=False)
    mogile_key          = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))

    def __init__(self):
        self.title = ''
        self.description = ''
        self.description_parsed = ''
        self.type = None
        self.discussion_id = 0
        self.status = 'normal'
        self.file_blob = None
        self.old_mogile_key = None
        self.mogile_key = None

    def _get_primary_artist(self):
        #return self.user_submission[0].user
        for index in xrange(0,len(self.user_submission)):
            if self.user_submission[index].ownership_status == 'primary':
                return self.user_submission[index].user
    primary_artist = property(_get_primary_artist)

    def get_derived_by_type (self, type):
        for index in xrange(0,len(self.derived_submission)):
            if self.derived_submission[index].derivetype == type:
                return self.derived_submission[index]
        return None

    def get_users_by_relationship (self, relationship):
        users = []
        for index in xrange(0,len(self.user_submission)):
            if self.user_submission[index].relationship == relationship:
                users.append( self.user_submission[index].user )
        return users

    def update_description (self, description):
        self.description = description
        self.description_parsed = bbcode.parser.parse(description)
        self.description_plain = bbcode.parser_plaintext.parse(description)

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
            for word in self.description_plain.lower().split(' '):
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


class DerivedSubmission(BaseTable):
    __tablename__       = 'derived_submission'
    id                  = Column(types.Integer, primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey('submission.id'), nullable=False)
    derivetype          = Column(derived_submission_derivetype_type, nullable=False)
    mogile_key          = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)

    def __init__(self, derivetype):
        self.derivetype = derivetype

class HistoricSubmission(BaseTable):
    __tablename__       = 'historic_submission'
    id                  = Column(types.Integer, primary_key=True)
    submission_id       = Column(types.Integer, ForeignKey("submission.id"), nullable=False)
    mogile_key          = Column(types.String(150), nullable=False)
    mimetype            = Column(types.String(35), nullable=False)
    edited_at           = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    edited_by_id        = Column(types.Integer, ForeignKey('user.id'))

    def __init__(self, user):
        self.edited_by = user

    def _get_previous_title(self):
        return "Historic Submission: %s" % self.mogile_key
    previous_title = property(_get_previous_title)

    def _get_previous_text_parsed(self):
        return "[%s]"%h.link_to('View Historic Submission',h.url_for(controller='gallery', action='file', filename=self.mogile_key))
    previous_text_parsed = property(_get_previous_text_parsed)

class UserSubmission(BaseTable):
    __tablename__       = 'user_submission'
    id                  = Column(types.Integer, primary_key=True)
    user_id             = Column(types.Integer, ForeignKey("user.id"))
    submission_id       = Column(types.Integer, ForeignKey("submission.id"))
    relationship        = Column(user_submission_relationship_type, nullable=False)
    ownership_status    = Column(user_submission_ownership_status_type, nullable=False)
    review_status       = Column(user_submission_review_status_type, nullable=False)

    def __init__(self, user, relationship, ownership_status, review_status):
        self.user = user
        self.relationship = relationship
        self.ownership_status = ownership_status
        self.review_status = review_status

class Comment(BaseTable):
    __tablename__       = 'comment'
    id                  = Column(types.Integer, primary_key=True)
    user_id             = Column(types.Integer, ForeignKey('user.id'))
    left                = Column(types.Integer, nullable=False)
    right               = Column(types.Integer, nullable=False)
    subject             = Column(types.UnicodeText, nullable=False)
    time                = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    content             = Column(types.UnicodeText, nullable=False)
    content_parsed      = Column(types.UnicodeText, nullable=False)
    content_short       = Column(types.UnicodeText, nullable=False)

    def add_to_nested_set(self, parent, discussion):
        """Call on a new Comment to fix the affected nested set values.
        
        discussion paremeter is the news/journal/submission this comment
        belongs to, so we don't have to hunt it down again.
        """

        # Easy parts; remember the parent/discussion and add to bridge table
        self._parent = parent
        self._discussion = discussion

        discussion.comments.append(self)

        if not parent:
            # This comment is a brand new top-level one; its left and right
            # need to be higher than the highest right
            last_comment = Session.query(Comment) \
                .with_parent(discussion, property='comments') \
                .order_by(Comment.right.desc()) \
                .first()
            if last_comment:
                self.left = last_comment.right + 1
                self.right = last_comment.right + 2
            else:
                # First comment at all
                self.left = 1
                self.right = 2

            return

        # Otherwise, we're replying to an existing comment.
        # The new comment's left should be the parent's old right, as it's
        # being inserted as the last descendant, and every left or right
        # value to the right of that should be bumped up by two.
        parent_right = parent.right

        self.left = parent_right
        self.right = parent_right + 1

        # Sure wish this reflection stuff were documented
        bridge_table = object_mapper(discussion) \
                       .get_property('comments') \
                       .secondary
        foreign_column = None
        for c in bridge_table.c:
            if c.name != 'comment_id':
                foreign_column = c
                break

        join = sql.exists([1],
            sql.and_(
                foreign_column == discussion.id,
                bridge_table.c.comment_id == comment_table.c.id,
                )
            )

        for side in ['left', 'right']:
            column = getattr(comment_table.c, side)
            Session.execute(
                comment_table.update(
                    sql.and_(column >= parent_right, join),
                    values={column: column + 2}
                    )
                )

    def get_discussion(self):
        """Returns this comment's associated news/journal/submission."""
        if not hasattr(self, '_discussion'):
            self._discussion = (self.news
                                or self.journal_entry
                                or self.submission)[0]
        return self._discussion

    def get_parent(self):
        """Returns this comment's parent."""
        if not hasattr(self, '_parent'):
            self._parent = Session.query(Comment) \
                .with_parent(self.get_discussion(), property='comments') \
                .filter(Comment.left < self.left) \
                .filter(Comment.right > self.left) \
                .order_by(Comment.left.desc()) \
                .first()
        return self._parent

    def __init__(self, user, subject, content):
        self.user_id = user.id
        self.subject = subject
        self.left = 0
        self.right = 0
        self.content = content
        self.content_parsed = content
        self.content_short = content


class NewsComment(BaseTable):
    __tablename__       = 'news_comment'
    news_id             = Column(types.Integer, ForeignKey('news.id'), primary_key=True)
    comment_id          = Column(types.Integer, ForeignKey('comment.id'), primary_key=True)

class JournalEntryComment(BaseTable):
    __tablename__       = 'journal_entry_comment'
    journal_entry_id    = Column(types.Integer, ForeignKey('journal_entry.id'), primary_key=True)
    comment_id          = Column(types.Integer, ForeignKey('comment.id'), primary_key=True)


class SubmissionComment(BaseTable):
    __tablename__       = 'submission_comment'
    submission_id       = Column(types.Integer, ForeignKey('submission.id'), primary_key=True)
    comment_id          = Column(types.Integer, ForeignKey('comment.id'), primary_key=True)
    
class Tag(BaseTable):
    __tablename__       = 'tag'
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
                # Need to create tag.
                if create:
                    tag = Tag(text=text)
                    Session.save(tag)
                else:
                    raise
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
    __tablename__       = 'submission_tag'
    submission_id       = Column(types.Integer, ForeignKey('submission.id'), primary_key=True, autoincrement=False)
    tag_id              = Column(types.Integer, ForeignKey('tag.id'), primary_key=True, autoincrement=False)

    def __init__(self, tag):
        self.tag = tag

class UserRelationship(BaseTable):
    __tablename__       = 'user_relationship'
    from_user_id        = Column(types.Integer, ForeignKey('user.id'), primary_key=True)
    to_user_id          = Column(types.Integer, ForeignKey('user.id'), primary_key=True)
    relationship        = Column(user_relationship_type, nullable=False)

UserRelationship.user = relation(User, primaryjoin=UserRelationship.from_user_id==User.id, backref='relationships')
UserRelationship.target = relation(User, primaryjoin=UserRelationship.to_user_id==User.id)

EditLog.last_edited_by = relation(User)

EditLogEntry.editlog = relation(EditLog, backref='entries')
EditLogEntry.edited_by = relation(User)

News.author = relation(User)
News.editlog = relation(EditLog)
News.comments = relation(Comment, secondary=NewsComment.__table__, backref='news', order_by=Comment.left)

UserSubmission.submission = relation(Submission, backref='user_submission')
UserSubmission.user = relation(User, backref='user_submission')

Submission.editlog = relation(EditLog)
Submission.comments = relation(Comment, secondary=SubmissionComment.__table__, backref='submission', order_by=Comment.left)

DerivedSubmission.submission = relation(Submission, backref='derived_submission', lazy=False)

HistoricSubmission.submission = relation(Submission, backref='historic_submission')
HistoricSubmission.edited_by = relation(User)

JournalEntry.editlog = relation(EditLog)
JournalEntry.comments = relation(Comment, secondary=JournalEntryComment.__table__, backref='journal_entry', order_by=Comment.left)
JournalEntry.user = relation(User, backref='journals')

Comment.user = relation(User, backref='comments')

Tag.submissions = relation(Submission, backref='tags', secondary=SubmissionTag.__table__)

