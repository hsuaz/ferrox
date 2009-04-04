import os.path, os, time

__all__ = ['FileStorage', 'get_instance']

def get_instance(url):
    backend, uri = url.split('://', 1)
    return backends[backend](url)

class Storage:
    def __init__(self, url):
        raise NotImplemented('Use get_interface(url) or instantiate your class directly.')

    def __setitem__(self, key, value):
        """ Returns used key name or raises appropriate exception. IOError, MemoryError, etc. """
        raise NotImplemented('add() is abstract')

    def __getitem__(self, key):
        """ Returns data or raises appropriate exception. KeyError, IOError, Memory"""
        raise NotImplemented('fetch() is abstract')

    def __delitem__(self, key):
        raise NotImplemented('delete() is abstract')

    def __contains__(self, key):
        try:
            self.fetch(key)
        except KeyError:
            return False
        return True

    def rename(self, key, new_key):
        new_key = self.add(new_key, self.fetch(key))
        self.delete(key)
        return new_key

    def mangle_key(self, key, count=5):
        """ Takes the given key, returns a (probably) non-existent key. """
        if count == 0: raise RuntimeError('Couldn\'t get a unique key.')
        old_key = key
        prefix = int(time.time() * 1000000.)
        if '/' in key:
            folder, file = key.rsplit('/', 1)
            key = "%s/%x.%s" % (folder, prefix, file)
        else:
            key = "%x.%s" % (prefix, key)
        if key in self: return self.mangle_key(old_key, count - 1)
        return key

    def unmangle_key(self, key):
        """ Reverses mangle_key.

        Don't use this on an unmangled key."""
        if '/' in key:
            folder, file = key.rsplit('/', 1)
            tossaway, file = key.split('.', 1)
            return "%s/%s" % (folder, file)
        else:
            tossaway, file = key.split('.', 1)
            return file


class FileStorage(Storage):
    def __init__(self, url):
        if not url.startswith('file://'):
            raise TypeError('Not a "file" url.')
        self.path = url[7:]
        if not os.path.isabs(self.path):
            self.path = os.path.abspath(self.path)

    def _folder_mangle(self, key):
        folder = key
        if '/' in key:
            folder, key = key.split('/', 1)
            if len(folder) >= 3:
                key = os.path.join(folder[0], folder[1], folder[2], folder, key)
            elif len(folder) == 2:
                key = os.path.join(folder[0], folder[1], folder, key)
            elif len(folder) == 1:
                key = os.path.join(folder[0], folder, key)
        return os.path.join(self.path, key)
        
    def __setitem__(self, key, value):
        filename = self._folder_mangle(key)
        pathname = os.path.dirname(filename)
        if not os.access(pathname, os.F_OK):
            os.makedirs(pathname)
        f = open(filename, 'w')
        f.write(value)
        f.close()
        
    def __getitem__(self, key):
        filename = self._folder_mangle(key)
        if key not in self: raise KeyError(key)
        f = open(filename, 'r')
        value = f.read()
        f.close()
        return value
        
    def __delitem__(self, key):
        filename = self._folder_mangle(key)
        if key not in self: raise KeyError(key)
        os.unlink(filename)
        
    def __contains__(self, key):
        filename = self._folder_mangle(key)
        return os.access(filename, os.F_OK)

    def rename(self, key, new_key):
        if key not in self: raise KeyError(key)
        old_filename = self._folder_mangle(key)
        new_filename = self._folder_mangle(new_key)
        if old_filename == new_filename: return True
        os.renames(old_filename, new_filename)
        return True

    def items_by_prefix(self, prefix):
        path = ''
        if '/' in prefix: 
            path, prefix = prefix.rsplit('/', 1)
            path += '/'

        files = []
        mangled_path = self._folder_mangle(path)
        # check root directory
        for name in os.listdir(mangled_path):
            if name.startswith(prefix):
                full_name = os.path.join(mangled_path, name)
                if os.path.isfile(full_name):
                    files.append(path + name)
                elif os.path.isdir(full_name):
                    files += self.items_by_prefix(path + name + '/')
        return files
    
        
class MogileStorage(Storage):
    def __init__(self, url):
        if not url.startswith('mogile://'):
            raise TypeError('Not a "mogile" url.')
        self.domain, self.trackers = url[9:].split('/', 1)
        self.trackers = self.trackers.split('/')
        self.client = mogilefs.Client(self.domain, self.trackers)
        
    def __setitem__(self, key, value):
        self.client.send_file(key, value)
        
    def __getitem__(self, key):
        return self.client[key]
        
    def __delitem__(self, key):
        self.client.delete(key)
        
    def __contains__(self, key):
        after, keys = self.client.list_keys(key)
        return key in keys
        
    def rename(self, key, new_key):
        self.client.rename(key, new_key)
        return True

    def items_by_prefix(self, prefix):
        after, keys = self.client.list_keys(key)
        return keys

backends = {'file': FileStorage}

try:
    import ferrox.lib.mogilefs as mogilefs
except ImportError:
    pass
else:
    __all__.append('MogileStorage')
    backends['mogile'] = MogileStorage

