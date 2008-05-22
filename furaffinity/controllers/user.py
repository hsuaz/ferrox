from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.model import form
from furaffinity.lib.formgen import FormGenerator

import logging

log = logging.getLogger(__name__)

class UserController(BaseController):

    def view(self, username=None, sub_domain=None):
        """Default view for a user; shows eir recent activity and some simple
        stats/info.
        """
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/view.mako')

    def profile(self, username=None, sub_domain=None):
        """View a user's profile in painful detail."""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/profile.mako')

    def relationships(self, username=None, sub_domain=None):
        """Show (and possibly manage) user's relationships"""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/relationships.mako')

    def watch(self, username=None, sub_domain=None):
        c.form = FormGenerator()
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/watch.mako')

    def watch_confirm(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        validator = model.form.WatchForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error

        
        r = c.auth_user.get_or_create_relationship(c.user)

        if form_data['submissions']:
            r.relationship = r.relationship.union(['watching_submissions'])
        if form_data['journals']:
            r.relationship = r.relationship.union(['watching_journals'])
        
        model.Session.update(r)
        model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='view', username=c.user.username))


    def block(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        c.text = "Are you sure you want to block the user %s?"%c.user.display_name
        c.url = h.url(controller='user', action='block_confirm', username=c.user.username)
        c.fields = {}
        return render('/confirm.mako')

    def block_confirm(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
            
        validator = model.form.DeleteForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error
        
        if form_data['confirm']:
            r = c.auth_user.get_or_create_relationship(c.user)
            r.relationship = r.relationship.union(['blocking'])
            model.Session.update(r)
            model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='view', username=c.user.username))

    def friend(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        c.text = "Are you sure you want to add the user %s to your friend list?"%c.user.display_name
        c.url = h.url(controller='user', action='friend_confirm', username=c.user.username)
        c.fields = {}
        return render('/confirm.mako')

    def friend_confirm(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
            
        validator = model.form.DeleteForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error
        
        if form_data['confirm']:
            r = c.auth_user.get_or_create_relationship(c.user)
            r.relationship = r.relationship.union(['friend_to'])
            model.Session.update(r)
            model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='view', username=c.user.username))

    def settings(self):
        """Form for editing user settings.  Eventually."""
        return render('/PLACEHOLDER.mako')
