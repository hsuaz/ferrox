from __future__ import with_statement

import pylons

from furaffinity.lib import helpers as h
import furaffinity.lib.bbcode_for_fa as bbcode
from furaffinity.lib.image import ImageClass
from furaffinity.lib.mimetype import get_mime_type

from sqlalchemy import Column, ForeignKey, types, sql
from sqlalchemy import and_, or_, not_
from sqlalchemy.orm import relation
from sqlalchemy.databases.mysql import MSInteger, MSSet
from sqlalchemy.exceptions import IntegrityError, InvalidRequestError
from sqlalchemy.orm import eagerload, eagerload_all

from datetime import datetime, timedelta
import hashlib
import random
import re
import cStringIO
from binascii import crc32

from furaffinity.model.db import BaseTable, DateTime, Enum, IP, Session

# -- This stuff is tied to class UserAvatar --
if pylons.config['mogilefs.tracker'] == 'FAKE':
    from furaffinity.lib import fakemogilefs as mogilefs
else:
    from furaffinity.lib import mogilefs

### Custom types

note_status_type = Enum('unread', 'read')
user_relationship_type = Enum('watching_submissions', 'watching_journals', 'friend_to', 'blocking')

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
    __tablename__   = 'roles'
    id              = Column(types.Integer, primary_key=True)
    name            = Column(types.String(length=32), nullable=False)
    sigil           = Column(types.String(length=1), nullable=False)
    description     = Column(types.String(length=256), nullable=False)

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
    __tablename__   = 'permissions'
    id              = Column(types.Integer, primary_key=True)
    name            = Column(types.String(length=32), nullable=False)
    description     = Column(types.String(length=256), nullable=False)

    def __init__(self, name, description):
        self.name = name
        self.description = description

class RolePermission(BaseTable):
    __tablename__   = 'role_permissions'
    role_id         = Column(types.Integer, ForeignKey('roles.id'), primary_key=True)
    permission_id   = Column(types.Integer, ForeignKey('permissions.id'), primary_key=True)

Role.permissions = relation(Permission, secondary=RolePermission.__table__)

### Main user tables

class User(BaseTable):
    __tablename__   = 'users'
    id              = Column(types.Integer, primary_key=True)
    username        = Column(types.String(32), nullable=False)
    email           = Column(types.String(256), nullable=False)
    password        = Column(types.String(256), nullable=False)
    display_name    = Column(types.UnicodeText, nullable=False)
    role_id         = Column(types.Integer, ForeignKey('roles.id'), default=1)

    role            = relation(Role)
#    journals = relation(JournalEntry, backref='user')
#    user_submission = relation(UserSubmission, backref='user')

    @classmethod
    def get_by_name(cls, username, eagerloads=[]):
        """Fetch a user, given eir username."""
        try:
            q = Session.query(cls).filter_by(username=username)
            for el in eagerloads:
                q = q.options(eagerload(el))
            return q.one()
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
        if not hasattr(self, '_preference_cache'):
            self._preference_cache = dict()
            self._preference_cache.update(GuestUser.preferences)
            for row in self.preferences:
                self._preference_cache[row.key] = row.value
        return self._preference_cache[pref]

    def metadatum(self, datum):
        """Returns an item from this user's metadata, with caching (so don't
        worry about calling this method repeatedly).

        Return value is a dict with 'description' and 'value' keys.
        """
        if not hasattr(self, '_metadata_cache'):
            self._metadata_cache = dict()
            for row in self.metadata:
                self._metadata_cache[row.field.key] = dict(
                    description=row.field.description,
                    value=row.value,
                    )

        if not datum in self._metadata_cache:
            datum_row = Session.query(UserMetadataField) \
                        .filter_by(key=datum) \
                        .one()
            self._metadata_cache[datum] = dict(
                description=datum_row.description,
                value='',
            )

        return self._metadata_cache[datum]

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

    def get_relationship(self, other_user, relationship):
        """Returns the requested relationship object, if it exists."""
        return Session.query(UserRelationship) \
               .filter_by(from_user_id=self.id,
                          to_user_id=other_user.id,
                          relationship=relationship) \
               .first()

    def add_relationship(self, other_user, relationship):
        rel = UserRelationship()
        rel.user = self
        rel.target = other_user
        rel.relationship = relationship
        try:
            Session.save(rel)
        except IntegrityError:
            pass
        return

class UserRelationship(BaseTable):
    __tablename__       = 'user_relationships'
    from_user_id        = Column(types.Integer, ForeignKey('users.id'), primary_key=True)
    to_user_id          = Column(types.Integer, ForeignKey('users.id'), primary_key=True)
    relationship        = Column(user_relationship_type, nullable=False)

    def __init__(self):
        self.relationship = set()

UserRelationship.user = relation(User, primaryjoin=UserRelationship.from_user_id==User.id, backref='relationships')
UserRelationship.target = relation(User, primaryjoin=UserRelationship.to_user_id==User.id)

class IPLogEntry(BaseTable):
    __tablename__   = 'ip_log'
    id              = Column(types.Integer, primary_key=True)
    user_id         = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    ip              = Column(IP, nullable=False)
    start_time      = Column(DateTime, nullable=False, default=datetime.now)
    end_time        = Column(DateTime, nullable=False, default=datetime.now)

    user            = relation(User, backref='ip_log')

    def __init__(self, user_id, ip_integer):
        self.user_id = user_id
        self.ip = ip_integer
        self.start_time = datetime.now()
        self.end_time = datetime.now()

class UserPreference(BaseTable):
    __tablename__   = 'user_preferences'
    user_id         = Column(types.Integer, ForeignKey('users.id'), primary_key=True)
    key             = Column(types.String(length=32), primary_key=True)
    value           = Column(types.String(length=256), nullable=False)

    user            = relation(User, backref='preferences')

    def __init__(self, user, key, value):
        self.user = user
        self.key = key
        self.value = value

### Metadata

class UserMetadataField(BaseTable):
    __tablename__   = 'user_metadata_fields'
    id              = Column(types.Integer, primary_key=True)
    key             = Column(types.Unicode(length=32), nullable=False)
    description     = Column(types.UnicodeText, nullable=False)

class UserMetadata(BaseTable):
    __tablename__   = 'user_metadata'
    user_id         = Column(types.Integer, ForeignKey('users.id'), primary_key=True)
    field_id        = Column(types.Integer, ForeignKey('user_metadata_fields.id'), primary_key=True)
    value           = Column(types.Unicode(length=255), nullable=False)
    
    user            = relation(User, backref='metadata')
    field           = relation(UserMetadataField, lazy=False)

### Notes

class Note(BaseTable):
    __tablename__   = 'notes'
    id              = Column(types.Integer, primary_key=True)
    from_user_id    = Column(types.Integer, ForeignKey('users.id'))
    to_user_id      = Column(types.Integer, ForeignKey('users.id'))
    original_note_id= Column(types.Integer, ForeignKey('notes.id'))
    subject         = Column(types.UnicodeText, nullable=False)
    content         = Column(types.UnicodeText, nullable=False)
    content_parsed  = Column(types.UnicodeText, nullable=False)
    status          = Column(note_status_type, nullable=False)
    time            = Column(DateTime, nullable=False, default=datetime.now)

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


class UserAvatar(BaseTable):
    __tablename__       = 'user_avatars'
    id                  = Column(types.Integer, primary_key=True, autoincrement=True)
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    default             = Column(types.Boolean)
    mogile_key          = Column(types.String(length=200))
    title               = Column(types.Unicode(length=200))
    
    def __init__(self):
        pass
        
    def write_to_mogile(self, file_object, user=None):
        # Note: Must do this before commit.
        
        if not user:
            user = self.user
        max_size = int(pylons.config.get('avatar.max_size', 120))
        max_filesize = int(pylons.config.get('avatar.max_file_size', 40)) * 1024
        with ImageClass() as t:
            t.set_data(file_object['content'])
            toobig = t.get_resized(max_size, True, (len(file_object['content']) < max_filesize))
            if toobig:
                file_object['content'] = toobig.get_data()

        self.mogile_key = "avatar_%s_%x_%s"%(user.username, crc32(file_object['content']), file_object['filename'][-50:])
        
        store = mogilefs.Client(pylons.config['mogilefs.domain'], [pylons.config['mogilefs.tracker']])
        blobstream = cStringIO.StringIO(file_object['content'])
        store.send_file(self.mogile_key, blobstream)
        blobstream.close()
        
    def delete_from_mogile(self):
        # Note: Must do this before removing object from database.
        
        store = mogilefs.Client(pylons.config['mogilefs.domain'], [pylons.config['mogilefs.tracker']])
        store.delete(self.mogile_key)

User.avatars = relation(UserAvatar, backref='user')
User.default_avatar = relation(UserAvatar, primaryjoin=and_(User.id == UserAvatar.user_id, UserAvatar.default == True), uselist=False, lazy=False)

class UserBan(BaseTable):
    __tablename__       = 'user_bans'
    id                  = Column(types.Integer, primary_key=True, autoincrement=True)
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    admin_user_id       = Column(types.Integer, ForeignKey('users.id'))
    expires             = Column(DateTime) # NULL = Never
    revert_to_id        = Column(types.Integer, ForeignKey('roles.id'))
    reason              = Column(types.UnicodeText, nullable=False)
    admin_message       = Column(types.UnicodeText, nullable=False)

    revert_to           = relation(Role)

UserBan.admin = relation(User, primaryjoin=(User.id == UserBan.admin_user_id))
User.bans = relation(UserBan, backref='user', primaryjoin=(User.id == UserBan.user_id))

    

