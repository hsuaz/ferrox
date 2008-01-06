# This uses a stupid, extension-based guessing of mimetypes.
# This will need to be changed before we go release.

# fileobject must be a dict with ['filename'] and ['content']
# returns the mimetype of the fileobject

import mimetypes

def mpeg_audio_detector(content):
    offset = 0
    # ID3v2 detector
    if ( content[0:3] == 'ID3' ):
        offset = ((ord(content[6]) << 21) \
            | (ord(content[7]) << 14) \
            | (ord(content[8]) << 7) \
            | ord(content[9])) + 10

    # ID3v1 is at the end of the file. We don't care about it.
            
    # detect mpeg sync
    for i in xrange(offset,offset+2048):
        if ( len(content) < i+4 ):
            return (-2,-2)
        else:
            mpeg_head = (ord(content[i+0]) << 24) \
                | (ord(content[i+1]) << 16) \
                | (ord(content[i+2]) << 8) \
                | ord(content[i+3])

            if ( (mpeg_head&0xffe00000) == 0xffe00000 ):
                mpeg_version = (mpeg_head&0x00180000) >> 19
                if (mpeg_version == 0):
                    mpeg_version = 2.5
                elif (mpeg_version == 1):
                    mpeg_version = -1
                elif (mpeg_version == 2):
                    mpeg_version = 2
                else:
                    mpeg_version = 1
                    
                mpeg_layer = (mpeg_head&0x00060000) >> 17
                if (mpeg_layer == 0):
                    mpeg_layer = -1
                else:
                    mpeg_layer = 4 - mpeg_layer
                    
                #mpeg_crc = (mpeg_head&0x00010000) >> 16
                #if (mpeg_crc == 1):
                #    mpeg_crc = False
                #else:
                #    mpeg_crc = True
                return (mpeg_version,mpeg_layer)
        
    return (-2,-2)

def get_mime_type ( fileobject ):
    if ( fileobject['content'][0:2] == "\xff\xd8" ):
        return 'image/jpeg'
    elif ( fileobject['content'][0:4] == "\x89PNG" ):
        return 'image/png'
    elif ( fileobject['content'][0:3] == "GIF" ):
        return 'image/gif'
    elif ( fileobject['content'][0:3] == "FWS" ):
        return 'application/x-shockwave-flash'
    elif ( mpeg_audio_detector(fileobject['content']) > (0,0) ):
        return 'audio/mpeg'
    elif ( fileobject['content'][0:5] == r'{\rtf' ):
        return 'text/richtext'
    elif ( fileobject['content'][0:2] == 'PK' ):
        # Note that this covers DOCX and ODF, as well as ZIP files.
        # We'll have to deal with that at some point.
        return 'application/zip'
    else:
        return 'text/plain'
        #return mimetypes.guess_type(fileobject['filename'])[0]


#Word/Office        
#0       string          \376\067\0\043                  application/msword
#0       string          \320\317\021\340\241\261        application/msword
#0       string          \333\245-\0\0\0                 application/msword
