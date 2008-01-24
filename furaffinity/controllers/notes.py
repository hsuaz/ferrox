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
        notes_q = c.page_owner.recent_notes()
        c.notes_page = paginate.Page(notes_q, page_nr=page, items_per_page=20)
        c.notes_nav = c.notes_page.navigator(link_var='page')
        return render('notes/index.mako')

    def view(self, username, id):
        c.page_owner = model.retrieve_user(username)
        note_q = model.Session.query(model.Note)
        try:
            c.note = note_q.filter_by(id=id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            abort(404)

        if c.note.recipient != c.page_owner:
            abort(404)

        c.all_notes = note_q.filter_by(original_note_id=c.note.original_note_id) \
            .filter(sql.or_(
                model.Note.from_user_id == c.page_owner.id,
                model.Note.to_user_id == c.page_owner.id
                )) \
            .order_by(model.Note.time.desc())

        return render('notes/view.mako')
