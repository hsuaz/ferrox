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
                 always_scan=config['debug'])

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    map.connect('/', controller='index', action='index')
    map.connect('/login', controller='index', action='login')
    map.connect('/login_check', controller='index', action='login_check')
    map.connect('/logout', controller='index', action='logout')
    map.connect('/register', controller='index', action='register')
	
    map.connect('/gallery/submit_upload', controller='gallery', action='submit_upload' )
    map.connect('/gallery/submit', controller='gallery', action='submit' )
    map.connect('/gallery', controller='gallery', action='index' )
    map.connect('/gallery/view/:id', controller='gallery', action='view' )
    map.connect('/gallery/image/:filename', controller='gallery', action='file' )

    map.connect('/journal/submit_upload', controller='journal', action='post_commit' )
    map.connect('/journal/submit', controller='journal', action='post' )
    map.connect('/journal', controller='journal', action='index' )
    map.connect('/journal/view/:id', controller='journal', action='view' )

    # CUSTOM ROUTES HERE

    map.connect(':controller/:action/:id')
    map.connect('*url', controller='template', action='view')

    return map
