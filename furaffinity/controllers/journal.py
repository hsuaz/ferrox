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
    

class JournalController(BaseController):

    def index(self):
        c.error_text = 'Doesn\'t work yet.'
        c.error_title = 'WUT'
        return render('/error.mako')
        
    @check_perm('post_journal')
    def post(self):
        c.submitoptions = self.dict_to_option(dict(image="Image", video="Flash", audio="Music", text="Story"), 'image')
        c.prefill['title'] = ''
        c.prefill['content'] = ''
        return render('/journal/post.mako')

    @check_perm('post_journal')
    def post_commit(self):
        # -- validate form input --
        validator = model.form.JournalForm();
        journal_data = None
        try:
            journal_data = validator.to_python(request.params);
        except model.form.formencode.Invalid, error:
            pp = pprint.PrettyPrinter(indent=4)
            c.prefill = request.params
            c.input_errors = "There were input errors: %s<br><pre>%s</pre>" % (error, pp.pformat(c.prefill))
            return render('/gallery/submit.mako')
            #return self.submit()
        
        # -- put journal in database --
        journal_entry = model.JournalEntry(
            user_id = c.auth_user.id,
            title = journal_data['title'],
            content = journal_data['content']
        )
        model.Session.save(journal_entry)
        model.Session.commit()
        h.redirect_to(h.url_for(controller='journal', action='view', id = journal_entry.id))
            
    def view(self,id=None):
        try:
            id = int(id)
        except ValueError:
            c.error_text = 'Journal Entry ID must be a number.'
            c.error_title = 'Not Found'
            abort ( 404 )
            
        submission = None
        try:
            journal_entry = model.Session.query(model.JournalEntry).filter(model.JournalEntry.id==id).one()
        except sqlalchemy.exceptions.InvalidRequestError:
            c.error_text = 'Requested journal entry was not found.'
            c.error_title = 'Not Found'
            abort ( 404 )

        c.journal_entry_title = journal_entry.title
        c.journal_entry_content = journal_entry.content
        c.journal_entry_author = journal_entry.user.display_name
        c.journal_entry_time = journal_entry.time
        
        pp = pprint.PrettyPrinter (indent=4)
        return render('/journal/view.mako');
        
    def dict_to_option (self,opts=(),default=None):
        output = ''
        for k in opts.keys():
            if (opts[k] == ''):
                v = k
            else:
                v = opts[k]
            if (default == k):
                selected = ' selected="selected"'
            else:
                selected = ''
            output = "%s\n<option value=\"%s\"%s>%s</option>" % (output, k, selected, v)
        return output
    
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
            
