from distutils.core import setup, Extension
import commands


raw_libs = commands.getoutput('Wand-config --libs').split(' ')
libs = []
libdirs = ['/usr/local/lib']
for k,lib in enumerate(raw_libs):
    if ( lib[0:2] == '-l' ):
        libs.append(lib[2:])
    elif ( lib[0:2] == '-L' ):
        libdirs.append(lib[2:])

imagemagick = Extension('imagemagick',
                    sources = ['imagemagick.c'],
                    include_dirs = ['/usr/local/include'],
                    library_dirs = libdirs,
                    libraries = libs)

setup (name = 'imagemagick',
       version = '1.0',
       description = 'ImageMagick procedures we need for this software.',
       long_description = 'ImageMagick procedures we need for this software.',
       ext_modules = [imagemagick],
       author = 'Douglas Webster',
       )
