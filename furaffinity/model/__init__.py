from furaffinity.model.db import Session, metadata
from furaffinity.model.db.users import *
from furaffinity.model.db.messages import *
from furaffinity.model.db.submissions import *

# Run through tables and set their mysql engines all to InnoDB
for table in metadata.tables:
    metadata.tables[table].kwargs['mysql_engine'] = 'InnoDB'
