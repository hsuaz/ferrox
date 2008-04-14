from __future__ import with_statement

import hashlib
import time
import random
import cStringIO
import os.path
import mimetypes

import pylons

from sqlalchemy import Column, MetaData, Table, ForeignKey, types, sql
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.databases.mysql import MSInteger, MSEnum
from sqlalchemy.exceptions import InvalidRequestError

from datetime import datetime

from datetime import datetime, timedelta
from enum import *
from datetimeasint import *
import re

import sys
from binascii import crc32

from furaffinity.lib.thumbnailer import Thumbnailer
from furaffinity.lib.mimetype import get_mime_type
from furaffinity.lib import helpers as h
import furaffinity.lib.bbcode_for_fa as bbcode

import chardet
import codecs

search_enabled = True
try:
    import xapian
except ImportError:
    search_enabled = False

if pylons.config['mogilefs.tracker'] == 'FAKE':
    from furaffinity.lib import fakemogilefs as mogilefs
else:
    from furaffinity.lib import mogilefs

#This plays hell with websetup, so only use where needed.
#from furaffinity.lib import filestore

Session = scoped_session(sessionmaker(autoflush=True, transactional=True,
    bind=pylons.config['pylons.g'].sa_engine))

metadata = MetaData()

# Database specific types.
if re.match('^mysql', pylons.config['sqlalchemy.url']):
    ip_type = MSInteger(unsigned=True)
else:
    ip_type = types.String(length=11)
note_status_type = Enum(['unread','read'])
journal_status_type = Enum(['normal','under_review','removed_by_admin','deleted'])
submission_type_type = Enum(['image','video','audio','text'])
submission_status_type = Enum(['normal','under_review','removed_by_admin','unlinked','deleted'])
derived_submission_derivetype_type = Enum(['thumb','halfview'])
user_submission_ownership_status_type = Enum(['primary','normal'])
user_submission_review_status_type = Enum(['normal','under_review','removed_by_admin','deleted'])
user_submission_relationship_type = Enum(['artist','commissioner','gifted','isin'])

# Users

user_table = Table('user', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('username', types.String(32), nullable=False),
    Column('email', types.String(256), nullable=False),
    Column('password', types.String(256), nullable=False),
    Column('display_name', types.Unicode, nullable=False),
    Column('role_id', types.Integer, ForeignKey('role.id'), default=1),
    mysql_engine='InnoDB'
)

user_preference_table = Table('user_preference', metadata,
    Column('user_id', types.Integer, ForeignKey('user.id'), primary_key=True),
    Column('key', types.String(length=32), primary_key=True),
    Column('value', types.String(length=256), nullable=False),
    mysql_engine='InnoDB'
)

role_table = Table('role', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('name', types.String(length=32), nullable=False),
    Column('sigil', types.String(length=1), nullable=False),
    Column('description', types.String(length=256), nullable=False),
    mysql_engine='InnoDB'
)

role_permission_table = Table('role_permission', metadata,
    Column('role_id', types.Integer, ForeignKey('role.id'), primary_key=True),
    Column('permission_id', types.Integer, ForeignKey('permission.id'), primary_key=True),
    mysql_engine='InnoDB'
)

permission_table = Table('permission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('name', types.String(length=32), nullable=False),
    Column('description', types.String(length=256), nullable=False),
    mysql_engine='InnoDB'
)

ip_log_table = Table('ip_log', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('user_id', types.Integer, ForeignKey('user.id'), nullable=False),
    Column('ip', ip_type, nullable=False),
    Column('start_time', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('end_time', DateTimeAsInteger, nullable=False, default=datetime.now),
    mysql_engine='InnoDB'
)

# Notes

note_table = Table('note', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('from_user_id', types.Integer, ForeignKey("user.id")),
    Column('to_user_id', types.Integer, ForeignKey("user.id")),
    Column('original_note_id', types.Integer, ForeignKey("note.id")),
    Column('subject', types.Unicode, nullable=False),
    Column('content', types.Unicode, nullable=False),
    Column('content_parsed', types.Unicode, nullable=False),
    Column('status', note_status_type, nullable=False),
    Column('time', DateTimeAsInteger, nullable=False, default=datetime.now),
    mysql_engine='InnoDB'
)

# Journals

journal_entry_table = Table('journal_entry', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('user_id', types.Integer, ForeignKey("user.id")),
    Column('discussion_id', types.Integer, nullable=False),
    Column('title', types.Unicode, nullable=False),
    Column('content', types.Unicode, nullable=False),
    Column('content_parsed', types.Unicode, nullable=False),
    Column('content_short', types.Unicode, nullable=False),
    Column('time', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('status', journal_status_type, index=True ),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    mysql_engine='InnoDB'
)

# News

news_table = Table('news', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('author_user_id', types.Integer, ForeignKey("user.id")),
    Column('title', types.Unicode, nullable=False),
    Column('content', types.Unicode, nullable=False),
    Column('content_parsed', types.Unicode, nullable=False),
    Column('content_short', types.Unicode, nullable=False),
    Column('time', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('is_anonymous', types.Boolean, nullable=False, default=False),
    Column('is_deleted', types.Boolean, nullable=False, default=False),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    mysql_engine='InnoDB'
)

# Submissions

submission_table = Table('submission', metadata,
    Column('id', types.Integer, primary_key=True),
    #Column('image_metadata_id', types.Integer, ForeignKey("image_metadata.id"), nullable=False),
    Column('title', types.String(length=128), nullable=False),
    Column('description', types.Text, nullable=False),
    Column('description_parsed', types.Text, nullable=False),
    Column('type', submission_type_type, nullable=False),
    Column('discussion_id', types.Integer, nullable=False),
    Column('time', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('status', submission_status_type, index=True, nullable=False),
    Column('mogile_key', types.String(150), nullable=False),
    Column('mimetype', types.String(35), nullable=False),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    mysql_engine='InnoDB'
)

derived_submission_table = Table('derived_submission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('submission_id', types.Integer, ForeignKey("submission.id"), nullable=False),
    Column('derivetype', derived_submission_derivetype_type, nullable=False),
    Column('mogile_key', types.String(150), nullable=False),
    Column('mimetype', types.String(35), nullable=False),
    mysql_engine='InnoDB'
)

historic_submission_table = Table('historic_submission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('submission_id', types.Integer, ForeignKey("submission.id"), nullable=False),
    Column('mogile_key', types.String(150), nullable=False),
    Column('mimetype', types.String(35), nullable=False),
    Column('edited_at', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('edited_by_id', types.Integer, ForeignKey('user.id')),
    mysql_engine='InnoDB'
)

user_submission_table = Table('user_submission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('user_id', types.Integer, ForeignKey("user.id")),
    Column('submission_id', types.Integer, ForeignKey("submission.id")),
    Column('relationship', user_submission_relationship_type, nullable=False),
    Column('ownership_status', user_submission_ownership_status_type, nullable=False),
    Column('review_status', user_submission_review_status_type, nullable=False),
    mysql_engine='InnoDB'
)

editlog_table = Table('editlog', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('last_edited_at', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('last_edited_by_id', types.Integer, ForeignKey('user.id')),
    mysql_engine='InnoDB'
)

editlog_entry_table = Table('editlog_entry', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    Column('edited_at', DateTimeAsInteger, nullable=False, default=datetime.now),
    Column('edited_by_id', types.Integer, ForeignKey('user.id')),
    Column('reason', types.String(length=250)),
    Column('previous_title', types.Text, nullable=False),
    Column('previous_text', types.Text, nullable=False),
    Column('previous_text_parsed', types.Text, nullable=False),
    mysql_engine='InnoDB'
)

# Comments

comment_table = Table('comment', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('user_id', types.Integer, ForeignKey('user.id')),
    Column('left', types.Integer, nullable=False),
    Column('right', types.Integer, nullable=False),
    Column('content', types.Unicode, nullable=False),
    Column('content_parsed', types.Unicode, nullable=False),
    Column('content_short', types.Unicode, nullable=False),
    mysql_engine='InnoDB'
)

news_comment_table = Table('news_comment', metadata,
    Column('news_id', types.Integer, ForeignKey('news.id'), primary_key=True),
    Column('comment_id', types.Integer, ForeignKey('comment.id'), primary_key=True),
    mysql_engine='InnoDB'
)

# Tags

tag_table = Table('tag', metadata,
    Column('id', types.Integer, primary_key=True, autoincrement=False),
    Column('text', types.String(length=20), index=True, unique=True),
    mysql_engine='InnoDB'
)

submission_tag_table = Table('submission_tag', metadata,
    #Column('id', types.Integer, primary_key=True),
    Column('submission_id', types.Integer, ForeignKey('submission.id'), primary_key=True, autoincrement=False),
    Column('tag_id', types.Integer, ForeignKey('tag.id'), primary_key=True, autoincrement=False),
    mysql_engine='InnoDB'
)

# Mappers

class JournalEntry(object):
    def __init__(self, user_id, title, content):
        content = h.escape_once(content)
        self.user_id = user_id
        self.discussion_id = 0
        self.title = title
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)

        self.status = 'normal'

    def update_content (self, content):
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        
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
                words.append(rmex.sub('',word))
            words = set(words)
            for word in words:
                xapian_document.add_term("T%s"%word)

            # description
            words = []
            # FIX ME: needs bbcode parser. should be plain text representation.
            for word in self.content.lower().split(' '):
                words.append(rmex.sub('',word))
            words = set(words)
            for word in words:
                xapian_document.add_term("P%s"%word)

            return xapian_document
        else:
            return None

class Permission(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description

class Role(object):
    @classmethod
    def get_by_name(cls, name):
        """Fetch a role, given its name."""
        try:
            return Session.query(cls).filter_by(name=name).one()
        except InvalidRequestError:
            return None

    def __init__(self, name, description=''):
        self.name = name
        self.description = description

class UserPreference(object):
    def __init__(self, user, key, value):
        self.user = user
        self.key = key
        self.value = value

class GuestRole(object):
    def __init__(self):
        self.name = "Guest"
        self.description = "Just a guest"
        self.sigil = ""

class GuestUser(object):
    '''Dummy object for not-logged-in users'''
    preferences = dict(
        style_sheet='duality',
        style_color='dark',
    )

    def __init__(self):
        self.id = 0
        self.username = "guest"
        self.display_name = "guest"
        self.role = GuestRole()
        self.is_guest = True

    def __nonzero__(self):
        '''Guest user objects evaluate to False so we can simply test the truth
        of c.auth_user to see if the user is logged in.'''
        return False

    def can(self, permission):
        return False

    def preference(self, pref):
        return self.preferences[pref]

class User(object):
    @classmethod
    def get_by_name(cls, username):
        """Fetch a user, given eir username."""
        try:
            return Session.query(cls).filter_by(username=username).one()
        except InvalidRequestError:
            return None

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
        self.display_name = username
        self.role = Role.get_by_name('Unverified')

    def set_password(self, password):
        algo_name = 'sha256'
        algo = hashlib.new(algo_name)
        algo.update(str(random.random()))
        salt = algo.hexdigest()[-10:]
        algo = hashlib.new(algo_name)
        algo.update(salt + password)
        self.password = "%s$%s$%s" % (algo_name, salt, algo.hexdigest())

    def check_password(self, password):
        (algo_name, salt, hashed_password) = self.password.split('$')
        algo = hashlib.new(algo_name)
        algo.update(salt)
        algo.update(password)
        return algo.hexdigest() == hashed_password

    def is_online(self):
        ip_log_q = Session.query(IPLogEntry).with_parent(self)
        last_log_entry = ip_log_q.order_by(IPLogEntry.end_time.desc()).first()
        if last_log_entry:
            return datetime.now() - last_log_entry.end_time < timedelta(0, 60 * 15)
        else:
            return False

    def can(self, permission):
        perm_q = Session.query(Role).with_parent(self).filter(
            Role.permissions.any(name=permission)
        )
        return perm_q.count() > 0

    def preference(self, pref):
        try:
            return self._preference_cache[pref]
        except AttributeError:
            self._preference_cache = dict()
            self._preference_cache.update(GuestUser.preferences)
            for row in self.preferences:
                self._preference_cache[row.key] = row.value
            return self._preference_cache[pref]

    def unread_note_count(self):
        """
        Returns the number of unread notes this user has.
        """

        return Session.query(Note) \
            .filter(Note.to_user_id == self.id) \
            .filter(Note.status == 'unread') \
            .count()

    def recent_notes(self):
        """
        Finds the most recent note in each of this user's conversations, in
        order from newest to oldest.  Returns a query object that can be paged
        however desired.
        """

        # Group-wise maximum, as inspired by the MySQL manual.  The only
        # difference between this and the example in the manual is that I add
        # the receipient's user id to the ON clause, ensuring that rows
        # belonging to each user are clustered together, and then filter out the
        # desired user with a WHERE.
        # I say "I" instead of "we" because this took me two days to figure out
        # and I think it's pretty fucking cool -- enough that I am going to put
        # my name on it.                                             -- Eevee

        older_note_a = note_table.alias()

        note_q = Session.query(Note).select_from(note_table
            .outerjoin(older_note_a,
                sql.and_(
                    note_table.c.original_note_id == older_note_a.c.original_note_id,
                    note_table.c.to_user_id == older_note_a.c.to_user_id,
                    note_table.c.time < older_note_a.c.time
                    )
                )
            ) \
            .filter(older_note_a.c.id == None) \
            .filter(Note.to_user_id == self.id) \
            .order_by(Note.time.desc())

        return note_q

class IPLogEntry(object):
    def __init__(self, user_id, ip_integer):
        self.user_id = user_id
        self.ip = ip_integer
        self.start_time = datetime.now()
        self.end_time = datetime.now()

class Submission(object):
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

    # Deprecated. Use get_derived_by_type instead.
    def get_derived_index (self,types):
        for index in xrange(0,len(self.derived_submission)):
            for type in types:
                if self.derived_submission[index].derivetype == type:
                    return index
        return None

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

    def to_xapian(self):
        if search_enabled:
            xapian_document = xapian.Document()
            xapian_document.add_term("I%d" % self.id)
            xapian_document.add_value(0, "I%d" % self.id)
            xapian_document.add_term("A%s" % self.primary_artist.id)

            # tags
            for tag in self.tags:
                xapian_document.add_term("G%s" % tag.text)

            # title
            words = []
            rmex = re.compile(r'[^a-z0-9-]')
            for word in self.title.lower().split(' '):
                words.append(rmex.sub('', word))
            words = set(words)
            for word in words:
                xapian_document.add_term("T%s" % word)

            # description
            words = []
            # FIX ME: needs bbcode parser. should be plain text representation.
            for word in self.description.lower().split(' '):
                words.append(rmex.sub('', word))
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
        print self.mimetype

        if self.type == 'image':
            toobig = None
            with Thumbnailer() as t:
                t.parse(self.file_blob,self.mimetype)
                toobig = t.generate(int(pylons.config['gallery.fullfile_size']))

            if toobig:
                self.file_blob = toobig['content']
        elif self.type == 'text':
            print self.mimetype
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
            with Thumbnailer() as t:
                t.parse(self.file_blob, self.mimetype)
                half_fileobject = t.generate(int(pylons.config['gallery.halfview_size']))

            if half_fileobject:
                new_derived_submission = False
                if not current:
                    current = DerivedSubmission('halfview')
                    new_derived_submission = True
                filename_parts = os.path.splitext(self.mogile_key)
                current.mogile_key = filename_parts[0] + '.half' + filename_parts[1]
                current.mimetype = self.mimetype
                current.file_blob = half_fileobject['content']
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
        with Thumbnailer() as t:
            use_self = True
            dont_bother = False
            if proposed:
                proposed_mimetype = get_mime_type(proposed)
                proposed_type = self.get_submission_type(proposed_mimetype)
                if proposed_type == 'image':
                    t.parse(proposed['content'], proposed_mimetype)
                    use_self = False

            if use_self:
                if self.type == 'image' and self.file_blob:
                    t.parse(self.file_blob, self.mimetype)
                else:
                    dont_bother = True

            if not dont_bother:
                thumb_fileobject = t.generate(int(pylons.config['gallery.thumbnail_size']))
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
            current.file_blob = thumb_fileobject['content']
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

class UserSubmission(object):
    def __init__(self, user_id, relationship, ownership_status, review_status):
        self.user_id = user_id
        self.relationship = relationship
        self.ownership_status = ownership_status
        self.review_status = review_status

class DerivedSubmission(object):
    def __init__(self, derivetype):
        self.derivetype = derivetype

class HistoricSubmission(object):
    def __init__(self, user):
        self.edited_by = user

    def _get_previous_title(self):
        return "Historic Submission: %s" % self.mogile_key
    previous_title = property(_get_previous_title)

    def _get_previous_text_parsed(self):
        return "[%s]"%h.link_to('View Historic Submission',h.url_for(controller='gallery', action='file', filename=self.mogile_key))
    previous_text_parsed = property(_get_previous_text_parsed)


class News(object):
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        self.author = author

    def update_content (self, content):
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        
class EditLog(object):
    def __init__(self,user):
        self.last_edited_by = user
        self.last_edited_at = datetime.now

    def update(self,editlog_entry):
        self.last_edited_by = editlog_entry.edited_by
        self.last_edited_at = editlog_entry.edited_at
        self.entries.append(editlog_entry)

class EditLogEntry(object):
    def __init__(self, user, reason, previous_title, previous_text, previous_text_parsed):
        self.edited_by = user
        self.edited_at = datetime.now()
        self.reason = reason
        self.previous_title = previous_title
        self.previous_text = previous_text
        self.previous_text_parsed = previous_text_parsed

class Comment(object):
    def add_to_nested_set(self, parent, discussion):
        """Call on a new Comment to fix the affected nested set values.
        
        discussion paremeter is the news/journal/submission this comment
        belongs to, so we don't have to hunt it down again.
        """

        # The new comment's left should be the parent's old right, as it's
        # being inserted as the last descendant, and every left or right
        # value to the right of that should be bumped up by two.
        parent_right = parent.right

        bridge_table = news_comment_table
        join = sql.exists([1],
            sql.and_(
                bridge_table.c.news_id == discussion.id,
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

        self.left = parent_right
        self.right = parent_right + 1

        self._parent = parent
        self._discussion = discussion

        # Don't forget to actually add the new comment..
        discussion.comments.append(self)

    def get_discussion(self):
        """Returns this comment's associated news/journal/submission."""
        if not hasattr(self, '_discussion'):
            self._discussion = Session.query(News).get(1)
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
        self.content = content
        self.content_parsed = content
        self.content_short = content

class SubmissionTag(object):
    def __init__(self, tag):
        self.tag = tag

class Tag(object):
    def __init__(self, text):
        self.text = text
        self.id = crc32(text)

class Note(object):
    def __init__(self, from_user_id, to_user_id, subject, content, original_note_id=None):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.subject = subject
        self.content = content
        self.content_parsed = bbcode.parser.parse(content)
        self.original_note_id = original_note_id
        self.status = 'unread'
        self.time = datetime.now()

    def update_content (self, content):
        self.content = content
        self.content_parsed = bbcode.parser.parse(content)
        
    def latest_note(self, recipient):
        """
        Returns the latest note in this note's thread, preferring one that was
        addressed to the provided recipient.
        """
        note_q = Session.query(Note).filter_by(original_note_id=self.original_note_id)
        latest_note = note_q.filter_by(to_user_id=recipient.id) \
            .order_by(Note.time.desc()) \
            .first()

        # TODO perf
        if not latest_note:
            # No note from this user on this thread
            latest_note = note_q.order_by(Note.time.desc()) \
                .first()

        return latest_note

    def base_subject(self):
        """
        Returns the subject without any prefixes attached.
        """
        return re.sub('^(Re: |Fwd: )+', '', self.subject)

ip_log_mapper = mapper(IPLogEntry, ip_log_table, properties=dict(
    user=relation(User, backref='ip_log')
    ),
)

user_mapper = mapper(User, user_table, properties=dict(
    role = relation(Role),
    preferences = relation(UserPreference, backref='user'),
    journals = relation(JournalEntry, backref='user'),
    user_submission = relation(UserSubmission, backref='user')
    ),
)

user_preference_mapper = mapper(UserPreference, user_preference_table)

editlog_mapper = mapper(EditLog, editlog_table, properties=dict(
    last_edited_by = relation(User)
    )
)

editlog_entry_mapper = mapper(EditLogEntry, editlog_entry_table, properties=dict(
    editlog = relation(EditLog, backref='entries'),
    edited_by = relation(User),
    )
)

news_mapper = mapper(News, news_table, properties=dict(
    author = relation(User),
    editlog = relation(EditLog),
    comments = relation(Comment, secondary=news_comment_table, order_by=comment_table.c.left),
    )
)

user_submission_mapper = mapper(UserSubmission, user_submission_table, properties=dict(
    submission = relation(Submission, backref='user_submission')
    )
)

submission_mapper = mapper(Submission, submission_table, properties=dict(
    editlog = relation(EditLog)
    )
)

derived_submission_mapper = mapper(DerivedSubmission,derived_submission_table, properties=dict(
    submission = relation(Submission, backref='derived_submission', lazy=False)
    )
)

historic_submission_mapper = mapper(HistoricSubmission,historic_submission_table, properties=dict(
    submission = relation(Submission, backref='historic_submission'),
    edited_by = relation(User)
    )
)

permission_mapper = mapper(Permission, permission_table)

role_mapper = mapper(Role, role_table, properties={
    'permissions':relation(Permission, secondary=role_permission_table)
})

journal_entry_mapper = mapper(JournalEntry, journal_entry_table, properties=dict(
    editlog = relation(EditLog)
    )
)

comment_mapper = mapper(Comment, comment_table, properties=dict(
    user = relation(User, backref='comments')
    )
)

tag_mapper = mapper(Tag, tag_table, properties=dict(
    submissions = relation(Submission, backref='tags', secondary=submission_tag_table)
    )
)

note_mapper = mapper(Note, note_table, properties=dict(
    sender = relation(User, primaryjoin=note_table.c.from_user_id==user_table.c.id),
    recipient = relation(User, primaryjoin=note_table.c.to_user_id==user_table.c.id),
    )
)

