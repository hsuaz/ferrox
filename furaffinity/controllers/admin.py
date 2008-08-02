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
    def ban(self):
        c.bans = model.Session.query(model.UserBan).all()
        return render('/admin/ban.mako')

    #@authed_admin()
    #def ban_commit(self):
    #    h.redirect_to(h.url_for(controller='admin', action='index'))

    @authed_admin()
    def ip(self):
        """Shows a list of recently-used IPs."""

        page = request.params.get('page', 0)
        ip_q = model.Session.query(model.IPLogEntry)
        ip_q = ip_q.order_by(model.IPLogEntry.end_time.desc())
        c.ip_page = paginate.Page(ip_q, page_nr=page, items_per_page=10)
        c.ip_nav = c.ip_page.navigator(link_var='page')
        return render('/admin/ip.mako')
