from furaffinity import model
import sqlalchemy.exceptions
import re

class TagException(Exception):
    pass

class TagNotFound(TagException):
    pass

cache_by_text = {}

def make_tags_into_string(tags):
    tagstring = ''
    for tag in tags:
        tagstring = "%s %s" % (tagstring, tag.text)
    return tagstring.strip()

def get_tags_from_string(tags_blob):
    tags = []
    rmex = re.compile(r'[^a-z0-9]')
    for tag in tags_blob.lower().split(' '):
        tags.append(rmex.sub('',tag))
    return set(tags)

def get_by_text(text, create=False):
    if not cache_by_text.has_key(text):
        try:
            tag = model.Session.query(model.Tag).filter(model.Tag.text == text).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            # Need to create tag.
            if create:
                tag = model.Tag(text=text)
                model.Session.save(tag)
            else:
                raise TagNotFound
        cache_by_text[text] = tag
    return cache_by_text[text]
    
