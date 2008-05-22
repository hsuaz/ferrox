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

    def watch_commit(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        validator = model.form.WatchForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error

        
        r = None
        for r in c.auth_user.relationships:
            if r.target == c.user:
                break
        
        if not r:
            r = model.UserRelationship()
            r.target = c.user
            model.Session.save(r)
            c.auth_user.relationships.append(r)
            #r.user = c.auth_user

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
        return render('user/block.mako')

    def friend(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/friend.mako')

    def settings(self):
        """Form for editing user settings.  Eventually."""
        return render('/PLACEHOLDER.mako')
