"""Setup the ferrox application"""
import logging

from paste.deploy import appconfig
from pylons import config

from ferrox.config.environment import load_environment
from ferrox.lib import hashing

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup ferrox here"""

    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)

    from ferrox import model
    print "Creating tables."
    model.metadata.create_all(bind=config['pylons.g'].sa_engine)

    print "Creating base data..."

    ### Config

    print "    ...config"
    config_fields = (
        ('gallery', 'max depth', model.Config.Regexp, u'^\d*$', 10, u'Maximal depth of user gallery', False),
    )
    for group, name, type, pattern, value, description, encrypted in config_fields:
        model.Session.save(
            model.Config(group, name, type, pattern, value, description, encrypted)
            )
                                                            
    ### Roles

    print "    ...roles"
    # .manage = You can manage other people's entries from this controller.
    avalable_permissions = [
        # admin
        ['admin.auth', 'Can log into admin panel.'],
        ['admin.ban', 'Can manage bans.'],
        ['admin.config_view', 'Can view config.'],
        ['admin.config_edit', 'Can edit config.'],
        ['admin.ip', 'Can see user IP addresses.'],
        ['admin.roles', 'Can manage user roles. (God mode cheat.)'],

        # back_compat probably doesn't need permissions
        
        # comments
        ['comments.reply', 'Can make comments.'],

        # debug
        ['debug', 'Can use debug functions.'],

        # editlog
        ['editlog', 'Can view edit logs.'],

        # gallery
        ['gallery.view', 'Can browse galleries and view pictures.'],
        ['gallery.upload', 'Can upload submissions.'],
        ['gallery.favorite', 'Can manage own favorites.'],
        ['gallery.manage', 'Can manage other people\'s submissions.'],

        # index
        ['index.register', 'Can register a new account. (Don\'t enable this.)'],
        ['index.login', 'Can log in to site.'],

        # journal
        ['journal.view', 'Can browse journals and view entries.'],
        ['journal.post', 'Can post journals.'],
        ['journal.manage', 'Can manage other people\'s journals.'],

        # news
        ['news.manage', 'Can manage site news.'],

        # notes
        ['notes.view', 'Can view notes.'],
        ['notes.write', 'Can write notes.'],
        ['notes.manage', 'Can view other people\'s notes.'],
        
        # search
        ['search.do', 'Can use site\'s search function.'],
        
        # stylesheets probably doesn't need permissions
        
        # template probably doesn't need permissions
        
        # user is view-only?

        # user_settings
        ['user_settings.avatars', 'Can manage own avatars.'],
        ['user_settings.relationships', 'Can manage own relationships.'],
        ['user_settings.manage', 'Can manage other people\'s settings.'],
    ]

    permissions = {}
    for p in avalable_permissions:
        permissions[p[0]] = model.Permission(*p)
        model.Session.save(permissions[p[0]])

    '''
    .permissions.append(permissions['admin.auth'])
    .permissions.append(permissions['admin.ban'])
    .permissions.append(permissions['admin.config_view'])
    .permissions.append(permissions['admin.config_edit'])
    .permissions.append(permissions['admin.ip'])
    .permissions.append(permissions['admin.roles'])
    .permissions.append(permissions['comments.reply'])
    .permissions.append(permissions['debug'])
    .permissions.append(permissions['editlog'])
    .permissions.append(permissions['gallery.view'])
    .permissions.append(permissions['gallery.upload'])
    .permissions.append(permissions['gallery.favorite'])
    .permissions.append(permissions['gallery.manage'])
    .permissions.append(permissions['index.register'])
    .permissions.append(permissions['index.login'])
    .permissions.append(permissions['journal.view'])
    .permissions.append(permissions['journal.post'])
    .permissions.append(permissions['journal.manage'])
    .permissions.append(permissions['news.manage'])
    .permissions.append(permissions['notes.view'])
    .permissions.append(permissions['notes.write'])
    .permissions.append(permissions['notes.manage'])
    .permissions.append(permissions['search.do'])
    .permissions.append(permissions['user_settings.avatars'])
    .permissions.append(permissions['user_settings.relationships'])
    .permissions.append(permissions['user_settings.manage'])
    '''
    
    null_role = model.Role('Null', 
                           'User who can\'t do anything. Literally.')
    null_role.sigil = ' '
    model.Session.save(null_role)

    guest_role = model.Role('Guest',
                            'Non-registered Users')
    guest_role.sigil = ' '
    guest_role.permissions.append(permissions['gallery.view'])
    guest_role.permissions.append(permissions['index.register'])
    guest_role.permissions.append(permissions['journal.view'])
    guest_role.permissions.append(permissions['search.do'])
    model.Session.save(guest_role)
    

    unverified_role = model.Role('Unverified',
                                 'User who has not verified eir email')
    unverified_role.sigil = '?'
    unverified_role.permissions.append(permissions['gallery.view'])
    unverified_role.permissions.append(permissions['journal.view'])
    unverified_role.permissions.append(permissions['notes.view'])
    unverified_role.permissions.append(permissions['notes.write'])
    unverified_role.permissions.append(permissions['search.do'])
    model.Session.save(unverified_role)

    banned_role = model.Role('Banned', 'User who has been banned.')
    banned_role.sigil = '-'
    banned_role.permissions.append(permissions['gallery.view'])
    banned_role.permissions.append(permissions['gallery.favorite'])
    banned_role.permissions.append(permissions['index.login'])
    banned_role.permissions.append(permissions['journal.view'])
    banned_role.permissions.append(permissions['notes.view'])
    banned_role.permissions.append(permissions['search.do'])
    model.Session.save(banned_role)

    normal_role = model.Role('Member', 'Regular user')
    normal_role.sigil = '~'
    normal_role.permissions.append(permissions['comments.reply'])
    normal_role.permissions.append(permissions['gallery.view'])
    normal_role.permissions.append(permissions['gallery.upload'])
    normal_role.permissions.append(permissions['gallery.favorite'])
    normal_role.permissions.append(permissions['index.login'])
    normal_role.permissions.append(permissions['journal.view'])
    normal_role.permissions.append(permissions['journal.post'])
    normal_role.permissions.append(permissions['notes.view'])
    normal_role.permissions.append(permissions['notes.write'])
    normal_role.permissions.append(permissions['search.do'])
    normal_role.permissions.append(permissions['user_settings.avatars'])
    normal_role.permissions.append(permissions['user_settings.relationships'])
    normal_role.permissions.append(permissions['user_settings.manage'])
    model.Session.save(normal_role)

    admin_role = model.Role('Administrator', 'Site Administrator')
    admin_role.sigil = '@'
    admin_role.permissions.append(permissions['admin.auth'])
    admin_role.permissions.append(permissions['admin.ban'])
    admin_role.permissions.append(permissions['admin.config_view'])
    admin_role.permissions.append(permissions['admin.ip'])
    admin_role.permissions.append(permissions['admin.roles'])
    admin_role.permissions.append(permissions['comments.reply'])
    admin_role.permissions.append(permissions['editlog'])
    admin_role.permissions.append(permissions['gallery.view'])
    admin_role.permissions.append(permissions['gallery.upload'])
    admin_role.permissions.append(permissions['gallery.favorite'])
    admin_role.permissions.append(permissions['gallery.manage'])
    admin_role.permissions.append(permissions['index.register'])
    admin_role.permissions.append(permissions['index.login'])
    admin_role.permissions.append(permissions['journal.view'])
    admin_role.permissions.append(permissions['journal.post'])
    admin_role.permissions.append(permissions['journal.manage'])
    admin_role.permissions.append(permissions['news.manage'])
    admin_role.permissions.append(permissions['notes.view'])
    admin_role.permissions.append(permissions['notes.write'])
    admin_role.permissions.append(permissions['notes.manage'])
    admin_role.permissions.append(permissions['search.do'])
    admin_role.permissions.append(permissions['user_settings.avatars'])
    admin_role.permissions.append(permissions['user_settings.relationships'])
    admin_role.permissions.append(permissions['user_settings.manage'])
    model.Session.save(admin_role)

    sysadmin_role = model.Role('Bastard Operator From Hell', 'Users that have access to the underlying software.')
    sysadmin_role.sigil = '^'
    sysadmin_role.permissions.append(permissions['admin.auth'])
    sysadmin_role.permissions.append(permissions['admin.ban'])
    sysadmin_role.permissions.append(permissions['admin.config_view'])
    sysadmin_role.permissions.append(permissions['admin.ip'])
    sysadmin_role.permissions.append(permissions['admin.roles'])
    sysadmin_role.permissions.append(permissions['comments.reply'])
    sysadmin_role.permissions.append(permissions['debug'])
    sysadmin_role.permissions.append(permissions['editlog'])
    sysadmin_role.permissions.append(permissions['gallery.view'])
    sysadmin_role.permissions.append(permissions['gallery.upload'])
    sysadmin_role.permissions.append(permissions['gallery.favorite'])
    sysadmin_role.permissions.append(permissions['gallery.manage'])
    sysadmin_role.permissions.append(permissions['index.register'])
    sysadmin_role.permissions.append(permissions['index.login'])
    sysadmin_role.permissions.append(permissions['journal.view'])
    sysadmin_role.permissions.append(permissions['journal.post'])
    sysadmin_role.permissions.append(permissions['journal.manage'])
    sysadmin_role.permissions.append(permissions['news.manage'])
    sysadmin_role.permissions.append(permissions['notes.view'])
    sysadmin_role.permissions.append(permissions['notes.write'])
    sysadmin_role.permissions.append(permissions['notes.manage'])
    sysadmin_role.permissions.append(permissions['search.do'])
    sysadmin_role.permissions.append(permissions['user_settings.avatars'])
    sysadmin_role.permissions.append(permissions['user_settings.relationships'])
    sysadmin_role.permissions.append(permissions['user_settings.manage'])
    model.Session.save(sysadmin_role)

    print "    ...user metadata"
    metadata_fields = (
        (u'bio',            u'Short bio'),
        (u'artist_type',    u'Artist type'),
        (u'location',       u'Location'),
        (u'interests',      u'Interests'),
        (u'occupation',     u'Occupation'),
        (u'age',            u'Age'),
        (u'nerd_shell',     u'Shell'),
        (u'nerd_os',        u'Operating system'),
        (u'nerd_browser',   u'Browser'),
        (u'fav_quote',      u'Favorite quote'),
        (u'fav_movie',      u'Favorite movie'),
        (u'fav_game',       u'Favorite game'),
        (u'fav_player',     u'Favorite music player'),
        (u'fav_artist',     u'Favorite artist'),
        (u'fav_animal',     u'Favorite animal'),
        (u'fav_site',       u'Favorite Web site'),
        (u'fav_food',       u'Favorite food'),
    )
    for key, description in metadata_fields:
        model.Session.save(
            model.UserMetadataField(key=key, description=description)
            )

    print "Done."
    print "Creating test data..."

    print "    ...users"
    u = model.User('fender', 'asdf')
    u.display_name = u'Fender'
    u.email = u'nobody@example.net'
    u.role = admin_role
    model.Session.save(u)

    u = model.User('eevee', 'pretzel')
    u.display_name = u'Eevee'
    u.email = u'ferrox@veekun.com'
    u.role = admin_role
    model.Session.save(u)

    p = model.UserPreference(u, 'style_sheet', 'sufficiently-advanced')
    model.Session.save(p)
    p = model.UserPreference(u, 'style_color', 'light')
    model.Session.save(p)

    u = model.User('net-cat', 'asdf')
    u.display_name = u'net-cat'
    u.email = u'nobody@example.net'
    u.role = admin_role
    model.Session.save(u)

    u = model.User('luser', 'asdf')
    u.display_name = u'Luser'
    u.email = u'nobody@example.net'
    u.role = normal_role
    model.Session.save(u)

    print "Done."
    model.Session.commit()

    try:
        import magic
    except ImportError:
        print 'WARNING: mimetypes will be detected by filename instead of magic. In FreeBSD, install "devel/py-magic" from ports.'

    try:
        import xapian
        xapian.WritableDatabase('submission.xapian', xapian.DB_CREATE_OR_OVERWRITE)
        xapian.WritableDatabase('journal.xapian', xapian.DB_CREATE_OR_OVERWRITE)
    except ImportError:
        print 'WARNING: Unable to load Xapian bindings. Search disabled.'
