# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is Reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
#
# All portions of the code written by CondeNet are Copyright (c) 2006-2010
# CondeNet, Inc. All Rights Reserved.
################################################################################
from urllib import unquote_plus
from urllib2 import urlopen
from urlparse import urlparse, urlunparse
from threading import local
import signal
from copy import deepcopy
import cPickle as pickle
import re, math, random
from donelist.lib.utils._utils import *
from BeautifulSoup import BeautifulSoup

from time import sleep
from datetime import datetime, timedelta
from pylons.i18n import ungettext, _

from mako.filters import url_escape
 

        
iters = (list, tuple, set)

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    
        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'
    
    """
    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value): 
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'

storage = Storage

def storify(mapping, *requireds, **defaults):
    """
    Creates a `storage` object from dictionary `mapping`, raising `KeyError` if
    d doesn't have all of the keys in `requireds` and using the default 
    values for keys found in `defaults`.

    For example, `storify({'a':1, 'c':3}, b=2, c=0)` will return the equivalent of
    `storage({'a':1, 'b':2, 'c':3})`.
    
    If a `storify` value is a list (e.g. multiple values in a form submission), 
    `storify` returns the last element of the list, unless the key appears in 
    `defaults` as a list. Thus:
    
        >>> storify({'a':[1, 2]}).a
        2
        >>> storify({'a':[1, 2]}, a=[]).a
        [1, 2]
        >>> storify({'a':1}, a=[]).a
        [1]
        >>> storify({}, a=[]).a
        []
    
    Similarly, if the value has a `value` attribute, `storify will return _its_
    value, unless the key appears in `defaults` as a dictionary.
    
        >>> storify({'a':storage(value=1)}).a
        1
        >>> storify({'a':storage(value=1)}, a={}).a
        <Storage {'value': 1}>
        >>> storify({}, a={}).a
        {}
    
    """
    def getvalue(x):
        if hasattr(x, 'value'):
            return x.value
        else:
            return x
    
    stor = Storage()
    for key in requireds + tuple(mapping.keys()):
        value = mapping[key]
        if isinstance(value, list):
            if isinstance(defaults.get(key), list):
                value = [getvalue(x) for x in value]
            else:
                value = value[-1]
        if not isinstance(defaults.get(key), dict):
            value = getvalue(value)
        if isinstance(defaults.get(key), list) and not isinstance(value, list):
            value = [value]
        setattr(stor, key, value)

    for (key, value) in defaults.iteritems():
        result = value
        if hasattr(stor, key): 
            result = stor[key]
        if value == () and not isinstance(result, tuple): 
            result = (result,)
        setattr(stor, key, result)
    
    return stor

class UrlParser(object):
    """
    Wrapper for urlparse and urlunparse for making changes to urls.
    All attributes present on the tuple-like object returned by
    urlparse are present on this class, and are setable, with the
    exception of netloc, which is instead treated via a getter method
    as a concatenation of hostname and port.

    Unlike urlparse, this class allows the query parameters to be
    converted to a dictionary via the query_dict method (and
    correspondingly updated vi update_query).  The extension of the
    path can also be set and queried.

    The class also contains reddit-specific functions for setting,
    checking, and getting a path's subreddit.  It also can convert
    paths between in-frame and out of frame cname'd forms.

    """

    __slots__ = ['scheme', 'path', 'params', 'query',
                 'fragment', 'username', 'password', 'hostname',
                 'port', '_url_updates', '_orig_url', '_query_dict']

    valid_schemes = ('http', 'https', 'ftp', 'mailto')
    cname_get = "cnameframe"

    def __init__(self, url):
        u = urlparse(url)
        for s in self.__slots__:
            if hasattr(u, s):
                setattr(self, s, getattr(u, s))
        self._url_updates = {}
        self._orig_url    = url
        self._query_dict  = None

    def update_query(self, **updates):
        """
        Can be used instead of self.query_dict.update() to add/change
        query params in situations where the original contents are not
        required.
        """
        self._url_updates.update(updates)

    @property
    def query_dict(self):
        """
        Parses the `params' attribute of the original urlparse and
        generates a dictionary where both the keys and values have
        been url_unescape'd.  Any updates or changes to the resulting
        dict will be reflected in the updated query params
        """
        if self._query_dict is None:
            def _split(param):
                p = param.split('=')
                return (unquote_plus(p[0]),
                        unquote_plus('='.join(p[1:])))
            self._query_dict = dict(_split(p) for p in self.query.split('&')
                                    if p)
        return self._query_dict

    def path_extension(self):
        """
        Fetches the current extension of the path.
        """
        return self.path.split('/')[-1].split('.')[-1]

    def set_extension(self, extension):
        """
        Changes the extension of the path to the provided value (the
        "." should not be included in the extension as a "." is
        provided)
        """
        pieces = self.path.split('/')
        dirs = pieces[:-1]
        base = pieces[-1].split('.')
        base = '.'.join(base[:-1] if len(base) > 1 else base)
        if extension:
            base += '.' + extension
        dirs.append(base)
        self.path =  '/'.join(dirs)
        return self


    def unparse(self):
        """
        Converts the url back to a string, applying all updates made
        to the feilds thereof.

        Note: if a host name has been added and none was present
        before, will enforce scheme -> "http" unless otherwise
        specified.  Double-slashes are removed from the resultant
        path, and the query string is reconstructed only if the
        query_dict has been modified/updated.
        """
        # only parse the query params if there is an update dict
        q = self.query
        if self._url_updates or self._query_dict is not None:
            q = self._query_dict or self.query_dict
            q.update(self._url_updates)
            q = query_string(q).lstrip('?')

        # make sure the port is not doubly specified 
        if self.port and ":" in self.hostname:
            self.hostname = self.hostname.split(':')[0]

        # if there is a netloc, there had better be a scheme
        if self.netloc and not self.scheme:
            self.scheme = "http"

        return urlunparse((self.scheme, self.netloc,
                           self.path.replace('//', '/'),
                           self.params, q, self.fragment))

    def path_has_subreddit(self):
        """
        utility method for checking if the path starts with a
        subreddit specifier (namely /r/ or /reddits/).
        """
        return (self.path.startswith('/r/') or
                self.path.startswith('/reddits/'))

    def get_subreddit(self):
        """checks if the current url refers to a subreddit and returns
        that subreddit object.  The cases here are:

          * the hostname is unset or is g.domain, in which case it
            looks for /r/XXXX or /reddits.  The default in this case
            is Default.
          * the hostname is a cname to a known subreddit.

        On failure to find a subreddit, returns None.
        """
        from pylons import g
        from r2.models import Subreddit, Sub, NotFound, DefaultSR
        try:
            if not self.hostname or self.hostname.startswith(g.domain):
                if self.path.startswith('/r/'):
                    return Subreddit._by_name(self.path.split('/')[2])
                elif self.path.startswith('/reddits/'):
                    return Sub
                else:
                    return DefaultSR()
            elif self.hostname:
                return Subreddit._by_domain(self.hostname)
        except NotFound:
            pass
        return None

    def is_reddit_url(self, subreddit = None):
        """utility method for seeing if the url is associated with
        reddit as we don't necessarily want to mangle non-reddit
        domains

        returns true only if hostname is nonexistant, a subdomain of
        g.domain, or a subdomain of the provided subreddit's cname.
        """
        from pylons import g
        return (not self.hostname or
                is_subdomain(self.hostname, g.domain) or
                is_authorized_cname(self.hostname, g.authorized_cnames) or
                (subreddit and subreddit.domain and
                 is_subdomain(self.hostname, subreddit.domain)))

    def path_add_subreddit(self, subreddit):
        """
        Adds the subreddit's path to the path if another subreddit's
        prefix is not already present.
        """
        if not self.path_has_subreddit():
            self.path = (subreddit.path + self.path)
        return self

    @property
    def netloc(self):
        """
        Getter method which returns the hostname:port, or empty string
        if no hostname is present.
        """
        if not self.hostname:
            return ""
        elif getattr(self, "port", None):
            return self.hostname + ":" + str(self.port)
        return self.hostname

    def mk_cname(self, require_frame = True, subreddit = None, port = None):
        """
        Converts a ?cnameframe url into the corresponding cnamed
        domain if applicable.  Useful for frame-busting on redirect.
        """

        # make sure the url is indeed in a frame
        if require_frame and not self.query_dict.has_key(self.cname_get):
            return self

        # fetch the subreddit and make sure it 
        subreddit = subreddit or self.get_subreddit()
        if subreddit and subreddit.domain:

            # no guarantee there was a scheme
            self.scheme = self.scheme or "http"

            # update the domain (preserving the port)
            self.hostname = subreddit.domain
            self.port = self.port or port

            # and remove any cnameframe GET parameters
            if self.query_dict.has_key(self.cname_get):
                del self._query_dict[self.cname_get]

            # remove the subreddit reference
            self.path = lstrips(self.path, subreddit.path)
            if not self.path.startswith('/'):
                self.path = '/' + self.path

        return self

    def is_in_frame(self):
        """
        Checks if the url is in a frame by determining if
        cls.cname_get is present.
        """
        return self.query_dict.has_key(self.cname_get)

    def put_in_frame(self):
        """
        Adds the cls.cname_get get parameter to the query string.
        """
        self.update_query(**{self.cname_get:random.random()})

    def __repr__(self):
        return "<URL %s>" % repr(self.unparse())

    def domain_permutations(self, fragments=False, subdomains=True):
        """
          Takes a domain like `www.reddit.com`, and returns a list of ways
          that a user might search for it, like:
          * www
          * reddit
          * com
          * www.reddit.com
          * reddit.com
          * com
        """
        ret = set()
        if self.hostname:
            r = self.hostname.split('.')

            if subdomains:
                for x in xrange(len(r)-1):
                    ret.add('.'.join(r[x:len(r)]))

            if fragments:
                for x in r:
                    ret.add(x)

        return ret

    @classmethod
    def base_url(cls, url):
        u = cls(url)

        # strip off any www and lowercase the hostname:
        netloc = strip_www(u.netloc.lower())

        # http://code.google.com/web/ajaxcrawling/docs/specification.html
        fragment = u.fragment if u.fragment.startswith("!") else ""

        return urlunparse((u.scheme.lower(), netloc,
                           u.path, u.params, u.query, fragment))




