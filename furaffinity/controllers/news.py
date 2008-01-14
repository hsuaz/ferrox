import logging

import formencode

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate 

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
        c.form_defaults = {'title': '', 'content': ''}
        return render('news/post.mako')

    @check_perm('administrate')
    def do_post(self):
        schema = model.form.NewsForm()
        try:
            form_result = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form_defaults = error.value
            print c.form_defaults
            c.form_errors = error.error_dict or {}
            return render('news/post.mako')            
        else:
            title = h.escape_once(form_result['title'])
            content = h.escape_once(form_result['content'])
            news = model.News(title, content, c.auth_user)
            news.is_anonymous = form_result['is_anonymous']
            model.Session.save(news)
            model.Session.commit()
            h.redirect_to('/news')
        
    @check_perm('administrate')
    def edit(self):
        news_q = model.Session.query(model.News)
        c.item = news_q.filter_by(id = c.id).one()
        print dir(c.item)
        c.form_defaults = h.to_dict(c.item)
        return render('news/edit.mako')

    @check_perm('administrate')
    def edit_commit(self, id):
        news_q = model.Session.query(model.News)
        c.item = news_q.filter_by(id = id).one()
        schema = model.form.NewsForm()
        try:
            form_result = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form_defaults = error.value
            print c.form_defaults
            c.form_errors = error.error_dict or {}
            return render('news/edit.mako')            
        else:
            title = h.escape_once(form_result['title'])
            content = h.escape_once(form_result['content'])
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

