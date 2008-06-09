import pylons

from sqlalchemy import MetaData
from sqlalchemy.databases.mysql import MSEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from furaffinity.model.db.types import Enum, DateTime, IP

_engine = pylons.config['pylons.g'].sa_engine

Session = scoped_session(sessionmaker(autoflush=True, transactional=True,
                                      bind=_engine))

metadata = MetaData()

BaseTable = declarative_base(metadata=metadata)


# MySQL has a real enum type
if _engine.url.drivername == 'mysql':
    Enum = MSEnum
    # However, it sucks and requires us to quote everything even though every
    # enum value has to be a string.  So let's fix that

    old_init = Enum.__init__
    def new_init(self, *enums, **kwargs):
        enums = ["'%s'" % x for x in enums]
        return old_init(self, *enums, **kwargs)
    
    Enum.__init__ = new_init
