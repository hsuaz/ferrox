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
    normal_user_type = model.UserType()
    normal_user_type.sigil = '~'
    normal_user_type.name = 'Member'
    model.Session.save(normal_user_type)

    admin_user_type = model.UserType()
    admin_user_type.sigil = '@'
    admin_user_type.name = 'Adminstrator'
    model.Session.save(admin_user_type)

    print "Creating test data"
    j = model.Journal()
    j.header = 'foo'
    j.footer = 'bar'

    je = model.JournalEntry('title', 'content')
    model.Session.save(je)


    j.entries.append(je)
    model.Session.save(j)

    u = model.User('fender', 'asdf')
    u.display_name = 'Fender'
    u.user_type = admin_user_type
    u.journals.append(j)
    model.Session.save(u)

    model.Session.commit()
