#!/usr/bin/python

import os
import sys
import logging

from pretty import pprint,pretty

import bottle
from bottle import request, response, redirect, abort
import beaker.middleware
import beaker.cache
import beaker.util
import dropbox

import settings
from utils import route_instance
from decorators import *
from models import *

class Webapp (object):

    def __init__(self, config):
        self.config = config
        self.setup_logging()
        self.setup_cache()
        self.setup_routes()
        self.setup_models()

    def run(self):
        pass

    @route('/')
    def hello(self):
        return 'Hello, world.'

    @route('/dump')
    @content_type('text/plain')
    @authenticated
    def dump(self):
        return pretty(self.config)

    @route('/login')
    def login(self):
        return 'This is the login page.'

    @hook('before_request')
    def before_request_hook(self):
        self.log.info('before_request hook')

        request.db = Session()
        request.session = request.environ['beaker.session']
        request.box = dropbox.session.DropboxSession(
                self.config['app_key'],
                self.config['app_secret'],
                self.config['access_type'],
                )

    @hook('after_request')
    def after_request_hook(self):
        self.log.info('after_request hook')
        request.db.commit()

    def setup_models(self):
        initmodels(self.config['dburi'])

    def setup_routes(self):
        route_instance(self)

    def setup_logging(self):
        levelname = self.config.get('loglevel', 'INFO')
        level = getattr(logging, levelname)

        logging.basicConfig(
                level=level,
                format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

        self.log = logging.getLogger('dropblog')
        self.log.info('logging at level %s' % levelname)

    def setup_cache(self):
        self.log.info('cache directory is %s',
                self.config['cache']['cache.data_dir'])
        cachemgr = beaker.cache.CacheManager(
                **beaker.util.parse_cache_config_options(
                    self.config['cache']))

######################################################################

settings.load_config()
app = beaker.middleware.SessionMiddleware(
        bottle.app(),
        settings.config['session'])

DBAPP = Webapp(settings.config)

######################################################################

if __name__ == '__main__':
    bottle.run(app=app, reloader=True)

