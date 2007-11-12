"""Setup the furaffinity application"""
import logging

from paste.deploy import appconfig
from pylons import config

from furaffinity.config.environment import load_environment

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
    u.display_name = 'Fender'
    u.role = admin_role
    model.Session.save(u)

    u = model.User('eevee', 'pretzel')
    u.display_name = 'Eevee'
    u.role = admin_role
    model.Session.save(u)

    n = model.News('headline', 'news content')
    n.author = u
    model.Session.save(n)

    model.Session.commit()
