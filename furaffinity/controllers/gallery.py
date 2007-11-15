import logging

from furaffinity.lib.base import *

from pylons.decorators.secure import *

import os
import md5
import mimetypes
import sqlalchemy.exceptions
import pprint
from PIL import Image
from PIL import ImageFile
import StringIO
from tempfile import TemporaryFile

log = logging.getLogger(__name__)

imagestore = os.getcwd() + '/furaffinity/public/data'
imageurl = '/data'

thumbnail_maxsize = 120

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
    

class GalleryController(BaseController):

    def index(self):
        c.error_text = 'Doesn\'t work yet.'
        c.error_title = 'WUT'
        return render('/error.mako')
        
    @check_perm('submit_art')
    def submit(self):
        c.submitoptions = h.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), 'image')
        c.prefill['title'] = ''
        c.prefill['description'] = ''
        return render('/gallery/submit.mako')

    @check_perm('submit_art')
    def submit_upload(self):
        # -- validate form input --
        validator = model.form.SubmitForm();
        submission_data = None
        try:
            submission_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            pp = pprint.PrettyPrinter(indent=4)
            c.prefill = request.params
            c.submitoptions = h.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), request.params['type'])
            c.input_errors = "There were input errors: %s %s" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
            #return self.submit()
        
        # -- generate image data --
        fullfile_hash = self.hash(submission_data['fullfile']['content'])
        if ( submission_data['type'] == 'image' ):
            parser_fullfile = ImageFile.Parser()
            parser_fullfile.feed(submission_data['fullfile']['content'])
            
            fullfile_image = parser_fullfile.close()
            fullfile_mimetype = mimetypes.guess_type("a.%s" % fullfile_image.format)[0]

            fullfile_width = fullfile_image.size[0]
            fullfile_height = fullfile_image.size[1]
        else:
            fullfile_width = 0
            fullfile_height = 0
            fullfile_mimetype = mimetypes.guess_type(submission_data['fullfile']['filename'])[0]
            
        fullfile_ext = mimetypes.guess_extension(fullfile_mimetype)
        
        # -- generate thumbnail, if needed --
        thumbnail_exists = True
        if ( submission_data['thumbfile'] != None ):
            # -- thumbnail submitted --
            parser_thumbnail = ImageFile.Parser()
            parser_thumbnail.feed(submission_data['thumbfile']['content'])
            thumbnail_image = parser_thumbnail.close()
            
            if ( thumbnail_image.size[0] > thumbnail_maxsize or thumbnail_image.size[1] > thumbnail_maxsize ):
                # -- submitted thumbnail is too big --
                (thumbnail_content,thumbnail_width,thumbnail_height) = self.thumbnail_from_image ( thumbnail_image, thumbnail_maxsize )
            else:
                thumbnail_content = submission_data['thumbfile']['content']
                thumbnail_width = thumbnail_image.size[0]
                thumbnail_height = thumbnail_image.size[1]
            thumbnail_mimetype = mimetypes.guess_type("a.%s" % thumbnail_image.format)[0]
        else:
            # -- thumbnail not submitted --
            if ( submission_data['type'] == 'image' ):
                # -- generate thumbnail from fullfile --
                (thumbnail_content,thumbnail_width,thumbnail_height) = self.thumbnail_from_image ( fullfile_image, thumbnail_maxsize )
                thumbnail_image = None
                thumbnail_mimetype = fullfile_mimetype
            else:
                # -- non-image, uses default thumbnail --
                thumbnail_exists = False
        
        if ( thumbnail_exists ):
            thumbnail_ext = mimetypes.guess_extension(thumbnail_mimetype)
            thumbnail_hash = self.hash(thumbnail_content)
        
        # -- store image in mogile or wherever --
        try:
            self.image_manager ( 'store', fullfile_hash + fullfile_ext , submission_data['fullfile']['content'] )
        except ImageManagerExceptionFileExists:
            try:
                submission = model.Session.query(model.Submission).filter(model.Submission.hash==fullfile_hash).one()
            except sqlalchemy.exceptions.InvalidRequestError:
                # This should never ever happen.
                #c.error_text = 'Requested submission was not found. (SQL/Mogile Sync Issue)'
                #c.error_title = 'Not Found'
                #abort ( 404 )
                pass;
            else:
                h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id))
                return None
                
        # -- store thumbnail in mogile or wherever --
        if ( thumbnail_exists ):
            try:
                self.image_manager ( 'store', thumbnail_hash + thumbnail_ext , thumbnail_content )
            except ImageManagerExceptionFileExists:
                pass
            except ImageManagerExceptionAccessDenied:
                c.error_text = 'Unable to open file for writing.'
                c.error_title = 'Filesystem Error'
                abort ( 500 )

        # -- put submission in database --
        submission = model.Submission(
            hash = fullfile_hash,
            title = submission_data['title'],
            description = submission_data['description'],
            description_parsed = submission_data['description'], # waiting for bbcode parser
            height = fullfile_height,
            width = fullfile_width,
            type = submission_data['type'],
            mimetype = fullfile_mimetype,
            discussion_id = 0,
            status = 'normal'
        )
        model.Session.save(submission)
        user_submission = model.UserSubmission(
            user_id = session['user_id'],
            relationship = 'artist',
            status = 'primary'
        )
        submission.user_submission.append(user_submission)
        model.Session.save(submission)
        if ( thumbnail_exists ):
            derived_submission = model.DerivedSubmission(
                hash = thumbnail_hash,
                height = thumbnail_height,
                width = thumbnail_width,
                mimetype = thumbnail_mimetype,
                derivetype = 'thumb'
            )
            submission.derived_submission.append(derived_submission)
            model.Session.save(submission)
        model.Session.commit()
        h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id))
            
    def view(self,id=None):
        try:
            id = int(id)
        except ValueError:
            c.error_text = 'Submission ID must be a number.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        submission = None
        try:
            submission = model.Session.query(model.Submission).filter(model.Submission.id==id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = 'Requested submission was not found.'
            c.error_title = 'Not Found'
            abort ( 404 )
        filename=submission.hash+mimetypes.guess_extension(submission.mimetype)
        if ( submission.derived_submission != None ):
            tn_filename= "%s%s"%(submission.derived_submission[0].hash,mimetypes.guess_extension(submission.derived_submission[0].mimetype))
            c.submission_thumbnail = h.url_for(controller='gallery', action='file', filename=tn_filename, id=None)
        else:
            #c.submission_thumbnail = h.url_for(controller='gallery', action='file', filename=tn_filename, id=None)
            # supply default thumbnail for type here
            c.submission_thumbnail = ''
        c.submission_file = h.url_for(controller='gallery', action='file', filename=filename, id=None)
        c.submission_title = submission.title
        c.submission_description = submission.description_parsed
        c.submission_artist = submission.user_submission[0].user.display_name
        c.submission_time = submission.time
        c.submission_type = submission.type
        
        pp = pprint.PrettyPrinter (indent=4)
        c.misc = submission.derived_submission[0].mimetype
        return render('/gallery/view.mako');
        
    def file(self,filename=None):
        filename = os.path.basename(filename)
        try:
            filedata = self.image_manager('dump',filename)
        except ImageManagerExceptionFileNotFound:
            c.error_text = 'Requested file was not found.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        response.headers['Content-Type'] = mimetypes.guess_type(filename)
        response.headers['Content-Length'] = len(filedata)
        return filedata
        
    def thumbnail_from_image (self,image,max_size,file_type=None):
        aspect = float(image.size[0]) / float(image.size[1])
        if (aspect > 1.0):
            #wide
            width = int(max_size)
            height = int(max_size / aspect)
        else:
            #tall
            width = int(max_size * aspect)
            height  = int(max_size)
        
        if ( file_type == None ):
            file_type = image.format
        
        new_image = image.resize(( width, height ), Image.ANTIALIAS)
        buffer = TemporaryFile()
        new_image.save(buffer, file_type)
        buffer.seek(0)
        content = buffer.read()
        buffer.close()
        #new_image.close()
        return (content,width,height)
    
    def hash(self,s):
        m = md5.new()
        m.update(s)
        return m.hexdigest()
        
    def image_manager(self,action,hash,data=''):
        # Please replace this function with something that doesn't suck.
        folder = '/' + hash[0:3] + '/'  + hash[3:6] + '/'  + hash[6:9] + '/'  + hash[9:12]
        filename = hash
        if (action=='store'):
            if ( not os.access ( imagestore + folder, os.F_OK ) ):
                os.makedirs  ( imagestore + folder )
            if ( os.access ( imagestore + folder + '/' + filename, os.F_OK ) ):
                raise ImageManagerExceptionFileExists
            f = open(imagestore + folder + '/' + filename,'wb')
            if (f):
                f.write(data)
                f.close()
                return True
            else:
                raise ImageManagerExceptionAccessDenied
        elif (action=='dump'):
            try:
                f = open ( imagestore + folder + '/' + filename, 'rb' )
            except IOError:
                raise ImageManagerExceptionFileNotFound
            else:
                c = f.read()
                f.close()
                return c
        elif (action=='delete'):
            return None;
        else:
            raise ImageManagerExceptionBadAction
            
