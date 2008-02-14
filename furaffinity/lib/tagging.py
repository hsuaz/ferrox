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

# for Tag objects
def make_tags_into_string(tags):
    tagstring = ''
    for tag in tags:
        tagstring = "%s %s" % (tagstring, tag.text)
    return tagstring.strip()

# returns array of strings
def get_tags_from_string(tags_blob):
    tags = []
    rmex = re.compile(r'[^a-z0-9]')
    for tag in tags_blob.lower().split(' '):
        tags.append(rmex.sub('',tag))
    return list(set(tags))

# returns two arrays of strings
def get_neg_and_pos_tags_from_string(tags_blob):
    pos_tags = []
    neg_tags = []
    #print "tagging %s %s"%(pos_tags,neg_tags)
    rmex = re.compile(r'[^a-z0-9]')
    if tags_blob != None:
        for tag in tags_blob.lower().split(' '):
            sanitized_tag = rmex.sub('',tag)
            if len(sanitized_tag)>0:
                if len(tag)>1 and tag[0] == '-':
                    neg_tags.append(sanitized_tag)
                elif len(tag)>0:
                    pos_tags.append(sanitized_tag)
            
    pos_tags = list(set(pos_tags))
    neg_tags = list(set(neg_tags))
    
    for tag in pos_tags:
        try:
            neg_tags.remove(tag)
        except ValueError:
            pass
    
    pos_tags.sort()
    neg_tags.sort()
    return (pos_tags,neg_tags)

# for array of tags
def recreate_tag_string(positive_tags,negative_tags):
    tagstring = ''
    for tag in positive_tags:
        tagstring = "%s %s" % (tagstring, tag)
    for tag in negative_tags:
        tagstring = "%s -%s" % (tagstring, tag)
    return tagstring.strip()
    

def get_id_by_text(text):
    return crc32(text)
    
def get_by_text(text, create=False):
    if not cache_by_text.has_key(text):
        tag_id = get_id_by_text(text)
        try:
            tag = model.Session.query(model.Tag).filter(model.Tag.id == tag_id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            # Need to create tag.
            if create:
                tag = model.Tag(text=text)
                model.Session.save(tag)
            else:
                raise TagNotFound
        cache_by_text[text] = tag
    return cache_by_text[text]
    
def cache_by_list(list):
    list_of_tags_fetched = []
    total_tags_to_fetch = 0
    tag_query = model.Session.query(model.Tag)

    query_eval = 'or_('
    first = True
    for text in list:
        if not cache_by_text.has_key(text):
            if first:
                first = False
            else:
                query_eval += ','
                
            query_eval += "model.Tag.id == %d"%get_id_by_text(text)
            total_tags_to_fetch += 1
    query_eval += ')'
    
    tags = tag_query.filter(eval(query_eval)).all()
    for tag in tags:
        cache_by_text[tag.text] = tag
        list_of_tags_fetched.append(tag.text)
    return list_of_tags_fetched
