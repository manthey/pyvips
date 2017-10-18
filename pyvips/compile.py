# flake8: noqa

import pkgconfig

# we must have the vips package to be able to do anything
if not pkgconfig.exists('vips'): 
    raise Exception('unable to find pkg-config package "vips"')
if pkgconfig.installed('vips', '< 8.2'):
    raise Exception('pkg-config "vips" is too old -- need libvips 8.2 or later')

from cffi import FFI

ffi = FFI()

# we need to define this before we import the decls: they need to know which
# bits of decl to make
def at_least_libvips(x, y):
    """Is this at least libvips x.y?"""

    major = vips_lib.vips_version(0)
    minor = vips_lib.vips_version(1)

    return major > x or (major == x and minor >= y)

import decls

from .error import *

# redirect all vips warnings to logging

class GLogLevelFlags(object):
    # log flags 
    FLAG_RECURSION          = 1 << 0
    FLAG_FATAL              = 1 << 1

    # GLib log levels 
    LEVEL_ERROR             = 1 << 2       # always fatal 
    LEVEL_CRITICAL          = 1 << 3
    LEVEL_WARNING           = 1 << 4
    LEVEL_MESSAGE           = 1 << 5
    LEVEL_INFO              = 1 << 6
    LEVEL_DEBUG             = 1 << 7

    LEVEL_TO_LOGGER = {
        LEVEL_DEBUG : 10,
        LEVEL_INFO : 20,
        LEVEL_MESSAGE : 20,
        LEVEL_WARNING : 30,
        LEVEL_ERROR : 40,
        LEVEL_CRITICAL : 50,
    }

def _log_handler(domain, level, message, user_data):
    logger.log(GLogLevelFlags.LEVEL_TO_LOGGER[level], 
               '{0}: {1}'.format(_to_string(ffi.string(domain)), 
                                 _to_string(ffi.string(message))))

# keep a ref to the cb to stop it being GCd
_log_handler_cb = ffi.callback('GLogFunc', _log_handler)
_log_handler_id = glib_lib.g_log_set_handler(_to_bytes('VIPS'), 
                           GLogLevelFlags.LEVEL_DEBUG | 
                           GLogLevelFlags.LEVEL_INFO | 
                           GLogLevelFlags.LEVEL_MESSAGE | 
                           GLogLevelFlags.LEVEL_WARNING | 
                           GLogLevelFlags.LEVEL_CRITICAL | 
                           GLogLevelFlags.LEVEL_ERROR | 
                           GLogLevelFlags.FLAG_FATAL | 
                           GLogLevelFlags.FLAG_RECURSION,
                           _log_handler_cb, ffi.NULL)

# ffi doesn't like us looking up methods during shutdown: make a note of the
# remove handler here
_remove_handler = glib_lib.g_log_remove_handler

# we must remove the handler on exit or libvips may try to run the callback
# during shutdown
def _remove_log_handler():
    global _log_handler_id
    global _remove_handler

    if _log_handler_id:
        _remove_handler(_to_bytes('VIPS'), _log_handler_id)
        _log_handler_id = None

atexit.register(_remove_log_handler)

from .enums import *
from .base import *
from .gobject import *
from .gvalue import *
from .vobject import *
from .vinterpolate import *
from .voperation import *
from .vimage import *

__all__ = [
    'Error', 'Image', 'Operation', 'GValue', 'Interpolate', 'GObject',
    'VipsObject', 'type_find', 'type_name', 'version', '__version__',
    'at_least_libvips',
    'cache_set_max', 'cache_set_max_mem', 'cache_set_max_files'
]