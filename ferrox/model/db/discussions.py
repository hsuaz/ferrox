from ferrox.model.db import BaseTable

from sqlalchemy import Column, types
from sqlalchemy.orm import object_mapper, relation
from sqlalchemy.ext.declarative import DeclarativeMeta

class Discussion(BaseTable):
    __tablename__       = 'discussions'
    id                  = Column(types.Integer, primary_key=True)
    comment_count       = Column(types.Integer, nullable=False, default=0)

    def get_parent_post(self):
        """Returns this discussion's associated news/journal/submission."""
        if not hasattr(self, '_parent_post'):
            self._parent_post = (self.news
                            or self.journal_entry
                            or self.submission)[0]
        return self._parent_post
