# Copied from: http://trac.gispython.org/lab/browser/buildout/pcl.buildout/trunk/hooks/libjpeg.py
# OS X (libtool) fix added by: Koinu <ferrox@koinu.us>

import logging
import os
import sys

import zc.buildout

log = logging.getLogger('libjpeg hook')

def pre_make(options, buildout):
    """Custom pre-make hook for building libjpeg."""
    # The installation procedure is arrogant enough to expect all the
    # directories to exist and fails otherwise.
    for dir in ('bin', 'man/man1', 'include', 'lib'):
        os.makedirs(os.path.join(options['location'], dir))
    # The old libtool shipped in the libjpeg tarball does not work on OS X.
    if sys.platform.lower() == 'darwin':
        log.info('Updating libtool')
        os.system("ln -s `which glibtool` libtool")

