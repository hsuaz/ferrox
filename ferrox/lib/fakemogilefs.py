'''
This class is so you can use mogilefs functions without acutally having to set up mogilefs.

FOR TESTING PURPOSES ONLY. NOT FOR USE IN PRODUCTION.

If you need another mogilefs class or method implemented, do it yourself.
'''

import sys
import os.path
import os

class Client:
    
    def __init__(self, domain, trackers,clas=None, root=None, verify_data=False, verify_repcount=False):
        self.domain = domain
        pass;
        
    def reload(self):
        # Do nothing.
        pass
        
    def set_pref_ip(self, pref_ip):
        # Do nothing.
        pass
        
    def replication_wait(self, key, mindevcount, seconds):
        # Do nothing.
        pass
        
    def send_bigfile(self, key, source, clas=None, description="", overwrite=True, chunksize=1024*1024*16):
        # Same as send_file for our purposes...
        return self.send_file(key, source, clas)
        
    def send_file(self, key, source, clas=None, blocksize=1024*1024):
        if not os.access(self.domain, os.F_OK):
            os.makedirs(self.domain)
        
        opened = False
        if not hasattr(source, 'read'):
            source = open(source,'rb')
            opened = True
        
        dest = open(os.path.join(self.domain, key), 'wb')
        source.seek(0)
        dest.write(source.read())
        
        if opened:
            source.close()
            
        dest.close()
        
        return True
    
    def new_file(self, key, clas=None, bytes=0):
        if not os.access(self.domain, os.F_OK):
            os.makedirs(self.domain)
        return open(os.path.join(self.domain, key), 'wb')
        
    def cat(self, key,fp=sys.stdout, big=False):
        f = open(os.path.join(self.domain, key), 'rb')
        data = f.read()
        fp.write(data)
        f.close()
        return data
        
    def get_bigfile_as_lines(self, key):
        f = open(os.path.join(self.domain, key), 'rb')
        lines = []
        for line in f:
            lines.append(line)
        f.close()
        return lines
    
    def get_bigfile_as_file(self, key):
        return open(os.path.join(self.domain, key), 'rb')
        
    def get_file_data(self, key, fp=None, timeout=5):
        f = open(os.path.join(self.domain, key), 'rb')
        data = f.read()
        f.close()
        if fp:
            fp.write(data)
        return data
        
    def set_file_data(self, key, data, clas=None):
        f = open(os.path.join(self.domain, key), 'wb')
        f.write(data)
        f.close()
        return True
        
    def delete(self, key):
        os.unlink(os.path.join(self.domain, key))
        return True
        
    def sleep(self, seconds):
        # Do nothing
        pass
        
    def rename(self, fkey, tkey):
        os.rename(os.path.join(self.domain, fkey), os.path.join(self.domain, tkey))
        return True
    
    def list_keys(self, prefix, after=None, limit=None):
        keys = os.listdir(self.domain)
        match_keys = []
        
        for key in keys:
            if key[0:len(prefix)] == prefix:
                match_keys.append(key)
        
        start = 0
        if after:
            start = match_keys.index(after)
        if not limit:
            limit = 1000
                
        return (match_keys[start+limit:1], match_keys[start:limit])
