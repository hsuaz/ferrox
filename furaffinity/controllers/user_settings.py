from furaffinity.controllers.user import fetch_relationships
from furaffinity.lib.base import *
from furaffinity.lib.formgen import FormGenerator
from furaffinity.model import form

import pylons.config
import logging
import formencode

log = logging.getLogger(__name__)

class UserSettingsController(BaseController):

    def index(self, username=None):
        """Slightly less fillerific settings index."""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        return render('/user/settings/index.mako')

    def relationships(self, username=None, sub_domain=None):
        """Edit user's relationships"""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        fetch_relationships()
        c.form = FormGenerator()

        if 'other_user' in request.params:
            c.other_user = model.User.get_by_name(
                request.params['other_user']
                )
        if c.other_user:
            if c.other_user in c.relationship_order:
                c.relationship_order.remove(c.other_user)
            c.relationship_order.insert(0, c.other_user)

            c.relationships[c.other_user] = []
            if 'relationship' in request.params:
                c.relationships[c.other_user].append(
                    request.params['relationship']
                    )

        return render('user/settings/relationships.mako')

    def relationships_commit(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        relationship_changes = {}  # user, relationship => change

        # Iterate through requested and existing relationships.  Track them in
        # a hash, adding 1 for a requested relationship and subtracting 1 for
        # an existing one.  At the end, anything with a +1 needs adding and
        # anything with a -1 needs removing

        # Requested relationships first
        for rel_username in request.params.getall('users'):
            rel_user = model.User.get_by_name(rel_username)
            if not rel_user:
                # Shouldn't happen; someone screwing around, so don't care
                continue
            
            relationships = request.params.getall('user:%s' % rel_username)
            for relationship in relationships:
                relationship_changes[rel_user, relationship] = 1

        # Existing relationships
        for rel in c.user.relationships:
            relationship_changes.setdefault((rel.target, rel.relationship), 0)
            relationship_changes[rel.target, rel.relationship] -= 1

        # Create and remove db rows as necessary, but only for users that
        # appeared in the form in the first place
        for (target, relationship), change \
            in relationship_changes.iteritems():

            if change > 0:
                c.user.add_relationship(target, relationship)
            elif change < 0:
                rel = c.user.get_relationship(target, relationship)
                model.Session.delete(rel)

        model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='relationships', username=c.user.username))

