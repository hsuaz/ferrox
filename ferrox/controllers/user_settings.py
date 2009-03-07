from ferrox.controllers.user import fetch_relationships
from ferrox.lib.base import *
from ferrox.lib.formgen import FormGenerator
from ferrox.lib.mimetype import get_mime_type
from ferrox.model import form

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

    @check_perm('user_settings.avatars')
    def avatars(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username, ['avatars'])
        if not c.user:
            abort(404)
        return render('/user/settings/avatars.mako')

    @check_perm('user_settings.avatars')
    def avatars_update(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username, ['avatars'])
        if not c.user:
            abort(404)

        default_avatar_id = 0
        if request.params['default'].isdigit():
            default_avatar_id = int(request.params['default'])

        deletions = []
        for k in request.params.keys():
            if k[0:6] == 'delete' and k[7:].isdigit():
                deletions.append(int(k[7:]))

        # First, update default
        if not c.user.default_avatar or default_avatar_id != c.user.default_avatar.id:
            if c.user.default_avatar:
                c.user.default_avatar.default = False
                model.Session.update(c.user.default_avatar)
            
            for av in c.user.avatars:
                if av.id == default_avatar_id:
                    av.default = True
                    model.Session.update(av)
                    break
                    
        # Process deletions
        for av in c.user.avatars:
            if av.id in deletions:
                if av.default:
                    default_avatar_id = 0

                # I really don't like this. This could go to hell with large
                # enough data sets.
                # XXX PERF
                for cls in [model.News, model.UserSubmission,
                            model.JournalEntry, model.Comment]:
                    for obj in model.Session.query(cls) \
                                    .filter_by(avatar_id=av.id).all():
                        obj.avatar = None
                        model.Session.update(obj)

                c.user.avatars.remove(av)
                model.Session.delete(av)
        
        # If there is no default set the first avatar in the collection
        if default_avatar_id == 0:
            if c.user.avatars:
                c.user.avatars[0].default = True
                model.Session.update(c.user.avatars[0])

        model.Session.commit()
        h.redirect_to(h.url_for(controller='user_settings', action='avatars', username=c.user.username))

    @check_perm('user_settings.avatars')
    def avatars_upload(self, username=None, sub_domain=None):
        validator = model.form.AvatarForm() 
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error
            
        c.user = model.User.get_by_name(username, ['avatars'])
        if not c.user:
            abort(404)
            
        # Process new avatar upload
        if form_data['avatar'] and get_mime_type(form_data['avatar']) \
            in ('image/jpeg', 'image/gif', 'image/png'):

            useravatar = model.UserAvatar()
            useravatar.title = form_data['title']
            useravatar.default = form_data['default'] 

            if form_data['default'] and c.user.default_avatar:
                c.user.default_avatar.default = False

            useravatar.write_to_mogile(form_data['avatar'], c.user)
            c.user.avatars.append(useravatar)

        model.Session.commit()
        h.redirect_to(h.url_for(controller='user_settings', action='avatars', username=c.user.username))

    @check_perm('user_settings.relationships')
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
        # other_user indicates we are trying to add somebody
        if c.other_user:
            if c.other_user in c.relationship_order:
                c.relationship_order.remove(c.other_user)
            c.relationship_order.insert(0, c.other_user)

            # If they asked for a relationship, make sure it defaults to on
            if 'relationship' in request.params:
                rel = request.params['relationship']
                if rel not in c.relationships[c.other_user]:
                    c.relationships[c.other_user].append(rel)

        return render('user/settings/relationships.mako')

    @check_perm('user_settings.relationships')
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

