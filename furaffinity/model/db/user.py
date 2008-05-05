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
from furaffinity.model.datetimeasint import *
from furaffinity.model.enum import *

### Custom types

if re.match('^mysql', pylons.config['sqlalchemy.url']):
    ip_type = MSInteger(unsigned=True)
else:
    ip_type = types.String(length=11)

note_status_type = Enum(['unread','read'])

### Dummy classes

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

### Roles and permissions

class Role(BaseTable):
    __tablename__   = 'role'
    id              = Column(types.Integer, primary_key=True)
    name            = Column(types.String(length=32), nullable=False)
    sigil           = Column(types.String(length=1), nullable=False)
    description     = Column(types.String(length=256), nullable=False)
#    mysql_engine='InnoDB'

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

class Permission(BaseTable):
    __tablename__   = 'permission'
    id              = Column(types.Integer, primary_key=True)
    name            = Column(types.String(length=32), nullable=False)
    description     = Column(types.String(length=256), nullable=False)
#    mysql_engine='InnoDB'

    def __init__(self, name, description):
        self.name = name
        self.description = description

class RolePermission(BaseTable):
    __tablename__   = 'role_permission'
    role_id         = Column(types.Integer, ForeignKey('role.id'), primary_key=True)
    permission_id   = Column(types.Integer, ForeignKey('permission.id'), primary_key=True)
#    mysql_engine='InnoDB'

Role.permissions = relation(Permission, secondary=RolePermission.__table__)

### Main user tables

class User(BaseTable):
    __tablename__   = 'user'
    id              = Column(types.Integer, primary_key=True)
    username        = Column(types.String(32), nullable=False)
    email           = Column(types.String(256), nullable=False)
    password        = Column(types.String(256), nullable=False)
    display_name    = Column(types.Unicode, nullable=False)
    role_id         = Column(types.Integer, ForeignKey('role.id'), default=1)
#    mysql_engine='InnoDB'

    role            = relation(Role)
#    journals = relation(JournalEntry, backref='user')
#    user_submission = relation(UserSubmission, backref='user')

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

class IPLogEntry(BaseTable):
    __tablename__   = 'ip_log'
    id              = Column(types.Integer, primary_key=True)
    user_id         = Column(types.Integer, ForeignKey('user.id'), nullable=False)
    ip              = Column(ip_type, nullable=False)
    start_time      = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
    end_time        = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
#    mysql_engine='InnoDB'

    user            = relation(User, backref='ip_log')

    def __init__(self, user_id, ip_integer):
        self.user_id = user_id
        self.ip = ip_integer
        self.start_time = datetime.now()
        self.end_time = datetime.now()

class UserPreference(BaseTable):
    __tablename__   = 'user_preference'
    user_id         = Column(types.Integer, ForeignKey('user.id'), primary_key=True)
    key             = Column(types.String(length=32), primary_key=True)
    value           = Column(types.String(length=256), nullable=False)
#    mysql_engine='InnoDB'
    user            = relation(User, backref='preferences')

    def __init__(self, user, key, value):
        self.user = user
        self.key = key
        self.value = value

class Note(BaseTable):
    __tablename__   = 'note'
    id              = Column(types.Integer, primary_key=True)
    from_user_id    = Column(types.Integer, ForeignKey('user.id'))
    to_user_id      = Column(types.Integer, ForeignKey('user.id'))
    original_note_id= Column(types.Integer, ForeignKey('note.id'))
    subject         = Column(types.Unicode, nullable=False)
    content         = Column(types.Unicode, nullable=False)
    content_parsed  = Column(types.Unicode, nullable=False)
    status          = Column(note_status_type, nullable=False)
    time            = Column(DateTimeAsInteger, nullable=False, default=datetime.now)
#    mysql_engine='InnoDB'

    sender          = relation(User, primaryjoin=(from_user_id==User.id))
    recipient       = relation(User, primaryjoin=(to_user_id==User.id))

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
        self.content = h.escape_once(content)
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

