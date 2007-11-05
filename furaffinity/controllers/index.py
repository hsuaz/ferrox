import logging

from furaffinity.lib.base import *

from pylons.decorators.secure import *

log = logging.getLogger(__name__)

class IndexController(BaseController):

    def index(self):
        news_q = model.Session.query(model.News)
        c.news = news_q.order_by(model.News.time.desc()).limit(5)
        return render('/index.mako')

    def register(self):
        return render('/register.mako')
    
    def login(self):
        if c.auth_user:
            # This shouldn't really happen, so no need to be nice about it
            h.redirect_to('/')
        return render('/login.mako')
        
    #@https()
    def login_check(self):
        username = request.params.get('username') or ''
        user_q = model.Session.query(model.User)
        user = user_q.filter_by(username = username).first()
        if user and user.check_password(request.params.get('password')):
            session['user_id'] = user.id
            session.save()
            h.redirect_to(request.headers.get('referer', '/'))
        else:
            c.error_msg = "Either there is no such account '%s', or the provided password was incorrect." % h.sanitize(username)
            c.prefill['username'] = username
            return self.login()

    def logout(self):
        session['user_id'] = None
        session.save()
        h.redirect_to(request.headers.get('referer', '/'))
