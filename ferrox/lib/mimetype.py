import os.path
import mimetypes

try:
    import magic
    def get_mime_type(fileobject):
        ms = magic.open(magic.MAGIC_MIME)
        ms.load()
        type = ms.buffer(fileobject['content'])
        ms.close()
        if ';' in type:
            return type.split(';')[0]
        return type
except ImportError:
    def get_mime_type(fileobject):
        return mimetypes.guess_type(fileobject['filename'])[0]

def mangle_filename(filename, mimetype):
    name, ext = os.path.splitext(filename)
    return name + mimetypes.guess_extension(mimetype)
    