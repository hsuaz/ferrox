from furaffinity.lib.base import *
#import furaffinity.lib.paginate as paginate
from furaffinity.lib import pagination
from furaffinity.model import form
from furaffinity.lib.formgen import FormGenerator

import pylons.config
import logging
import math
import formencode

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
    
    def settings(self):
        """Form for editing user settings.  Eventually."""
        return render('/PLACEHOLDER.mako')
