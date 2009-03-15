# This is my image library. It behaves as follows:
# declare an object using the with statement. (This is not strictly necessary if you're using the C library, but the failover 
# code relies on it for temp file cleanup. Python 2.5 ONLY. Also, the failover code should NOT be used in production. Ever.)
#
#   with ImageClass() as i:
#
# Feed the contents of an image file into the class.
#
#       i.set_data(submission_data['content'])
#
# You can also do this directly in the constructor.
#
#       with ImageClass(submission_data['content']) as i:
#
# You can generate a new image with a different size with the get_resized() method.
#
# size can be an integer or any data type that can be tuple()'d. [0] corresponds to width and [1] corresponds to height.
# If size is an integer, it is assumed to mean that the width and height are the same.
# If sizeup  is True, an image with dimensions smaller than size will be increased in size.
# If sizedown  is True, an image with dimensions larger than size will be decreased in size. (default)
# If an image is generated, A new ImageClass will be returned.
# If no image is generated, None will be returned
#
#       t.get_resized(120) # generates a thumbnail of size 120 if submission_data['content'] contained an image larger than that.
#
#

from __future__ import with_statement
import os
from tempfile import *

#try:
#    import imagemagick
#    use_c_lib = True
#except ImportError:
use_c_lib = False
#    print 'Warning: Build the module in contrib to get better performance.'

class ImageClass:
    def __enter__(self):
        return self

    def __init__(self, file_stream = None):
        self.temporary_files = []
        self.original = None
        self.height = 0
        self.width = 0
        
        if file_stream:
            self.set_data(file_stream)

    def set_data(self,file_stream):
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

            imagedata = os.popen("identify -format \"%%m %%w %%h \" %s"%temporary_file[1])
            information = imagedata.read().split(' ')
            imagedata.close()
            self.width = int(information[1])
            self.height = int(information[2])

    def get_resized(self, size, sizedown = True, sizeup = False):
        do_generate = False
        
        # (width, height)
        if type(size) == type(int()) or type(size) == type(float()):
            size = (size, size)
        
        size = tuple([float(x) for x in size])
        
        if sizeup and (self.height < size[1]) and (self.width < size[0]):
            do_generate = True
        elif sizedown and ((self.height > size[1]) or (self.width > size[0])):
            do_generate = True

        if do_generate:
            if use_c_lib:
                old_aspect = float(self.width) / float(self.height)
                new_aspect = size[0] / size[1]
                
                if old_aspect < new_aspect:
                    width = int(size[0] * old_aspect / new_aspect)
                    height = int(size[1])
                else:
                    width = int(size[0])
                    height = int(size[1] * new_aspect / old_aspect)
                
                return ImageClass(imagemagick.resize(self.original, width, height))

            else:
                temporary_file = mkstemp()
                os.close(temporary_file[0])
                self.temporary_files.append(temporary_file)

                os.system("convert %s -resize %dx%d %s"%(self.original[1],size[0],size[1],temporary_file[1]))

                f = open(temporary_file[1],'rb')
                data = f.read()
                f.close()
                
                return ImageClass(data)

    def get_metadata (self):
        if use_c_lib:
            return imagemagick.get_metadata(self.original)
        else:
            return {}

    def get_data (self):
        if use_c_lib:
            return self.original
        else:
            f = open(self.original[1],'rb')
            data = f.read()
            f.close()
            return data
        
    
    def __exit__(self, type, value, tb):
        if tb == None:
            for temporary_file in self.temporary_files:
                if os.path.exists(temporary_file[1]):
                    os.unlink(temporary_file[1])


if __name__ == '__main__':
    import os.path
    with ImageClass() as i:
        filename = raw_input('Input filename: ')
        filename = (filename[1:-1] if filename[0] == '"' else filename)
        
        size = raw_input('Size (w,h or int): ')
        if ',' in size:
            size = tuple([int(x) for x in size.split(',')])
        else:
            size = int(size)
            size = (size, size)
        f = open(filename,'rb')
        i.set_data(f.read())
        i_new = i.get_resized(size)
        f.close()
        filename_new = os.path.splitext(filename)
        filename_new = filename_new[0] + '.out' + filename_new[1]
        f = open(filename_new, 'wb')
        f.write(i_new.get_data())
        f.close()
        print "Entered Dims: %d %d" % (size[0], size[1])
        print "Old Dims: %d %d (%f)" % (i.width, i.height, float(i.width)/float(i.height))
        print "New Dims: %d %d (%f)" % (i_new.width, i_new.height, float(i_new.width)/float(i_new.height))
        
