from furaffinity.model.db import BaseTable, DateTime, Enum, IP, Session
from furaffinity.model.db.user import *

from sqlalchemy.orm import object_mapper, relation

search_enabled = True
try:
    import xapian
    if xapian.major_version() < 1:
        search_enabled = False
except ImportError:
    search_enabled = False


class EditLog(BaseTable):
    __tablename__       = 'editlog'
    id                  = Column(types.Integer, primary_key=True)
    last_edited_at      = Column(DateTime, nullable=False, default=datetime.now)
    last_edited_by_id   = Column(types.Integer, ForeignKey('users.id'))
    last_edited_by      = relation(User)

    def __init__(self,user):
        self.last_edited_by = user
        self.last_edited_at = datetime.now

    def update(self,editlog_entry):
        self.last_edited_by = editlog_entry.edited_by
        self.last_edited_at = editlog_entry.edited_at
        self.entries.append(editlog_entry)

class EditLogEntry(BaseTable):
    __tablename__       = 'editlog_entries'
    id                  = Column(types.Integer, primary_key=True)
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    edited_at           = Column(DateTime, nullable=False, default=datetime.now)
    edited_by_id        = Column(types.Integer, ForeignKey('users.id'))
    reason              = Column(types.String(length=250))
    previous_title      = Column(types.UnicodeText, nullable=False)
    previous_text       = Column(types.UnicodeText, nullable=False)
    previous_text_parsed= Column(types.UnicodeText, nullable=False)
    editlog             = relation(EditLog, backref='entries')
    edited_by           = relation(User)

    def __init__(self, user, reason, previous_title, previous_text, previous_text_parsed):
        self.edited_by = user
        self.edited_at = datetime.now()
        self.reason = reason
        self.previous_title = previous_title
        self.previous_text = previous_text
        self.previous_text_parsed = previous_text_parsed

class Message(BaseTable):
    """
    Table to contain any sort of "message", as a lot of these columns were
    grossly duplicated across half a dozen other tables.

    Tables that join to this should have classes that also inherit from
    MessageDelegator; this will allow you to access Message columns as if
    they were in your class, without confusing SQLalchemy.
    """
    # XXX constructor inheritance

    __tablename__       = 'messages'
    id                  = Column(types.Integer, primary_key=True)
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
#    discussion_id       = Column(types.Integer, ForeignKey('discussions.id'))
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    content             = Column(types.UnicodeText, nullable=False)
    content_parsed      = Column(types.UnicodeText, nullable=False)
    content_short       = Column(types.UnicodeText, nullable=False)
    avatar              = relation(UserAvatar)
    editlog             = relation(EditLog)
    user                = relation(User)

    def __init__(self, title, content, user):
        self.title = title
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
        if hasattr(Message, name):
            return getattr(self.message, name)
        raise AttributeError

    def __setattr__(self, name, value):
        if hasattr(Message, name):
            setattr(self.message, name, value)
        else:
            BaseTable.__setattr__(self, name, value)

class News(BaseTable, MessageDelegator):
    __tablename__       = 'news'
    id                  = Column(types.Integer, primary_key=True)
    message_id          = Column(types.Integer, ForeignKey('messages.id'))
    is_anonymous        = Column(types.Boolean, nullable=False, default=False)
    is_deleted          = Column(types.Boolean, nullable=False, default=False)
    message             = relation(Message, lazy=False)

    def __init__(self, title, content, author):
        self.message = Message(title=title, content=content, user=author)

class JournalEntry(BaseTable, MessageDelegator):
    __tablename__       = 'journal_entries'
    id                  = Column(types.Integer, primary_key=True)
    message_id          = Column(types.Integer, ForeignKey('messages.id'))
    status              = Column(Enum('normal', 'under_review', 'removed_by_admin', 'deleted'), index=True, default='normal')
    message             = relation(Message, lazy=False)

    def __init__(self, user, title, content):
        content = h.escape_once(content)
        self.message = Message(title=title, content=content, user=user)

    def __str__(self):
        return "Journal entry titled %s" % self.title
    
    def update_content (self, content):
        self.content = h.escape_once(content)
        self.content_parsed = bbcode.parser_long.parse(content)
        self.content_short = bbcode.parser_short.parse(content)
        self.content_plain = bbcode.parser_plaintext.parse(content)

    def to_xapian(self):
        if not search_enabled:
            return None

        xapian_document = xapian.Document()
        xapian_document.add_term("I%d" % self.id)
        xapian_document.add_value(0, "I%d" % self.id)
        xapian_document.add_term("A%s" % self.user.id)

        # Title
        words = []
        rmex = re.compile(r'[^a-z0-9-]')
        for word in self.title.lower().split(' '):
            words.append(rmex.sub('', word[0:20]))
        for word in set(words):
            xapian_document.add_term("T%s" % word)

        # Description
        words = []
        # FIX ME: needs bbcode parser. should be plain text representation.
        for word in self.content_plain.lower().split(' '):
            words.append(rmex.sub('', word[0:20]))
        for word in set(words):
            xapian_document.add_term("P%s" % word)

        return xapian_document

class Comment(BaseTable, MessageDelegator):
    __tablename__       = 'comments'
    id                  = Column(types.Integer, primary_key=True)
    message_id          = Column(types.Integer, ForeignKey('messages.id'))
    left                = Column(types.Integer, nullable=False)
    right               = Column(types.Integer, nullable=False)
    message             = relation(Message, lazy=False)

    def __init__(self, user, title, content):
        self.message = Message(title=title, content=content, user=user)
        self.left = 0
        self.right = 0

    def add_to_nested_set(self, parent, discussion):
        """Call on a new Comment to fix the affected nested set values.
        
        discussion paremeter is the news/journal/submission this comment
        belongs to, so we don't have to hunt it down again.
        """

        # Easy parts; remember the parent/discussion and add to bridge table
        self._parent = parent
        self._discussion = discussion

        discussion.comments.append(self)

        if not parent:
            # This comment is a brand new top-level one; its left and right
            # need to be higher than the highest right
            last_comment = Session.query(Comment) \
                .with_parent(discussion, property='comments') \
                .order_by(Comment.right.desc()) \
                .first()
            if last_comment:
                self.left = last_comment.right + 1
                self.right = last_comment.right + 2
            else:
                # First comment at all
                self.left = 1
                self.right = 2

            return

        # Otherwise, we're replying to an existing comment.
        # The new comment's left should be the parent's old right, as it's
        # being inserted as the last descendant, and every left or right
        # value to the right of that should be bumped up by two.
        parent_right = parent.right

        self.left = parent_right
        self.right = parent_right + 1

        # Sure wish this reflection stuff were documented
        bridge_table = object_mapper(discussion) \
                       .get_property('comments') \
                       .secondary
        foreign_column = None
        for c in bridge_table.c:
            if c.name != 'comment_id':
                foreign_column = c
                break

        join = sql.exists([1],
            and_(
                foreign_column == discussion.id,
                bridge_table.c.comment_id == Comment.id,
                )
            )

        for side in ['left', 'right']:
            column = getattr(Comment.__table__.c, side)
            Session.execute(
                Comment.__table__.update(
                    and_(column >= parent_right, join),
                    values={column: column + 2}
                    )
                )

    def get_discussion(self):
        """Returns this comment's associated news/journal/submission."""
        if not hasattr(self, '_discussion'):
            self._discussion = (self.news
                                or self.journal_entry
                                or self.submission)[0]
        return self._discussion

    def get_parent(self):
        """Returns this comment's parent."""
        if not hasattr(self, '_parent'):
            self._parent = Session.query(Comment) \
                .with_parent(self.get_discussion(), property='comments') \
                .filter(Comment.left < self.left) \
                .filter(Comment.right > self.left) \
                .order_by(Comment.left.desc()) \
                .first()
        return self._parent

class Note(BaseTable, MessageDelegator):
    __tablename__   = 'notes'
    id              = Column(types.Integer, primary_key=True)
    message_id          = Column(types.Integer, ForeignKey('messages.id'))
    to_user_id      = Column(types.Integer, ForeignKey('users.id'))
    original_note_id= Column(types.Integer, ForeignKey('notes.id'))
    status          = Column(Enum('unread', 'read'), nullable=False, default='unread')
    message             = relation(Message, lazy=False)
    recipient       = relation(User)

    # Create a 'sender' wrapper property, as the usual 'user' property that
    # Message has is a bit vague with two user relations
    def __set_sender(self, sender):
        self.message.user = sender
    def __get_sender(self):
        return self.message.user
    sender          = property(__get_sender, __set_sender)


    def __init__(self, sender, recipient, title, content, original_note_id=None):
        self.message = Message(title=title, content=content, user=sender)
        self.recipient = recipient
        self.original_note_id = original_note_id

    def latest_note(self, recipient):
        """
        Returns the latest note in this note's thread, preferring one that was
        addressed to the provided recipient.
        """
        note_q = Session.query(Note).filter_by(original_note_id=self.original_note_id)
        latest_note = note_q.filter_by(to_user_id=recipient.id) \
            .join('message') \
            .order_by(Message.time.desc()) \
            .first()

        # TODO perf
        if not latest_note:
            # No note from this user on this thread
            latest_note = note_q \
                .join('message') \
                .order_by(Message.time.desc()) \
                .first()

        return latest_note

    def base_subject(self):
        """
        Returns the subject without any prefixes attached.
        """
        return re.sub('^(Re: |Fwd: )+', '', self.title)

