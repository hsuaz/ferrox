from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.lib.formgen import FormGenerator
from furaffinity.model import form

import formencode
import logging

log = logging.getLogger(__name__)

class NewsController(BaseController):
    def index(self):
        """Paged list of all news."""
        page_link_var = 'p'
        page = request.params.get(page_link_var, 0)
        news_q = model.Session.query(model.News)
        news_q = news_q.order_by(model.News.time.desc())
        c.newspage = paginate.Page(news_q, page_nr=page, items_per_page=10)
        c.newsnav = c.newspage.navigator(link_var=page_link_var)
        return render('news/index.mako')

    def view(self, id):
        page_link_var = 'p'
        page = request.params.get(page_link_var, 0)
        news_q = model.Session.query(model.News)
        news_q = news_q.filter_by(id=id)
        c.news = news_q.one()
        return render('news/view.mako')

    @check_perm('administrate')
    def post(self):
        """Form for posting news."""
        c.form = FormGenerator()
        return render('news/post.mako')

    @check_perm('administrate')
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
        model.Session.save(news)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('administrate')
    def edit(self):
        """Form for editing news."""
        c.form = FormGenerator()
        c.item = model.Session.query(model.News).get(c.id)
        c.form.defaults = h.to_dict(c.item)
        return render('news/edit.mako')

    @check_perm('administrate')
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
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('administrate')
    def delete(self):
        """Form handler for deleting news."""
        news_q = model.Session.query(model.News)
        item = news_q.filter_by(id=c.id).one()
        item.is_deleted = True
        model.Session.save(item)
        model.Session.commit()
        h.redirect_to('/news')

    @check_perm('administrate')
    def undelete(self):
        """Form handler for restoring deleted news."""
        news_q = model.Session.query(model.News)
        item = news_q.filter_by(id=c.id).one()
        item.is_deleted = False
        model.Session.save(item)
        model.Session.commit()
        h.redirect_to('/news')
