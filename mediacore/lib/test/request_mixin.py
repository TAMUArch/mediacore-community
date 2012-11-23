# -*- coding: utf-8 -*-
# This file is a part of MediaCore CE, Copyright 2009-2012 MediaCore Inc.
# The source code in this file is dual licensed under the MIT license or the 
# GPL version 3 or (at your option) any later version.
# See LICENSE.txt in the main project directory, for more information.
#
# Copyright (c) 2012 Felix Schwarz <felix.schwarz@oss.schwarz.eu>

from cStringIO import StringIO
import urllib

from beaker.session import SessionObject
import pylons
from pylons.controllers.util import Request, Response
from pylons.util import ContextObj
from routes.util import URLGenerator
from webob.request import environ_from_url

from mediacore.lib.i18n import Translator


def create_wsgi_environ(url, request_method, request_body=None):
        wsgi_environ = environ_from_url(url)
        wsgi_environ.update({
            'REQUEST_METHOD': request_method,
        })
        if request_body:
            if hasattr(request_body, 'items'):
                # support parameters as dict
                request_body = request_body.items()
            if not isinstance(request_body, basestring):
                request_body = urllib.urlencode(request_body)
            wsgi_environ.update({
                'wsgi.input': StringIO(request_body),
                'CONTENT_LENGTH': str(len(request_body)),
                'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            })
        return wsgi_environ

class RequestMixin(object):
    def init_fake_request(self, server_name='mediacore.example', language='en', 
            method='GET', post_vars=None):
        app_globals = self.pylons_config['pylons.app_globals']
        translator = Translator(language, app_globals.plugin_mgr.locale_dirs())
        pylons.translator._push_object(translator)
        pylons.app_globals._push_object(app_globals)
        
        if post_vars and method.upper() != 'POST':
            raise ValueError('You must not specify post_vars for request method %r' % method)
        wsgi_environ = create_wsgi_environ('http://%s' % server_name, 
            method.upper(), request_body=post_vars)
        request = Request(wsgi_environ, charset='utf-8')
        request.language = language
        request.settings = app_globals.settings
        pylons.request._push_object(request)
        response = Response(content_type='application/xml', charset='utf-8')
        pylons.response._push_object(response)
        
        session = SessionObject(wsgi_environ)
        pylons.session._push_object(session)

        routes_url = URLGenerator(self.pylons_config['routes.map'], wsgi_environ)
        pylons.url._push_object(routes_url)

        pylons.tmpl_context._push_object(ContextObj())
        return request
    
    def remove_globals(self):
        for global_ in (pylons.request, pylons.response, pylons.session, 
                        pylons.tmpl_context, pylons.translator, pylons.url,):
            global_._pop_object()

