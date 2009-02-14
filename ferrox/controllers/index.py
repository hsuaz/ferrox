from pylons.decorators.secure import *

from ferrox.controllers.gallery import find_submissions
from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator

import formencode
import hashlib
import logging

log = logging.getLogger(__name__)

class IndexController(BaseController):
    def index(self):
        """Main site index page."""
        c.news = model.Session.query(model.News) \
                      .filter_by(is_deleted=False) \
                      .order_by(model.News.time.desc()) \
                      .limit(5)

        c.recent_submissions = find_submissions(page_size=12)[0]
        return render('/index.mako')

    @check_perm('index.register')
    def register(self):
        """User registration."""
        c.form = FormGenerator()
        c.form.defaults = {'username': '',
                           'email': '',
                           'email_confirm': '',
                           'password': '',
                           'password_confirm': ''}
        return render('/register.mako')

    @check_perm('index.register')
    def register_check(self):
        """User registration POST target."""
        schema = model.form.RegisterForm()
        try:
            form_data = schema.to_python(request.params)
        except formencode.Invalid, error:
            c.form = FormGenerator(form_error=error)
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
        c.verify_link = h.link_to('Verify', url=h.url_for(controller='index',
                                                          action='verify',
                                                          username=username,
                                                          code=hash))
        return render('/register_success.mako')

    @check_perm('index.register')
    def verify(self):
        """Account verification."""
        username = request.params['username']
        code = request.params['code']
        user = model.User.get_by_name(username)
        hasher = hashlib.md5()
        hasher.update(user.username)
        hasher.update(str(user.id))
        hash = hasher.hexdigest()
        if hash == code:
            user.role = model.Role.get_by_name('Member')
            model.Session.commit()
        c.verified = (hash == code)
        return render('/verify.mako')

    def login(self):
        """User login form."""
        if c.auth_user:
            # This shouldn't really happen, so no need to be nice about it
            h.redirect_to('/')

        c.form = FormGenerator()
        return render('/login.mako')

    #@https()
    def login_check(self):
        """User login POST target."""
        if c.auth_user:
            # This shouldn't really happen, so no need to be nice about it
            h.redirect_to('/')

        username = request.params.get('username', '')
        user_q = model.Session.query(model.User)
        user = user_q.filter_by(username = username).first()
        c.form = FormGenerator()
        if user and user.check_password(request.params.get('password')):
            if not user.can('index.login'):
                c.error_msgs.append(
                    "This account (%s) still needs to be verified. " \
                    "Please check the email address provided for the " \
                    "verification code." % h.escape_once(username)
                    )
                c.form.defaults['username'] = username
                return render('/login.mako')
            else:
                session['user_id'] = user.id
                session.save()
                h.redirect_to(request.headers.get('referer', '/'))
        else:
            c.error_msgs.append(
                "Either there is no such account '%s', or the provided " \
                "password was incorrect." % h.escape_once(username)
                )
            c.form.defaults['username'] = username
            return render('/login.mako')

    def logout(self):
        """Logout POST target."""
        del session['user_id']
        if 'admin_last_used' in session:
            del session['admin_last_used']
        session.save()
        h.redirect_to(request.headers.get('referer', '/'))
