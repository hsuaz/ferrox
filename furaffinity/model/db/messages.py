from furaffinity.model.db import BaseTable, DateTime, Enum, IP, Session
from furaffinity.model.db.user import *

class Message(BaseTable):
    """
    Table to contain any sort of "message", as a lot of these columns were
    grossly duplicated across half a dozen other tables.
    """

    __tablename__       = 'messages'
    id                  = Column(types.Integer, primary_key=True)
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
#    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, nullable=False, default=datetime.now)
    subject             = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    content             = Column(types.UnicodeText, nullable=False)
    content_parsed      = Column(types.UnicodeText, nullable=False)
    content_short       = Column(types.UnicodeText, nullable=False)
    avatar              = relation(UserAvatar)
#    editlog             = relation(EditLog)
    user                = relation(User)

    def __init__(self, subject, content, user):
        self.subject = subject
        self.content = content
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        self.user = user
        self.avatar_id = None

    def update_content(self, content):
        self.content = h.escape_once(content)
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)

class MessageDelegator(object):
    """Tiny base class for delegating to self.message when appropriate."""
    def __getattr__(self, name):
        if self.message and hasattr(self.message, name):
            return getattr(self.message, name)
        raise AttributeError

class News(BaseTable, MessageDelegator):
    __tablename__       = 'news'
    id                  = Column(types.Integer, primary_key=True)
    message_id          = Column(types.Integer, ForeignKey('messages.id'))
    is_anonymous        = Column(types.Boolean, nullable=False, default=False)
    is_deleted          = Column(types.Boolean, nullable=False, default=False)
    message             = relation(Message, lazy=False)

    def __init__(self, title, content, author):
        self.message = Message(subject=title, content=content, user=author)

