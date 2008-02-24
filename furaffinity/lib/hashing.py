import os

try:
    import hashlib
    hash_library = 'HASHLIB'
    hash_algorithm = 'SHA256'
    hash_secure = True
except:
    import sha
    hash_library = 'SHA'
    hash_algorithm = 'SHA1'
    hash_secure = False


class NoUsableHashFunction(Exception):
    pass

class FerroxHash:
    def __init__(self):
        self.new()

    def new(self):
        if hash_library == 'HASHLIB':
            self.hash = hashlib.new('SHA256')
        elif hash_library == 'SHA':
            self.hash = sha.new()
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

def hash_string(s):
    h = FerroxHash()
