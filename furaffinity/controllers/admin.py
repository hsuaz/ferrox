from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.model import form
from furaffinity.lib.formgen import FormGenerator

import time
import logging

log = logging.getLogger(__name__)

class AdminController(BaseController):

    @authed_admin()
    @check_perm('administrate')
    def index(self):
        """Admin index.  Nothing much right now."""

        return render('/admin/index.mako')

    def auth(self):
        c.form = FormGenerator()
        c.form.defaults['username'] = c.auth_user.username
        return render('/admin/login.mako')
        
    def auth_verify(self):
        """User login POST target."""
        username = request.params.get('username', '')
        user_q = model.Session.query(model.User)
        user = user_q.filter_by(username = username).first()
        c.form = FormGenerator()
        if user and user.check_password(request.params.get('password')):
            if not user.can('log_in'):
                c.error_msgs.append(
                    "This account (%s) still needs to be verified. " \
                    "Please check the email address provided for the " \
                    "verification code." % h.escape_once(username)
                    )
                c.form.defaults['username'] = username
                return render('/login.mako')
            else:
                session['user_id'] = user.id
                if user.can('administrate'):
                    session['admin_last_used'] = int(time.time())
                else:
                    session['admin_last_used'] = 0
                session.save()
                h.redirect_to(request.headers.get('referer', '/'))
        else:
            c.error_msgs.append(
                "Either there is no such account '%s', or the provided " \
                "password was incorrect." % h.escape_once(username)
                )
            c.form.defaults['username'] = username
            return render('/login.mako')
    
    @authed_admin()
    def show_bans(self):
        c.bans = model.Session.query(model.UserBan).all()
        return render('/admin/showbans.mako')

    @authed_admin()
    def ban(self, username=None):
        c.roles = model.Session.query(model.Role).all()
        c.form = FormGenerator()
        c.form.defaults['username'] = username
        return render('/admin/addban.mako')

    @authed_admin()
    def ban_commit(self, username=None):
        validator = model.form.BanForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return render('/error.mako')

        user_ban = model.UserBan()
        user_ban.admin = c.auth_user
        user_ban.expires = form_data['expiration']
        user_ban.revert_to = form_data['username'].role
        user_ban.reason = form_data['reason']
        user_ban.admin_message = form_data['notes']
        model.Session.save(user_ban)

        form_data['username'].bans.append(user_ban)
        form_data['username'].role = form_data['role_id']
        model.Session.commit()


        h.redirect_to(h.url_for(controller='admin', action='show_bans'))

    @authed_admin()
    def ip(self):
        """Shows a list of recently-used IPs."""

        page = request.params.get('page', 0)
        ip_q = model.Session.query(model.IPLogEntry)
        ip_q = ip_q.order_by(model.IPLogEntry.end_time.desc())
        c.ip_page = paginate.Page(ip_q, page_nr=page, items_per_page=10)
        c.ip_nav = c.ip_page.navigator(link_var='page')
        return render('/admin/ip.mako')
