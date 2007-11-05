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

from datetime import datetime

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
    Column('is_deleted', types.Boolean, nullable=False, default=False)
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
user_mapper = mapper(User, user_table, properties = dict(
    journals = relation(Journal, secondary=user_journals_table),
    role = relation(Role)
    ),
)

class News(object):
    def __init__(self, title, content):
        self.title = title
        self.content = content
      
news_mapper = mapper(News, news_table, properties = dict(author = relation(User)),)


