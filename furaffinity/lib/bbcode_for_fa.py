from bbcode import *
from base import *
import furaffinity.model

class User(TagBase):
    no_close = True

    def __init__(self):
        self.last_error = None
        pass

    def start(self, name, params):
        if not params:
            self.last_error = "no username provided for [%s]"%name
            return ''
        
        if ';' in params:
            (username, linktype) = params.split(';')
        else:
            username = params
            linktype = 'name'
            
        if name == 'icon':
            linktype = 'icon'
        
        user_object = furaffinity.model.User.get_by_name(username)
        
        if user_object:
            if linktype == 'name':
                return h.link_to(user_object.display_name, h.url_for(controller='user', action='view', username=user_object.username))
            elif linktype == 'icon':
                return h.link_to("(Icon for %s goes here)"%user_object.display_name, h.url_for(controller='user', action='view', username=user_object.username))
            elif linktype == 'both':
                return h.link_to("(Icon for %s goes here)%s"%(user_object.display_name,user_object.display_name), h.url_for(controller='user', action='view', username=user_object.username))

        self.last_error = "invalid username provided for [%s]"%name
        return ''
        
        
parser = BBcodeParser(sanitizer=h.escape_once)
parser.tag_handlers['b'] = Bold()
parser.tag_handlers['i'] = Italic()
parser.tag_handlers['u'] = Underline()
parser.tag_handlers['s'] = Strike()
parser.tag_handlers['quote'] = Quote()
parser.tag_handlers['url'] = URL(h.escape_once)
parser.tag_handlers['code'] = Code()
parser.tag_handlers['user'] = User()
parser.tag_handlers['icon'] = parser.tag_handlers['user']

parser_long = BBcodeParser(sanitizer=h.escape_once) # for use with [cut] tags
parser_long.tag_handlers.update(parser.tag_handlers)
parser_long.tag_handlers['cut'] = Cut()

parser_short = BBcodeParser(sanitizer=h.escape_once) # for use with [cut] tags
parser_short.tag_handlers.update(parser.tag_handlers)
parser_short.tag_handlers['cut'] = Cut(False)

parser_plaintext = BBCodeParser(sanitizer=h.escape_once)
parser_plaintext.tag_handlers['b'] = \
    parser_plaintext.tag_handlers['i'] = \
    parser_plaintext.tag_handlers['u'] = \
    parser_plaintext.tag_handlers['s'] = \
    parser_plaintext.tag_handlers['quote'] = \
    parser_plaintext.tag_handlers['url'] = \
    parser_plaintext.tag_handlers['code'] = \
    parser_plaintext.tag_handlers['user'] = \
    parser_plaintext.tag_handlers['icon'] = \
    parser_plaintext.tag_handlers['cut'] = Blank(False)
