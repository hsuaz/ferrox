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

from furaffinity.lib.formgen import FormGenerator
import furaffinity.lib.helpers as h
import furaffinity.lib.hashing as hashing
from furaffinity.lib.querylog import QueryLog
import furaffinity.model as model
import furaffinity.model.form as form

from decorator import decorator
from datetime import datetime
from time import time

def check_perm(permission):
    '''Decorator for checking permission on user before running a controller method'''
    @decorator
    def check(func, *args, **kwargs):
        if not c.auth_user.can(permission):
            return abort(403)
        else:
            return func(*args, **kwargs)
    return check

def check_perms(permissions):
    '''Decorator for checking multiple permissions on user before running a controller method.
       Note: ONLY ONE of the permissions in the list has to be true. If you want to assert
       ALL permissions, use multiple @check_perm or @check_perms decorators.'''
    @decorator
    def check(func, *args, **kwargs):
        if not (c.auth_user):
            return render('/denied.mako')
        else:
            for permission in permissions:
                if c.auth_user.can(permission):
                    return func(*args, **kwargs)
            return render('/denied.mako')
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

        c.empty_form = FormGenerator()
        c.error_msgs = []
        c.route = request_config().mapper_dict

        user_q = model.Session.query(model.User)
        user_id = session.get('user_id', None)
        if user_id:
            c.auth_user = user_q.filter_by(id = user_id).first()

            # User may have been deleted in the interim
            if not c.auth_user:
                session['user_id'] = None
                session.save()
                return

            ip = request.environ['REMOTE_ADDR']
            if c.auth_user.can('administrate'):
                session['admin_ip'] = ip

            # Log IPs
            ip_log_q = model.Session.query(model.IPLogEntry)
            last_ip_record = ip_log_q.filter_by(user_id = user_id) \
                .order_by(model.IPLogEntry.end_time.desc()).first()
            if last_ip_record and last_ip_record.ip == ip:
                last_ip_record.end_time = datetime.now()
            else:
                model.Session.save(model.IPLogEntry(user_id, ip))
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
