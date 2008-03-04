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

