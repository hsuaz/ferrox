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
        c.user = c.auth_user if username==c.auth_user.username else model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/relationships.mako')

    def relationships_change(self, username=None, sub_domain=None):
        """Show (and possibly manage) user's relationships"""
        c.user = None
        if c.auth_user.username == username:
            c.user = c.auth_user
        else:
            abort(403)
            c.user = model.User.get_by_name(username)

        if not c.user:
            abort(404)
            
        """ This form doesn't need a validator. All we're doing is checking for field presence and the form is very dynamic. """
        
        for r in c.user.relationships:
            if request.params.has_key("ws_%d"%r.target.id):
                r.relationship = r.relationship.union(['watching_submissions'])
            else:
                r.relationship = r.relationship.difference(['watching_submissions'])

            if request.params.has_key("wj_%d"%r.target.id):
                r.relationship = r.relationship.union(['watching_journals'])
            else:
                r.relationship = r.relationship.difference(['watching_journals'])

            if request.params.has_key("b_%d"%r.target.id):
                r.relationship = r.relationship.union(['blocking'])
            else:
                r.relationship = r.relationship.difference(['blocking'])

            if request.params.has_key("f_%d"%r.target.id):
                r.relationship = r.relationship.union(['friend_to'])
            else:
                r.relationship = r.relationship.difference(['friend_to'])

            if not r.relationship:
                model.Session.delete(r)
        
        model.Session.commit()
        h.redirect_to(h.url_for(controller='user', action='relationships', username=c.user.username))

    def watch(self, username=None, sub_domain=None):
        c.form = FormGenerator()

        if username == c.auth_user.username:
            c.error_title = '''You can't watch yourself!'''
            c.error_text = 'You have attempted to watch yourself. How very narcissistic of you.'
            return render('/error.mako')
        
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)
        return render('user/watch.mako')

    def watch_confirm(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You can't watch yourself!'''
            c.error_text = 'You have attempted to watch yourself. How very narcissistic of you.'
            return render('/error.mako')
        
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
        else:
            r.relationship = r.relationship.difference(['watching_submissions'])

        if form_data['journals']:
            r.relationship = r.relationship.union(['watching_journals'])
        else:
            r.relationship = r.relationship.difference(['watching_journals'])
     
        if not r.relationship:
            model.Session.delete(r)

        model.Session.update(r)
        model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='view', username=c.user.username))


    def block(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You can't block yourself!'''
            c.error_text = 'Despite the fact the you hate apparently yourself, there are far more effective ways to deprive us of your company.'
            return render('/error.mako')
        
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        r = c.auth_user.get_or_create_relationship(c.user)
        if 'blocking' in r.relationship:
            c.text = "Are you sure you want to unblock the user %s?"%c.user.display_name
        else:
            c.text = "Are you sure you want to block the user %s?"%c.user.display_name
            
        c.url = h.url(controller='user', action='block_confirm', username=c.user.username)
        c.fields = {}
        return render('/confirm.mako')

    def block_confirm(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You can't block yourself!'''
            c.error_text = 'Despite the fact the you hate apparently yourself, there are far more effective ways to deprive us of your company.'
            return render('/error.mako')
        
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
            if 'blocking' in r.relationship:
                r.relationship = r.relationship.difference(['blocking'])
                if not r.relationship:
                    model.Session.delete(r)
            else:
                r.relationship = r.relationship.union(['blocking'])
            model.Session.update(r)
            model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='view', username=c.user.username))

    def friend(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You can't befriend yourself!'''
            c.error_text = 'You have attempted to befriend youself. Might I recommend any of a number of treatments for multiple personality disorder?'
            return render('/error.mako')
        
        c.user = model.User.get_by_name(username)
        if not c.user:
            abort(404)

        r = c.auth_user.get_or_create_relationship(c.user)
        if 'friend_to' in r.relationship:
            c.text = "Are you sure you want to remove the user %s from your friend list?"%c.user.display_name
        else:
            c.text = "Are you sure you want to add the user %s to your friend list?"%c.user.display_name
        c.url = h.url(controller='user', action='friend_confirm', username=c.user.username)
        c.fields = {}
        return render('/confirm.mako')

    def friend_confirm(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You can't befriend yourself!'''
            c.error_text = 'You have attempted to befriend youself. Might I recommend any of a number of treatments for multiple personality disorder?'
            return render('/error.mako')
        
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
            if 'friend_to' in r.relationship:
                r.relationship = r.relationship.difference(['friend_to'])
                if not r.relationship:
                    model.Session.delete(r)
            else:
                r.relationship = r.relationship.union(['friend_to'])
            model.Session.update(r)
            model.Session.commit()

        h.redirect_to(h.url_for(controller='user', action='view', username=c.user.username))

    def fuck(self, username=None, sub_domain=None):
        if username == c.auth_user.username:
            c.error_title = '''You have attempted to fuck yourself.'''
            c.error_text = 'You have either attempted to fuck yourself, or have been given the suggestion to do so. Congratulations.<br><br>&hearts; net-cat'
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

