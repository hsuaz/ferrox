from ferrox.model.db import BaseTable
from ferrox.model.db.users import *

class Config(BaseTable):
    """
    Table to contain all config parametrs
    """

    __tablename__	= 'config'
    id			= Column(types.Integer, primary_key=True)
    section		= Column(types.String(length=32), nullable=False)
    name		= Column(types.String(length=32), nullable=False)
    type		= Column(types.Integer, nullable=False)
    pattern		= Column(types.UnicodeText)
    value		= Column(types.UnicodeText)
    comment		= Column(types.UnicodeText)
    hidden		= Column(types.Boolean, nullable=False)

    # Possible types:
    Regexp    = 1
    List      = 2
    MultiList = 3

    @classmethod
    def get(cls, name, section='global'):
        """
        Get a value from config section
        If section don't specified use section 'global'
        """
        try:
            return Session.query(cls).filter_by(name=name, section=section).one()
        except InvalidRequestError:
            return None

    @classmethod 
    def get_all(cls):
        """
        Get all values from DB
        """
        try:
            return Session.query(cls)
        except InvalidRequestError:
            return None

    @classmethod
    def set(cls, value, name, section='global'):
        """
        Set a value
        If section don't specified use section 'global'
        """
        try:
            row = Session.query(cls).filter_by(name=name, section=section).one()
        except InvalidRequestError:
            return None
        row.value = value

    @classmethod
    def get_sections(cls):
        """
        Get names of all available sections
        """
        try:
            return Session.query(cls.section).distinct()
        except InvalidRequestError:
            return None

    @classmethod
    def get_values_of(cls, section='global', offset=0, limit=20):
        """
        Get list of values from section
        """
        data = {}
        data["data"] = []

        try:
            data["total"] = Session.query(cls).filter_by(section=section).count()
        except InvalidRequestError:
            return None

        if not offset.isdigit() or offset < 0:
            offset = 0
        if not limit.isdigit() or limit < 0:
            limit = 20

        try:
            list = Session.query(cls).filter_by(section=section).order_by(Config.name.desc()).offset(offset).limit(limit)
        except InvalidRequestError:
            return None

        for row in list:
            data["data"].append((
                row.id,
                row.section,
                row.type,
                row.pattern,
                row.name,
                row.value,
                row.comment,
                row.name,
                row.value or '',
                row.comment or '',
            ))
        return data

    @classmethod
    def delete(cls, section, name):
        Session.query(cls).filter_by(name=name, section=section).delete()
        return None

    def __init__(self, section, name, type, pattern, value, comment, hidden):
        self.section 	= section
        self.name	= name
        self.type	= type
        self.pattern	= pattern
        self.value	= value
        self.comment	= comment
        self.hidden	= hidden
