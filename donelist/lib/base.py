"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request,Response, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render
from utils import storify, string2js, read_http_date
import re, hashlib

import donelist.lib.helpers as h
import donelist.model as model

class BaseController(WSGIController):
    def try_pagecache(self):
        pass

    def __before__(self):
        self.pre()
        self.try_pagecache()

    def __after__(self):
        self.post()

    def pre(self):
        pass

    def post(self):
        pass

    def get_client_ip(self,environ):
        '''Get the client ip from the request environ.'''
        
        true_client_ip = environ.get('HTTP_TRUE_CLIENT_IP')
        ip_hash = environ.get('HTTP_TRUE_CLIENT_IP_HASH')
        forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
        remote_addr = environ.get('REMOTE_ADDR')
        
        if(g.ip_hash
           and true_client_ip
           and ip_hash
           and hashlib.md5(true_client_ip + g.ip_hash).hexdigest() \
           == ip_hash.lower()):
            ip = true_client_ip
        elif remote_addr in g.proxy_addr and forwarded_for:
            ip = forwarded_for.split(',')[-1]
        else:
            ip = environ['REMOTE_ADDR']
        return ip
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        request.ip = self.get_client_ip(environ)

        if environ.get('HTTP_X_DONT_DECODE'):
            request.charset = None
            
        request.get = storify(request.GET)
        # print request.get
        request.post = storify(request.POST)
        request.referer = environ.get('HTTP_REFERER')
        request.path = environ.get('PATH_INFO')
        request.user_agent = environ.get('HTTP_USER_AGENT')
        request.fullpath = environ.get('FULLPATH',request.path)
        request.port = environ.get('request_port')

        if_modified_since = environ.get('HTTP_IF_MODIFIED_SINCE')
        if if_modified_since:
            request.if_modified_since = read_http_date(if_modified_since)
        else:
            request.if_modified_since = None

        action = request.environ['pylons.routes_dict'].get('action')
        print action
        if action:
            meth = request.method.upper()
            print "method:%s" % meth
            if meth == 'HEAD':
                meth = 'GET'
            # request.environ['pylos.routes_dict']['action'] = meth + '_' +action
            print "action:%s" %  action
          
            # print request.environ['pylons.routes_dict']
            # print 'action_name:%s' % request.environ['pylons.routes_dict']['action_name']
            # print request.environ['pylons.routes_dict']['action']
            # request.environ['pylons.routes_dict']['action_name'] = action
            # request.environ['pylons.routes_dict']['action'] = handler_name
        c.thread_pool = environ['paste.httpserver.thread_pool']
        c.response=Response()

        try:
            res = WSGIController.__call__(self, environ, start_response)
        except Exception as e:
            if g.exception_logging:
                try:
                    log_exception(e, *sys.exc_info())
                except Exception as f:
                    print "log_exception() freaked out: %r" % f
            raise
        return res

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
