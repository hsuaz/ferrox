from furaffinity.lib.base import *
#import furaffinity.lib.paginate as paginate
from furaffinity.lib import pagination
from furaffinity.model import form
from furaffinity.lib.formgen import FormGenerator
from furaffinity.lib.mimetype import get_mime_type

import pylons.config
import logging
import math
import formencode

log = logging.getLogger(__name__)

class UserController(BaseController):

    def ajax_tooltip(self, username=None):
        """Returns HTML fragment for the user tooltip."""

        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        # Relationships
        if c.auth_user:
            c.is_friend = c.auth_user.get_relationship(c.user, 'friend_to')
            c.friend_of = c.user.get_relationship(c.auth_user, 'friend_to')

            c.blocking = c.auth_user.get_relationship(c.user, 'blocking')
            c.blocked_by = c.user.get_relationship(c.auth_user, 'blocking')

        return render('user/ajax_tooltip.mako')

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

    def _fetch_relationships(self):
        """Populates c.relationships with a dict of user => [relationships],
        filtering to those owned by c.other_user if one exists.
        """
        if c.other_user:
            relationships = model.Session.query(model.UserRelationship) \
                              .filter_by(from_user_id=c.user.id,
                                         to_user_id=c.other_user.id) \
                              .all()
        else:
            relationships = c.user.relationships

        c.relationships = {}
        for rel in relationships:
            if not rel.target in c.relationships:
                c.relationships[rel.target] = []
            c.relationships[rel.target].append(rel.relationship)

        c.relationship_order = c.relationships.keys()
        c.relationship_order.sort(cmp=lambda a, b: cmp(a.username,
                                                       b.username))
        return

    # XXX: friendof?  construct hashes from this instead?
    def relationships(self, username=None, sub_domain=None, other_user=None):
        """Show user's relationships"""
        c.user = model.User.get_by_name(username)
        c.other_user = model.User.get_by_name(other_user)
        self._fetch_relationships()

        return render('user/relationships.mako')

    def relationships_edit(self, username=None, sub_domain=None):
        """Edit user's relationships"""
        c.user = model.User.get_by_name(username)

        self._fetch_relationships()
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

        return render('user/relationships_edit.mako')

    def fuck(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You have attempted to fuck yourself.'''
            c.error_text = 'You have either attempted to fuck yourself, or have been given the suggestion to do so. Congratulations. <br/><br/> &hearts; net-cat'
            return render('/error.mako')
        
        abort(404)

    def memberlist(self, pageno=1):
        validator = model.form.MemberListPagingForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error

        q = model.Session.query(model.User)
        num_users = q.count()

        q = q.order_by(model.User.__table__.c.username)


        pageno = (form_data['page'] if form_data['page'] else 1) - 1
        perpage = form_data['perpage'] if form_data['perpage'] else int(pylons.config.get('userlist.default_perpage',12))
        c.paging_links = pagination.populate_paging_links(pageno=pageno, num_pages=int(math.ceil(float(num_users)/float(perpage))), perpage=perpage, radius=int(pylons.config.get('paging.radius', 3)))

        q = q.limit(perpage).offset(perpage*pageno)
        c.users = q.all()

        return render('/user/memberlist.mako')
    
    def avatar(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username, ['avatars'])
        if not c.user:
            abort(404)
        return render('/user/avatar.mako')

    def avatar_update(self, username=None, sub_domain=None):
        c.user = model.User.get_by_name(username, ['avatars'])
        if not c.user:
            abort(404)

        default_avatar_id = int(request.params['default']) if request.params['default'].isdigit() else 0

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

                # I really don't like this. This could go to hell with large enough data sets.
                for cls in [model.News, model.UserSubmission, model.JournalEntry, model.Comment]:
                    for obj in model.Session.query(cls).filter_by(avatar_id=av.id).all():
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
        h.redirect_to(h.url_for(controller='user', action='avatar', username=c.user.username))
        #return "<pre>%s</pre>" % form_data

    def avatar_upload(self, username=None, sub_domain=None):
        validator = model.form.AvatarForm() 
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            return error
            
        c.user = model.User.get_by_name(username, ['avatars'])
        if not c.user:
            abort(404)
            
        # Process new avatar upload
        if form_data['avatar'] and get_mime_type(form_data['avatar']) in ('image/jpeg', 'image/gif', 'image/png'):
            useravatar = model.UserAvatar()
            useravatar.title = form_data['title']
            useravatar.default = form_data['default'] 

            if form_data['default'] and c.user.default_avatar:
                c.user.default_avatar.default = False

            useravatar.write_to_mogile(form_data['avatar'], c.user)
            c.user.avatars.append(useravatar)

        model.Session.commit()
        h.redirect_to(h.url_for(controller='user', action='avatar', username=c.user.username))

