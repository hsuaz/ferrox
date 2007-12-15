from furaffinity.lib.base import *
import sqlalchemy.exceptions
import os
import mimetypes

imagestore = os.getcwd() + '/furaffinity/public/data'
imageurl = '/data'

class ImageManagerException(Exception):
    pass

class ImageManagerExceptionFileExists(ImageManagerException):
    pass
    
class ImageManagerExceptionFileNotFound(ImageManagerException):
    pass
    
class ImageManagerExceptionAccessDenied(ImageManagerException):
    pass
    
class ImageManagerExceptionBadAction(ImageManagerException):
    pass
    

# This function will return the image_metadata of an image if it exists, checked by hash.
# It returns a non-saved, non-committed image_metadata if it's a new file.
# Else throw exception.
def store(hash,mimetype,data):
    # Please replace this function with something that doesn't suck.
    
    try:
        image_metadata = model.Session.query(model.ImageMetadata).filter(model.ImageMetadata.hash==hash).one()
    except sqlalchemy.exceptions.InvalidRequestError:
        folder = '/' + hash[0:3] + '/'  + hash[3:6] + '/'  + hash[6:9] + '/'  + hash[9:12]
        filename = hash + mimetypes.guess_extension(mimetype)
        if ( not os.access ( imagestore + folder, os.F_OK ) ):
            os.makedirs  ( imagestore + folder )
        if ( os.access ( imagestore + folder + '/' + filename, os.F_OK ) ):
            # File exists in store but no entry in image_metadata
            #raise ImageManagerExceptionFileExists
            pass
        f = open(imagestore + folder + '/' + filename,'wb')
        if (f):
            f.write(data)
            f.close()
            image_metadata = model.ImageMetadata(
                hash = hash,
                height = 0,
                width = 0,
                mimetype = mimetype,
                count = 0
            )
            return image_metadata
        else:
            raise ImageManagerExceptionAccessDenied
            
    else:
        # File already exists in filestore
        return image_metadata
            
def dump(hash):
    hash = hash.split('.')[0]
    try:
        image_metadata = model.Session.query(model.ImageMetadata).filter(model.ImageMetadata.hash==hash).one()
    except sqlalchemy.exceptions.InvalidRequestError:
        raise ImageManagerExceptionFileNotFound
    folder = '/' + hash[0:3] + '/'  + hash[3:6] + '/'  + hash[6:9] + '/'  + hash[9:12]
    filename = hash + mimetypes.guess_extension(image_metadata.mimetype)
    try:
        f = open ( imagestore + folder + '/' + filename, 'rb' )
    except IOError:
        raise ImageManagerExceptionFileNotFound
    else:
        d = f.read()
        f.close()
        return (d,image_metadata)

        
def get_submission_file(metadata):
    return metadata.hash+mimetypes.guess_extension(metadata.mimetype)

def delete(hash):
    hash = hash.split('.')[0]
    try:
        image_metadata = model.Session.query(model.ImageMetadata).filter(model.ImageMetadata.hash==hash).one()
    except sqlalchemy.exceptions.InvalidRequestError:
        raise ImageManagerExceptionFileNotFound
    image_metadata.disable()
    model.Session.commit()

def undelete(hash):
    hash = hash.split('.')[0]
    try:
        image_metadata = model.Session.query(model.ImageMetadata).filter(model.ImageMetadata.hash==hash).one()
    except sqlalchemy.exceptions.InvalidRequestError:
        raise ImageManagerExceptionFileNotFound
    image_metadata.enable()
    model.Session.commit()

def purge(hash):
    # this function is untested, bitches
    hash = hash.split('.')[0]
    try:
        image_metadata = model.Session.query(model.ImageMetadata).filter(model.ImageMetadata.hash==hash).one()
    except sqlalchemy.exceptions.InvalidRequestError:
        raise ImageManagerExceptionFileNotFound
    model.Session.delete(image_metadata)
    folder = '/' + hash[0:3] + '/'  + hash[3:6] + '/'  + hash[6:9] + '/'  + hash[9:12]
    filename = hash + mimetypes.guess_extension(image_metadata.mimetype)

    try:
        os.unlink ( imagestore + folder + '/' + filename, 'rb' )
    except:
        raise ImageManagerExceptionAccessDenied
