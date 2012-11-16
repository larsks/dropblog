#!/usr/bin/python

import os
import sys
import logging
import urllib

import bottle
from bottle import request, response, redirect, abort
import dropbox

from models import *

class decorator (object):
    pass

class content_type (decorator):
    def __init__(self, _content_type):
        self._content_type = _content_type

    def __call__(self, f):
        def _(*args, **kwargs):
            response.content_type = self._content_type
            return f(*args, **kwargs)

        return _

class route (decorator):
    '''Sets the __route__ attribute on a class method.  This is used by
    setup_routes() to configure Bottle routing on a class instance.'''

    def __init__(self, _route):
        self._route = _route

    def __call__(self, f):
        f.__route__ = self._route
        return f

class hook (decorator):
    '''Sets the __hook__ attribute on a class method.  This is used by
    setup_routes() to configure Bottle routing on a class instance.'''

    def __init__(self, _hook):
        self._hook = _hook

    def __call__(self, f):
        f.__hook__ = self._hook
        return f

class authenticated (decorator):
    def __init__(self, f):
        self.f = f
        self.log = logging.getLogger('dropblog.authenticated')

    def __call__(self, *args, **kwargs):
        if not request.session.get('authenticated'):
            self.log.info('session is not authenticated')
            redirect('/login?%s' % (
                urllib.urlencode(dict(url=request.url))))

        if not 'uid' in request.session:
            self.log.warn('session is missing uid')
            redirect('/login?%s' % (
                urllib.urlencode(dict(url=request.url))))

        uid = request.session['uid']
        user = request.db.query(User).get(uid)

        # If this happens, maybe the user has been deleted since
        # the session was authenticated.  Have them reconnect with
        # dropbox to re-create database entry.
        if user is None:
            self.log.warn('user with uid=%s not found in database', uid)
            redirect('/login?%s' % (
                urllib.urlencode(dict(url=request.url))))

        request.user = user

        request.box.set_token(
                user.dropbox_key,
                user.dropbox_secret,
                )
        request.box = dropbox.client.DropboxClient(request.box)

        return self.f(*args, **kwargs)

