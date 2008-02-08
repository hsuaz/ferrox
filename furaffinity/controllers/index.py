import logging

from furaffinity.lib.base import *

from pylons.decorators.secure import *

import formencode
import hashlib

log = logging.getLogger(__name__)

class IndexController(BaseController):

    def index(self):
        news_q = model.Session.query(model.News)
        news_q = news_q.filter_by(is_deleted = False)
        news_q = news_q.order_by(model.News.time.desc())
        c.news = news_q.limit(5)
        return render('/index.mako')

    def register(self):
        c.form_defaults = {'username': '', 
                           'email': '',
                           'email_confirm': '',
                           'password': '',
                           'password_confirm': ''}
        return render('/register.mako')
    
    def register_check(self):
        schema = model.form.RegisterForm(foo = 'bar')
        try:
            form_result = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form_defaults = error.value
            c.form_errors = error.error_dict or {}
            return render('/register.mako')            
        else:
            username = form_result['username']
            email = form_result['email']
            password = form_result['password']
            user = model.User(username, password) 
            user.email = email
            model.Session.save(user)
            model.Session.commit()
            hasher = hashlib.md5()
            hasher.update(user.username)
            hasher.update(str(user.id))
            hash = hasher.hexdigest()
            c.verify_link = h.link_to('Verify', url=h.url_for(controller = 'index', 
                                                              action = 'verify', 
                                                              username = username, 
                                                              code = hash))
            return render('/regsuccess.mako')

    def verify(self):
        username = request.params['username']
        code = request.params['code']
        user_q = model.Session.query(model.User)
        user = user_q.filter_by(username = username).first()
        hasher = hashlib.md5()
        hasher.update(user.username)
        hasher.update(str(user.id))
        hash = hasher.hexdigest()
        if hash == code:
            user.verified = True
            model.Session.save(user)
            model.Session.commit()
        c.verified = (hash == code)
        return render('/verify.mako')

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
            if not user.verified:
                c.error_msgs.append("This account (%s) still needs to be verified. " \
                                    "Please check the email address provided for the " \
                                    "verification code." % h.escape_once(username))
                c.prefill['username'] = username
                return self.login()
            else:
                session['user_id'] = user.id
                session.save()
                h.redirect_to(request.headers.get('referer', '/'))
        else:
            c.error_msgs.append("Either there is no such account '%s', or the provided password was incorrect." % h.escape_once(username))
            c.prefill['username'] = username
            return self.login()

    def logout(self):
        session['user_id'] = None
        session.save()
        h.redirect_to(request.headers.get('referer', '/'))
