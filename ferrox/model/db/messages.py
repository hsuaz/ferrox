from ferrox.model.db import BaseTable, DateTime, Enum, IP, Session
from ferrox.model.db.users import *
from ferrox.model.db.discussions import *

from sqlalchemy.orm import object_mapper, relation
from sqlalchemy.ext.declarative import DeclarativeMeta

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

    def __init__(self, user, reason, previous_title, previous_text, previous_text_parsed=None):
        if not previous_text_parsed:
            previous_text_parsed = previous_text
        self.edited_by = user
        self.edited_at = datetime.now()
        self.reason = reason
        self.previous_title = previous_title
        self.previous_text = previous_text
        self.previous_text_parsed = previous_text_parsed

class Comment(BaseTable):
    __tablename__       = 'comments'
    id                  = Column(types.Integer, primary_key=True)
    discussion_id       = Column(types.Integer, ForeignKey('discussions.id'))
    left                = Column(types.Integer, nullable=False, default=0)
    right               = Column(types.Integer, nullable=False, default=0)

    # Message columns
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, index=True, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    content             = Column(types.UnicodeText, nullable=False)
    user                = relation(User)
    avatar              = relation(UserAvatar)
    editlog             = relation(EditLog)

    def __init__(self, parent=None, **kwargs):
        """Creates a new comment.  If a parent is specified, the other
        comments in this discussion will have their left/right values adjusted
        appropriately.
        """

        super(Comment, self).__init__(**kwargs)

        self._parent = parent

        if not parent:
            # This comment is a brand new top-level one; its left and right
            # need to be higher than the highest right
            last_comment = Session.query(Comment) \
                .filter(Comment.discussion_id == self.discussion_id) \
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

        for side in ['left', 'right']:
            column = getattr(Comment.__table__.c, side)
            Session.execute(
                Comment.__table__.update(
                    and_(column >= parent_right,
                         Comment.discussion_id == self.discussion_id
                         ),
                    values={column: column + 2}
                    )
                )

    def get_parent(self):
        """Returns this comment's parent."""
        if not hasattr(self, '_parent'):
            self._parent = Session.query(Comment) \
                .filter(Comment.discussion_id == self.discussion_id) \
                .filter(Comment.left < self.left) \
                .filter(Comment.right > self.left) \
                .order_by(Comment.left.desc()) \
                .first()
        return self._parent

class News(BaseTable):
    __tablename__       = 'news'
    id                  = Column(types.Integer, primary_key=True)
    discussion_id       = Column(types.Integer, ForeignKey('discussions.id'))
    is_anonymous        = Column(types.Boolean, nullable=False, default=False)
    is_deleted          = Column(types.Boolean, nullable=False, default=False)

    # Message columns
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, index=True, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    content             = Column(types.UnicodeText, nullable=False)
    user                = relation(User)
    avatar              = relation(UserAvatar)
    editlog             = relation(EditLog)

    def __init__(self, **kwargs):
        self.discussion = Discussion()
        super(News, self).__init__(**kwargs)

class JournalEntry(BaseTable):
    __tablename__       = 'journal_entries'
    id                  = Column(types.Integer, primary_key=True)
    discussion_id       = Column(types.Integer, ForeignKey('discussions.id'))
    status              = Column(Enum('normal', 'under_review', 'removed_by_admin', 'deleted'), index=True, default='normal')

    # Message columns
    user_id             = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, index=True, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    content             = Column(types.UnicodeText, nullable=False)
    user                = relation(User)
    avatar              = relation(UserAvatar)
    editlog             = relation(EditLog)

    def __init__(self, **kwargs):
        self.discussion = Discussion()
        super(JournalEntry, self).__init__(**kwargs)

    def __str__(self):
        return "Journal entry titled %s" % self.title
    
    def update_content (self, content):
        self.content = h.html_escape(content)
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

class Note(BaseTable):
    __tablename__       = 'notes'
    id                  = Column(types.Integer, primary_key=True)
    to_user_id          = Column(types.Integer, ForeignKey('users.id'))
    original_note_id    = Column(types.Integer, ForeignKey('notes.id'))
    status              = Column(Enum('unread', 'read'), nullable=False, default='unread')

    # Message columns
    # NOTE: user_id/user became from_user_id/sender
    from_user_id        = Column(types.Integer, ForeignKey('users.id'))
    avatar_id           = Column(types.Integer, ForeignKey('user_avatars.id'))
    editlog_id          = Column(types.Integer, ForeignKey('editlog.id'))
    time                = Column(DateTime, index=True, nullable=False, default=datetime.now)
    title               = Column(types.Unicode(length=160), nullable=False, default='(no subject)')
    content             = Column(types.UnicodeText, nullable=False)
    sender              = relation(User, primaryjoin=from_user_id==User.id)
    avatar              = relation(UserAvatar)
    editlog             = relation(EditLog)

    def latest_note(self, recipient):
        """
        Returns the latest note in this note's thread, preferring one that was
        addressed to the provided recipient.
        """
        note_q = Session.query(Note).filter_by(original_note_id=self.original_note_id)
        latest_note = note_q.filter_by(to_user_id=recipient.id) \
            .order_by(Note.time.desc()) \
            .first()

        # TODO perf
        if not latest_note:
            # No note from this user on this thread
            latest_note = note_q \
                .order_by(Note.time.desc()) \
                .first()

        return latest_note

    def base_subject(self):
        """
        Returns the subject without any prefixes attached.
        """
        return re.sub('^(Re: |Fwd: )+', '', self.title)

### Relations

Discussion.comments     = relation(Comment, backref='discussion', order_by=Comment.left)

EditLogEntry.edited_by  = relation(User)
EditLogEntry.editlog    = relation(EditLog, backref='entries')

EditLog.last_edited_by  = relation(User)

JournalEntry.discussion = relation(Discussion, backref='journal_entry')

News.discussion         = relation(Discussion, backref='news')

Note.recipient          = relation(User, primaryjoin=Note.to_user_id==User.id)
