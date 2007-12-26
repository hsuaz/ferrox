from __future__ import with_statement
import os
from tempfile import *
from PIL import Image

# To use this incredible hack:
#with ImageFromString() as ifs:
#    i= ifs.parse(get_file_stream())
#do image stuff here
#i.show()

class ImageFromString:
    def __enter__(self):
        return self
    
    def __init__(self):
        self.temporary_files = []
        
    def parse(self,file_stream):
        temporary_file = mkstemp()
        os.close(temporary_file[0])
        self.temporary_files.append(temporary_file)

        f = open(temporary_file[1],'r+b')
        f.seek(0)
        f.write(file_stream)
        f.close()

        try:
            i = Image.open(temporary_file[1])
            i.load()
        except IOError, (err):
            if ( str(err) == 'cannot read interlaced PNG files' ):
                os.system ( "mogrify -interlace none %s" % temporary_file[1] )
                i = Image.open(temporary_file[1])
                i.load()
        
        return i


    def __exit__(self, type, value, tb):
        if ( tb == None ):
            for temporary_file in self.temporary_files:
                if ( os.path.exists(temporary_file[1]) ):
                    os.unlink(temporary_file[1])
            
