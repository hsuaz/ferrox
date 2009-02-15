from ferrox.lib.base import *
from ferrox.model import form
from ferrox.lib.formgen import FormGenerator
import ferrox.lib.pagination as pagination
import pylons.config

import formencode
import time
import logging

log = logging.getLogger(__name__)

class AdminController(BaseController):

    @authed_admin()
    @check_perm('admin.auth')
    def index(self):
        """Admin index.  Nothing much right now."""

        return render('/admin/index.mako')

    def auth(self):
        c.form = FormGenerator()
        c.form.defaults['username'] = c.auth_user.username
        return render('/admin/login.mako')
        
    def auth_verify(self):
        """User login POST target."""
        username = request.params.get('username', '')
        user_q = model.Session.query(model.User)
        user = user_q.filter_by(username = username).first()
        c.form = FormGenerator()
        if user and user.check_password(request.params.get('password')):
            if not user.can('index.login'):
                c.error_msgs.append(
                    "This account (%s) still needs to be verified. " \
                    "Please check the email address provided for the " \
                    "verification code." % h.html_escape(username)
                    )
                c.form.defaults['username'] = username
                return render('/login.mako')
            else:
                session['user_id'] = user.id
                if user.can('admin.auth'):
                    session['admin_last_used'] = int(time.time())
                else:
                    session['admin_last_used'] = 0
                session.save()
                h.redirect_to(h.url_for(controller='admin', action='index'))
        else:
            c.error_msgs.append(
                "Either there is no such account '%s', or the provided " \
                "password was incorrect." % h.html_escape(username)
                )
            c.form.defaults['username'] = username
            return render('/login.mako')
    
    @authed_admin()
    @check_perm('admin.ban')
    def show_bans(self):
        c.bans = model.Session.query(model.UserBan).all()
        return render('/admin/showbans.mako')

    @authed_admin()
    @check_perm('admin.ban')
    def ban(self, username=None):
        c.roles = model.Session.query(model.Role).all()
        c.form = FormGenerator()
        c.form.defaults['username'] = username
        return render('/admin/addban.mako')

    @authed_admin()
    @check_perm('admin.ban')
    def ban_commit(self, username=None):
        validator = model.form.BanForm()
        try:
            form_data = validator.to_python(request.params)
        except formencode.Invalid, error:
            #c.roles = model.Session.query(model.Role).all()
            #c.form = FormGenerator()
            #c.form.defaults['username'] = username
            print error
            return render('/error.mako')

        user_ban = model.UserBan()
        user_ban.admin = c.auth_user
        user_ban.expires = form_data['expiration']
        user_ban.revert_to = form_data['username'].role
        user_ban.reason = form_data['reason']
        user_ban.admin_message = form_data['notes']
        user_ban.expired = False
        model.Session.save(user_ban)

        form_data['username'].bans.append(user_ban)
        form_data['username'].role = form_data['role_id']
        model.Session.commit()


        h.redirect_to(h.url_for(controller='admin', action='show_bans'))

    @authed_admin()
    @check_perm('admin.ip')
    def ip(self):
        """Shows a list of recently-used IPs."""

        page = int(request.params.get('page', 0))
        c.ips = model.Session.query(model.IPLogEntry)
        c.ips = c.ips.order_by(model.IPLogEntry.end_time.desc())
        number_of_ips = c.ips.count()
        pageno = int(request.params.get('page', 1)) - 1
        perpage = int(request.params.get('perpage', None) or \
                      pylons.config.get('admin.ip_default_perpage', 12))
        c.paging_links = pagination.populate_paging_links(
            pageno = pageno,
            num_pages = int((number_of_ips + 0.5) // perpage),
            perpage = perpage,
            radius = int(pylons.config.get('paging.radius', 3))
        )
        c.ips = c.ips.limit(perpage).offset(perpage * page)
        
        return render('/admin/ip.mako')

    @authed_admin()
    @check_perm('admin.config_view')
    def config(self):
        action = request.params.get('action')
        if action == 'save':
            if c.auth_user.can('admin.config_edit'):
                value = request.params.get('value')
                if c.auth_user.can('admin.config_admin'):
                    section = request.params.get('section')
                    name = request.params.get('name')
                    type = request.params.get('type')
                    pattern = request.params.get('pattern')
                    comment = request.params.get('comment')
                else:
                    section = request.params.get('old_section')
                    name = request.params.get('old_name')
                    type = request.params.get('old_type')
                    pattern = request.params.get('old_pattern')
                    comment = request.params.get('old_comment')
                model.Config.delete(section, name)
                model.Session.save(model.Config(section, name, type, pattern, value, comment, 0))
                model.Session.commit()
                return "done"
            else:
                return "You don't have permissions to edit configuration"
        return render('/admin/config.mako')
        
    @authed_admin()
    @check_perm('admin.config_view')
    @jsonify
    def config_ajax(self):
        action = request.params.get('action')
        if action == 'empty_list':
            return {
                'metadata' : [{'name' : 'x', 'title' : 'Choose section'}],
                'data' : [],
                'total' : 0,
            }
        elif action == 'get_tree':
            list = model.Config.get_sections()
            items = []
            for row in list:
                section = row.section
                items.append({
                    'id' : 'section:' + section,
                    'text' : section.capitalize(),
                    'isFolder' : 0,
                    'section' : section,
                })
            return {
                'items' : items,
            }
        elif action == 'get_values':
            section = request.params.get('section')
            start = request.params.get('start')
            limit = request.params.get('limit')
            data = model.Config.get_values_of(section, start, limit)
            return {
                'metadata' : [
                    {'name' : 'id',       'title' : 'ID',      'hidden' : 1},
                    {'name' : 'section',  'title' : 'Section', 'hidden' : 1},
                    {'name' : 'type',     'title' : 'Type',    'hidden' : 1},
                    {'name' : 'pattern',  'title' : 'Pattern', 'hidden' : 1},
                    {'name' : 'name',     'title' : 'Name',    'renderer' : 'var_name'},
                    {'name' : 'value',    'title' : 'Value',   'renderer' : 'var_value'},
                    {'name' : 'comment',  'title' : 'Comment', 'renderer' : 'html'},
                    {'name' : 'fname',    'title' : 'Name',    'hidden' : 1},
                    {'name' : 'fvalue',   'title' : 'Value',   'hidden' : 1},
                    {'name' : 'fcomment', 'title' : 'Comment', 'hidden' : 1},
		],
		'data' : data["data"],
		'total' : data["total"],
	    }
        return None
