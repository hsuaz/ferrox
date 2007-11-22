import os

try:
    import mhash
    hash_library = 'MHASH'
except:
    try:
        import hashlib
        hash_library = 'HASHLIB'
    except:
        import sha
        hash_library = 'SHA'

        
class NoUsableHashFunction(Exception):
    pass

class FerroxHash:
    def __init__(self):
        if ( hash_library == 'MHASH' ):
            self.hash = mhash.MHASH(mhash.MHASH_WHIRLPOOL)
            self.algorithm = 'WHIRLPOOL'
        elif ( hash_library == 'HASHLIB' ):
            self.hash = hashlib.new('sha512')
            self.algorithm = 'SHA512'
        elif ( hash_library == 'SHA' ):
            self.hash = sha.new()
            self.algorithm = 'SHA1'
        else:
            raise NoUsableHashFunction
        self.digest_size = self.hash.digest_size

    def update(self,s):
        self.hash.update(s)
    
    def digest(self):
        return self.hash.digest()
    
    def hexdigest(self):
        return self.hash.hexdigest()
    
    def copy(self):
        return self.hash.copy()


def make_salt(bytes=5):
    return os.urandom(bytes)
