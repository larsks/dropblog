#!/usr/bin/python

import os
import sys

import misaka
import dropbox

import models

def dropbox_session(db, token=None):
    app_key = db.query(models.Setting).get('app_key').value
    app_secret = db.query(models.Setting).get('app_secret').value
    access_type = db.query(models.Setting).get('access_type').value

    sess = dropbox.session.DropboxSession(
            app_key,
            app_secret,
            access_type,
            )

    if token is not None:
        sess.set_token(token.key, token.secret)

    return sess

def filter_markdown(s):
    '''Transform Markdown into HTML.'''
    return misaka.html(s,
            extensions=misaka.EXT_TABLES|misaka.EXT_NO_INTRA_EMPHASIS|misaka.EXT_AUTOLINK,
            render_flags=misaka.HTML_USE_XHTML)

def methodroute(f):
    '''Sets the __route__ attribute on a class method.  This is used by
    setup_routes() to configure Bottle routing on a class instance.'''
    def _(f):
        f.__route__ = route
        return f

    return _

def routeapp(thing):
    for kw in dir(thing):
        attr = getattr(thing, kw)
        route = getattr(attr, '__route__', None)
        if route:
            bottle.route(route, attr)

