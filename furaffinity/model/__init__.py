from __future__ import with_statement

import pylons

from furaffinity.lib.image import ImageClass
from furaffinity.lib.mimetype import get_mime_type
from furaffinity.lib import helpers as h
import furaffinity.lib.bbcode_for_fa as bbcode

from sqlalchemy import Column, MetaData, Table, ForeignKey, types, sql
from sqlalchemy.orm import mapper, object_mapper, relation
from sqlalchemy.databases.mysql import MSInteger, MSEnum
from sqlalchemy.exceptions import InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base

from binascii import crc32
import cStringIO
import chardet
import codecs
from datetime import datetime, timedelta
from datetimeasint import *
from enum import *
import hashlib
import mimetypes
import os.path
import random
import re
import sys

from furaffinity.model.db.user import *
from furaffinity.model.db.blob import *
from furaffinity.model.db import Session, metadata

search_enabled = True
try:
    import xapian
except ImportError:
    search_enabled = False

if pylons.config['mogilefs.tracker'] == 'FAKE':
    from furaffinity.lib import fakemogilefs as mogilefs
else:
    from furaffinity.lib import mogilefs
    
#This plays hell with websetup, so only use where needed.
#from furaffinity.lib import filestore

