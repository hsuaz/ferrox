from sqlalchemy import MetaData
from sqlalchemy.databases.mysql import MSEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

import sys

from furaffinity.model.db.types import Enum, DateTime, IP

Session = scoped_session(sessionmaker())
metadata = MetaData()
BaseTable = declarative_base(metadata=metadata)

def connect(engine):
    Session.configure(autoflush=True, autocommit=False, bind=engine)

    # MySQL has a real enum type
    if engine.url.drivername == 'mysql':
        global Enum
        Enum = MSEnum
        # However, it sucks and requires us to quote everything even though
        # every enum value has to be a string.  So let's fix that

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
