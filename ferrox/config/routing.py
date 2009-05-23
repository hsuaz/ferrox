"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'],
                 explicit=True)

    # We do this a lot, so be epic lazy
    require_post = dict(conditions=dict(method=['POST']))

    # Error documents (404, etc) controller.  Goes up here to prevent some
    # other mapping from overriding it
    map.connect('/error/document', controller='error', action='document')

    map.connect('/', controller='index', action='index')
    map.connect('/login', controller='index', action='login')
    map.connect('/login_check', controller='index', action='login_check', **require_post)
    map.connect('/logout', controller='index', action='logout', **require_post)
    map.connect('/register', controller='index', action='register')
    map.connect('/register_check', controller='index', action='register_check', **require_post)
    map.connect('/verify', controller='index', action='verify')
    map.connect('/users/:username', controller='user', action='view')
    map.connect('/~:username/ajax_tooltip', controller='user', action='ajax_tooltip')
    map.connect('/~:username/profile', controller='user', action='profile')
    map.connect('/~:username/stats', controller='user', action='stats')
    map.connect('/~:username/commissions', controller='user', action='commissions')

    map.connect('/~:username/settings', controller='user_settings', action='index')
    map.connect('/~:username/settings/avatars', controller='user_settings', action='avatars')
    map.connect('/~:username/settings/avatars_update', controller='user_settings', action='avatars_update')
    map.connect('/~:username/settings/avatars_upload', controller='user_settings', action='avatars_upload')
    map.connect('/~:username/settings/relationships', controller='user_settings', action='relationships')
    map.connect('/~:username/settings/relationships/edit', controller='user_settings', action='relationships_edit')
    map.connect('/~:username/settings/relationships/commit', controller='user_settings', action='relationships_commit', **require_post)
    
    map.connect('/users', controller='user', action='memberlist')
    map.connect('/~:username/relationships', controller='user', action='relationships')

    map.connect('/~:username/watch', controller='user', action='watch')
    map.connect('/~:username/block', controller='user', action='block')
    map.connect('/~:username/friend', controller='user', action='friend')
    map.connect('/~:username/fuck', controller='user', action='fuck')
    #map.connect('/journals/fill', controller='journal', action='fill')

    map.connect('/news', controller='news', action='index')
    map.connect('/news/post', controller='news', action='post')
    map.connect('/news/do_post', controller='news', action='do_post')
    map.connect('/news/:id/edit', controller='news', action='edit')
    map.connect('/news/:id/edit_commit', controller='news', action='edit_commit', **require_post)
    map.connect('/news/:id/editlog', controller='editlog', action='news')
    map.connect('/news/:id', controller='news', action='view')

    map.connect('/*post_url/comments', controller='comments', action='view')
    map.connect('/*post_url/comments/reply', controller='comments', action='reply')
    map.connect('/*post_url/comments/reply_commit', controller='comments', action='reply_commit')
    map.connect('/*post_url/comments/:id', controller='comments', action='view')
    map.connect('/*post_url/comments/:id/reply', controller='comments', action='reply')
    map.connect('/*post_url/comments/:id/reply_commit', controller='comments', action='reply_commit')

    map.connect('/~:username/notes', controller='notes', action='user_index')
    map.connect('/~:username/notes/write', controller='notes', action='write')
    map.connect('/~:username/notes/write_send', controller='notes', action='write_send', **require_post)
    map.connect('/~:username/notes/:id', controller='notes', action='view')
    map.connect('/~:username/notes/:id/ajax_expand', controller='notes', action='ajax_expand')
    map.connect('/~:username/notes/:id/reply', controller='notes', action='reply')
    map.connect('/~:username/notes/:id/forward', controller='notes', action='forward')

    map.connect('/~:username/watchstream', controller='gallery', action='watchstream')
    map.connect('/~:username/favorites', controller='gallery', action='favorites')
    map.connect('/~:username/gallery', controller='gallery', action='index')
    map.connect('/~:username/gallery/submit', controller='gallery', action='submit')
    map.connect('/~:username/gallery/submit_upload', controller='gallery', action='submit_upload', **require_post)
    map.connect('/~:username/gallery/:id', controller='gallery', action='view')
    map.connect('/~:username/gallery/:id/edit', controller='gallery', action='edit')
    map.connect('/~:username/gallery/:id/edit_commit', controller='gallery', action='edit_commit', **require_post)
    map.connect('/~:username/gallery/:id/delete', controller='gallery', action='delete')
    map.connect('/~:username/gallery/:id/delete_commit', controller='gallery', action='delete_commit', **require_post)
    map.connect('/~:username/gallery/:id/log', controller='gallery', action='log')
    map.connect('/~:username/gallery/:id/favorite', controller='gallery', action='favorite')

    map.connect('/gallery', controller='gallery', action='index')
    map.connect('/download/*filename', controller='gallery', action='file')
    map.connect('/derived/*filename', controller='gallery', action='derived_file')

    map.connect('/~:username/journals/watchstream', controller='journal', action='index', watchstream=True)
    map.connect('/~:username/journals', controller='journal', action='index')
    map.connect('/~:username/journals/post', controller='journal', action='post')
    map.connect('/~:username/journals/post_commit', controller='journal', action='post_commit', **require_post)
    map.connect('/~:username/journals/:year', controller='journal', action='index')
    map.connect('/~:username/journals/:year/:month', controller='journal', action='index')
    map.connect('/~:username/journals/:year/:month/:day', controller='journal', action='index')
    map.connect('/~:username/journals/:year/:month/:day/:id', controller='journal', action='view')
    map.connect('/~:username/journals/:year/:month/:day/:id/edit', controller='journal', action='edit')
    map.connect('/~:username/journals/:year/:month/:day/:id/edit_commit', controller='journal', action='edit_commit', **require_post)
    map.connect('/~:username/journals/:year/:month/:day/:id/delete', controller='journal', action='delete')
    map.connect('/~:username/journals/:year/:month/:day/:id/delete_commit', controller='journal', action='delete_commit', **require_post)
    map.connect('/~:username/journals/:year/:month/:day/:id/editlog', controller='editlog', action='journal')
    map.connect('/journals', controller='journal', action='index')
    map.connect('/journals/:year', controller='journal', action='index')
    map.connect('/journals/:year/:month', controller='journal', action='index')
    map.connect('/journals/:year/:month/:day', controller='journal', action='index')

    map.connect('/search', controller='search', action='index')
    map.connect('/search/do', controller='search', action='do')

    map.connect('/admin', controller='admin', action='index')
    map.connect('/admin/auth', controller='admin', action='auth')
    map.connect('/admin/auth_verify', controller='admin', action='auth_verify')
    map.connect('/admin/config', controller='admin', action='config')
    map.connect('/admin/config_ajax', controller='admin', action='config_ajax')
    map.connect('/admin/ip', controller='admin', action='ip')
    map.connect('/admin/show_bans', controller='admin', action='show_bans')
    map.connect('/admin/ban', controller='admin', action='ban', username=None)
    map.connect('/admin/ban_commit', controller='admin', action='ban_commit', **require_post)
    map.connect('/~:username/ban', controller='admin', action='ban')
    
    #map.connect('/stylesheets/:sheet/:color', controller='stylesheets', action='index', color=None)

    map.connect('/debug', controller='debug', action='index')
    map.connect('/debug/crash', controller='debug', action='crash')

    ### Backwards compatibility
    map.connect('/view/:id', controller='back_compat', action='view_submission')

    # Defaults that we may or may not actually be using
    map.connect('*url', controller='template', action='view')

    return map
