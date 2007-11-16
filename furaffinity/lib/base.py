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

import furaffinity.lib.helpers as h
import furaffinity.model as model

from decorator import decorator

def check_perm(permission):
    '''Decorator for checking permission on user before running a controller method'''
    @decorator
    def check(func, *args, **kwargs):
        if not c.auth_user.can(permission):
            return abort(403)
        else:
            return func(*args, **kwargs)
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
