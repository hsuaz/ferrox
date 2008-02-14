"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from webhelpers import *

import re
import time
import struct
import socket

try:
    import magic
    def get_mime_type(fileobject):
        ms = magic.open(magic.MAGIC_MIME)
        ms.load()
        type = ms.buffer(fileobject['content'])
        ms.close()
        return type
except ImportError:
    import mimetypes
    def get_mime_type(fileobject):
        return mimetypes.guess_type(fileobject['filename'])[0]
        
def normalize_newlines(string):
    """Adjust all line endings to be the Linux line break, \\x0a."""
    return re.compile("\x0d\x0a|\x0d").sub("\x0a", string)
    
def to_dict(model):
    '''Convert a SQLAlchemy model instance into a dictionary'''
    model_dict = {}
    for propname in model.c.keys():
        model_dict[propname] = getattr(model, propname)
    return model_dict

def embed_flash(url,dims=None):
    rv = """
<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,40,0" id="page_content" """

    if ( dims != None ):
        rv = rv + "height=\"%d\" width=\"%d\"" % dims

    rv = rv + """>
    <param name="movie" value="%s" />
    <param name="quality" value="high" />
    <param name="bgcolor" value="#FFFFFF" />
    <embed src="%s" quality="high" bgcolor="#FFFFFF" name="myMoviename" align="" type="application/x-shockwave-flash"  pluginspage="http://www.macromedia.com/go/getflashplayer" """ % (url,url)
    
    if ( dims != None ):
        rv = rv + "height=\"%d\" width=\"%d\"" % dims
    
    rv = rv + """></embed>
</object>
""" 
    
    return rv

def embed_mp3(url):
    return """
    <object width="300" height="42">
    <param name="src" value="%s">
    <param name="autoplay" value="true">
    <param name="controller" value="true">
    <param name="bgcolor" value="#FF9900">
    <embed src="%s" autostart="true" loop="false" width="300" height="42" controller="true" bgcolor="#FF9900"></embed>
    </object>
"""%(url,url)

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
