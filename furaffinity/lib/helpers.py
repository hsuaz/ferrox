"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from webhelpers.rails.wrapped import *
from routes import url_for, redirect_to
import pylons.config

import os
import re
import time

def normalize_newlines(string):
    """Adjust all line endings to be the Linux line break, \\x0a."""
    return re.compile("\x0d\x0a|\x0d").sub("\x0a", string)

def to_dict(model):
    '''Convert a SQLAlchemy model instance into a dictionary'''
    model_dict = {}
    for propname in model.__table__.c.keys():
        model_dict[propname] = getattr(model, propname)
    return model_dict

def embed_flash(url,dims=None):
    rv = """
<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,40,0" id="page_content" """

    if dims != None:
        rv = rv + "height=\"%d\" width=\"%d\"" % dims

    rv = rv + """>
    <param name="movie" value="%s" />
    <param name="quality" value="high" />
    <param name="bgcolor" value="#FFFFFF" />
    <embed src="%s" quality="high" bgcolor="#FFFFFF" name="myMoviename" align="" type="application/x-shockwave-flash"  pluginspage="http://www.macromedia.com/go/getflashplayer" """ % (url,url)

    if dims != None:
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
        if opts[k] == '':
            v = k
        else:
            v = opts[k]
        if default == k:
            selected = ' selected="selected"'
        else:
            selected = ''
        output = "%s\n<option value=\"%s\"%s>%s</option>" % (output, k, selected, v)
    return output

def format_time(datetime):
    """Format a datetime object standardly."""
    format_string = '%m/%d/%y %I:%M %p'
    if hasattr(datetime,'strftime'):
        return datetime.strftime(format_string)
    else:
        return time.strftime(format_string,time.gmtime(datetime))

def image_tag(source, alt=None, size=None, **options):
    """
    Copied from the default pylons webhelpers, to fix alt='' not working.

    Also copies alt into title, if one isn't specified.
    """

    options['src'] = rails.asset_tag.compute_public_path(source, 'images')

    if alt == None:
        alt = os.path.splitext(os.path.basename(source))[0].title()
    options['alt'] = alt

    if not 'title' in options:
        options['title'] = options['alt']

    if size and re.match('^(\d+|)x(\d+|)$', size) and size != 'x':
        width, height = size.split('x')
        if width:
            options['width'] = width
        if height:
            options['height'] = height

    return tag('img', **options)

def form(*args, **kwargs):
    raise RuntimeError("Do not use the built-in webhelpers form tags "
                       "functions.  Use formgen instead.  If you don't need "
                       "errors or defaults, use c.empty_form.")
start_form = form
end_form = form
text_field = form
submit = form
password_field = form
check_box = form
radio_buttom = form
hidden_field = form
file_field = form

def indented_comments(comments):
    """Given a list of comment rows, returns them with an indent property set
    corresponding to the depth relative to the first (presumably the root).

    The comments should be in order by left.  This will always put them in
    the correct order.
    """

    last_comment = None
    indent = 0
    right_ancestry = []
    for comment in comments:
        if last_comment \
           and comment.left < last_comment.right:
            indent = indent + 1
            right_ancestry.append(last_comment)

        for i in xrange(len(right_ancestry) - 1, -1, -1):
            if comment.left > right_ancestry[i].right:
                indent = indent - 1
                right_ancestry.pop(i)

        if len(right_ancestry):
            comment._parent = right_ancestry[-1]

        comment.indent = indent

        last_comment = comment

    return comments


def get_avatar_url(object = None):
    if hasattr(object, 'avatar') and object.avatar:
        return url_for(controller='gallery', action='file', filename=object.avatar.mogile_key)
    else:
        av = None
        if hasattr(object, 'primary_artist'):
            av = object.primary_artist.default_avatar
        elif hasattr(object, 'author'):
            av = object.author.default_avatar
        elif hasattr(object, 'user'):
            av = object.user.default_avatar
        elif hasattr(object, 'default_avatar') and object.default_avatar:
            av = object.user.default_avatar
        if av:
            return url_for(controller='gallery', action='file', filename=av.mogile_key)
    
    return pylons.config.get('avatar.default', '/default_avatar.png')


def objects_to_option_tags(objects, default=None, id_attr='id', name_attr='name'):
    output = ''
    
    for o in objects:
        output += """<option value="%d"%s>%s</option>""" % (getattr(o, id_attr), 
                ' selected="selected"' if default==getattr(o, id_attr) else '', getattr(o, name_attr))

    return output
    
