import logging

from furaffinity.lib.base import *
from furaffinity.lib.formgen import FormGenerator

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
        c.form = FormGenerator()
        c.form.defaults = {'username': '',
                           'email': '',
                           'email_confirm': '',
                           'password': '',
                           'password_confirm': ''}
        return render('/register.mako')

    def register_check(self):
        schema = model.form.RegisterForm(foo = 'bar')
        try:
            form_data = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
            import sys
            sys.stderr.write(str(c.form.errors))
            return render('/register.mako')

        username = form_data['username']
        email = form_data['email']
        password = form_data['password']
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
        return render('/register_success.mako')

    def verify(self):
        username = request.params['username']
        code = request.params['code']
        user = model.retrieve_user(username)
        hasher = hashlib.md5()
        hasher.update(user.username)
        hasher.update(str(user.id))
        hash = hasher.hexdigest()
        if hash == code:
            user.role = model.retrieve_role('Member')
            model.Session.commit()
        c.verified = (hash == code)
        return render('/verify.mako')

    def login(self):
        if c.auth_user:
            # This shouldn't really happen, so no need to be nice about it
            h.redirect_to('/')

        c.form = FormGenerator()
        return render('/login.mako')

    #@https()
    def login_check(self):
        if c.auth_user:
            # This shouldn't really happen, so no need to be nice about it
            h.redirect_to('/')

        username = request.params.get('username', '')
        user_q = model.Session.query(model.User)
        user = user_q.filter_by(username = username).first()
        c.form = FormGenerator()
        if user and user.check_password(request.params.get('password')):
            if not user.can('log_in'):
                c.error_msgs.append("This account (%s) still needs to be verified. " \
                                    "Please check the email address provided for the " \
                                    "verification code." % h.escape_once(username))
                c.form.defaults['username'] = username
                return render('/login.mako')
            else:
                session['user_id'] = user.id
                session.save()
                h.redirect_to(request.headers.get('referer', '/'))
        else:
            c.error_msgs.append("Either there is no such account '%s', or the provided password was incorrect." % h.escape_once(username))
            c.form.defaults['username'] = username
            return render('/login.mako')

    def logout(self):
        session['user_id'] = None
        session.save()
        h.redirect_to(request.headers.get('referer', '/'))
