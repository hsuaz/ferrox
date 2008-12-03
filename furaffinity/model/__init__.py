from ferrox.model.db import Session, metadata
from ferrox.model.db.users import *
from ferrox.model.db.messages import *
from ferrox.model.db.submissions import *

# Run through tables and set their mysql engines all to InnoDB
for table in metadata.tables:
    metadata.tables[table].kwargs['mysql_engine'] = 'InnoDB'
