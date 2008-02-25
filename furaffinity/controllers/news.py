import logging

import formencode

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.lib.formgen import FormGenerator
from furaffinity.model import form

log = logging.getLogger(__name__)

class NewsController(BaseController):

    def index(self):
        page_link_var = 'p'
        page = request.params.get(page_link_var, 0)
        news_q = model.Session.query(model.News)
        news_q = news_q.order_by(model.News.time.desc())
        c.newspage = paginate.Page(news_q, page_nr=page, items_per_page=10)
        c.newsnav = c.newspage.navigator(link_var=page_link_var)
        return render('news/index.mako')

    @check_perm('administrate')
    def post(self):
        c.form = FormGenerator()
        return render('news/post.mako')

    @check_perm('administrate')
    def do_post(self):
        c.form = FormGenerator()
        schema = model.form.NewsForm()
        try:
            form_result = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form.defaults = error.value
            c.form.errors = error.error_dict
            return render('news/post.mako')

        title = h.escape_once(form_result['title'])
        content = h.escape_once(form_result['content'])
        news = model.News(title, content, c.auth_user)
        news.is_anonymous = form_result['is_anonymous']
        model.Session.save(news)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('administrate')
    def edit(self):
        c.form = FormGenerator()
        news_q = model.Session.query(model.News)
        c.item = news_q.filter_by(id = c.id).one()
        c.form.defaults = h.to_dict(c.item)
        import sys
        sys.stderr.write(str(c.form.defaults))
        return render('news/edit.mako')

    @check_perm('administrate')
    def edit_commit(self, id):
        c.form = FormGenerator()
        news_q = model.Session.query(model.News)
        c.item = news_q.filter_by(id = id).one()
        schema = model.form.NewsForm()
        try:
            form_result = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form.defaults = error.value
            c.form.errors = error.error_dict
            return render('news/edit.mako')

        title = h.escape_once(form_result['title'])
        content = h.escape_once(form_result['content'])
        if c.item.title != title or c.item.content != content:
            if c.item.editlog == None:
                c.item.editlog = model.EditLog(c.auth_user)
            editlog_entry = model.EditLogEntry(c.auth_user, 'no reasons yet',
                c.item.title,c.item.content,c.item.content)
            c.item.editlog.update(editlog_entry)
            c.item.title = title
            c.item.content = content
        c.item.is_anonymous = form_result['is_anonymous']
        model.Session.save(c.item)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('administrate')
    def delete(self):
        news_q = model.Session.query(model.News)
        item = news_q.filter_by(id = c.id).one()
        item.is_deleted = True
        model.Session.save(item)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('administrate')
    def undelete(self):
        news_q = model.Session.query(model.News)
        item = news_q.filter_by(id = c.id).one()
        item.is_deleted = False
        model.Session.save(item)
        model.Session.commit()
        h.redirect_to('/news')

