#!/usr/bin/env python
"""
$Id: mogilefs.py 4014 2007-09-05 16:05:22Z justin $

client module for MogileFS

 Copyright 2005 Justin Azoff

 License:
    GPL

>>> import mogilefs
>>> c=mogilefs.Client(domain='test',trackers=['edge:7001'])
>>> c.list_keys('m')
('mogilefs.py', ['mogilefs.py'])
>>> c.send_file('motd', '/etc/motd')
True
>>> print c.get_file_data('motd') # or print c['motd']
Linux dell 2.6.8 #1 Wed Jan 12 15:42:17 EST 2005 i686 GNU/Linux

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.

>>> c.rename('motd', '/etc/motd')
True
>>> print c.get_file_data('motd')
None
>>> print c.get_file_data('/etc/motd')
Linux dell 2.6.8 #1 Wed Jan 12 15:42:17 EST 2005 i686 GNU/Linux

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.

>>> f=c.new_file('hello')
>>> f.write('hello world\n')
12
>>> f.close()
True
>>> print c.get_file_data('hello')
hello world

>>> c.list_keys()
Traceback (most recent call last):
  File "<stdin>", line 1, in ?
TypeError: list_keys() takes at least 2 arguments (1 given)
>>> c.list_keys('m')
('mogilefs.py', ['mogilefs.py'])
>>> c.list_keys('/')
('/etc/motd', ['/etc/motd'])
>>> 
>>> f=open("/tmp/foo", 'w')
>>> c.get_file_data('/etc/motd', fp=f)
True
>>> f.close()
>>> print open("/tmp/foo").read()
Linux dell 2.6.8 #1 Wed Jan 12 15:42:17 EST 2005 i686 GNU/Linux

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.

>>> #c.get_file_data('/etc/motd', sys.stdout) works too



"""



import md5
import cStringIO
import re
import time
import sys, os
import socket
import signal
from select import select
import random

from urllib import quote_plus, unquote_plus, urlencode
#import urllib2
import pycurl

from errno import EINPROGRESS, EISCONN, EAGAIN

class MogileFSError(Exception):
    pass

class common:
    debug = os.getenv("MOGFS_DEBUG")
    def _debug(self, msg, ref=""):
        if not self.debug:
            return

        print >>sys.stderr, "%s\n%s" % (msg, ref)
        return

    def _fail(self, s):
        self.croak ("MogileFS: %s" % s)
    def croak(self, s):
        raise MogileFSError(s)

class Backend(common):
    MSG_NOSIGNAL    =    0x4000 #not defined in socket.py for some reason
    FLAG_NOSIGNAL = MSG_NOSIGNAL

    def __init__(self, hosts, timeout = 5):
        self.hosts       = hosts
        self.host_dead   = {}
        self.lasterr     = None
        self.lasterrstr  = None
        self.sock_cache  = None
        self.pref_ip     = {}
        self.timeout     = timeout

    def _fail(self, s):
        self.croak ("MogileFS::Backend: %s" % s)

    def reload(self):
        self.__init__(self.hosts, self.timeout)

    def _wait_for_readability(self, fileno=None, timeout=0):
        if not (fileno and timeout):
            return 0

        #select returns the 3 lists back: either
        #([], [], []) or
        #([<open file ...>], [], []), so we do:
        #test with bool(select.select([sys.stdin],[],[],1)[0])
        return bool (select([fileno], [], [], timeout)[0])


    def do_request(self, cmd=None, args={},retry=0):
        """Send the command 'cmd' to the server with the 'args'
        dictionary as arguments"""

        if not cmd and args is None:
            self._fail("invalid arguments to do_request")

        if self.FLAG_NOSIGNAL:
            try :
                signal.signal(signal.SIGPIPE, signal.SIG_IGN)
            except:
                pass

        sock = self.sock_cache
        argstr = self._encode_url_string(args);
        req = "%s %s\r\n" % (cmd, argstr)

        #reqlen = len(req);
        rv = 0

        def maybereetry(reason):
            if retry < 2:
                self.sock_cache = None
                return self.do_request(cmd, args, retry +1 )
            else :
                return self._fail(reason)
        
        if sock:
            # try our cached one, but assume it might be bogus
            try :
                # getpeername can raise an exception too
                self._debug("SOCK: cached = %s, REQ: %s" % (sock.getpeername(),req));
                sock.sendall(req, self.FLAG_NOSIGNAL)
                rv = 1
            except socket.error:
                self.sock_cache = None
            #except error: #still get Broken pipe, wtf?
            #    self.sock_cache = None

        if not rv:
            sock = self._get_sock()
            if not sock:
                return self._fail("couldn't connect to mogilefsd backend") #already tries all hosts
            self._debug("SOCK: %s, REQ: %s"  % (sock.getpeername(), req))
            try :
                sock.sendall(req, self.FLAG_NOSIGNAL)
                rv = 1
            except socket.error:
                return maybereetry("error talking to mogilefsd tracker")
            #except error:
            #    return maybereetry("error talking to mogilefsd tracker")
            self.sock_cache = sock;

        # wait up to 3 seconds for the socket to come to life
        if not self._wait_for_readability(sock, self.timeout):
            sock.close()
            return maybereetry("socket never became readable")

        #fixme: replace with use of more generic _getline function?
        sockfile = sock.makefile()
        line = sockfile.readline()
        self._debug("RESPONSE: %s" % line);
        if not line:
            return maybereetry("socket closed on read")

        parts = re.split('\s',line,2)
        # ERR <errcode> <errstr>
        #match = re.match('^ERR\s+(\w+)\s*(\S*)', line)
        if parts[0] == 'ERR':
            self.lasterr = parts[1]
            self.lasterrstr = unquote_plus(parts[2])
            self._fail("LASTERR: %s %s" % (parts[1], self.lasterrstr))
            return None

        # OK <arg_len> <response>
        elif parts[0] == 'OK':
            args = self._decode_url_string(parts[1])
            self._debug("RETURN_VARS: ", args)
            if not args: #emtpy args is still OK!
                return True
            return args

        self._fail("invalid response from server: [%s]" % line);
        return None

    def errstr(self):
        return "%s %s" % (self.lasterr, self.lasterrstr)

    def _connect_sock(self, sock, sin, timeout=0.25):
        """Connect the socket object 'sock' to the (host,port) pair 'sin'"""

        #huh timeout ||= 0.25;

        # make the socket non-blocking for the connection if wanted, but
        # unconditionally set it back to blocking mode at the end

        if timeout:
            sock.setblocking(0)
        else:
            sock.setblocking(1)

        try :
            r = sock.connect_ex(sin)
        except socket.gaierror:
            r = 'does not throw an exception my ass'
        if r:
            if r == EINPROGRESS:
                inprogress = True
            else :
                inprogress = False
            ret = False
        else:
            ret = True
            

        if r and timeout and inprogress:
            if select([], [sock], [], timeout)[1]:
                r = sock.connect_ex(sin)
                # EISCONN means connected & won't re-connect, so success
                if not r or r == EISCONN:
                    ret = True

        # turn blocking back on, as we expect to do blocking IO on our sockets
        if timeout:
            sock.setblocking(1)

        return ret


    def _sock_to_host(self, host):
        """Try and set self.sock to a connection to 'host'"""
        
        # create a socket and try to do a non-blocking connect
        ip, port = host.split(":")
        port=int(port)
        connected = False

        # try preferred ips
        if ip in self.pref_ip:
            prefip = self.pref_ip[ip]
            self._debug("using preferred ip %s over %s" % (prefip, ip))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sin = (prefip, port)
            if self._connect_sock(sock, sin, 0.1):
                connected = True
            else:
                self._debug("failed connect to preferred ip %s" % prefip)
                sock.close()
        # now try the original ip
        if not connected:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sin = (ip, port)
            if not self._connect_sock(sock, sin):
                return None

        # just throw back the socket we have so far
        return sock



    def _encode_url_string(self, args):
        return "&".join(
            ["%s=%s" % (
                        quote_plus(str(k)),
                        quote_plus(str(v))
                       ) 
            for k,v in args.items() if v]
        )

    def _decode_url_string(self, arg):
        out = {}
        if not arg:
            return out

        #arg = unquote_plus(arg)
        pairs = arg.split('&')
        for pair in pairs:
            name, value = pair.split('=',1)
            out[name] = unquote_plus(value)

        return out
            
    def _get_sock(self):
        """return a new mogilefsd socket, trying different hosts until one is found,
           or None if they're all dead"""

        size = len(self.hosts)
        if size > 15:
            tries = 15
        else :
            tries = size
        #create something like [3, 4, 5,   0, 1, 2]
        idx = random.randint(1, size)
        #indexes = range(pivot,size) + range(0,pivot) 
        #maybe just use random.shuffle(self.hosts) ?

        now = time.time();
        for t in xrange(tries):
            host = self.hosts[idx % size]
            idx +=1

            # try dead hosts every 5 seconds
            # if host is down and last down time is
            # less than 5 seconds, ignore
            if host in self.host_dead and self.host_dead[host] > now - 5:
                continue

            sock = self._sock_to_host(host)
            if sock:
                return sock

            # mark sock as dead
            self._debug("marking host dead: %s @ %s" %(host, time.ctime(now)))
            self.host_dead[host] = now
            

        return None


class Client(common):
    def __init__(self, domain, trackers,clas=None, root=None, verify_data=False, verify_repcount=False):
        self.domain   = domain
        self.trackers = trackers
        self.backend  = Backend(trackers)
        self.admin = Admin(trackers)
        self.root=root
        self.clas=clas
        
        self.verify_data = verify_data
        self.verify_repcount = verify_repcount
        
    def  _fail(self, s):
        return self.croak("MogileFS: %s" % s)

    def reload(self):
        return self.__init__(self.domain, self.trackers)

    
    def errstr(self):
        return self.backend.errstr()

    def set_pref_ip(self, pref_ip):
        self.backend.pref_ip = pref_ip


    def replication_wait(self, key, mindevcount, seconds):
        for x in range(seconds):
            if len(self.get_paths(key)) >= mindevcount:
                return True
            time.sleep(1)
        return False

    def send_bigfile(self, key, source, clas=None, description="", overwrite=True, chunksize=1024*1024*16):
        #default to saved?
        if clas is None:
            clas = self.clas

        prekey  = "_big_pre:"  + key
        infokey = "_big_info:" + key
        if prekey in self or infokey in self:
            if not overwrite:
                self._fail("pre file or info file for %s already exists")
            self.delete_small(prekey)
            self.delete_small(infokey)

        self[prekey] = "starttime:%d" % int(time.time()) 

        opened = False
        if not hasattr(source, 'read'):
            source = open(source)
            opened = True

        chunkinfo = []

        cnum = 1
        totalsize = 0
        oldclass = self.clas # i can't pass class to setitem
        while 1:
            self._debug("Buffering...")
            chunk = source.read(chunksize)
            if not chunk:
                break
            md5sum = md5.md5(chunk).hexdigest()
            size = len(chunk)
            ckey = "%s,%d" % (key, cnum) 
            chunkinfo.append((md5sum, size, ckey))


            self.set_file_data(ckey, chunk, clas)

            cnum +=1
            totalsize += size

        info = self._make_bigfile_info(key, description, totalsize, chunkinfo)
        self[infokey] = info
        self.delete_small(prekey)
        
        if opened:
            source.close()

        return True

    def _make_bigfile_info(self, key, description, size, chunkinfo):
        chunks = str(len(chunkinfo))
        size = str(size)

        info = []
        a = info.append
        
        #many ways to do this, lets do it like this to keep it indented
        a("des " + description)
        a("type file")
        a("compressed 0")
        a("filename " + key)
        a("chunks " + chunks)
        a("size " + size)
        a("")

        cnum = 1
        for md5sum, size, ckey in chunkinfo:
            paths = self.get_paths(ckey)
            a("part %d bytes=%d md5=%s paths: %s" %(cnum, size, md5sum, ", ".join(paths)))
            cnum +=1
        
        return "\n".join(info)

    def send_file(self, key, source, clas=None, blocksize=1024*1024):
        """send file as key and class. source should be an open file object
        or something that supports .read(), or a valid filename.
        This function is sort of redundant though
        large files should use send_bigfile and small files can just use
        c[key]=file.read()
        """

        #default to saved?
        if clas is None:
            clas = self.clas

        opened = False
        if not hasattr(source, 'read'):
            source = open(source)
            opened = True
            

        source.seek(0, 2)
        size = source.tell()
        source.seek(0)

        f=self.new_file(key, clas, size)
        while 1:
            data = source.read(blocksize)
            if not data:
                break
            f.write(data)
        f.close()

        if opened:
            source.close()
        
        return True

    def new_file(self, key, clas=None, bytes=0):
        """returns MogileFS::NewFile object, or None if no device
        available for writing"""

        #default to saved?
        if clas is None:
            clas = self.clas

        res = self.backend.do_request("create_open", {
                'domain':      self.domain,
                'class':        clas,
                'key':         key,
                'multi_dest':  1
            })
        if not res:
            return None

        dests = [];  # [ [devid,path], [devid,path], ... ]

        # determine old vs. new format to populate destinations
        if not 'dev_count' in res:
            dests.append((res['devid'], res['path']))
        else:
            dev_count = int(res['dev_count'])
            for i in xrange (1, dev_count +1):
                dests.append((res['devid_%d' % i] , res['path_%d' % i]))

        self._debug("Dests", dests)

        main_dest = dests.pop(0)
        main_devid, main_path = main_dest

        # create a MogileFS::NewFile object, based off of IO::File
        if main_path.startswith("http://"):
            return HTTPFile(
                                        mg    = self,
                                        fid   = res['fid'],
                                        path  = main_path,
                                        devid = main_devid,
                                        backup_dests = dests,
                                        clas = clas,
                                        key   = key,
                                        content_length = bytes,
                                        )
        else:
            return File(
                              mg    = self,
                              fid   = res['fid'],
                              path  = main_path,
                              devid = main_devid,
                              clas = clas,
                              key   = key
                              )

    # old style calling:
    #   get_paths(key, noverify)
    # new style calling:
    #   get_paths(key, { noverify => 0/1, zone => "zone" });
    # but with both, second parameter is optional
    def get_paths(self, key, noverify=0, zone=None):

        try :
            res = self.backend.do_request("get_paths", {
                'domain':    self.domain,
                'key':       key,
                'noverify':  noverify,
                'zone':      zone
            })
        except MogileFSError, e:
            if 'unknown_key' in str(e):
                return []
            else:
                raise

        numpaths = int( res['paths'] )
        paths = [res['path%d' % x] for x in xrange(1,numpaths + 1)]
        if len(paths) > 0 and paths[0].startswith('http'):
            return paths
        else :# for nfs
            return ["%s/%s" % (self.root,p) for p in paths]

    def cat(self, key,fp=sys.stdout, big=False):
        if not big:
            data = self.get_file_data(key, fp)
            if data is not None:
                return data
            else :
                return self.cat(key, fp=fp, big=True)

        else :
            for part in self.get_bigfile_iter(key):
                fp.write(part)

    def get_bigfile_iter(self, key):
        """Return the parts of a bigfile"""

        info = self._get_bigfile_info(key)
        if not info:
            return
        for part in info['parts']:
            #paths = part['paths']
            #would be cool if I could use getitem here....
            #don't really need to retry, or if I do, another function should
            paths = self.get_paths("%s,%d" % (key, part['part']))
            datapart = self._get_path_data(paths,checksum = part['md5'])

            yield datapart

    def get_bigfile_as_lines(self, key):
        extra = None
        for part in self.get_bigfile_iter(key):
            lines = part.splitlines()
            for line in lines[:-1]:
                if extra:
                    line = extra+line
                    extra = None
                yield line
            if lines[-1][-1]=='\n':
                yield lines[-1]
            else :
                extra = lines[-1]

    def get_bigfile_as_file(self, key):
        info = self._get_bigfile_info(key)
        return BigFile(self, key, info)
    
    def get_file_data(self, key, fp=None, timeout=5):
        """return the file data pointed to by 'key'
        if fp is given, the data is written to it"""

        #this doesn't retry itself at all, I've found that unlike writing,
        #reading is a lot more forgiving of errors, plus this already retries
        #each path
        paths = self.get_paths(key, noverify=0)
        if not paths:
            return None
        
        self._debug("Retreving %s..." % key)
        return self._get_path_data(paths, fp, timeout)
        

    def _get_path_data(self, paths, fp=None, timeout=5, checksum=None):
        """given a key, returns a scalar reference pointing at a string containing
        the contents of the file.  if fp is specified, the file contents will be
        written to it... for HTTP this should lower memory usage."""

        md5err = ioerr = 0

        # iterate over each
        for path in paths + paths: #try each path twice?
            if path.startswith('http://'):
                # try via HTTP
                
                try :
                    if fp is None:
                        ofp = cStringIO.StringIO()
                    else :
                        ofp = fp
                    curl = pycurl.Curl()
                    curl.setopt(pycurl.URL, path)
                    curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
                    #curl.setopt(pycurl.TIMEOUT, timeout)
                    #next two lines: if I don't get 1 byte in 5 seconds, abort
                    curl.setopt(pycurl.LOW_SPEED_TIME, 5)
                    curl.setopt(pycurl.LOW_SPEED_LIMIT, 1)
                    curl.setopt(pycurl.WRITEFUNCTION, ofp.write)
                    curl.perform()
                    curl.close()
                    if fp is None:
                        contents = ofp.getvalue()
                        if not checksum or md5.md5(contents).hexdigest() == checksum:
                            return contents
                        else :
                            self._debug("Checksum error on path %s" % path)
                            md5err +=1
                            continue
                    else :
                        return True
                except pycurl.error:
                    #ofp.seek(0)
                    self._debug("IO error on path %s" % path)
                    ioerr += 1
                    continue

            else:
                # open the file from disk and just grab it all
                try :
                    f = open(path)
                    contents = f.read()
                    f.close()
                    if fp is None:
                        if not checksum or md5.md5(contents).hexdigest() == checksum:
                            return contents
                        else :
                            self._debug("Checksum error on path %s" % path)
                            md5err +=1
                            continue
                    else :
                        fp.write(contents)
                        return True
                        
                except IOError:
                    self._debug("IO error on path %s" % path)
                    if fp:
                        fp.seek(0)
                    ioerr +=1
                    continue

        return self._fail("unable to read all paths %s. ioerr: %d, md5err: %d" % (paths, ioerr, md5err))
        #return False

    def set_file_data(self, key, data, clas=None):
        """Set the file pointed to by 'key' to data using 'clas'"""
        #This used to fail in intersting ways if the stored goes down
        #right before the filed checks it's filesize, so retry

        l = len(data)

        tries = 2
        for x in range(1,tries+1):
            try :
                self._debug("Sending... try %d" % x)
                #more or less self[key]=data
                f = self.new_file(key, clas, bytes=l)
                f.write(data)
                f.close()
                break #if I made it here everything is ok!
            except MogileFSError, e:
                if x==tries:
                    raise
                else :
                    self._debug("Send: %s" % e)
                    continue
        return True

    def delete(self, key):
        if self.delete_small(key):
            return True
        if self.delete_big(key):
            return True
        return False

    def delete_small(self, key):
        """TODO: delete method on MogileFS::NewFile object
           this method returns undef only on a fatal error such as inability to actually
           delete a resource and inability to contact the server.  attempting to delete
           something that doesn't exist counts as success, as it doesn't exist."""
        
        try :
            self.backend.do_request("delete", {
                'domain':  self.domain,
                'key':     key
            })
        except MogileFSError, e:
            if 'unknown_key' in str(e):
                return False
            else:
                raise

        return True

    def delete_big(self, key):
        info = self._get_bigfile_info(key)
        if not info:
            return
        
        chunks = info['chunks']
        for i in xrange(1, chunks + 1):
            self.delete_small("%s,%d" % (key, i))

        self.delete_small("_big_info:" + key)
        return True

    def sleep(self, seconds):
        """just makes some sleeping happen.  first and only argument is number of
            seconds to instruct backend thread to sleep for"""

        self.backend.do_request("sleep", {'duration':  seconds})
        return

    def rename(self, fkey, tkey):
        if self.rename_small(fkey, tkey):
            return True
        if self.rename_big(fkey, tkey):
            return True
        return False
        
    def rename_small(self, fkey, tkey):
        """this method renames a file.  it returns an undef on error (only a fatal error
           is considered as undef; "file didn't exist" isn't an error)"""

        try :
            self.backend.do_request("rename", {
                'domain':    self.domain,
                'from_key':  fkey,
                'to_key':    tkey,
            })
        except MogileFSError, e:
            if 'unknown_key' in str(e):
                return False
            else:
                raise
        return True

    def rename_big(self, fkey, tkey):
        info = self._get_bigfile_info(fkey)
        if not info:
            return
        
        chunks = info['chunks']
        for i in xrange(1, chunks + 1):
            self.rename_small("%s,%d" % (fkey, i), "%s,%d" %(tkey, i))

        self.rename_small("_big_info:" + fkey, "_big_info:" + tkey)
        return True


    def list_keys(self, prefix, after=None, limit=None):
        """used to get a list of keys matching a certain prefix.
           prefix specifies what you want to get a list of.  after is the item specified
           as a return value from this function last time you called it.  limit is optional
           and defaults to 1000 keys returned.
          
           if you expect an array of return values, returns:
             ($after, $keys)
           but if you expect only a single value, you just get the arrayref of keys.  the
           value $after is to be used as $after when you call this function again.
          
           when there are no more keys in the list, you will get back undef(s)."""

        try :
            res = self.backend.do_request("list_keys", {
                'domain':  self.domain,
                'prefix':  prefix,
                'after':   after,
                'limit':   limit
            })
        except MogileFSError, e:
            if 'none_match' in str(e) or 'no_key' in str(e):
                return "", []
            else:
                raise

        # construct our list of keys and the new after value
        resafter = res['next_after']
        reslist = []
        key_count = int( res['key_count'] )
        for i in xrange(1, key_count+1):
            reslist.append(res['key_%i' % i])

        #return wantarray ? ($resafter, $reslist) : $reslist;
        return resafter, reslist

    def _parse_bigfile_info(self, info):
        res = {}
        res['parts']=[]
        res['maxnum']=0

        # parse out the header data
        header = ["des", "type", "compressed", "filename", "chunks", "size"]
        for line in info.splitlines():
            for f in header:
                if line.startswith(f):
                    res[f] = line[len(f)+1:]
                    try :
                        res[f] = int(res[f])
                    except ValueError:
                        pass
                    header.remove(f)
                    continue

            if line.startswith("part"):
                fields = re.split('[\s,=]+', line)
                part, bytes, md5, paths = int(fields[1]), int(fields[3]), fields[5], fields[7:]
                res['maxnum'] = max(res['maxnum'], part)
                res['parts'].append({
                        'part' : part,
                        'bytes': bytes, 
                        'md5': md5, 
                        'paths': paths
                        })

        return res

    def _get_bigfile_info(self, key):
        newkey = "_big_info:" + key
        info=self.get_file_data(newkey)
        if not info:
            return None
        return self._parse_bigfile_info(info)

    def __contains__(self, key):
        if self.get_paths(key):
            return True
        elif self.get_paths('_big_info:' + key):
            return True
        return False

    def __getitem__(self, key):
        #support KeyError?
        return self.get_file_data(key)
    
    def __setitem__(self, key, data):
        """Set the file pointed to by 'key' to data using self.clas as the class"""

        self.set_file_data(key, data,self.clas)
    
    def __delitem__(self, key):
        return self.delete(key)
           
    def __iter__(self):
        return iter( self.list_keys('/')[1] )

    def setdefault(self, k, default=None):
        f = self[k]
        if f:
            return f
        else :
            self[k] = default
            return default

class Admin(common):
    def __init__(self, trackers):
        self.trackers = trackers
        self.backend  = Backend(trackers)

    def _fail(self, s):
        self.croak ("MogileFS:Admin %s" % s)

    def get_hosts(self,hostid=None):
        args = {}
        if hostid:
            args['hostid'] = hostid

        res = self.backend.do_request("get_hosts", args)
        ret = []
        fields = "hostid status hostname hostip http_port remoteroot".split()
        hosts = int(res['hosts']) + 1
        for ct in xrange(1, hosts):
            ret.append(dict([ (f, res['host%d_%s' % (ct, f)]) for f in fields]))

        return ret

    def get_devices(self, devid=None):
        args = {}
        if devid:
            args['devid'] = devid

        res = self.backend.do_request("get_devices", args)

        ret = []
        fields = "devid hostid status mb_total mb_used mb_free mb_asof".split()
        devices = int(res['devices']) +1
        for ct in xrange(1, devices):
            d = dict([ (f, res['dev%d_%s' % (ct, f)]) for f in fields])
            #try and convert any to a number
            for k in d:
                try :
                    d[k] = int(d[k])
                except ValueError:
                    pass
            ret.append(d)
            
        return ret

    def get_freespace(self, devid=None):
        """Get the free space for the entire cluster, or a specific node"""
        return sum([x['mb_free'] for x in  self.get_devices(devid)])

    def get_stats(self, stats=['all']):
        args = {}
        for type in stats:
            args[type]=1
        res = self.backend.do_request("stats", args)

        ret = {}
        if 'replicationcount' in res:
            ret['replication'] = {}
            repcount = int(res['replicationcount']) + 1
            for i in xrange(1, repcount):
                domain = res['replication%ddomain' % i]
                clas   = res['replication%dclass' % i]
                devcount   = int(res['replication%ddevcount' % i])
                files  = int(res['replication%dfiles' % i])
                ret['replication'].setdefault(domain,{}).setdefault(clas, {})[devcount] = files

        if 'filescount' in res:
            ret['files'] = {}
            repcount = int(res['filescount']) + 1
            for i in xrange(1, repcount):
                domain = res['files%ddomain' % i]
                clas   = res['files%dclass' % i]
                files  = int(res['files%dfiles' % i])
                ret['files'].setdefault(domain,{})[clas] = files
        
        if 'devicescount' in res:
            ret['devices'] = {}
            devcount = int(res['devicescount']) +1
            for i in xrange(1, devcount):
                ret['devices'][res['devices%did'    %i]] = {
                    'host':   res['devices%dhost'   %i],
                    'status': res['devices%dstatus' %i],
                    'files':  int(res['devices%dfiles'  %i])
                    }
                
        return ret

    def get_domains(self):
        res = self.backend.do_request("get_domains")

        ret = {}
        
        domains = int(res['domains']) +1 
        for i in xrange(1, domains):
            domain = res['domain%d' % i]
            ret[domain]={}
            classes = int(res['domain%dclasses' % i]) + 1
            for k in xrange(1, classes):
                name = res['domain%dclass%dname' % (i,k)]
                mindevcount = int(res['domain%dclass%dmindevcount' % (i,k)])
                ret[domain][name]=mindevcount
                
        return ret

    def create_domain(self, domain):
        res = self.backend.do_request("create_domain", {'domain': domain})
        if res['domain'] == domain:
            return True
        return False        

    def create_class(self, domain, clas, mindevcount):
        return self._mod_class(domain, clas, mindevcount, 'create') # be explicit
    def update_class(self, domain, clas, mindevcount):
        return self._mod_class(domain, clas, mindevcount, 'update') # be explicit

    def _mod_class(self, domain, clas, mindevcount, verb='create'):
        res = self.backend.do_request("%s_class" % verb, {
            'domain': domain,
            'class': clas,
            'mindevcount': mindevcount
            })

        if res['class'] == clas:
            return True

        return False

    def change_device_state(self, host, device, state):
        
        res = self.backend.do_request("set_state", {
            'host': host,
            'device': device,
            'state': state
            })
        return bool(res)

class HTTPFile(common):
    def __init__(self, mg, fid, path, devid, backup_dests, clas, key, content_length):
        #there is a way that uses locals() or such to do this automagically...
        self.mg             = mg
        self.fid            = fid
        self.path           = path
        self.devid          = devid
        self.backup_dests   = backup_dests or []
        self.clas           = clas
        self.key            = key
        self.content_length = content_length

        self.data           = cStringIO.StringIO()
        self.data_in        = ""
        self.bytes_out      = 0
        self.pos            = 0
        self.length         = 0
        self.sock           = None
        self.host           = None

        self._writecall     = 0
        self._wroteheader   = False
        self._closed        = False

        if not self._parse_url(path):
            self._fail("Unable to parse url")

    def _fail(self, s):
        #delete a temporary file if one exists
        if not self._closed:
            self._backend_close(delete=True)
        self.croak ("MogileFS:HTTPFILE %s" % s)

    def _parse_url(self, url):
        #parts = urllib2.urlparse.urlparse(url)
        match = re.match('http://(.+?)(/.+)$', url)
        if not match:
            return False

        tmp = match.groups()
        self.path = url
        self.host, self.uri = tmp[0], tmp[1]
        return True

    def _sock_to_host(self, host):
        # setup
        ip, port = host.split(':')
        port = int(port)

        # create the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sin = (ip, port)

        # unblock the socket
        sock.setblocking(0)

        # attempt a connection
        ret = False
        r = sock.connect_ex(sin)
        if not r: #no error
            ret = True
        elif r == EINPROGRESS:
            # watch for writeability
            if select([], [sock], [], 3)[1]:
                r = sock.connect_ex(sin)

                # EISCONN means connected & won't re-connect, so success
                if not r or r == EISCONN:
                    ret = True

        # just throw back the socket we have
        if ret:
            return sock
        return None

    def _connect_sock(self):
        if self.sock:
            return True

        down_hosts = []

        while not self.sock and self.host:
            # attempt to connect
            self.sock = self._sock_to_host(self.host)
            if self.sock:
                self._debug("connected to %s" % self.host)
                return True

            down_hosts.append(self.host)
            if not self.backup_dests:
                self.host = None
            else :
                dest = self.backup_dests.pop(0)
                # dest is [$devid,$path]
                devid, path = dest
                if not self._parse_url(path):
                    self._fail("bogus URL")
                self.devid = devid

        return self._fail("unable to open socket to storage node (tried: %s):" % ' '.join(down_hosts));
        

    def _getline(self):
        #see also readline in socket.py
        if not self.sock:
            return None

        sock = self.sock

        nl = self.data_in.find('\n')
        if nl >= 0:
            nl += 1
            data = self.data_in
            self.data_in = data[nl:]
            return data[:nl]

        buffers = []
        if self.data_in:
            buffers.append(self.data_in)

        # nope, we have to read a line
        while select([sock], [], [], 5)[0]:
            try :
                data = sock.recv(1024)
                if not data:
                    break
            except socket.error,e:
                if e[1] == EAGAIN:
                    continue
                else : #save current buffer
                    buffers.append(data)   #can this have anything in case of error?
                    self.data_in = "".join(buffers)
                    return None

            buffers.append(data) 
            #return a line if we got one
            nl = data.find('\n')
            if nl >= 0:
                nl += 1
                self.data_in = data[nl:]
                buffers[-1]  = data[:nl]
                return "".join(buffers)


        # if we got here, nothing was readable in our time limit
        return None
 
    def _repoint_to_backup(self):
        """set self.host, self.path, and self.devid to a backup, set the socket to None"""

        devid, path = self.backup_dests.pop(0)
        if not self._parse_url(path):
            self._fail("bogus URL");
        self.devid = devid
        self._debug("retrying with %s" % self.path)
        self.sock = None
        self._wroteheader = False
        self._writecall = 0

    def _write_header(self):
        if self.content_length:
            l = self.content_length
        else :
            l = self.length
        #after the header I am on my "second" write
        #i can sometimes retry for the first and second write only
        #print 'about to write header, kill mogstored'
        #time.sleep(10)
        return self._writeall("PUT %s HTTP/1.0\r\nContent-length: %s\r\n\r\n" % (self.uri, l))

    def _writeall(self, data):
        """send all of data to self.sock with a timeout"""

        # setup data and counters
        bytesleft = len(data)
        bytessent = 0
        sockerr = False

        # main sending loop for data, will keep looping until all of the data
        # we've been asked to send is sent
        while bytesleft and select([], [self.sock], [], 5)[1]:
            try :
                bytesout = self.sock.send(data[bytessent:])
                bytessent += bytesout
                bytesleft -= bytesout
                self.bytes_out += bytesout
            except socket.error, e:
                if e[1] == EAGAIN:
                    continue
                else :
                    self._debug("error writing to node for device %s: %s" % (self.host, e[1]))
                    sockerr = True
                    break

        if bytesleft:
            self.sock = None #find a better place for this.
            if not sockerr:
                self._debug("error writing to node for device %s: Select Timeout" % self.host )
            return False

        return True

    def _write(self, data):
        """send all of data to self.sock
        send a HTTP header if needed.
        reconnect and restart if possible"""

        self._writecall +=1



        if not self._wroteheader:
            if self._write_header():
                self._wroteheader = True
            else :
                self._wroteheader = False
                #don't bother bailing out here, the next blocks of code will do it for me
        

        # main sending loop for data, will keep looping until all of the data
        # we've been asked to send is sent
        if self._writeall(data):
            return True


        # at this point, we had a socket error, since we have bytes left, and
        # the loop above didn't finish sending them.  if this was our first
        # write, let's try to fall back to a different host.
        # no, I can do it also if I am writing a a whole chunk
        #if not self.bytes_out and self.backup_dests:
        #print self.backup_dests, self.content_length, self.bytes_out, self._writecall
        if self.backup_dests and (self.content_length == 0 or self._writecall == 1):
            self._repoint_to_backup()
            self._connect_sock()
            self._wroteheader = False
            # now repass this write to try again
            return self._write(data)

        # total failure (croak)
        self.sock = None
        return self._fail("unable to write to any allocated storage node")

    def write(self, data):
        newlen = len(data)
        #self.pos += newlen
        if not self.sock and self.content_length:
            self._connect_sock()
            #self._write_header()
            #self._write("PUT %s HTTP/1.0\r\nContent-length: %s\r\n\r\n" % (self.uri, self.content_length))

        # write some data to our socket
        if self.sock:
            # save the first 1024 bytes of data so that we can seek back to it
            # and do some work later
            if self.length < 1024 :
                if self.length + newlen > 1024 :
                    self.length = 1024
                    self.data.write(data[: 1024 - self.length])
                else:
                    self.length += newlen
                    self.data.write(data)

            # actually write
            self._write(data);
        else :
            # or not, just stick it on our queued data
            self.data.write(data)
            self.length += newlen;

        return newlen

    def close(self):
        # if we're closed and we have no sock...
        if self._closed :
            self._fail("File already closed")
        if not self.sock:
            self._connect_sock()
            #self._write("PUT %s HTTP/1.0\r\nContent-length: %s\r\n\r\n" % (self.uri, self.length))
            self._write(self.data.getvalue())

        # set a message in $! and $@
        #my $err = sub {
        #    $@ = "$_[0]\n";
        #    return undef;
        #};

        # get response from put
        if self.sock:
            line = self._getline()
            if not line:
                if self.backup_dests and self.content_length == 0:
                    self._repoint_to_backup()
                    return self.close()
                else :
                    self._fail("Unable to read response line from server")
            match = re.match('^HTTP/\d+\.\d+\s+(\d+)', line)
            if match:
                code = match.groups()[0]
                code = int(code)
                found_header = False
                # all 2xx responses are success
                if not (code >= 200 and code <= 299):
                    body=[]
                    # read through to the body
                    l = self._getline()
                    while l:
                        l = self._getline()
                        # remove trailing stuff
                        l=l.rstrip()
                        if not l:
                            found_header = True
                        if not found_header :
                            continue
                        # add line to the body, with a space for readability
                        body.append(l)
                    #$body = substr($body, 0, 512) if length $body > 512;
                    body = " ".join(body)[:512]
                    self.sock.close()
                    self._fail("HTTP reponse %d from upload: %s" % (code, body))
            else :
                self._fail("Response line not understood: " + line);
            self.sock.close()
            
            self._backend_close()

            #verify the data if I haven't been streaming the file
            if self.mg.verify_data and not self.content_length:
                start = time.time()
                self._debug("waiting for verification.....")
                if self.data.getvalue() != self.mg[self.key]:
                    self._fail("Data verification error")
                endtime = time.time() - start
                self._debug("file verified in %d seconds!" % endtime)
                
            if self.mg.verify_repcount:
                tmp = self.mg.admin.get_domains()[self.mg.domain][self.clas or 'default']
                mindevcount = min(tmp, 2) #tracker only ever returns 2....
                start = time.time()
                self._debug("waiting for replication.....")
                if not self.mg.replication_wait(self.key, mindevcount, 20):
                    self._fail("Send/replication failed")
                endtime = time.time() - start
                self._debug("file replicated in %d seconds!" % endtime)

            return True

    def _backend_close(self, delete=False):
        mg = self.mg
        domain = mg.domain
        fid   = self.fid
        devid = self.devid
        path  = self.path

        key = self.key

        if delete: #closing a tempfile and I want to delete it
            key = None

        if self.content_length :
            size = self.content_length
        else :
            size = self.length

        rv = mg.backend.do_request("create_close", {
                'fid':     fid,
                'devid':   devid,
                'domain':  domain,
                'size':    size,
                'key':     key,
                'path':    path
            })
        if not rv:
            # set $@, as our callers expect $@ to contain the error message that
            # failed during a close.  since we failed in the backend, we have to
            # do this manually.
            self._fail("%s: %s" % (mg.backend.lasterr, mg.backend.lasterrstr))
        self._closed=True
        return True

    def tell(self):
        return self.data.tell()

    def seek(self, *args):
        return self.data.seek(*args)

    #def eof(self):
        #return bool( self.pos >= self.length)

    def read(self, *args):
        return self.data.read(*args)

    def readline(self):
        return self.data.readline()
    def __iter__(self):
        return self.data.__iter__()


class BigFile:
    def __init__(self, mogile, key, info):
        self.mogile = mogile
        self.key = key
        self.info = info
        self.datapartcache = {}

    def read(self, len, offset):
        parts = self.info['parts']
        x = 0
        skippedbytes = 0
        try :
            while offset >= parts[x]['bytes']:
                offset -= parts[x]['bytes']
                skippedbytes += parts[x]['bytes']
                x += 1
        except IndexError: #aka EOF
            return ''

        if x in self.datapartcache:
            datapart = self.datapartcache[x]
        else :
            self.datapartcache.clear()
            part = parts[x]
            paths = self.mogile.get_paths("%s,%d" % (self.key, part['part']))
            datapart = self.mogile._get_path_data(paths,checksum = part['md5'])
            self.datapartcache[x] = datapart

        if offset+len > parts[x]['bytes']:
            newlen = offset + len - parts[x]['bytes']
            newoffset = skippedbytes + parts[x]['bytes']
            return datapart[offset:offset+len]+self.read(newlen, newoffset)
        else :
            return datapart[offset:offset+len]

def test():
    good = open("/etc/motd").read()
    c=Client(domain='test',trackers=['peter:7001','lois:7001'])

    c.delete('/etc/motd')
    c.send_file('/etc/motd', '/etc/motd')
    assert(c.get_file_data('/etc/motd') == good)

    c.delete('/etc/motd_0')
    c.rename("/etc/motd", "/etc/motd_0")
    for x in range(10):
        c.delete('/etc/motd_%d' % (x+1))
        c.rename("/etc/motd_%d" % x, "/etc/motd_%d" % (x+1))
    assert(c.get_file_data('/etc/motd_%d' % (x+1)) == good)

    want = 'f6b3f164c99761234858a4d2c12d0840'
    x=0
    while 1:
        time.sleep(1)
        try :
            start = time.time()
            m = md5.md5()
            [m.update(p) for p in c.get_bigfile_iter('/isos//ubuntu-5.04-install-i386.iso')]
            end = time.time()
            x+=1
            print time.ctime(), (m.hexdigest() == want), end-start, 'seconds', x
        except MogileFSError, e:
            if "unable to read all paths" in str(e):
                print time.ctime(), e
                continue
