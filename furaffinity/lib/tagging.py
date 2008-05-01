from furaffinity import model
import sqlalchemy.exceptions
from sqlalchemy import or_, and_, not_
import re
from binascii import crc32

class TagException(Exception):
    pass

class TagNotFound(TagException):
    pass

cache_by_text = {}


"""
Terms:
tag_string = user input  (a b -c)
compiled_tag_string = tag_string using ids instead of raw tag names (1 2 !3)
tag_object_array = Array of model.Tag objects
"""

def break_apart_tag_string(tag_string, include_negative=False):
    negative = []
    positive = []

    rmex = re.compile(r'[^a-z0-9-]')
    compiled_tag_string = ''

    if tag_string:
        for tag_text in tag_string.split(' '):
            tag_text = rmex.sub('', tag_text)
            if len(tag_text) > 1 and tag_text[0] == '-':
                negative.append(tag_text[1:])
            elif len(tag_text) > 0:
                positive.append(tag_text)
            
    if include_negative:
        return (positive, negative)
    else:
        return positive
        
def break_apart_compiled_tag_string(compiled_tag_string, include_negative=False):
    negative = []
    positive = []
    
    rmex = re.compile(r'[^0-9!]')
    compiled_tag_string = ''

    for tag_id in tag_string.split(' '):
        tag_id = rmex.sub('', tag_id)
        if len(tag_id) > 1 and tag_id[0] == '-':
            negative.append(int(tag_id[1:]))
        elif len(tag_text) > 0:
            positive.append(int(tag_id))
            
    if include_negative:
        return (positive, negative)
    else:
        return positive

# postive and negative are tag_object_arrays
def make_tag_string(positive, negative = []):
    tag_string = ''
    for x in positive:
        tag_string += str(x) + ' '
    for x in negative:
        tag_string += "-%s "%str(x)
    return tag_string.strip()
    
# postive and negative are tag_object_arrays
def make_compiled_tag_string(positive, negative = []):
    compiled_tag_string = ''
    for x in positive:
        if int(x) == 0:
            raise Exception("Tag '%s' is not in the database yet. Try model.Session.commit()"%str(x))
        compiled_tag_string += "%d "%x
    for x in negative:
        if int(x) == 0:
            raise Exception("Tag '%s' is not in the database yet. Try model.Session.commit()"%str(x))
        compiled_tag_string += "-%d "%x
    return compiled_tag_string.strip()

