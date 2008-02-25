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

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    map.connect('/', controller='index', action='index')
    map.connect('/login', controller='index', action='login')
    map.connect('/login_check', controller='index', action='login_check', **require_post)
    map.connect('/logout', controller='index', action='logout', **require_post)
    map.connect('/register', controller='index', action='register')
    map.connect('/register_check', controller='index', action='register_check', **require_post)
    map.connect('/verify', controller='index', action='verify')
    map.connect('/users/:username', controller='user', action='view')
    map.connect('/users/:username/settings', controller='user', action='settings')

    map.connect('/news/:id/edit', controller='news', action='edit')
    map.connect('/news/:id/edit_commit', controller='news', action='edit_commit', **require_post)

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
    map.connect('/users/:username/journals/:id', controller='journal', action='view')
    map.connect('/users/:username/journals/:id/edit', controller='journal', action='edit')
    map.connect('/users/:username/journals/:id/edit_commit', controller='journal', action='edit_commit', **require_post)
    map.connect('/users/:username/journals/:id/delete', controller='journal', action='delete')
    map.connect('/users/:username/journals/:id/delete_commit', controller='journal', action='delete_commit', **require_post)
    map.connect('/users/:username/journals/:id/editlog', controller='editlog', action='journal')

    map.connect('/view/:id', controller='gallery', action='forward_to_user')
    #map.connect('/journal', controller='journal', action='index')

    map.connect('/stylesheets/:sheet/:color', controller='stylesheets', action='index', color=None)

    map.connect('/debug', controller='debug', action='index')
    map.connect('/debug/crash', controller='debug', action='crash')

    map.connect(':controller/:action/:id', action='index', id=None)
    map.connect('*url', controller='template', action='view')

    return map
