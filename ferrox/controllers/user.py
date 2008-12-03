from ferrox.controllers.gallery import find_submissions
from ferrox.lib.base import *
#import ferrox.lib.paginate as paginate
from ferrox.lib import pagination
from ferrox.lib.formgen import FormGenerator
from ferrox.model import form

import pylons.config
import logging
import math
import formencode

log = logging.getLogger(__name__)

def fetch_relationships(other_user=None):
    """Populates c.relationships with a dict of user => [relationships],
    filtering to those owned by c.other_user if one exists.
    """
    if other_user:
        relationships = model.Session.query(model.UserRelationship) \
                          .filter_by(from_user_id=c.user.id,
                                     to_user_id=other_user.id) \
                          .all()
    else:
        relationships = c.user.relationships

    c.relationships = {}
    for rel in relationships:
        if not rel.target in c.relationships:
            c.relationships[rel.target] = []
        c.relationships[rel.target].append(rel.relationship)

    c.relationship_order = c.relationships.keys()
    c.relationship_order.sort(cmp=lambda a, b: cmp(a.username, b.username))
    return

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

        # Recent submissions
        joined_tables = model.Submission.__table__ \
                        .join(model.UserSubmission.__table__) \
                        .join(model.User.__table__)
        where = [model.User.id == c.user.id]
        (c.recent_submissions,
            submission_ct) = find_submissions(joined_tables=joined_tables,
                                              where_clauses=where,
                                              page_size=10)

        c.recent_journals = model.Session.query(model.JournalEntry) \
                            .filter_by(status='normal') \
                            .join('message') \
                            .filter_by(user_id=c.user.id) \
                            .order_by(model.Message.time.desc()) \
                            .limit(10) \
                            .all()
        return render('user/view.mako')

    def profile(self, username=None, sub_domain=None):
        """View a user's profile in painful detail."""
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/profile.mako')

    # XXX: friendof?  construct hashes from this instead?
    def relationships(self, username=None, sub_domain=None, other_user=None):
        """Show user's relationships"""
        c.user = model.User.get_by_name(username)
        c.other_user = model.User.get_by_name(other_user)
        fetch_relationships(c.other_user)

        return render('user/relationships.mako')

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
