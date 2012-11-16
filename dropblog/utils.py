#!/usr/bin/python

import os
import sys
import urllib

import bottle
import misaka
import dropbox

from models import *

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

