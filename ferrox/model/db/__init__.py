from sqlalchemy import MetaData
from sqlalchemy.databases.mysql import MSEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

import sys

from ferrox.model.db.types import Enum, DateTime, IP

Session = scoped_session(sessionmaker())
metadata = MetaData()
BaseTable = declarative_base(metadata=metadata)

# XXX stopgap until bbcode is actually implemented and all use of these can be
# changed
BaseTable.content_short = property(lambda self: self.content)
BaseTable.content_parsed = property(lambda self: self.content)
BaseTable.content_plain = property(lambda self: self.content)

def connect(engine):
    Session.configure(autoflush=True, autocommit=False, bind=engine)

    if engine.url.drivername == 'mysql':
        # MySQL has a real enum type.
        # However, it sucks and requires us to quote everything even though
        # every enum value has to be a string.  So let's fix that:
        global Enum
        Enum = MSEnum

        old_init = Enum.__init__
        def new_init(self, *enums, **kwargs):
            enums = ["'%s'" % x for x in enums]
            return old_init(self, *enums, **kwargs)
        
        Enum.__init__ = new_init

# Only connect automatically if we're already within Pylons
if 'pylons' in sys.modules:
    import pylons
    engine = pylons.config['pylons.g'].sa_engine
    connect(engine)
