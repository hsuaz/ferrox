"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from webhelpers import *

import re
import time
import struct
import socket

def sanitize(string):
    """Cleanse an untrusted string of any characters unfriendly to HTML."""
    string = string.replace('&', '&amp;')
    string = string.replace('<', '&lt;')
    string = string.replace('>', '&gt;')
    string = string.replace('"', '&quot;')
    string = re.sub(u'([^\x0d\x0a\x20-\x7f])', lambda match: '&#x%x;' % ord(match.group), string)
    return normalize_newlines(string)

def normalize_newlines(string):
    """Adjust all line endings to be the Linux line break, \\x0a."""
    return re.compile("\x0d\x0a|\x0d").sub("\x0a", string)
    
def to_dict(model):
    '''Convert a SQLAlchemy model instance into a dictionary'''
    model_dict = {}
    for propname in model.c.keys():
        model_dict[propname] = getattr(model, propname)
    return model_dict

def embed_flash(url):
    return """
<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,40,0" id="page_content">
    <param name="movie" value="%s" />
    <param name="quality" value="high" />
    <param name="bgcolor" value="#FFFFFF" />
    <embed src="%s" quality="high" bgcolor="#FFFFFF" name="myMoviename" aligh="" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer"></embed>
</object>
""" % (url,url)

def dict_to_option (opts=(),default=None):
    output = ''
    for k in opts.keys():
        if (opts[k] == ''):
            v = k
        else:
            v = opts[k]
        if (default == k):
            selected = ' selected="selected"'
        else:
            selected = ''
        output = "%s\n<option value=\"%s\"%s>%s</option>" % (output, k, selected, v)
    return output

def ip_to_integer(ip_string):
    """Convert an IP in a.b.c.d form into a packed integer."""
    return struct.unpack('I', socket.inet_aton(ip_string))[0]

def ip_to_string(ip_integer):
    """Convert an IP in packed integer form to a.b.c.d form."""
    return socket.inet_ntoa(struct.pack('I', ip_integer))

def format_time(datetime):
    """Format a datetime object standardly."""
    return datetime.strftime('%m/%d/%y %I:%M %p')

