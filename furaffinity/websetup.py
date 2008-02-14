"""Setup the furaffinity application"""
import logging

from paste.deploy import appconfig
from pylons import config

from furaffinity.config.environment import load_environment
from furaffinity.lib import hashing

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup furaffinity here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)
    from furaffinity import model
    print "Creating tables"
    model.metadata.create_all(bind=config['pylons.g'].sa_engine)
    print "Successfully setup"

    print "Creating base data"
    nli_role = model.Role('Not logged in', 'The role assigned to users who are not logged in.')
    nli_role.sigil = ' '
    model.Session.save(nli_role)

    normal_role = model.Role('Member', 'Regular user')
    normal_role.sigil = '~'
    submit_perm = model.Permission('submit_art',
                                  'Can submit content to site.')
    normal_role.permissions.append(submit_perm)
    journal_perm = model.Permission('post_journal',
                                  'Can post journals to site.')
    normal_role.permissions.append(journal_perm)
    model.Session.save(normal_role)

    admin_role = model.Role('Administrator', 'Administrator')
    admin_role.sigil = '@'
    admin_perm = model.Permission('administrate',
                                  'General access to administration tools.')
    admin_role.permissions.append(admin_perm)
    admin_role.permissions.append(submit_perm)
    admin_role.permissions.append(journal_perm)
    model.Session.save(admin_role)

    print "Creating test data"
    u = model.User('fender', 'asdf')
    u.display_name = u'Fender'
    u.email = u'nobody@furaffinity.net'
    u.role = admin_role
    u.verified = True
    model.Session.save(u)

    u = model.User('eevee', 'pretzel')
    u.display_name = u'Eevee'
    u.email = u'nobody@furaffinity.net'
    u.role = admin_role
    u.verified = True
    model.Session.save(u)

    p = model.UserPreference(u, 'style_sheet', 'sufficiently-advanced')
    model.Session.save(p)
    p = model.UserPreference(u, 'style_color', 'light')
    model.Session.save(p)
    
    u = model.User('net-cat', 'asdf')
    u.display_name = u'net-cat'
    u.email = u'nobody@furaffinity.net'
    u.role = admin_role
    u.verified = True
    model.Session.save(u)
    
    u = model.User('luser', 'asdf')
    u.display_name = u'Luser'
    u.email = u'nobody@furaffinity.net'
    u.role = normal_role
    u.verified = True
    model.Session.save(u)

    n = model.News(u'headline', u'news content', u)
    model.Session.save(n)

    model.Session.commit()

    try:
        import magic
    except ImportError:
        print 'WARNING: mimetypes will be detected by filename instead of magic. In FreeBSD, install "devel/py-magic" from ports.'
        
    try:
        import xapian
        xapian.WritableDatabase('submission.xapian',xapian.DB_CREATE_OR_OVERWRITE)
        xapian.WritableDatabase('journal.xapian',xapian.DB_CREATE_OR_OVERWRITE)
        xapian.WritableDatabase('news.xapian',xapian.DB_CREATE_OR_OVERWRITE)
    except ImportError:
        print 'WARNING: Unable to load Xapian bindings. Search disabled.'
    
