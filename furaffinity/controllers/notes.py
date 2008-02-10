import logging
import formencode
import sqlalchemy
from sqlalchemy import sql

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate

from furaffinity.model import form

log = logging.getLogger(__name__)

class NotesController(BaseController):

    def user_index(self, username):
        page = request.params.get('page', 0)
        c.page_owner = model.retrieve_user(username)
        note_q = c.page_owner.recent_notes()
        c.notes_page = paginate.Page(note_q, page_nr=page, items_per_page=20)
        c.notes_nav = c.notes_page.navigator(link_var='page')
        return render('notes/index.mako')

    def _note_setup(self, username, id):
        c.page_owner = model.retrieve_user(username)
        note_q = model.Session.query(model.Note)
        try:
            c.note = note_q.filter_by(id=id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            abort(404)

        if c.note.recipient != c.page_owner and c.note.sender != c.page_owner:
            abort(404)

    def view(self, username, id):
        self._note_setup(username, id)
        c.javascripts = ['notes']

        note_thread_id = c.note.original_note_id

        note_q = model.Session.query(model.Note)
        c.all_notes = note_q.filter_by(original_note_id=note_thread_id) \
            .filter(sql.or_(
                model.Note.from_user_id == c.page_owner.id,
                model.Note.to_user_id == c.page_owner.id
                )) \
            .order_by(model.Note.time.asc())

        c.latest_note = note_q.filter_by(original_note_id=note_thread_id) \
            .filter_by(to_user_id=c.page_owner.id) \
            .order_by(model.Note.time.desc()) \
            .first()

        rendered = render('notes/view.mako')

        # Mark all notes on this thread addressed to this user as read, but do
        # it *after* the page is rendered so the user can see what *was* unread
        # TODO perf
        if c.page_owner == c.auth_user:
            unread_notes = note_q.filter_by(original_note_id=note_thread_id) \
                .filter_by(to_user_id=c.page_owner.id) \
                .filter_by(status='unread') \
                .all()
            for note in unread_notes:
                note.status = 'read'
            model.Session.flush()

        return rendered

    def ajax_expand(self, username, id):
        self._note_setup(username, id)
        return render('notes/ajax_expand.mako')
