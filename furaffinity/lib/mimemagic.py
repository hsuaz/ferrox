# This uses a stupid, extension-based guessing of mimetypes.
# This will need to be changed before we go release.

# fileobject must be a dict with ['filename'] and ['content']
# returns the mimetype of the fileobject

import mimetypes

def get_mime_type ( fileobject ):
    return mimetypes.guess_type(fileobject['filename'])[0]
