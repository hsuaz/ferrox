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

user_type_table = Table('user_type', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('sigil', types.String(1), nullable=False),
    Column('name', types.String(64), nullable=False)
)

user_table = Table('user', metadata,
    Column('id', types.Integer, primary_key=True),
    Column('username', types.String(32), nullable=False),
    Column('password', types.String(64), nullable=False),
    Column('display_name', types.Unicode, nullable=False),
    Column('user_type_id', types.Integer, ForeignKey("user_type.id"), default=1)
)

user_journals_table = Table('user_journal', metadata,
    Column('user_id', types.Integer, ForeignKey("user.id")),
    Column('journal_id', types.Integer, ForeignKey("journal.id"))
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

class UserType(object):
    pass
user_type_mapper = mapper(UserType, user_type_table)

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

    def is_admin(self):
        return self.user_type.sigil == '@'
user_mapper = mapper(User, user_table, properties = dict(
    journals = relation(Journal, secondary=user_journals_table),
    user_type = relation(UserType)
    ),
)

