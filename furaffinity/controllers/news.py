import logging

from furaffinity.lib.base import *

from pylons.decorators.secure import *

log = logging.getLogger(__name__)

class NewsController(BaseController):

    def index(self):
        news_q = model.Session.query(model.News)
        c.news = news_q.order_by(model.News.time.desc())
        return render('news/index.mako')

    def post(self):
        return render('news/post.mako')
        
    def do_post(self):
        title = request.params.get('title')
        content = request.params.get('content')
        news = model.News(title, content)
        news.author = c.auth_user
        model.Session.save(news)
        model.Session.commit()
        h.redirect_to('/news')

