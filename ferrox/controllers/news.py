from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator
from ferrox.model import form

import formencode
import logging
import sqlalchemy

log = logging.getLogger(__name__)

class NewsController(BaseController):
    def index(self):
        """Paged list of all news."""
        page_link_var = 'p'
        page = request.params.get(page_link_var, 0)
        c.newsitems = model.Session.query(model.News) \
                           .join('message') \
                           .order_by(model.Message.time.desc())
        return render('news/index.mako')

    def view(self, id):
        page_link_var = 'p'
        page = request.params.get(page_link_var, 0)
        c.news = model.Session.query(model.News).get(id)
        if not c.news:
            abort(404)
        return render('news/view.mako')

    @check_perm('news.manage')
    def post(self):
        """Form for posting news."""
        c.form = FormGenerator()
        return render('news/post.mako')

    @check_perm('news.manage')
    def do_post(self):
        """Form handler for posting news."""
        c.form = FormGenerator()
        schema = model.form.NewsForm()
        try:
            form_data = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form.defaults = error.value
            c.form.errors = error.error_dict
            return render('news/post.mako')

        title = h.escape_once(form_data['title'])
        #content = h.escape_once(form_data['content'])
        content = form_data['content']
        news = model.News(title, content, c.auth_user)
        news.is_anonymous = form_data['is_anonymous']
        if form_data['avatar_id']:
            av = model.Session.query(model.UserAvatar).filter_by(id = form_data['avatar_id']).filter_by(user_id = c.auth_user.id).one()
            news.avatar = av
        model.Session.save(news)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('news.manage')
    def edit(self):
        """Form for editing news."""
        c.form = FormGenerator()
        c.item = model.Session.query(model.News).get(c.id)
        c.form.defaults = h.to_dict(c.item)
        return render('news/edit.mako')

    @check_perm('news.manage')
    def edit_commit(self, id):
        """Form handler for editing news."""
        c.item = model.Session.query(model.News).get(id)
        schema = model.form.NewsForm()
        try:
            form_data = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
            return render('news/edit.mako')

        title = h.escape_once(form_data['title'])
        #content = h.escape_once(form_data['content'])
        content = form_data['content']
        if c.item.title != title or c.item.content != content:
            if c.item.editlog == None:
                c.item.editlog = model.EditLog(c.auth_user)
            editlog_entry = model.EditLogEntry(c.auth_user, 'no reasons yet',
                                               c.item.title, c.item.content,
                                               c.item.content_parsed)
            c.item.editlog.update(editlog_entry)
            c.item.title = title
            c.item.update_content(content)
        c.item.is_anonymous = form_data['is_anonymous']
        #c.item.avatar_id = form_data['avatar_id']
        if form_data['avatar_id']:
            av = model.Session.query(model.UserAvatar).filter_by(id = form_data['avatar_id']).filter_by(user_id = c.auth_user.id).one()
            c.item.avatar = av
        else:
            c.item.avatar = None
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('news.manage')
    def delete(self):
        """Form handler for deleting news."""
        news_q = model.Session.query(model.News)
        item = news_q.filter_by(id=c.id).one()
        item.is_deleted = True
        model.Session.save(item)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('news.manage')
    def undelete(self):
        """Form handler for restoring deleted news."""
        news_q = model.Session.query(model.News)
        item = news_q.filter_by(id=c.id).one()
        item.is_deleted = False
        model.Session.save(item)
        model.Session.commit()
        h.redirect_to('/news')
