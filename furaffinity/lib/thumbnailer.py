# This is my thumbnailer library. It behaves as follows:
# declare an object using the with statement.
#
#   with Thumbnailer() as t:
#
# Feed the contents of an image file and its mimetype into the parser.
#
#       t.parse(submission_data['content'],submission_data['mimetype'])
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
# This version of this class works by piping the appropriate ImageMagick commands.

from __future__ import with_statement
import os
from tempfile import *

try:
    import imagemagick
    use_c_lib = True
except ImportError:
    use_c_lib = False
    print 'Warning: Build the module in contrib to get better performance.'

class Thumbnailer:
    def __enter__(self):
        return self

    def __init__(self):
        self.temporary_files = []
        self.original = None
        #self.type = None
        self.height = 0
        self.width = 0

    def parse(self,file_stream,mimetype):
        if use_c_lib:
            self.original = file_stream
            (self.width, self.height) = imagemagick.get_size(file_stream)
        else:
            temporary_file = mkstemp()
            os.close(temporary_file[0])
            self.temporary_files.append(temporary_file)

            f = open(temporary_file[1],'r+b')
            f.seek(0)
            f.write(file_stream)
            f.close()

            self.original = temporary_file

            #print("idenitify -format \"%%m %%w %%h\" %s"%temporary_file[1])
            imagedata = os.popen("identify -format \"%%m %%w %%h \" %s"%temporary_file[1])
            information = imagedata.read().split(' ')
            imagedata.close()
            #self.type = information[0]
            self.width = int(information[1])
            self.height = int(information[2])

    def generate(self, linear_dimension, sizedown = True, sizeup = False):
        do_generate = False
        if ( sizeup and (self.height < linear_dimension) and (self.width < linear_dimension) ):
            do_generate = True
        elif ( sizedown and ((self.height > linear_dimension) or (self.width > linear_dimension)) ):
            do_generate = True

        if ( do_generate ):
            if ( use_c_lib ):
                aspect = float(self.width) / float(self.height)
                print "%d %d %f"%(self.width,self.height,aspect)
                if (aspect > 1.0):
                    #wide
                    width = int(linear_dimension)
                    height = int(linear_dimension / aspect)
                else:
                    #tall
                    width = int(linear_dimension * aspect)
                    height  = int(linear_dimension)

                return dict (
                    content = imagemagick.resize(self.original, width, height),
                    width = width,
                    height = height
                )

            else:
                temporary_file = mkstemp()
                os.close(temporary_file[0])
                self.temporary_files.append(temporary_file)

                os.system("convert %s -resize %dx%d %s"%(self.original[1],linear_dimension,linear_dimension,temporary_file[1]))
                imagedata = os.popen("identify -format \"%%m %%w %%h \" %s"%temporary_file[1])
                information = imagedata.read().split(' ')
                imagedata.close()
                width = int(information[1])
                height = int(information[2])

                f = open(temporary_file[1],'rb')
                data = f.read()
                f.close()
                return dict (
                    content = data,
                    width = int(information[1]),
                    height = int(information[2])
                )

    def get_metadata (self):
        if use_c_lib:
            return imagemagick.get_metadata(self.original)
        else:
            return {}

    def __exit__(self, type, value, tb):
        if ( tb == None ):
            for temporary_file in self.temporary_files:
                if ( os.path.exists(temporary_file[1]) ):
                    os.unlink(temporary_file[1])


