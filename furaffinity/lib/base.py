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

import furaffinity.lib.helpers as h
import furaffinity.lib.hashing as hashing
import furaffinity.model as model

from decorator import decorator
from datetime import datetime

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
                if (c.auth_user.can(permission)):
                    return func(*args, **kwargs)
            return render('/denied.mako')
    return check
    
class GuestRole(object):
    def __init__(self):
        self.name = "Guest"
        self.description = "Just a guest"
        self.sigil = ""
    
class GuestUser(object):
    '''Dummy object for not-logged-in users'''
    def __init__(self):
        self.id = 0
        self.username = "guest"
        self.display_name = "guest"
        self.role = GuestRole()
        self.is_guest = True
        
    def can(self, permission):
        return False

class BaseController(WSGIController):

    def __before__(self, action, **params):
        c.prefill = {}
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

            if c.auth_user.can('administrate'):
                session['admin_ip'] = request.environ['REMOTE_ADDR']

            # Log IPs
            ip_integer = h.ip_to_integer(request.environ['REMOTE_ADDR'])
            ip_log_q = model.Session.query(model.IPLogEntry)
            last_ip_record = ip_log_q.filter_by(user_id = user_id) \
                .order_by(model.ip_log_table.c.end_time.desc()).first()
            if last_ip_record and int(last_ip_record.ip) == ip_integer:
                last_ip_record.end_time = datetime.now()
            else:
                model.Session.save(model.IPLogEntry(user_id, ip_integer))
            model.Session.commit()
        else:
            c.auth_user = GuestUser()

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
