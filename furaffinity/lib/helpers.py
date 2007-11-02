"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from webhelpers import *

import re

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
