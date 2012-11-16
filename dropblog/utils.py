#!/usr/bin/python

import os
import sys

import bottle
import misaka
import dropbox

from models import *

def dropbox_session(db, key=None, secret=None):
    app_key = db.query(Setting).get('app_key').value
    app_secret = db.query(Setting).get('app_secret').value
    access_type = db.query(Setting).get('access_type').value

    sess = dropbox.session.DropboxSession(
            app_key,
            app_secret,
            access_type,
            )

    if key is not None and secret is not None:
        sess.set_token(key, secret)

    return sess

def dropbox_client_for(uid):
    u = Session().query(Models).get(uid)
    if not u:
        raise KeyError(uid)

    sess = dropbox_session(db, u.key, u.secret)
    return dropbox.client.DropboxClient(sess)

def filter_markdown(s):
    '''Transform Markdown into HTML.'''
    return misaka.html(s,
            extensions=misaka.EXT_TABLES|misaka.EXT_NO_INTRA_EMPHASIS|misaka.EXT_AUTOLINK,
            render_flags=misaka.HTML_USE_XHTML)

def route_instance(thing):
    for kw in dir(thing):
        attr = getattr(thing, kw)
        route = getattr(attr, '__route__', None)
        if route:
            bottle.route(route)(attr)

        hook = getattr(attr, '__hook__', None)
        if hook:
            bottle.hook(hook)(attr)

