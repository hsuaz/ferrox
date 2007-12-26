# This is my thumbnailer library. It behaves as follows:
# declare an object using the with statement.
#
#   with Thumbnailer() as t:
#
# Feed the contents of an image file into the parser.
#
#       t.parse(submission_data['content'])
#
# Generate a thumbnail with the generate() method.
# linear_dimension is the target width or height.
# Of sizeup  is True, an image with dimensions smaller than linear_dimension will be increased in size.
# If sizedown  is True, an image with dimensions larger than linear_dimension will be decreased in size.
# If an image is generated, the contents of the image file will be returned. (It will be the same filetype as the parsed file.)
# If no image is generated, None will be returned
#
#       t.generate(120) # generates a thumbnail of size 120 if submission_data['content'] contained an image larger than that.
#
#
# This version is based on PIL. It uses ImageMagick's 'mogrify' to deinterlace PNG files.
# It still has bugs and is not well tested. Don't use it.

from __future__ import with_statement
import os
from tempfile import *
from PILworkaround import ImageFromString
from PIL import Image
import StringIO 

class Thumbnailer:
    def __enter__(self):
        return self
    
    def __init__(self):
        self.temporary_files = []
        self.original = None;
        self.type = None;
        self.height = 0;
        self.width = 0;
        self.image = None
        
    def parse(self,file_stream):
        #temporary_file = mkstemp()
        #os.close(temporary_file[0])
        #self.temporary_files.append(temporary_file)

        #self.original = temporary_file
        with ImageFromString() as pill:
            self.image = pill.parse(file_stream)
        self.type = self.image.format
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        
    def generate(self, linear_dimension, sizedown = True, sizeup = False):
        do_generate = False
        if ( sizeup and (self.height < linear_dimension) and (self.width < linear_dimension) ):
            do_generate = True
        elif ( sizedown and ((self.height > linear_dimension) or (self.width > linear_dimension)) ):
            do_generate = True
            
        if ( do_generate ):
            aspect = float(self.image.size[0]) / float(self.image.size[1])
            if (aspect > 1.0):
                #wide
                width = int(linear_dimension)
                height = int(linear_dimension / aspect)
            else:
                #tall
                width = int(linear_dimension * aspect)
                height  = int(linear_dimension)
            i = self.image.resize((width, height), Image.ANTIALIAS)
            stringbuff = StringIO.StringIO()
            i.save(stringbuff, self.type)
            data = stringbuff.getvalue()
            stringbuff.close()
            return dict (
                content = data,
                width = i.size[0],
                height = i.size[1]
            )
        
    def __exit__(self, type, value, tb):
        # This still causes locking errors with certain filetypes.
        # I can't figure out how to make PIL close a file...
        #if ( tb == None ):
        #    for temporary_file in self.temporary_files:
        #        if ( os.path.exists(temporary_file[1]) ):
        #            os.unlink(temporary_file[1])
        pass;    

