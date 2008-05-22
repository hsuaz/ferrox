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

    map.sub_domains = True
    map.sub_domains_ignore = ['www']
    # We do this a lot, so be epic lazy
    require_post = dict(conditions=dict(method=['POST']))
    with_sub_domain = dict(conditions=dict(sub_domain=True))

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    map.connect('/', controller='user', action='view', **with_sub_domain)
    
    map.connect('/', controller='index', action='index')
    map.connect('/login', controller='index', action='login')
    map.connect('/login_check', controller='index', action='login_check', **require_post)
    map.connect('/logout', controller='index', action='logout', **require_post)
    map.connect('/register', controller='index', action='register')
    map.connect('/register_check', controller='index', action='register_check', **require_post)
    map.connect('/verify', controller='index', action='verify')
    map.connect('/users/:username', controller='user', action='view')
    map.connect('/users/:username/profile', controller='user', action='profile')
    map.connect('/users/:username/settings', controller='user', action='settings')

    map.connect('/news', controller='news', action='index')
    map.connect('/news/post', controller='news', action='post')
    map.connect('/news/do_post', controller='news', action='do_post')
    map.connect('/news/:id/edit', controller='news', action='edit')
    map.connect('/news/:id/edit_commit', controller='news', action='edit_commit', **require_post)
    map.connect('/news/:id/editlog', controller='editlog', action='news')
    map.connect('/news/:id', controller='news', action='view')

    map.connect('/*discussion_url/comments', controller='comments', action='view')
    map.connect('/*discussion_url/comments/reply', controller='comments', action='reply')
    map.connect('/*discussion_url/comments/reply_commit', controller='comments', action='reply_commit')
    map.connect('/*discussion_url/comments/:id', controller='comments', action='view')
    map.connect('/*discussion_url/comments/:id/reply', controller='comments', action='reply')
    map.connect('/*discussion_url/comments/:id/reply_commit', controller='comments', action='reply_commit')

    map.connect('/users/:username/notes', controller='notes', action='user_index')
    map.connect('/users/:username/notes/write', controller='notes', action='write')
    map.connect('/users/:username/notes/write_send', controller='notes', action='write_send', **require_post)
    map.connect('/users/:username/notes/:id', controller='notes', action='view')
    map.connect('/users/:username/notes/:id/ajax_expand', controller='notes', action='ajax_expand')
    map.connect('/users/:username/notes/:id/reply', controller='notes', action='reply')
    map.connect('/users/:username/notes/:id/forward', controller='notes', action='forward')

    map.connect('/users/:username/gallery', controller='gallery', action='index')
    map.connect('/users/:username/gallery/submit', controller='gallery', action='submit')
    map.connect('/users/:username/gallery/submit_upload', controller='gallery', action='submit_upload', **require_post)
    map.connect('/users/:username/gallery/:id', controller='gallery', action='view')
    map.connect('/users/:username/gallery/:id/edit', controller='gallery', action='edit')
    map.connect('/users/:username/gallery/:id/edit_commit', controller='gallery', action='edit_commit', **require_post)
    map.connect('/users/:username/gallery/:id/delete', controller='gallery', action='delete')
    map.connect('/users/:username/gallery/:id/delete_commit', controller='gallery', action='delete_commit', **require_post)
    map.connect('/users/:username/gallery/:id/editlog', controller='editlog', action='submission')

    map.connect('/gallery', controller='gallery', action='index')
    map.connect('/download/:filename', controller='gallery', action='file')

    map.connect('/users/:username/journals', controller='journal', action='index')
    map.connect('/users/:username/journals/post', controller='journal', action='post')
    map.connect('/users/:username/journals/post_commit', controller='journal', action='post_commit', **require_post)
    map.connect('/users/:username/journals/:year', controller='journal', action='index')
    map.connect('/users/:username/journals/:year/:month', controller='journal', action='index')
    map.connect('/users/:username/journals/:year/:month/:day', controller='journal', action='index')
    map.connect('/users/:username/journals/:year/:month/:day/:id', controller='journal', action='view')
    map.connect('/users/:username/journals/:year/:month/:day/:id/edit', controller='journal', action='edit')
    map.connect('/users/:username/journals/:year/:month/:day/:id/edit_commit', controller='journal', action='edit_commit', **require_post)
    map.connect('/users/:username/journals/:year/:month/:day/:id/delete', controller='journal', action='delete')
    map.connect('/users/:username/journals/:year/:month/:day/:id/delete_commit', controller='journal', action='delete_commit', **require_post)
    map.connect('/users/:username/journals/:year/:month/:day/:id/editlog', controller='editlog', action='journal')
    map.connect('/journals', controller='journal', action='index')
    map.connect('/journals/:year', controller='journal', action='index')
    map.connect('/journals/:year/:month', controller='journal', action='index')
    map.connect('/journals/:year/:month/:day', controller='journal', action='index')

    map.connect('/stylesheets/:sheet/:color', controller='stylesheets', action='index', color=None)

    map.connect('/debug', controller='debug', action='index')
    map.connect('/debug/crash', controller='debug', action='crash')

    map.connect('/search', controller='search', action='index')
    map.connect('/search/do', controller='search', action='do')
    
    map.connect('/users/:username/relationships', controller='user', action='relationships')
    map.connect('/users/:username/watch', controller='user', action='watch')
    map.connect('/users/:username/watch_commit', controller='user', action='watch_commit')
    map.connect('/users/:username/block', controller='user', action='block', confirm=None)
    map.connect('/users/:username/friend', controller='user', action='friend', confirm=None)
    #map.connect('/journals/fill', controller='journal', action='fill')
    
    # Backwards compatibility
    map.connect('/view/:id', controller='back_compat', action='view_submission')

    # Defaults that we may or may not actually be using
    map.connect('*url', controller='template', action='view')

    return map
