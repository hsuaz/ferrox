from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator
import ferrox.lib.paginate as paginate
from ferrox.model import form
from pylons import config

import formencode
import logging

from sqlalchemy import sql

log = logging.getLogger(__name__)

class CommentsController(BaseController):
    def _get_parent_post(self, post_url):
        # Need to prepend a slash to make this an absolute URL
        route = config['routes.map'].match('/' + post_url)

        if route['action'] != 'view':
            abort(404)

        if route['controller'] == u'news':
            table = model.News
        elif route['controller'] == 'journal':
            table = model.JournalEntry
        elif route['controller'] == 'gallery':
            table = model.Submission
        else:
            abort(404)

        # XXX validate that this item matches the comment
        item = model.Session.query(table).get(route['id'])
        if item:
            return item
        else:
            abort(404)

    def view(self, post_url, id=None):
        """View a comment subtree, or all comments if no id is given."""
        c.post_url = post_url
        post = self._get_parent_post(post_url)

        if id == None:
            # No parent
            c.comments = post.discussion.comments
        else:
            # Parent and its children
            parent = model.Session.query(model.Comment).get(id)

            if not parent or parent.discussion != post.discussion:
                abort(404)

            c.comments = model.Session.query(model.Comment) \
                .filter(model.Comment.discussion_id == parent.discussion.id) \
                .filter(model.Comment.left >= parent.left) \
                .filter(model.Comment.left <= parent.right) \
                .all()

        return render('comments/view.mako')

    @check_perm('comments.reply')
    def reply(self, post_url, id=None):
        """Post a comment, either top-level or replying to another comment."""
        post = self._get_parent_post(post_url)
        c.form = FormGenerator()
        if id:
            c.comment = model.Session.query(model.Comment).get(id)

            if c.comment.discussion != post.discussion:
                abort(404)
        else:
            c.comment = None
        return render('comments/reply.mako')

    @check_perm('comments.reply')
    def reply_commit(self, post_url, id=None):
        """Form handler for reply to a comment."""
        post = self._get_parent_post(post_url)
        if id:
            c.parent = model.Session.query(model.Comment).get(id)

            if c.parent.discussion != post.discussion:
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
            title = h.escape_once(form_data['title']),
            content = h.escape_once(form_data['content']),
            discussion = post.discussion,
            parent = c.parent,
        )
        model.Session.save(comment)
        model.Session.commit()

        h.redirect_to(h.url_for(controller='comments', action='view',
                                post_url=post_url,
                                id=comment.id))
