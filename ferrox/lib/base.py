"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render
from routes import request_config
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.orm import eagerload, eagerload_all

from ferrox.lib.formgen import FormGenerator
import ferrox.lib.helpers as h
import ferrox.lib.hashing as hashing
from ferrox.lib.config import Config
from ferrox.lib.querylog import QueryLog
import ferrox.model as model
import ferrox.model.form as form
import ferrox.lib.inet as inet

from decorator import decorator
from datetime import datetime
from time import time

def check_perm(*permissions):
    '''Decorator for checking permission on user before running a controller method

    Note: Only one permission needs to be matched. If you want to check for all
    permissions, stack the decorators.'''
    @decorator
    def check(func, *args, **kwargs):
        for permission in permissions:
            if c.auth_user.can(permission):
                return func(*args, **kwargs)
        return abort(403)
    return check

def authed_admin():
    @decorator
    def check(func, *args, **kwargs):
        session_timeout = int(config.get('admin.session_timeout', 15*60))
        if int(session.get('admin_last_used', 0)) > int(time() - session_timeout):
            session['admin_last_used'] = int(time())
            session.save()
            return func(*args, **kwargs)
        h.redirect_to(h.url_for(controller='admin', action='auth'))
        return None
    return check

class BaseController(WSGIController):

    def __before__(self, action, **params):
        # This is done as a closure so it can just be called from the footer
        # in the template, putting off the final time() as late as possible
        start_time = time()
        def time_elapsed():
            return time() - start_time
        c.time_elapsed = time_elapsed
        c.query_log = QueryLog()

        c.config = Config().readdb(model.Config)
        c.empty_form = FormGenerator()
        c.error_msgs = []
        c.route = request_config().mapper_dict
        c.javascripts = ['jquery-1.2.6.pack', 'common']
        c.site_name = config.get('site_name', 'Ferrox')

        if 'user_id' in session:
            try:
                user_id = session['user_id']
                c.auth_user = model.Session.query(model.User) \
                    .options(eagerload('active_bans')) \
                    .get(user_id)
            except InvalidRequestError:
                # User may have been deleted in the interim
                del session['user_id']
                session.save()

        if c.auth_user:
            ip = request.environ['REMOTE_ADDR']
            ip = inet.pton(ip)
            if c.auth_user.can('admin.auth'):
                session['admin_ip'] = ip

            cip = inet.ntop(ip)

            # Log IPs
            ip_log_q = model.Session.query(model.IPLogEntry)
            last_ip_record = ip_log_q.filter_by(user_id = user_id) \
                .order_by(model.IPLogEntry.end_time.desc()).first()
            if last_ip_record and last_ip_record.ip == cip:
                last_ip_record.end_time = datetime.now()
            else:
                model.Session.add(model.IPLogEntry(user_id, ip))

            # Check to see if there are any active bans to expire
            if c.auth_user.active_bans:
                for ban in c.auth_user.active_bans:
                    if ban.expires <= datetime.now():
                        ban.expired = True
                        c.auth_user.role = ban.revert_to

            # Magical commit.
            model.Session.commit()

        else:
            c.auth_user = model.GuestUser()

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()

            # For whatever reason, query log isn't reliably gc'd, so nuke
            # it manually here
            c.query_log = None

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
