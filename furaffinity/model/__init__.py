try:
    import hashlib
    use_hashlib = True
except:
    import sha
    use_hashlib = False

import random

import pylons

from sqlalchemy import Column, MetaData, Table, ForeignKey, types, sql
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.databases.mysql import MSInteger, MSEnum
from sqlalchemy.exceptions import InvalidRequestError

from datetime import datetime

from datetime import datetime, timedelta
from enum import *
import re

import sys
from binascii import crc32

search_enabled = True
try:
    import xapian
except ImportError:
    search_enabled = False

#This plays hell with websetup, so only use where needed.
#from furaffinity.lib import filestore

Session = scoped_session(sessionmaker(autoflush=True, transactional=True,
    bind=pylons.config['pylons.g'].sa_engine))

metadata = MetaData()

# Database specific types.
if re.match('^mysql', pylons.config['sqlalchemy.url']):
    ip_type = MSInteger(unsigned=True)
    # MSEnum is horribly broken.
    #hash_algorithm_type = MSEnum('WHIRLPOOL','SHA512','SHA256','SHA1')
    #journal_status_type = MSEnum('normal','under_review','removed_by_admin','deleted')
    #submission_type_type = MSEnum('image','video','audio','text')
    #submission_status_type = MSEnum('normal','under_review','removed_by_admin','unlinked','deleted')
    #derived_submission_derivetype_type = MSEnum('thumb')
    #user_submission_status_type = MSEnum('primary','normal','deleted')
    #user_submission_relationship_type = MSEnum('artist','commissioner','gifted','isin')
else:
    ip_type = types.String(length=11)
#hash_algorithm_type = Enum(['WHIRLPOOL','SHA512','SHA256','SHA1'])
note_status_type = Enum(['unread','read'])
journal_status_type = Enum(['normal','under_review','removed_by_admin','deleted'])
submission_type_type = Enum(['image','video','audio','text'])
submission_status_type = Enum(['normal','under_review','removed_by_admin','unlinked','deleted'])
derived_submission_derivetype_type = Enum(['thumb','halfview'])
user_submission_status_type = Enum(['primary','normal','deleted'])
user_submission_relationship_type = Enum(['artist','commissioner','gifted','isin'])

# Users

user_table = Table('user', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('username', types.String(32), nullable=False),
    Column('email', types.String(256), nullable=False),
    Column('password', types.String(256), nullable=False),
    #Column('salt', types.String(5), nullable=False),
    #Column('hash_algorithm', hash_algorithm_type, nullable=False),
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
    Column('start_time', types.DateTime, nullable=False, default=datetime.now),
    Column('end_time', types.DateTime, nullable=False, default=datetime.now),
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
    Column('time', types.DateTime, nullable=False, default=datetime.now),
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
    Column('time', types.DateTime, nullable=False, default=datetime.now),
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
    Column('time', types.DateTime, nullable=False, default=datetime.now),
    Column('is_anonymous', types.Boolean, nullable=False, default=False),
    Column('is_deleted', types.Boolean, nullable=False, default=False),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    mysql_engine='InnoDB'
)

# Submissions

image_metadata_table = Table('image_metadata', metadata,
    Column('id', types.Integer, primary_key=True, autoincrement=True),
    Column('hash', types.String(length=64), nullable=False, unique=True, index=True),
    Column('height', types.Integer, nullable=False),
    Column('width', types.Integer, nullable=False),
    Column('mimetype', types.String(length=35), nullable=False),
    Column('submission_count', types.Integer, nullable=False),
    mysql_engine='InnoDB'
)

submission_table = Table('submission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('image_metadata_id', types.Integer, ForeignKey("image_metadata.id"), nullable=False),
    Column('title', types.String(length=128), nullable=False),
    Column('description', types.Text, nullable=False),
    Column('description_parsed', types.Text, nullable=False),
    Column('type', submission_type_type, nullable=False),
    Column('discussion_id', types.Integer, nullable=False),
    Column('time', types.DateTime, nullable=False, default=datetime.now),
    Column('status', submission_status_type, index=True, nullable=False),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    mysql_engine='InnoDB'
)

derived_submission_table = Table('derived_submission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('submission_id', types.Integer, ForeignKey("submission.id"), nullable=False),
    Column('image_metadata_id', types.Integer, ForeignKey("image_metadata.id"), nullable=False),
    Column('derivetype', derived_submission_derivetype_type, nullable=False),
    mysql_engine='InnoDB'
)

user_submission_table = Table('user_submission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('user_id', types.Integer, ForeignKey("user.id")),
    Column('submission_id', types.Integer, ForeignKey("submission.id")),
    Column('relationship', user_submission_relationship_type, nullable=False),
    Column('status', user_submission_status_type, nullable=False),
    mysql_engine='InnoDB'
)

editlog_table = Table('editlog', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('last_edited_at', types.DateTime, nullable=False, default=datetime.now),
    Column('last_edited_by_id', types.Integer, ForeignKey('user.id')),
    mysql_engine='InnoDB'
)

editlog_entry_table = Table('editlog_entry', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('editlog_id', types.Integer, ForeignKey('editlog.id')),
    Column('edited_at', types.DateTime, nullable=False, default=datetime.now),
    Column('edited_by_id', types.Integer, ForeignKey('user.id')),
    Column('reason', types.String(length=250)),
    Column('previous_title', types.Text, nullable=False),
    Column('previous_text', types.Text, nullable=False),
    Column('previous_text_parsed', types.Text, nullable=False),
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
    def __init__(self, user_id, title, content, content_parsed):
        self.user_id = user_id
        self.discussion_id = 0
        self.title = title
        self.content = content
        self.content_parsed = content_parsed
        self.status = 'normal'

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

def retrieve_role(name):
    try:
        return Session.query(Role).filter_by(name=name).one()
    except InvalidRequestError:
        return None

class Role(object):
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

def retrieve_user(username):
    try:
        return Session.query(User).filter_by(username=username).one()
    except InvalidRequestError:
        return None

class User(object):
    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
        self.display_name = username
        self.role = retrieve_role('Unverified')

    def set_password(self, password):
        if use_hashlib:
            algo_name = 'sha256'
            algo = hashlib.new(algo_name)
            algo.update(str(random.random()))
            salt = algo.hexdigest()[-10:]
            algo = hashlib.new(algo_name)
            algo.update(salt + password)
            self.password = "%s$%s$%s" % (algo_name, salt, algo.hexdigest())
        else:
            algo_name = 'sha1'
            algo = sha.new()
            algo.update(str(random.random()))
            salt = algo.hexdigest()[-10:]
            algo = sha.new()
            algo.update(salt + password)
            self.password = "%s$%s$%s" % (algo_name, salt, algo.hexdigest())

    def check_password(self, password):
        (algo_name, salt, hashed_password) = self.password.split('$')
        if use_hashlib:
            algo = hashlib.new(algo_name)
            algo.update(salt)
            algo.update(password)
            return algo.hexdigest() == hashed_password
        else:
            if algo_name != 'sha1':
                raise RuntimeError("Hashed password needs python2.5")
            algo = sha.new()
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

class ImageMetadata(object):
    def __init__(self, hash, height, width, mimetype, count, disable=False ):
        self.hash = hash
        self.height = height
        self.width = width
        self.mimetype = mimetype
        if disable:
            self.submission_count = -count
        else:
            self.submission_count = count

    def count_inc(self):
        if self.submission_count > 0:
            sign = abs(self.submission_count) / self.submission_count
        else:
            sign = 1
        self.submission_count = sign * (abs(self.submission_count) + 1)

    def count_dec(self):
        if self.submission_count > 0:
            sign = abs(self.submission_count) / self.submission_count
            self.submission_count = sign * (abs(self.submission_count) - 1)

    def enable(self):
        self.submission_count = abs(self.submission_count)

    def disable(self):
        self.submission_count = -abs(self.submission_count)

    def is_enabled(self):
        return ( self.submission_count > 0 )

    def get_filename(self):
        from furaffinity.lib import filestore
        return filestore.get_submission_file(self)



class IPLogEntry(object):
    def __init__(self, user_id, ip_integer):
        self.user_id = user_id
        self.ip = ip_integer
        self.start_time = datetime.now()
        self.end_time = datetime.now()

class Submission(object):
    def __init__(self, title, description, description_parsed, type, discussion_id, status ):
        self.title = title
        self.description = description
        self.description_parsed = description_parsed
        self.type = type
        self.discussion_id = discussion_id
        self.status = status

    def primary_artist(self):
        #return self.user_submission[0].user
        for index in xrange(0,len(self.user_submission)):
            if self.user_submission[index].status == 'primary':
                return self.user_submission[index].user

    # Deprecated. Use get_derived_by_type instead.
    def get_derived_index (self,types):
        for index in xrange(0,len(self.derived_submission)):
            for type in types:
                if self.derived_submission[index].derivetype == type:
                    return index
        return None

    def get_derived_by_type (self, type):
        for index in xrange(0,len(self.user_submission)):
            if self.derived_submission[index].derivetype == type:
                return self.derived_submission[index]
        return None

    def get_users_by_relationship (self, relationship):
        users = []
        for index in xrange(0,len(self.user_submission)):
            if self.user_submission[index].relationship == relationship:
                users.append( self.user_submission[index].user )
        return users

    def to_xapian(self):
        if search_enabled:
            xapian_document = xapian.Document()
            xapian_document.add_term("I%d"%self.id)
            xapian_document.add_value(0,"I%d"%self.id)
            xapian_document.add_term("A%s"%self.primary_artist().id)

            # tags
            for tag in self.tags:
                xapian_document.add_term("G%s"%tag.text)

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
            for word in self.description.lower().split(' '):
                words.append(rmex.sub('',word))
            words = set(words)
            for word in words:
                xapian_document.add_term("P%s"%word)

            return xapian_document
        else:
            return None

class UserSubmission(object):
    def __init__(self, user_id, relationship, status ):
        self.user_id = user_id
        self.relationship = relationship
        self.status = status

class DerivedSubmission(object):
    def __init__(self, derivetype ):
        self.derivetype = derivetype

class News(object):
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author

class EditLog(object):
    def __init__(self,user):
        self.last_edited_by = user
        self.last_edited_at = datetime.now()

    def update(self,editlog_entry):
        self.last_edited_by = editlog_entry.edited_by
        self.last_edited_at = editlog_entry.edited_at
        self.editlog_entries.append(editlog_entry)

class EditLogEntry(object):
    def __init__(self, user, reason, previous_title, previous_text, previous_text_parsed):
        self.edited_by = user
        self.edited_at = datetime.now()
        self.reason = reason
        self.previous_title = previous_title
        self.previous_text = previous_text
        self.previous_text_parsed = previous_text_parsed

class SubmissionTag(object):
    def __init__ (self, tag):
        self.tag = tag

class Tag(object):
    def __init__ (self, text):
        self.text = text
        self.id = crc32(text)

class Note(object):
    def __init__(self, from_user_id, to_user_id, subject, content, original_note_id=None):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.subject = subject
        self.content = content
        self.content_parsed = content  # bbcode placeholder
        self.original_note_id = original_note_id
        self.status = 'unread'
        self.time = datetime.now()

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
    editlog = relation(EditLog, backref='editlog_entries'),
    edited_by = relation(User),
    )
)

news_mapper = mapper(News, news_table, properties=dict(
    author = relation(User),
    editlog = relation(EditLog),
    )
)

user_submission_mapper = mapper(UserSubmission, user_submission_table, properties=dict(
    submission = relation(Submission, backref='user_submission')
    )
)

image_metadata_mapper = mapper(ImageMetadata, image_metadata_table)

submission_mapper = mapper(Submission, submission_table, properties=dict(
    metadata = relation(ImageMetadata, backref='submission'),
    editlog = relation(EditLog)
    )
)

derived_submission_mapper = mapper(DerivedSubmission,derived_submission_table, properties=dict(
    submission = relation(Submission, backref='derived_submission'),
    metadata = relation(ImageMetadata, backref='derived_submission')
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

tag_mapper = mapper(Tag, tag_table, properties=dict(
    submissions = relation(Submission, backref='tags', secondary=submission_tag_table)
    )
)

note_mapper = mapper(Note, note_table, properties=dict(
    sender = relation(User, primaryjoin=note_table.c.from_user_id==user_table.c.id),
    recipient = relation(User, primaryjoin=note_table.c.to_user_id==user_table.c.id),
    )
)
