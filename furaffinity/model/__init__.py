from furaffinity.model.db import Session, metadata
from furaffinity.model.db.user import *
from furaffinity.model.db.blob import *

# Run through tables and set their mysql engines all to InnoDB
for table in metadata.tables:
    metadata.tables[table].kwargs['mysql_engine'] = 'InnoDB'
