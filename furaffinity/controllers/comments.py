from furaffinity.lib.base import *
from furaffinity.lib.formgen import FormGenerator
import furaffinity.lib.paginate as paginate
from furaffinity.model import form
from pylons import config

import formencode
import logging

from sqlalchemy import sql

log = logging.getLogger(__name__)

class CommentsController(BaseController):
    def _get_discussion(self, discussion_url):
        # Need to prepend a slash to make this an absolute URL
        route = config['routes.map'].match('/' + discussion_url)

        if route['action'] != 'view':
            abort(404)

        if route['controller'] == 'news':
            table = model.News
        elif route['controller'] == 'journal':
            table = model.JournalEntry
        elif route['controller'] == 'gallery':
            table = model.Submission
        else:
            abort(404)

        # XXX validate that this item matches the comment
        item = model.Session.query(table).get(route['id'])
        print item
        if item:
            return item
        else:
            abort(404)

    def view(self, discussion_url, id=None):
        """View a comment subtree, or all comments if no id is given."""
        c.discussion_url = discussion_url
        discussion = self._get_discussion(discussion_url)

        if id == None:
            # No parent
            c.comments = discussion.comments
        else:
            # Parent and its children
            parent = model.Session.query(model.Comment).get(id)

            if parent.get_discussion() != discussion:
                abort(404)

            c.comments = model.Session.query(model.Comment) \
                .with_parent(discussion, property='comments') \
                .filter(model.Comment.left >= parent.left) \
                .filter(model.Comment.left <= parent.right) \
                .all()

        return render('comments/view.mako')

    def reply(self, discussion_url, id=None):
        """Post a comment, either top-level or replying to another comment."""
        discussion = self._get_discussion(discussion_url)
        c.form = FormGenerator()
        if id:
            c.comment = model.Session.query(model.Comment).get(id)

            if c.comment.get_discussion() != discussion:
                abort(404)
        else:
            c.comment = None
        return render('comments/reply.mako')

    def reply_commit(self, discussion_url, id=None):
        """Form handler for reply to a comment."""
        discussion = self._get_discussion(discussion_url)
        if id:
            c.parent = model.Session.query(model.Comment).get(id)

            if c.parent.get_discussion() != discussion:
                abort(404)
        else:
            c.parent = None
        validator = model.form.CommentForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
            return render('comments/reply.mako')

        comment = model.Comment(
            user = c.auth_user,
            subject = h.escape_once(form_data['subject']),
            content = h.escape_once(form_data['content']),
        )
        model.Session.save(comment)

        comment.add_to_nested_set(c.parent, discussion)

        model.Session.commit()
        h.redirect_to(h.url_for(controller='comments', action='view',
                                discussion_url=discussion_url,
                                id=comment.id))
