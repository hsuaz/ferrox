import random
try:
    import hashlib
    use_hashlib = True
except:
    import sha
    use_hashlib = False
    
import pylons

from sqlalchemy import Column, MetaData, Table, ForeignKey, types
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from furaffinity.model import form;

from datetime import datetime

from enum import *



Session = scoped_session(sessionmaker(autoflush=True, transactional=True,
    bind=pylons.config['pylons.g'].sa_engine))

metadata = MetaData()

# Users

user_table = Table('user', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('username', types.String(32), nullable=False),
    Column('password', types.String(64), nullable=False),
    Column('display_name', types.Unicode, nullable=False),
    Column('role_id', types.Integer, ForeignKey('role.id'), default=1)
)

role_table = Table('role', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('name', types.String(32), nullable=False),
    Column('sigil', types.String(1), nullable=False),
    Column('description', types.String(256), nullable=False),
)

role_permission_table = Table('role_permission', metadata,
    Column('role_id', types.Integer, ForeignKey('role.id'), primary_key=True),
    Column('permission_id', types.Integer, ForeignKey('permission.id'),
           primary_key=True),
)

permission_table = Table('permission', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('name', types.String(32), nullable=False),
    Column('description', types.String(256), nullable=False),
)

# Journals

journal_entry_table = Table('journal_entry', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('title', types.Unicode, nullable=False),
    Column('content', types.Unicode, nullable=False),
    Column('time', types.DateTime, nullable=False, default=datetime.now),
    Column('is_deleted', types.Boolean, nullable=False, default=False)
)

journal_table = Table('journal', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('header', types.Unicode),
    Column('footer', types.Unicode)
)

journal_entries_table = Table('journal_entries', metadata,
    Column('journal_id', types.Integer, ForeignKey("journal.id")),
    Column('journal_entry_id', types.Integer, ForeignKey("journal_entry.id"))
)

user_journals_table = Table('user_journal', metadata,
    Column('user_id', types.Integer, ForeignKey("user.id")),
    Column('journal_id', types.Integer, ForeignKey("journal.id"))
)

news_table = Table('news', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('author_user_id', types.Integer, ForeignKey("user.id")),
    Column('title', types.Unicode, nullable=False),
    Column('content', types.Unicode, nullable=False),
    Column('time', types.DateTime, nullable=False, default=datetime.now),
    Column('is_anonymous', types.Boolean, nullable=False, default=False),
    Column('is_deleted', types.Boolean, nullable=False, default=False),
)    
submission_table = Table('submission', metadata,
	Column('id', types.Integer, primary_key=True),
	Column('hash', types.String(64), nullable=False, unique=True, primary_key=True),
	Column('title', types.String(128), nullable=False),
	Column('description', types.String, nullable=False),
	Column('height', types.Integer, nullable=False),
	Column('width', types.Integer, nullable=False),
	Column('type', Enum(['image','video','audio','text'], empty_to_none=True, strict=True), nullable=False),
	Column('mimetype', types.String(35), nullable=False),
	Column('discussion_id', types.Integer, nullable=False),
    Column('time', types.DateTime, nullable=False, default=datetime.now),
    Column('status', Enum(['normal','under_review','removed_by_admin','unlinked','deleted'], empty_to_none=True, strict=True ), primary_key=True, nullable=False)
)

derived_submission_table = Table('derived_submission', metadata,
    Column('submission_id', types.Integer, ForeignKey("submission.id"), primary_key=True),
    Column('hash', types.String(64), nullable=False),
	Column('height', types.Integer, nullable=False),
	Column('width', types.Integer, nullable=False),
    Column('mimetype', types.String(20), nullable=False),
    Column('derivetype', Enum(['thumb'], empty_to_none=True, strict=True ), primary_key=True, nullable=False)
)

user_submission_table = Table('user_submission', metadata,
    Column('id', types.Integer, primary_key=True),
	Column('user_id', types.Integer, ForeignKey("user.id")),
	Column('submission_id', types.Integer, ForeignKey("submission.id")),
	Column('relationship', Enum(['artist','commissioner','gifted','isin'], empty_to_none=True, strict=True), nullable=False),
	Column('status', Enum(['primary','normal','deleted'], empty_to_none=True, strict=True), nullable=False),
)

class JournalEntry(object):
    def __init__(self, title, content):
        self.title = title
        self.content = content
journal_entry_mapper = mapper(JournalEntry, journal_entry_table)

class Journal(object):
    pass
journal_mapper = mapper(Journal, journal_table, properties = dict(
    entries = relation(JournalEntry, secondary=journal_entries_table, lazy=False)
    ),
)

class Permission(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description
permission_mapper = mapper(Permission, permission_table)

class Role(object):
    def __init__(self, name, description=''):
        self.name = name
        self.description = description
role_mapper = mapper(Role, role_table, properties={
    'permissions':relation(Permission, secondary=role_permission_table)
})

class User(object):
    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
        self.display_name = username

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

    def can(self, permission):
        perm_q = Session.query(Role).with_parent(self).filter(
            Role.permissions.any(name=permission)
        )
        return perm_q.count() > 0

class Submission(object):
    def __init__(self, hash, title, description, height, width, type, mimetype, discussion_id, status ):
        self.hash = hash
        self.title = title
        self.description = description
        self.height = height
        self.width = width
        self.type = type
        self.mimetype = mimetype
        self.discussion_id = discussion_id
        self.status = status

class UserSubmission(object):
    def __init__(self, user_id, relationship, status ):
        self.user_id = user_id
        #self.submission_id = submission_id
        self.relationship = relationship
        self.status = status

class DerivedSubmission(object):
    def __init__(self, hash, mimetype, derivetype, width, height ):
        self.hash = hash
        self.width = width
        self.height = height
        self.mimetype = mimetype
        self.derivetype = derivetype

user_mapper = mapper(User, user_table, properties = dict(
    journals = relation(Journal, secondary=user_journals_table),
    role = relation(Role),
    user_submission = relation(UserSubmission, backref='user')
    ),
)

class News(object):
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author
      
news_mapper = mapper(News, news_table, properties = dict(author = relation(User)),)


user_submission_mapper = mapper(UserSubmission, user_submission_table, properties=dict(
    submission = relation(Submission, backref='user_submission') #
    )
)

submission_mapper = mapper(Submission, submission_table)

derived_submission_mapper = mapper(DerivedSubmission,derived_submission_table, properties=dict(
    submission = relation(Submission, backref='derived_submission')
    )
)
