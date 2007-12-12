import logging

from furaffinity.lib.base import *
from furaffinity.lib import filestore

from pylons.decorators.secure import *

import os
import md5
import mimetypes
import sqlalchemy.exceptions
import pprint
from PIL import Image
from PIL import ImageFile
from tempfile import TemporaryFile
from sqlalchemy import or_,and_

log = logging.getLogger(__name__)


thumbnail_maxsize = 120


class GalleryController(BaseController):

    def index(self, username=None, pageno=1):
        user_q = model.Session.query(model.User)
        try:
            page_owner = user_q.filter_by(username = username).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = "User %s not found." % h.escape_once(username)
            c.error_title = 'User not found'
            return render('/error.mako')

        
        c.page_owner_display_name = page_owner.display_name
            
        # I'm having to do WAY too much coding in templates, so...
        submission_q = model.Session.query(model.UserSubmission)
        submissions = submission_q.filter(model.UserSubmission.status != 'deleted').filter_by(user_id = page_owner.id).all()
        #[offset:offset+perpage]
        if submissions:
            c.submissions = []
            for item in submissions:
                if ( item.submission.derived_submission[0] ):
                    thumbnail = filestore.get_submission_file(item.submission.derived_submission[0].metadata)
                else:
                    thumbnail = None
                c.submissions.append ( dict (
                    id = item.submission.id,
                    title = item.submission.title,
                    date = item.submission.time,
                    description = item.submission.description_parsed,
                    thumbnail = thumbnail
                ))
        else:
            c.submissions = None
            c.page_owner = page_owner.display_name
            
        c.is_mine = (c.auth_user != None) and (page_owner.id == c.auth_user.id)
        #pp = pprint.PrettyPrinter(indent=4)
        #return "<pre>%s</pre>" % pp.pformat(c.submissions)
        return render('/gallery/index.mako')
        
    @check_perm('submit_art')
    def submit(self):
        c.submitoptions = h.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), 'image')
        c.edit = False
        c.prefill['title'] = ''
        c.prefill['description'] = ''
        return render('/gallery/submit.mako')

    @check_perms(['submit_art','administrate'])
    def edit(self,id=None):
        submission = self.get_submission(id)
        self.is_my_submission(submission,True)
        c.submitoptions = h.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), 'image')
        c.edit = True
        c.prefill['title'] = submission.title
        c.prefill['description'] = submission.description
        return render('/gallery/submit.mako')

    @check_perms(['submit_art','administrate'])
    def delete(self,id=None):
        submission = self.get_submission(id)
        self.is_my_submission(submission,True)
        c.text = "Are you sure you want to delete the submission titled \" %s \"?"%submission.title
        c.url = h.url(action="delete_commit",id=id)
        c.fields = {}
        return render('/confirm.mako')
    
    @check_perms(['submit_art','administrate'])
    def edit_commit(self, id=None):
        # -- validate form input --
        validator = model.form.SubmitForm();
        submission_data = None
        try:
            submission_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            pp = pprint.PrettyPrinter(indent=4)
            c.edit = True
            c.prefill = request.params
            c.submitoptions = h.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), request.params['type'])
            c.input_errors = "There were input errors: %s %s" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
            #return self.submit()
            
        # -- get image from database, make sure user has permission --
        submission = self.get_submission(id)
        self.is_my_submission(submission,True)
        
        # -- generate image data --
        fullfile = self.generate_image_data( submission_data['fullfile'], submission_data['type'] )

        # -- generate thumbnail, if needed --
        thumbnail = self.generate_thumbnail(submission_data['thumbfile'],submission_data['type'],fullfile)
        
        #submission = self.get_submission(id)
        #self.is_my_submission(submission,True)
        
        # -- store image in mogile or wherever --
        submission.metadata.count_dec()
        fullfile['metadata'] = filestore.store( fullfile['hash'], fullfile['mimetype'], submission_data['fullfile']['content'] )
        fullfile['metadata'].height = fullfile['height']
        fullfile['metadata'].width = fullfile['width']
                
        # -- store thumbnail in mogile or wherever --
        if ( submission.derived_submission[0] ):
            submission.derived_submission[0].metadata.count_dec()
        if ( thumbnail['exists'] ):
            thumbnail['metadata'] = filestore.store ( thumbnail['hash'], thumbnail['mimetype'], thumbnail['content'] )
            thumbnail['metadata'].height = thumbnail['height']
            thumbnail['metadata'].width = thumbnail['width']
            #model.Session.save(thumbnail['metadata'])
            
        # -- put submission in database --
        submission.title = submission_data['title']
        submission.description = submission_data['description']
        submission.description_parsed = submission_data['description'] # waiting for bbcode parser
        submission.type = submission_data['type']
        submission.status = 'normal'
        #model.Session.save(submission)
        fullfile['metadata'].count_inc()
        submission.metadata = fullfile['metadata']
        #model.Session.save(submission)

        #model.Session.save(submission)
        if ( thumbnail['exists'] ):
            thumbnail['metadata'].count_inc()
            if ( not submission.derived_submission[0] ):
                derived_submission = model.DerivedSubmission(derivetype = 'thumb')
                derived_submission.metadata = thumbnail['metadata']
                submission.derived_submission.append(derived_submission)
            else:
                submission.derived_submission.metadata = thumbnail['metadata']
        else:
            if ( submission.derived_submission[0] ):
                # this should never happen, but we'll handle it anyway
                submission.derived_submission.pop()
            #model.Session.save(submission)
        model.Session.commit()
        h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id))
        
        
    @check_perms(['submit_art','administrate'])
    def delete_commit(self, id=None):
        # -- validate form input --
        pp = pprint.PrettyPrinter(indent=4)
        validator = model.form.DeleteForm();
        delete_form_data = None
        try:
            delete_form_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            return "There were input errors: %s" % (error)
            #return self.delete(id)
        
        submission = self.get_submission(id)
        self.is_my_submission(submission,True)
        
        if (delete_form_data['confirm'] != None):
            # -- update submission in database --
            submission.status = 'deleted'
            submission.user_submission[0].status = 'deleted'
            #model.Session.save()
            model.Session.commit()
            h.redirect_to(h.url_for(controller='gallery', action='index', username = submission.user_submission[0].user.username, id=None))
        else:
            h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id))

    @check_perm('submit_art')
    def submit_upload(self):
        # -- validate form input --
        validator = model.form.SubmitForm();
        submission_data = None
        try:
            submission_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            pp = pprint.PrettyPrinter(indent=4)
            c.edit = False
            c.prefill = request.params
            c.submitoptions = h.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), request.params['type'])
            c.input_errors = "There were input errors: %s %s" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
            #return self.submit()
        
        
        # -- generate image data --
        fullfile = self.generate_image_data( submission_data['fullfile'], submission_data['type'] )
        
        # -- generate thumbnail, if needed --
        thumbnail = self.generate_thumbnail(submission_data['thumbfile'],submission_data['type'],fullfile)
        
        # -- store image in mogile or wherever --
        fullfile['metadata'] = filestore.store( fullfile['hash'], fullfile['mimetype'], submission_data['fullfile']['content'] )
        fullfile['metadata'].height = fullfile['height']
        fullfile['metadata'].width = fullfile['width']
                
        # -- store thumbnail in mogile or wherever --
        if ( thumbnail['exists'] ):
            thumbnail['metadata'] = filestore.store ( thumbnail['hash'], thumbnail['mimetype'], thumbnail['content'] )
            thumbnail['metadata'].height = thumbnail['height']
            thumbnail['metadata'].width = thumbnail['width']
            #model.Session.save(thumbnail['metadata'])
            

        # -- put submission in database --
        submission = model.Submission(
            title = submission_data['title'],
            description = submission_data['description'],
            description_parsed = submission_data['description'], # waiting for bbcode parser
            type = submission_data['type'],
            discussion_id = 0,
            status = 'normal'
        )
        model.Session.save(submission)
        fullfile['metadata'].count_inc()
        submission.metadata = fullfile['metadata']
        model.Session.save(submission)
        user_submission = model.UserSubmission(
            user_id = session['user_id'],
            relationship = 'artist',
            status = 'primary'
        )
        submission.user_submission.append(user_submission)
        model.Session.save(submission)
        if ( thumbnail['exists'] ):
            derived_submission = model.DerivedSubmission(derivetype = 'thumb')
            thumbnail['metadata'].count_inc()
            derived_submission.metadata = thumbnail['metadata']
            submission.derived_submission.append(derived_submission)
            model.Session.save(submission)
        model.Session.commit()
        h.redirect_to(h.url_for(controller='gallery', action='view', id = submission.id))
            
    def view(self,id=None):
        submission = self.get_submission(id)
        filename=filestore.get_submission_file(submission.metadata)
        if ( submission.derived_submission != None ):
            #tn_filename= "%s%s"%(submission.derived_submission[0].hash,mimetypes.guess_extension(submission.derived_submission[0].mimetype))
            tn_filename=filestore.get_submission_file(submission.derived_submission[0].metadata)
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
        c.misc = submission.derived_submission[0].metadata.mimetype
        return render('/gallery/view.mako');
        
    def file(self,filename=None):
        filename = os.path.basename(filename)
        try:
            filedata = filestore.dump(filename)
        except filestore.ImageManagerExceptionFileNotFound:
            c.error_text = 'Requested file was not found.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        response.headers['Content-Type'] = filedata[1].mimetype
        response.headers['Content-Length'] = len(filedata[0])
        return filedata[0]
        
    def hash(self,s):
        m = md5.new()
        m.update(s)
        return m.hexdigest()
        
    def get_submission(self,id):
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
            
        return submission

    def is_my_submission(self,submission,abort=False):
        if ( not c.auth_user or (not c.auth_user.can('administrate') and (c.auth_user.id != journal_entry.user_id)) ):
            if (abort):
                c.error_text = 'You cannot edit this submission.'
                c.error_title = 'Forbidden'
                abort ( 403 )
            else:
                return False
        return True

    def generate_image_data(self,fullfile_form_data,submission_type):
        fullfile = {}
        fullfile['hash'] = self.hash(fullfile_form_data['content'])
        if ( submission_type == 'image' ):
            parser_fullfile = ImageFile.Parser()
            parser_fullfile.feed(fullfile_form_data['content'])
            
            fullfile['image'] = parser_fullfile.close()
            fullfile['mimetype'] = mimetypes.guess_type("a.%s" % fullfile['image'].format)[0]

            fullfile['width'] = fullfile['image'].size[0]
            fullfile['height'] = fullfile['image'].size[1]
        else:
            fullfile['width'] = 0
            fullfile['height'] = 0
            fullfile['mimetype'] = mimetypes.guess_type(fullfile_form_data['filename'])[0]
            
        fullfile['ext'] = mimetypes.guess_extension(fullfile['mimetype'])
        
        return fullfile

    def generate_thumbnail(self, thumbfile_form_data,submission_type,fullfile):
        thumbnail = {}
        thumbnail['exists'] = True
        if ( thumbfile_form_data != None ):
            # -- thumbnail submitted --
            parser_thumbnail = ImageFile.Parser()
            parser_thumbnail.feed(thumbfile_form_data['content'])
            thumbnail['image'] = parser_thumbnail.close()
            
            if ( thumbnail['image'].size[0] > thumbnail_maxsize or thumbnail['image'].size[1] > thumbnail_maxsize ):
                # -- submitted thumbnail is too big --
                (thumbnail['content'],thumbnail['width'],thumbnail['height']) = self.thumbnail_from_image ( thumbnail['image'], thumbnail_maxsize )
            else:
                thumbnail['content'] = thumbfile_form_data['content']
                thumbnail['width'] = thumbnail['image'].size[0]
                thumbnail['height'] = thumbnail['image'].size[1]
            thumbnail['mimetype'] = mimetypes.guess_type("a.%s" % thumbnail['image'].format)[0]
        else:
            # -- thumbnail not submitted --
            if ( submission_type == 'image' ):
                # -- generate thumbnail from fullfile --
                (thumbnail['content'],thumbnail['width'],thumbnail['height']) = self.thumbnail_from_image ( fullfile['image'], thumbnail_maxsize )
                thumbnail['image'] = None
                thumbnail['mimetype'] = fullfile['mimetype']
            else:
                # -- non-image, uses default thumbnail --
                thumbnail['exists'] = False
        
        if ( thumbnail['exists'] ):
            thumbnail['ext'] = mimetypes.guess_extension(thumbnail['mimetype'])
            thumbnail['hash'] = self.hash(thumbnail['content'])
        
        return thumbnail

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
    
